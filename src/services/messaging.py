"""Messages préparés, validés puis seulement ensuite envoyés.

Aucun email, SMS ou WhatsApp n'est envoyé par l'application de démonstration.
Les adaptateurs réels sont prévus derrière cette interface.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.base import utcnow
from src.db.models import Customer, MessageTemplate, OutboxMessage
from src.services.security import encrypt_text


DEFAULT_TEMPLATES = {
    "confirmation": {
        "subject": "Votre demande Azul AGADIR {reference}",
        "body": "Bonjour {prenom},\n\nVotre demande {reference} est bien enregistrée. "
                "Notre équipe vous confirmera les prix, horaires et détails pratiques.\n\n"
                "Merci,\nL'équipe Azul AGADIR",
    },
    "rappel": {
        "subject": "Rappel : votre expérience Azul AGADIR demain",
        "body": "Bonjour {prenom},\n\nPetit rappel pour votre expérience de demain. "
                "Le point de prise en charge et l'heure confirmée vous seront communiqués la veille.\n\n"
                "Azul AGADIR",
    },
    "demande_avis": {
        "subject": "Votre avis compte pour Azul AGADIR",
        "body": "Bonjour {prenom},\n\nMerci pour votre expérience. Vous pouvez laisser un avis vérifié "
                "depuis votre espace Azul AGADIR.\n\nMerci,\nL'équipe Azul AGADIR",
    },
    "relance_acompte": {
        "subject": "Votre acompte pour la réservation {reference}",
        "body": "Bonjour {prenom},\n\nVotre réservation {reference} est en attente d'acompte. "
                "Contactez-nous si vous avez besoin d'aide.\n\nAzul AGADIR",
    },
}


def render_message(template: str, customer: Customer | None = None, **context) -> str:
    values = {
        "prenom": customer.first_name if customer else "voyageur",
        "nom": customer.last_name if customer else "",
        **context,
    }
    try:
        return template.format(**values)
    except KeyError:
        return template


def ensure_default_templates(session: Session, actor_id: int | None = None) -> None:
    existing = {t.code for t in session.scalars(select(MessageTemplate)).all()}
    for code, content in DEFAULT_TEMPLATES.items():
        if code in existing:
            continue
        session.add(MessageTemplate(
            code=code, channel="email", locale="fr", subject=content["subject"],
            body=content["body"], is_approved=False, updated_at=utcnow(),
        ))
    session.flush()


def queue_message(
    session: Session,
    *,
    customer: Customer | None,
    channel: str,
    subject: str,
    body: str,
    booking_id: int | None = None,
    template_code: str | None = None,
    scheduled_at: datetime | None = None,
) -> OutboxMessage:
    recipient = None
    if customer:
        from src.services.security import decrypt_text
        recipient = decrypt_text(customer.email_enc) or decrypt_text(customer.phone_enc)
    message = OutboxMessage(
        booking_id=booking_id, customer_id=customer.id if customer else None,
        template_code=template_code, channel=channel,
        recipient_enc=encrypt_text(recipient), subject=subject, body=body,
        status="draft", scheduled_at=scheduled_at,
    )
    session.add(message)
    session.flush()
    return message


def approve_message(session: Session, message_id: int, actor_id: int) -> OutboxMessage:
    message = session.get(OutboxMessage, message_id)
    if not message:
        raise ValueError("Message introuvable.")
    message.status = "approved"
    message.approved_by = actor_id
    message.approved_at = utcnow()
    from .audit import log_action
    log_action(session, actor_id, "approve_message", "outbox", message.id)
    session.flush()
    return message


def mark_sent(session: Session, message_id: int) -> OutboxMessage:
    message = session.get(OutboxMessage, message_id)
    if not message or message.status != "approved":
        raise ValueError("Le message doit être validé par un humain avant tout envoi.")
    # Adaptateur de démonstration : aucun réseau. Brancher WhatsApp Cloud API,
    # SMTP ou un fournisseur SMS ici, après validation explicite.
    message.status = "sent"
    message.sent_at = utcnow()
    session.flush()
    return message
