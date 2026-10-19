"""Résumés et détections d'anomalies pour le gérant."""
from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models import Anomaly, Booking, CatalogItem, Review
from src.services.analytics import dashboard_metrics
from src.services.reviews import review_ai_summary
from .client import complete, is_available

SYSTEM = """Tu résumes des données de gestion pour Azul AGADIR.
Tu ne dois rien inventer. Tu cites uniquement les chiffres fournis.
Tu proposes des actions concrètes, sans modifier aucune donnée.
"""


def daily_brief(session: Session) -> str:
    metrics = dashboard_metrics(session)
    text = (
        f"Bonjour. Aujourd'hui : {metrics['today_bookings']} réservation(s) au programme, "
        f"{metrics['pending']} demande(s) en attente, {metrics['awaiting_deposit']} acompte(s) à relancer. "
        f"Chiffre d'affaires confirmé (DÉMO) : {metrics['revenue']:,.0f} MAD. "
        f"Note moyenne vérifiée : {metrics['rating']['average']}/5 sur {metrics['rating']['count']} avis. "
        f"{metrics['anomalies']} anomalie(s) ouverte(s)."
    ).replace(",", " ")
    if not is_available():
        return text
    ai = complete(SYSTEM, text + "\nReformule en 3 phrases maximum, avec 2 actions prioritaires.", max_tokens=220)
    return ai or text


def summary_for_reviews(session: Session, catalog_id: int | None = None) -> str:
    stmt = select(Review).where(Review.status == "published", Review.verified.is_(True))
    if catalog_id:
        stmt = stmt.where(Review.catalog_item_id == catalog_id)
    reviews = list(session.scalars(stmt).all())
    data = review_ai_summary(reviews)
    base = (
        f"{data['count']} avis publiés, moyenne {data['average']}/5.\n"
        f"{data['strengths']}\n{data['improvements']}"
    )
    if not is_available():
        return base
    ai = complete(SYSTEM, base + "\nRésume en 2 phrases, sans déformer les avis.", max_tokens=180)
    return ai or base


def detect_anomalies(session: Session) -> list[Anomaly]:
    """Contrôles simples, idempotents, sans supprimer aucune donnée."""
    today = date.today()
    created: list[Anomaly] = []
    existing = {a.anomaly_type for a in session.scalars(select(Anomaly)).all() if a.status == "open"}
    # Acomptes en attente depuis plus de 24 h
    for booking in session.scalars(select(Booking)).all():
        if booking.status == "pending" and booking.created_at and (today - booking.created_at.date()).days >= 1:
            if "acompte_non_paye" not in existing:
                created.append(Anomaly(
                    anomaly_type="acompte_non_paye", severity="high",
                    entity_type="booking", entity_id=booking.id,
                    details={"reference": booking.reference, "age_days": (today - booking.created_at.date()).days},
                ))
                existing.add("acompte_non_paye")
    # Fiches sans prix
    missing = session.scalar(select(CatalogItem).where(
        CatalogItem.price_from.is_(None), CatalogItem.kind.notin_(["spot"])
    ))
    if missing and "prix_manquant" not in existing:
        created.append(Anomaly(
            anomaly_type="prix_manquant", severity="info", entity_type="catalog",
            entity_id=missing.id, details={"note": "Prix à renseigner par le gestionnaire."},
        ))
    for anomaly in created:
        session.add(anomaly)
    session.flush()
    return created
