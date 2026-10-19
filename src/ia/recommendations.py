"""Recommandations personnalisées, sans vente forcée."""
from __future__ import annotations

from sqlalchemy.orm import Session

from src.db.models import CatalogItem
from src.services.catalog import all_items


def recommend(session: Session, interests: list[str] | None = None, kind: str | None = None, limit: int = 6) -> list[CatalogItem]:
    interests = interests or []
    pool = all_items(session, kind)
    scored = []
    for item in pool:
        overlap = len(set(item.vibes or []).intersection(interests))
        score = overlap * 10 + (item.rating_avg or 0) * 1.5
        if item.price_status == "missing":
            score -= 0.5
        scored.append((score, item))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _, item in scored[:limit]]


def cross_sell(session: Session, item: CatalogItem, limit: int = 3) -> list[CatalogItem]:
    """Compléments pertinents : repas après activité, transport, etc."""
    kind = "restaurant" if item.kind == "activity" else ("transport" if item.kind == "restaurant" else "activity")
    return recommend(session, interests=item.vibes or [], kind=kind, limit=limit)
