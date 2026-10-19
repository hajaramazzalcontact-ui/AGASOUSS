"""Panier multi-services et calcul des totaux.

Règle absolue : un prix inconnu n'est jamais remplacé par un prix inventé.
Le panier affiche alors « à confirmer » et bloque le paiement automatique.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models import AvailabilitySlot, Cart, CartItem, CatalogItem, Variant
from src.services.availability import can_book
from src.services.security import new_cart_token


def get_or_create_cart(session: Session, token: str | None = None, customer_id: int | None = None) -> Cart:
    cart = None
    if token:
        cart = session.scalar(select(Cart).where(Cart.token == token, Cart.status == "open"))
    if cart is None:
        cart = Cart(token=token or new_cart_token(), customer_id=customer_id, status="open")
        session.add(cart)
        session.flush()
    elif customer_id and not cart.customer_id:
        cart.customer_id = customer_id
    return cart


def add_item(
    session: Session,
    cart: Cart,
    catalog_id: int,
    *,
    variant_id: int | None = None,
    slot_id: int | None = None,
    item_type: str = "activity",
    service_date: date | None = None,
    start_at: datetime | None = None,
    adults: int = 1,
    children: int = 0,
    quantity: int = 1,
    details: dict | None = None,
) -> CartItem:
    item = session.get(CatalogItem, catalog_id)
    if not item:
        raise ValueError("Fiche introuvable.")
    variant = session.get(Variant, variant_id) if variant_id else None
    slot = session.get(AvailabilitySlot, slot_id) if slot_id else None
    if slot and not can_book(slot, max(1, quantity)):
        raise ValueError("Ce créneau n'est plus disponible.")

    unit_price = None
    price_status = "missing"
    if slot and slot.price_override is not None:
        unit_price = float(slot.price_override)
        price_status = item.price_status if item.price_status == "demo" else "confirmed"
    elif variant and variant.price is not None:
        unit_price = float(variant.price)
        price_status = variant.price_status or item.price_status or "missing"
    elif item.price_from is not None:
        unit_price = float(item.price_from)
        price_status = item.price_status or "missing"

    cart_item = CartItem(
        cart_id=cart.id,
        catalog_item_id=catalog_id,
        variant_id=variant.id if variant else None,
        slot_id=slot.id if slot else None,
        item_type=item_type or item.kind,
        service_date=service_date or (slot.start_at.date() if slot else None),
        start_at=start_at or (slot.start_at if slot else None),
        adults=max(1, adults), children=max(0, children), quantity=max(1, quantity),
        unit_price=unit_price, price_status=price_status,
        details=details or {},
    )
    session.add(cart_item)
    session.flush()
    return cart_item


def cart_totals(items: list[CartItem]) -> dict:
    known_total = 0.0
    unknown = 0
    lines = 0
    for line in items:
        lines += 1
        if line.unit_price is None:
            unknown += 1
        else:
            multiplier = max(1, int(line.quantity or 1))
            # Pour une activité, le prix est par personne ; pour un transport,
            # il peut être par véhicule. Le détail de la ligne porte l'unité.
            if line.item_type in {"activity", "restaurant"}:
                multiplier *= max(1, int(line.adults or 1)) + (
                    max(0, int(line.children or 0)) if line.item_type == "activity" else 0
                )
            if line.item_type == "accommodation" and line.details:
                multiplier *= max(1, int(line.details.get("nights") or 1))
            known_total += float(line.unit_price) * multiplier
    return {
        "lines": lines,
        "known_total": round(known_total, 2),
        "unknown_count": unknown,
        "all_prices_known": unknown == 0 and lines > 0,
        "currency": "MAD",
        "has_items": lines > 0,
    }


def remove_item(session: Session, cart_id: int, item_id: int) -> bool:
    item = session.get(CartItem, item_id)
    if item and item.cart_id == cart_id:
        session.delete(item)
        session.flush()
        return True
    return False


def clear_cart(session: Session, cart: Cart) -> None:
    for item in list(cart.items):
        session.delete(item)
    cart.status = "converted"
    session.flush()
