"""Rédaction assistée des messages, toujours validée par un humain."""
from __future__ import annotations

from src.db.models import Booking, Customer
from src.services.catalog import localized
from .client import complete, is_available
from .guardrails import redact_pii

SYSTEM = """Tu rédiges des messages clients pour Azul AGADIR.
Tu ne dois jamais inventer de prix, d'horaire, de disponibilité ou de garantie.
Tu reprends uniquement les faits fournis. Ton chaleureux, clair, concis.
Le message est un brouillon : un humain doit le valider avant envoi.
"""


def _facts(booking: Booking | None, locale: str = "fr") -> str:
    if not booking:
        return "Aucune réservation fournie."
    items = []
    for item in booking.items:
        items.append(f"{localized(item.catalog.name, locale)} — {item.service_date or 'date à confirmer'} — "
                     f"{item.line_total if item.line_total is not None else 'prix à confirmer'} MAD")
    return (
        f"Référence: {booking.reference}\nStatut: {booking.status}\n"
        f"Total connu: {booking.total_amount if booking.total_amount is not None else 'à confirmer'} MAD\n"
        f"Prestations: {'; '.join(items)}\n"
        f"Mode démo: {booking.is_demo}"
    )


def generate_message(
    kind: str,
    customer: Customer | None,
    booking: Booking | None = None,
    locale: str = "fr",
    extra: str = "",
) -> str:
    name = customer.first_name if customer else "voyageur"
    if kind == "rappel":
        local = (
            f"Azul {name},\n\nPetit rappel pour votre expérience Azul AGADIR. "
            "L'heure et le lieu de prise en charge confirmés vous seront transmis la veille. "
            "Si vous avez un doute, répondez à ce message.\n\nL'équipe Azul AGADIR"
        )
    elif kind == "demande_avis":
        local = (
            f"Azul {name},\n\nMerci d'avoir voyagé avec Azul AGADIR. "
            "Vous pouvez laisser un avis vérifié depuis votre espace. "
            "Chaque retour nous aide à améliorer l'expérience, sans jamais modifier les avis.\n\nL'équipe Azul AGADIR"
        )
    elif kind == "relance_acompte":
        ref = booking.reference if booking else "votre réservation"
        local = (
            f"Azul {name},\n\nVotre réservation {ref} est en attente d'acompte. "
            "Aucun paiement en ligne n'est activé dans cette démonstration. "
            "Contactez l'équipe pour connaître les modalités exactes.\n\nAzul AGADIR"
        )
    else:
        ref = booking.reference if booking else ""
        local = (
            f"Azul {name},\n\nVotre demande {ref} est bien enregistrée. "
            "Les prix, horaires et détails pratiques seront confirmés par un humain. "
            "Aucune information non vérifiée ne vous sera transmise.\n\nL'équipe Azul AGADIR"
        )
    if not is_available():
        return local
    facts = _facts(booking, locale) + "\n" + redact_pii(extra)
    ai = complete(
        SYSTEM,
        f"Langue: {locale}\nType de message: {kind}\nFaits vérifiés:\n{facts}\n"
        f"Rédige un brouillon de message, sans ajouter de fait. Maximum 130 mots.",
        max_tokens=300,
    )
    return ai or local
