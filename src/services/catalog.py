"""Catalogue : lecture, recherche, filtres, prix et disponibilités."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Iterable

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from src.db.models import (
    AccommodationDetail,
    ActivityDetail,
    AvailabilitySlot,
    CatalogItem,
    RestaurantDetail,
    Review,
    SpotDetail,
    TransportDetail,
    Variant,
)

VIBE_ORDER = ["aventure", "famille", "culture", "nature", "mer", "gastronomie", "detente", "jeux"]
KIND_LABELS = {
    "activity": {"fr": "Activité", "en": "Activity", "ar": "نشاط", "es": "Actividad"},
    "restaurant": {"fr": "Restaurant", "en": "Restaurant", "ar": "مطعم", "es": "Restaurante"},
    "accommodation": {"fr": "Hébergement", "en": "Stay", "ar": "إقامة", "es": "Alojamiento"},
    "spot": {"fr": "Spot & plage", "en": "Spot & beach", "ar": "موقع وشاطئ", "es": "Lugar y playa"},
    "transport": {"fr": "Transport", "en": "Transport", "ar": "نقل", "es": "Transporte"},
}
PRICE_UNIT_LABELS = {
    "personne": {"fr": "par personne", "en": "per person", "ar": "للشخص", "es": "por persona"},
    "nuit": {"fr": "par nuit", "en": "per night", "ar": "لليلة", "es": "por noche"},
    "véhicule": {"fr": "par véhicule", "en": "per vehicle", "ar": "للمركبة", "es": "por vehículo"},
    "course": {"fr": "par course", "en": "per ride", "ar": "للرحلة", "es": "por trayecto"},
}


def localized(value: Any, locale: str = "fr") -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return str(value.get(locale) or value.get("fr") or next(iter(value.values()), ""))
    if isinstance(value, (list, tuple)):
        return " · ".join(localized(v, locale) for v in value if v)
    return str(value)


def kind_label(kind: str, locale: str = "fr") -> str:
    return localized(KIND_LABELS.get(kind, {}), locale) or kind


def price_unit_label(unit: str | None, locale: str = "fr") -> str:
    return localized(PRICE_UNIT_LABELS.get(unit or "", {}), locale) or (unit or "")


def money(value: float | None, demo: bool = False) -> str:
    if value is None:
        return "—"
    txt = f"{value:,.0f}".replace(",", " ") + " MAD"
    return f"{txt} (DÉMO)" if demo else txt


def display_price(item: CatalogItem, locale: str = "fr") -> str:
    if item.price_from is None:
        return "Tarif à confirmer" if locale == "fr" else {
            "en": "Price on request", "ar": "السعر عند الطلب", "es": "Precio a confirmar"
        }.get(locale, "Price on request")
    unit = price_unit_label(item.price_unit, locale)
    suffix = " (DÉMO)" if item.price_status == "demo" else ""
    return f"dès {money(item.price_from, False)} {unit}{suffix}"


def all_items(session: Session, kind: str | None = None) -> list[CatalogItem]:
    stmt = select(CatalogItem).where(CatalogItem.status == "published")
    if kind:
        stmt = stmt.where(CatalogItem.kind == kind)
    return list(session.scalars(stmt.order_by(CatalogItem.name)).all())


def get_item(session: Session, item_id: int) -> CatalogItem | None:
    return session.get(CatalogItem, item_id)


def get_by_slug(session: Session, slug: str) -> CatalogItem | None:
    return session.scalar(select(CatalogItem).where(CatalogItem.slug == slug))


def detail_for(session: Session, item: CatalogItem):
    mapping = {
        "activity": ActivityDetail,
        "restaurant": RestaurantDetail,
        "accommodation": AccommodationDetail,
        "spot": SpotDetail,
        "transport": TransportDetail,
    }
    model = mapping.get(item.kind)
    return session.get(model, item.id) if model else None


def variants_for(session: Session, item_id: int) -> list[Variant]:
    return list(session.scalars(
        select(Variant).where(Variant.catalog_id == item_id, Variant.is_active.is_(True)).order_by(Variant.sort_order)
    ).all())


def slots_for(session: Session, variant_id: int, days: int = 45, limit: int = 120) -> list[AvailabilitySlot]:
    now = datetime.now()
    end = now + timedelta(days=days)
    slots = list(session.scalars(
        select(AvailabilitySlot)
        .where(
            AvailabilitySlot.variant_id == variant_id,
            AvailabilitySlot.start_at >= now,
            AvailabilitySlot.start_at <= end,
            AvailabilitySlot.status == "open",
        )
        .order_by(AvailabilitySlot.start_at).limit(limit)
    ).all())
    return [s for s in slots if (s.capacity or 0) - (s.booked_count or 0) > 0]


def item_reviews(session: Session, item_id: int, limit: int | None = None) -> list[Review]:
    stmt = select(Review).where(
        Review.catalog_item_id == item_id,
        Review.status == "published",
        Review.verified.is_(True),
    ).order_by(Review.created_at.desc())
    if limit:
        stmt = stmt.limit(limit)
    return list(session.scalars(stmt).all())


def recent_reviews(session: Session, limit: int = 6) -> list[Review]:
    return list(session.scalars(
        select(Review).where(Review.status == "published", Review.verified.is_(True))
        .order_by(Review.created_at.desc()).limit(limit)
    ).all())


def search_items(
    session: Session,
    *,
    kind: str | None = None,
    query: str = "",
    vibes: Iterable[str] | None = None,
    max_price: float | None = None,
    max_distance: float | None = None,
    min_rating: float | None = None,
    family: bool = False,
    duration_max: int | None = None,
    locale: str = "fr",
) -> list[CatalogItem]:
    items = all_items(session, kind)
    q = (query or "").strip().lower()
    selected_vibes = set(vibes or [])
    results: list[CatalogItem] = []
    for item in items:
        haystack = " ".join([
            localized(item.name, locale), localized(item.name, "fr"),
            localized(item.tagline, locale), localized(item.short_description, locale),
            localized(item.tags, locale), localized(item.district, locale),
            item.slug,
        ]).lower()
        if q and q not in haystack:
            continue
        if selected_vibes and not selected_vibes.intersection(set(item.vibes or [])):
            continue
        if max_price is not None and item.price_from is not None and item.price_from > max_price:
            continue
        if max_distance is not None and item.distance_center_km is not None and item.distance_center_km > max_distance:
            continue
        if min_rating is not None and (item.rating_avg or 0) < min_rating:
            continue
        detail = detail_for(session, item)
        if family and item.kind == "activity" and detail and "famille" not in (detail.audience or []):
            continue
        if duration_max and item.kind == "activity" and detail and (detail.duration_minutes or 0) > duration_max:
            continue
        results.append(item)
    return results


def stats_counts(session: Session) -> dict[str, int]:
    counts = {}
    for kind in ("activity", "restaurant", "accommodation", "spot"):
        counts[kind] = len(all_items(session, kind))
    return counts


def traveler_context(session: Session, item: CatalogItem, locale: str = "fr") -> str:
    """Contexte compact fourni à l'IA, sans donnée personnelle."""
    detail = detail_for(session, item)
    bits = [
        f"Type: {kind_label(item.kind, locale)}",
        f"Nom: {localized(item.name, locale)}",
        f"Résumé: {localized(item.short_description, locale)}",
        f"Ambiances: {', '.join(item.vibes or [])}",
        f"Zone: {item.zone or item.district or ''}",
        f"Distance: {item.distance_center_km or '?'} km",
        f"Prix: {display_price(item, locale)}",
        f"Note: {item.rating_avg or '—'}/5 ({item.review_count or 0} avis DÉMO)",
    ]
    if item.kind == "activity" and detail:
        bits.append(f"Durée: {detail.duration_minutes} min")
        bits.append(f"Public: {', '.join(detail.audience or [])}")
        bits.append(f"Sécurité: {localized(detail.safety_notes, locale)}")
    if item.kind == "restaurant" and detail:
        bits.append(f"Cuisines: {', '.join(detail.cuisines or [])}")
        bits.append(f"Options: {', '.join(detail.options or [])}")
    if item.kind == "transport" and detail:
        bits.append(f"Trajet: {detail.origin} → {detail.destination}")
        bits.append(f"Langues chauffeur: {', '.join(detail.driver_languages or [])}")
    return " | ".join(str(b) for b in bits if b and not str(b).endswith(": "))
