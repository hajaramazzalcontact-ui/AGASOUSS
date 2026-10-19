"""Cycle de vie d'une réservation multi-services."""
from __future__ import annotations

from datetime import date, datetime
from typing import Iterable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.config import CANCELLATION_POLICY, IS_DEMO
from src.db.base import utcnow
from src.db.models import (
    Booking,
    BookingItem,
    BookingStatusHistory,
    Cart,
    Customer,
    Payment,
    ProviderCommission,
    ReviewInvitation,
    Setting,
    Variant,
)
from src.services.availability import release_capacity, reserve_capacity
from src.services.audit import log_action
from src.services.cart import cart_totals
from src.services.messaging import queue_message, render_message
from src.services.scoring import score_booking_request
from src.services.security import (
    encrypt_text,
    hash_identifier,
    new_public_reference,
)
from src.services.tickets import issue_ticket


class BookingError(ValueError):
    pass


def upsert_customer(
    session: Session,
    *,
    first_name: str,
    last_name: str,
    email: str,
    phone: str,
    country: str = "",
    locale: str = "fr",
    stay_start: date | None = None,
    stay_end: date | None = None,
    adults: int = 1,
    children: list[int] | None = None,
    interests: list[str] | None = None,
    accommodation_id: int | None = None,
    budget_max: float | None = None,
    source: str = "",
    special_requests: str = "",
    marketing_opt_in: bool = False,
    consent: bool = True,
) -> Customer:
    if not consent:
        raise BookingError("Le consentement explicite est obligatoire pour enregistrer la demande.")
    if not (email or phone):
        raise BookingError("Un email ou un téléphone est nécessaire pour vous recontacter.")
    email_hash = hash_identifier(email)
    phone_hash = hash_identifier(phone)
    customer = None
    if email_hash:
        customer = session.scalar(select(Customer).where(Customer.email_hash == email_hash))
    if customer is None and phone_hash:
        customer = session.scalar(select(Customer).where(Customer.phone_hash == phone_hash))
    if customer is None:
        customer = Customer(
            first_name=(first_name or "Voyageur").strip()[:100],
            last_name=(last_name or "").strip()[:100],
            email_enc=encrypt_text(email), email_hash=email_hash,
            phone_enc=encrypt_text(phone), phone_hash=phone_hash,
            country=country or None, locale=locale,
            stay_start=stay_start, stay_end=stay_end,
            adults=max(1, adults), children=children or [],
            interests=interests or [], budget_max=budget_max,
            accommodation_id=accommodation_id,
            source=source or "site",
            special_requests_enc=encrypt_text(special_requests),
            marketing_opt_in=marketing_opt_in,
            is_demo=IS_DEMO,
        )
        session.add(customer)
        session.flush()
    else:
        customer.first_name = (first_name or customer.first_name).strip()[:100]
        customer.last_name = (last_name or customer.last_name).strip()[:100]
        customer.stay_start = stay_start or customer.stay_start
        customer.stay_end = stay_end or customer.stay_end
        customer.adults = max(1, adults)
        customer.children = children or customer.children
        customer.interests = interests or customer.interests
        customer.accommodation_id = accommodation_id or customer.accommodation_id
        customer.special_requests_enc = encrypt_text(special_requests) or customer.special_requests_enc
        customer.marketing_opt_in = marketing_opt_in
    if consent:
        from src.db.models import Consent
        session.add(Consent(
            customer_id=customer.id, purpose="réservation", granted=True,
            granted_at=utcnow(), policy_version="2026-01", source="site",
        ))
    session.flush()
    return customer


def _quantity_for(item_type: str, adults: int, children: int, quantity: int) -> int:
    if item_type in {"activity", "restaurant"}:
        return max(1, int(adults or 1) + (int(children or 0) if item_type == "activity" else 0))
    return max(1, int(quantity or 1))


def _line_total(
    unit_price: float | None,
    item_type: str,
    adults: int,
    children: int,
    quantity: int,
    details: dict | None = None,
) -> float | None:
    if unit_price is None:
        return None
    if item_type in {"activity", "restaurant"}:
        pax = max(1, int(adults or 1)) + (max(0, int(children or 0)) if item_type == "activity" else 0)
        return round(float(unit_price) * pax * max(1, int(quantity or 1)), 2)
    if item_type == "accommodation":
        nights = max(1, int((details or {}).get("nights") or 1))
        return round(float(unit_price) * max(1, int(quantity or 1)) * nights, 2)
    return round(float(unit_price) * max(1, int(quantity or 1)), 2)


def create_booking_from_cart(
    session: Session,
    cart: Cart,
    customer: Customer,
    *,
    special_requests: str = "",
    consent_version: str = "2026-01",
    auto_confirm: bool | None = None,
) -> Booking:
    items = list(cart.items)
    if not items:
        raise BookingError("Le panier est vide.")
    missing = [i for i in items if i.unit_price is None]
    if auto_confirm is None:
        setting = session.get(Setting, "auto_confirm_demo")
        auto_confirm = IS_DEMO and bool(setting.value) if setting else IS_DEMO

    # Revérifier et réserver la capacité avant de créer la réservation.
    for line in items:
        if line.slot_id:
            qty = _quantity_for(line.item_type, line.adults, line.children, line.quantity)
            reserve_capacity(session, line.slot_id, qty)

    booking = Booking(
        reference=new_public_reference("AZUL"),
        customer_id=customer.id,
        status="confirmed" if (auto_confirm and not missing) else "pending",
        total_amount=None, deposit_amount=None, currency="MAD",
        source=customer.source or "site",
        special_requests=special_requests or None,
        consent_version=consent_version,
        cancellation_policy=CANCELLATION_POLICY,
        is_demo=IS_DEMO,
        confirmed_at=utcnow() if auto_confirm and not missing else None,
    )
    session.add(booking)
    session.flush()

    total = 0.0
    for line in items:
        line_total = _line_total(
            line.unit_price, line.item_type, line.adults, line.children,
            line.quantity, line.details,
        )
        if line_total is not None:
            total += line_total
        variant = session.get(Variant, line.variant_id) if line.variant_id else None
        item = BookingItem(
            booking_id=booking.id, catalog_item_id=line.catalog_item_id,
            variant_id=line.variant_id, slot_id=line.slot_id,
            item_type=line.item_type, service_date=line.service_date,
            start_at=line.start_at,
            end_at=(line.start_at + __import__("datetime").timedelta(minutes=variant.duration_minutes)
                    if line.start_at and variant and variant.duration_minutes else line.start_at),
            adults=line.adults, children=line.children, quantity=line.quantity,
            unit_price=line.unit_price, line_total=line_total,
            price_status=line.price_status,
            pickup_catalog_id=line.details.get("pickup_catalog_id") if line.details else None,
            pickup_time=line.details.get("pickup_time") if line.details else None,
            return_required=bool(line.details.get("return_required")) if line.details else False,
            details=line.details or {},
            status=booking.status,
            is_demo=IS_DEMO,
        )
        session.add(item)
        session.flush()
        # commission partenaire, informative et non facturée automatiquement
        catalog = line.catalog
        if catalog and catalog.provider_id:
            provider = catalog.provider
            rate = provider.commission_rate if provider else 0
            session.add(ProviderCommission(
                provider_id=catalog.provider_id, booking_item_id=item.id,
                gross_amount=line_total, rate=rate,
                commission_amount=round((line_total or 0) * rate / 100, 2),
                status="pending",
            ))

    booking.total_amount = round(total, 2) if total else None
    booking.deposit_amount = round((booking.total_amount or 0) * 0.2, 2) if booking.total_amount else None
    if booking.total_amount:
        session.add(Payment(
            booking_id=booking.id, payment_type="deposit",
            amount=booking.deposit_amount, status="pending", method="manual",
            due_at=utcnow(),
            note="Acompte à confirmer; aucun paiement en ligne en V1.",
        ))
    # Score explicable
    completed = session.scalar(select(func.count(Booking.id)).where(
        Booking.customer_id == customer.id, Booking.status == "completed"
    )) or 0
    cancelled = session.scalar(select(func.count(Booking.id)).where(
        Booking.customer_id == customer.id, Booking.status == "cancelled"
    )) or 0
    group = sum(max(1, (i.adults or 1) + (i.children or 0)) for i in items)
    lead = 7
    dated = [i.service_date for i in items if i.service_date]
    if dated:
        lead = (min(dated) - date.today()).days
    score, explanation = score_booking_request(booking.total_amount, lead, group, completed, cancelled)
    booking.score = score
    booking.score_explanation = explanation
    session.add(BookingStatusHistory(
        booking_id=booking.id, from_status=None, to_status=booking.status,
        note="Création depuis le panier",
    ))
    if booking.status == "confirmed":
        issue_ticket(session, booking)
    message = render_message(
        "Bonjour {prenom}, votre demande {reference} est enregistrée. "
        "Les prix et horaires définitifs seront confirmés par un humain.",
        customer, reference=booking.reference,
    )
    queue_message(
        session, customer=customer, channel="email",
        subject=f"Votre demande Azul AGADIR {booking.reference}",
        body=message, booking_id=booking.id, template_code="confirmation",
    )
    for line in items:
        session.delete(line)
    cart.status = "converted"
    session.flush()
    log_action(session, None, "create_booking", "booking", booking.id, {"demo": IS_DEMO})
    return booking


def confirm_booking(session: Session, booking_id: int, actor_id: int | None = None) -> Booking:
    booking = session.get(Booking, booking_id)
    if not booking:
        raise BookingError("Réservation introuvable.")
    if booking.status == "cancelled":
        raise BookingError("Une réservation annulée ne peut pas être confirmée.")
    previous = booking.status
    booking.status = "confirmed"
    booking.confirmed_at = utcnow()
    for item in booking.items:
        item.status = "confirmed"
    issue_ticket(session, booking)
    session.add(BookingStatusHistory(
        booking_id=booking.id, from_status=previous, to_status="confirmed",
        actor_id=actor_id, note="Confirmation humaine",
    ))
    log_action(session, actor_id, "confirm_booking", "booking", booking.id)
    session.flush()
    return booking


def mark_deposit_received(session: Session, booking_id: int, actor_id: int | None = None) -> Booking:
    booking = session.get(Booking, booking_id)
    if not booking:
        raise BookingError("Réservation introuvable.")
    previous = booking.status
    booking.status = "deposit_received"
    payment = session.scalar(select(Payment).where(
        Payment.booking_id == booking_id, Payment.payment_type == "deposit"
    ))
    if payment:
        payment.status = "received"
        payment.received_at = utcnow()
        payment.recorded_by = actor_id
    else:
        session.add(Payment(
            booking_id=booking.id, payment_type="deposit",
            amount=booking.deposit_amount, status="received", method="manual",
            received_at=utcnow(), recorded_by=actor_id,
        ))
    session.add(BookingStatusHistory(
        booking_id=booking.id, from_status=previous, to_status="deposit_received",
        actor_id=actor_id, note="Acompte reçu (saisie manuelle)",
    ))
    log_action(session, actor_id, "deposit_received", "booking", booking.id)
    session.flush()
    return booking


def cancel_booking(session: Session, booking_id: int, reason: str, actor_id: int | None = None) -> Booking:
    booking = session.get(Booking, booking_id)
    if not booking:
        raise BookingError("Réservation introuvable.")
    previous = booking.status
    booking.status = "cancelled"
    booking.cancelled_at = utcnow()
    for item in booking.items:
        if item.slot_id:
            release_capacity(
                session, item.slot_id,
                _quantity_for(item.item_type, item.adults, item.children, item.quantity),
            )
        item.status = "cancelled"
    session.add(BookingStatusHistory(
        booking_id=booking.id, from_status=previous, to_status="cancelled",
        actor_id=actor_id, note=reason[:1000],
    ))
    log_action(session, actor_id, "cancel_booking", "booking", booking.id, {"reason": reason})
    session.flush()
    return booking


def complete_booking(session: Session, booking_id: int, actor_id: int | None = None) -> Booking:
    booking = session.get(Booking, booking_id)
    if not booking:
        raise BookingError("Réservation introuvable.")
    previous = booking.status
    booking.status = "completed"
    booking.completed_at = utcnow()
    for item in booking.items:
        item.status = "completed"
        existing = session.scalar(select(ReviewInvitation).where(ReviewInvitation.booking_item_id == item.id))
        if not existing:
            from datetime import timedelta
            base = item.end_at or item.start_at or utcnow()
            session.add(ReviewInvitation(
                booking_item_id=item.id, channel="whatsapp",
                scheduled_at=base + timedelta(hours=24),
                status="scheduled", is_demo=bool(booking.is_demo),
            ))
    session.add(BookingStatusHistory(
        booking_id=booking.id, from_status=previous, to_status="completed",
        actor_id=actor_id, note="Prestation terminée",
    ))
    log_action(session, actor_id, "complete_booking", "booking", booking.id)
    session.flush()
    return booking


def bookings_for_customer(session: Session, customer_id: int) -> list[Booking]:
    return list(session.scalars(
        select(Booking).where(Booking.customer_id == customer_id).order_by(Booking.created_at.desc())
    ).all())


def get_booking_by_reference(session: Session, reference: str) -> Booking | None:
    return session.scalar(select(Booking).where(Booking.reference == reference.strip()))
