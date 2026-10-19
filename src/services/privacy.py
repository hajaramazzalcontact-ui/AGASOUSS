"""Droits des personnes : accès, rectification, suppression, minimisation."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.base import utcnow
from src.db.models import Booking, Consent, Customer, OutboxMessage, Review
from src.services.audit import log_action
from src.services.security import decrypt_text, encrypt_text, hash_identifier


def customer_export(session: Session, customer_id: int) -> dict:
    customer = session.get(Customer, customer_id)
    if not customer:
        raise ValueError("Client introuvable.")
    bookings = list(session.scalars(select(Booking).where(Booking.customer_id == customer_id)).all())
    consents = list(session.scalars(select(Consent).where(Consent.customer_id == customer_id)).all())
    reviews = list(session.scalars(select(Review).where(Review.customer_id == customer_id)).all())
    return {
        "identite": {
            "prenom": customer.first_name, "nom": customer.last_name,
            "email": decrypt_text(customer.email_enc), "telephone": decrypt_text(customer.phone_enc),
            "pays": customer.country, "langue": customer.locale,
            "sejour": [str(customer.stay_start or ""), str(customer.stay_end or "")],
            "adultes": customer.adults, "enfants": customer.children,
            "interets": customer.interests, "source": customer.source,
            "demandes_particulieres": decrypt_text(customer.special_requests_enc),
        },
        "consentements": [
            {"finalite": c.purpose, "accorde": c.granted, "version": c.policy_version,
             "date": str(c.granted_at or ""), "retire": str(c.revoked_at or "")}
            for c in consents
        ],
        "reservations": [
            {"reference": b.reference, "statut": b.status, "total": b.total_amount,
             "date": str(b.created_at or "")}
            for b in bookings
        ],
        "avis": [
            {"note": r.rating, "commentaire": r.comment, "statut": r.status,
             "date": str(r.created_at or "")}
            for r in reviews
        ],
    }


def anonymize_customer(session: Session, customer_id: int, actor_id: int | None = None) -> Customer:
    """Anonymise les coordonnées tout en conservant les obligations comptables.

    Les réservations restent liées à un identifiant anonyme. Les avis publiés
    peuvent être conservés sans identité, conformément à la politique de
    modération ; les données de contact sont supprimées.
    """
    customer = session.get(Customer, customer_id)
    if not customer:
        raise ValueError("Client introuvable.")
    customer.first_name = "Client"
    customer.last_name = "anonymisé"
    customer.email_enc = None
    customer.email_hash = None
    customer.phone_enc = None
    customer.phone_hash = None
    customer.special_requests_enc = None
    customer.notes = None
    customer.anonymized_at = utcnow()
    for consent in session.scalars(select(Consent).where(Consent.customer_id == customer_id)).all():
        consent.revoked_at = utcnow()
    for message in session.scalars(select(OutboxMessage).where(OutboxMessage.customer_id == customer_id)).all():
        message.recipient_enc = None
        message.status = "cancelled" if message.status == "draft" else message.status
    log_action(session, actor_id, "anonymize_customer", "customer", customer_id)
    session.flush()
    return customer


def withdraw_consent(session: Session, customer_id: int, purpose: str) -> None:
    rows = session.scalars(select(Consent).where(
        Consent.customer_id == customer_id, Consent.purpose == purpose, Consent.revoked_at.is_(None)
    )).all()
    for row in rows:
        row.revoked_at = utcnow()
        row.granted = False
    session.flush()


def update_contact(session: Session, customer_id: int, *, email: str | None = None, phone: str | None = None) -> Customer:
    customer = session.get(Customer, customer_id)
    if not customer:
        raise ValueError("Client introuvable.")
    if email is not None:
        customer.email_enc = encrypt_text(email)
        customer.email_hash = hash_identifier(email)
    if phone is not None:
        customer.phone_enc = encrypt_text(phone)
        customer.phone_hash = hash_identifier(phone)
    session.flush()
    return customer
