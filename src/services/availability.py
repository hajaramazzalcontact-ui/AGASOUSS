"""Gestion des créneaux et des capacités.

Le stock n'est jamais supposé disponible : chaque ajout au panier et chaque
confirmation revérifie la capacité restante.
"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models import AvailabilitySlot, Variant


class AvailabilityError(ValueError):
    """Créneau fermé, complet ou quantité invalide."""


def remaining_capacity(slot: AvailabilitySlot) -> int:
    if slot is None:
        return 0
    return max(0, int(slot.capacity or 0) - int(slot.booked_count or 0))


def can_book(slot: AvailabilitySlot | None, quantity: int = 1) -> bool:
    if slot is None or quantity <= 0:
        return False
    if slot.status not in {"open", None}:
        return False
    if slot.start_at and slot.start_at < datetime.now():
        return False
    return remaining_capacity(slot) >= quantity


def get_slot(session: Session, slot_id: int) -> AvailabilitySlot | None:
    return session.get(AvailabilitySlot, slot_id)


def available_slots(
    session: Session,
    variant_id: int,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = 100,
) -> list[AvailabilitySlot]:
    stmt = select(AvailabilitySlot).where(AvailabilitySlot.variant_id == variant_id)
    if date_from:
        stmt = stmt.where(AvailabilitySlot.start_at >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        stmt = stmt.where(AvailabilitySlot.start_at <= datetime.combine(date_to, datetime.max.time()))
    stmt = stmt.order_by(AvailabilitySlot.start_at).limit(limit)
    slots = list(session.scalars(stmt).all())
    now = datetime.now()
    return [s for s in slots if s.status == "open" and s.start_at >= now and remaining_capacity(s) > 0]


def reserve_capacity(session: Session, slot_id: int, quantity: int) -> AvailabilitySlot:
    """Réserve atomiquement une capacité et renvoie le créneau actualisé.

    SQLite sérialise les écritures ; la vérification est refaite après
    verrouillage pour éviter la surréservation.
    """
    if quantity <= 0:
        raise AvailabilityError("La quantité doit être positive.")
    slot = session.scalar(
        select(AvailabilitySlot).where(AvailabilitySlot.id == slot_id).with_for_update()
    )
    if slot is None:
        raise AvailabilityError("Créneau introuvable.")
    if not can_book(slot, quantity):
        raise AvailabilityError("Ce créneau n'est plus disponible pour cette quantité.")
    slot.booked_count = int(slot.booked_count or 0) + quantity
    if remaining_capacity(slot) == 0:
        slot.status = "full"
    session.flush()
    return slot


def release_capacity(session: Session, slot_id: int, quantity: int) -> None:
    slot = session.get(AvailabilitySlot, slot_id)
    if not slot:
        return
    slot.booked_count = max(0, int(slot.booked_count or 0) - max(0, int(quantity)))
    if slot.booked_count < slot.capacity and slot.status == "full":
        slot.status = "open"
    session.flush()


def choose_variant(session: Session, variant_id: int) -> Variant | None:
    return session.get(Variant, variant_id)
