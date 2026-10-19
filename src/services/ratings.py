"""Calcul des notes à partir des seuls avis vérifiés et publiés."""
from __future__ import annotations

from collections import Counter
from statistics import mean
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models import CatalogItem, Review


def calculate_rating(reviews: list[Any]) -> dict:
    """Retourne moyenne, nombre, répartition et taux de réponse.

    Un avis compte uniquement s'il est vérifié et publié. Les avis masqués
    pour modération ne participent pas à la note publique.
    """
    valid = [r for r in reviews if getattr(r, "verified", False) and getattr(r, "status", None) == "published"]
    values = [int(r.rating) for r in valid if 1 <= int(r.rating) <= 5]
    distribution = {str(i): 0 for i in range(1, 6)}
    for value in values:
        distribution[str(value)] += 1
    avg = round(mean(values), 2) if values else 0.0
    responded = [r for r in valid if getattr(r, "manager_response", None)]
    return {
        "count": len(values),
        "average": avg,
        "distribution": distribution,
        "response_rate": round((len(responded) / len(values)) * 100, 1) if values else 0.0,
        "responded": len(responded),
    }


def refresh_catalog_rating(session: Session, catalog_id: int) -> dict:
    reviews = list(session.scalars(select(Review).where(Review.catalog_item_id == catalog_id)).all())
    stats = calculate_rating(reviews)
    item = session.get(CatalogItem, catalog_id)
    if item:
        item.rating_avg = stats["average"]
        item.review_count = stats["count"]
        session.flush()
    return stats


def rating_distribution_percent(distribution: dict[str, int]) -> dict[str, float]:
    total = sum(distribution.values()) or 1
    return {star: round((count / total) * 100, 1) for star, count in distribution.items()}


def monthly_satisfaction(reviews: list[Any]) -> dict[str, float]:
    """Moyenne mensuelle des avis publiés vérifiés, pour les graphiques."""
    buckets: dict[str, list[int]] = {}
    for review in reviews:
        if not (getattr(review, "verified", False) and getattr(review, "status", None) == "published"):
            continue
        created = getattr(review, "created_at", None)
        if not created:
            continue
        key = created.strftime("%Y-%m")
        buckets.setdefault(key, []).append(int(review.rating))
    return {key: round(mean(values), 2) for key, values in sorted(buckets.items())}
