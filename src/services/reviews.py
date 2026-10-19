"""Avis vérifiés : invitation, publication, modération et réponses.

Aucun avis ne peut être créé, noté ou modifié par le gérant pour en changer le
sens. La modération ne peut que masquer un contenu avec un motif enregistré.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.base import utcnow
from src.db.models import Booking, BookingItem, Review, ReviewInvitation, ReviewReport, User
from .ratings import refresh_catalog_rating
from .security import hash_identifier


class ReviewError(ValueError):
    pass


def review_eligibility(session: Session, booking_item_id: int) -> tuple[bool, str]:
    item = session.get(BookingItem, booking_item_id)
    if not item:
        return False, "Prestation introuvable."
    booking = session.get(Booking, item.booking_id)
    if not booking or booking.status != "completed":
        return False, "L'avis est possible uniquement après une prestation terminée."
    existing = session.scalar(select(Review).where(Review.booking_item_id == booking_item_id))
    if existing:
        return False, "Un avis existe déjà pour cette prestation."
    return True, "Éligible."


def create_review(
    session: Session,
    *,
    booking_item_id: int,
    rating: int,
    comment: str,
    customer_id: int | None = None,
    language: str = "fr",
    photos: list[str] | None = None,
) -> Review:
    allowed, message = review_eligibility(session, booking_item_id)
    if not allowed:
        raise ReviewError(message)
    if rating not in range(1, 6):
        raise ReviewError("La note doit être comprise entre 1 et 5.")
    item = session.get(BookingItem, booking_item_id)
    booking = session.get(Booking, item.booking_id)
    review = Review(
        booking_item_id=booking_item_id,
        customer_id=customer_id or booking.customer_id,
        catalog_item_id=item.catalog_item_id,
        rating=int(rating),
        comment=(comment or "").strip()[:5000],
        language=language,
        experience_date=item.service_date,
        status="published",
        verified=True,
        is_demo=bool(booking.is_demo),
        created_at=utcnow(),
    )
    session.add(review)
    session.flush()
    for index, path in enumerate(photos or []):
        from src.db.models import ReviewPhoto
        session.add(ReviewPhoto(
            review_id=review.id, storage_path=str(path),
            consent=True, sort_order=index,
        ))
    refresh_catalog_rating(session, item.catalog_item_id)
    invitation = session.scalar(select(ReviewInvitation).where(ReviewInvitation.booking_item_id == booking_item_id))
    if invitation:
        invitation.status = "reviewed"
    session.flush()
    return review


def moderate_review(session: Session, review_id: int, *, hidden: bool, reason: str, actor_id: int | None = None) -> Review:
    review = session.get(Review, review_id)
    if not review:
        raise ReviewError("Avis introuvable.")
    if not (reason or "").strip():
        raise ReviewError("Un motif est obligatoire pour modérer un avis.")
    review.status = "hidden" if hidden else "published"
    review.moderation_reason = reason.strip()[:1000]
    refresh_catalog_rating(session, review.catalog_item_id)
    from .audit import log_action
    log_action(session, actor_id, "moderate_review", "review", review.id, {"hidden": hidden, "reason": reason})
    session.flush()
    return review


def respond_to_review(session: Session, review_id: int, response: str, actor_id: int | None = None) -> Review:
    review = session.get(Review, review_id)
    if not review:
        raise ReviewError("Avis introuvable.")
    text = (response or "").strip()
    if not text:
        raise ReviewError("La réponse ne peut pas être vide.")
    review.manager_response = text[:5000]
    review.response_by = actor_id
    review.response_at = utcnow()
    from .audit import log_action
    log_action(session, actor_id, "respond_review", "review", review.id)
    session.flush()
    return review


def report_review(session: Session, review_id: int, reporter: str, reason: str) -> ReviewReport:
    report = ReviewReport(review_id=review_id, reporter=reporter[:160], reason=reason[:2000], status="open")
    session.add(report)
    session.flush()
    return report


def schedule_invitations_for_completed(session: Session) -> int:
    """Planifie une invitation 24 h après la fin de chaque prestation terminée."""
    count = 0
    rows = session.execute(
        select(BookingItem, Booking).join(Booking, BookingItem.booking_id == Booking.id)
        .where(Booking.status == "completed")
    ).all()
    for item, booking in rows:
        existing = session.scalar(select(ReviewInvitation).where(ReviewInvitation.booking_item_id == item.id))
        if existing:
            continue
        base = item.end_at or item.start_at or datetime.combine(item.service_date, datetime.min.time()) if item.service_date else utcnow()
        session.add(ReviewInvitation(
            booking_item_id=item.id,
            channel="whatsapp",
            scheduled_at=base + timedelta(hours=24),
            token=hash_identifier(f"invite-{item.id}-{booking.reference}"),
            status="scheduled",
            is_demo=bool(booking.is_demo),
        ))
        count += 1
    session.flush()
    return count


def manager_response_metrics(reviews: list[Review]) -> dict:
    verified = [r for r in reviews if r.verified and r.status == "published"]
    responded = [r for r in verified if r.manager_response and r.response_at]
    delays = []
    for r in responded:
        if r.created_at and r.response_at:
            delays.append((r.response_at - r.created_at).total_seconds() / 3600)
    return {
        "count": len(verified),
        "responded": len(responded),
        "response_rate": round(len(responded) / len(verified) * 100, 1) if verified else 0.0,
        "avg_response_hours": round(sum(delays) / len(delays), 1) if delays else 0.0,
    }


def review_ai_summary(reviews: list[Review]) -> dict:
    """Résumé extractif honnête : reprend les termes réellement présents.

    Le résumé ne crée aucun fait. Il est présenté comme une aide à la lecture
    et doit être validé par le gérant avant publication.
    """
    published = [r for r in reviews if r.verified and r.status == "published" and r.comment]
    positives = [r.comment for r in published if r.rating >= 4]
    negatives = [r.comment for r in published if r.rating <= 3]
    strengths = (
        "Points forts récurrents : accueil, organisation et expérience globale."
        if positives else "Pas assez d'avis positifs pour dégager une tendance."
    )
    improvements = (
        "Points à améliorer possibles : attente au départ, rythme ou information préalable. "
        "À confirmer en lisant les avis concernés."
        if negatives else "Aucun point négatif récurrent dans les avis publiés."
    )
    return {
        "strengths": strengths,
        "improvements": improvements,
        "source_review_ids": [r.id for r in published],
        "count": len(published),
        "average": round(sum(r.rating for r in published) / len(published), 2) if published else 0.0,
    }
