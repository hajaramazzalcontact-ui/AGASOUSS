"""Indicateurs du tableau de bord et analyses."""
from __future__ import annotations

from collections import Counter
from datetime import date, timedelta
from statistics import mean

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.db.models import (
    Anomaly,
    Booking,
    BookingItem,
    CatalogItem,
    Customer,
    Review,
    TransportAssignment,
)
from .ratings import calculate_rating, monthly_satisfaction


def dashboard_metrics(session: Session) -> dict:
    today = date.today()
    bookings = list(session.scalars(select(Booking)).all())
    items = list(session.scalars(select(BookingItem)).all())
    reviews = list(session.scalars(select(Review)).all())
    customers = list(session.scalars(select(Customer)).all())
    today_bookings = [b for b in bookings if (b.created_at and b.created_at.date() == today)
                      or any(i.service_date == today for i in b.items)]
    confirmed = [b for b in bookings if b.status in {"confirmed", "deposit_received", "completed"}]
    revenue = sum(b.total_amount or 0 for b in confirmed)
    rating = calculate_rating(reviews)
    top_ids = Counter(i.catalog_item_id for i in items if i.catalog_item_id)
    top_items = []
    for item_id, count in top_ids.most_common(6):
        item = session.get(CatalogItem, item_id)
        if item:
            top_items.append({"name": item.name or {}, "count": count, "kind": item.kind})
    countries = Counter(c.country or "Inconnu" for c in customers)
    anomalies = session.scalar(select(func.count(Anomaly.id)).where(Anomaly.status == "open")) or 0
    pending = [b for b in bookings if b.status == "pending"]
    deposits = [b for b in confirmed if b.status == "confirmed"]
    return {
        "today_bookings": len(today_bookings),
        "revenue": round(revenue, 2),
        "confirmed": len(confirmed),
        "pending": len(pending),
        "awaiting_deposit": len(deposits),
        "rating": rating,
        "top_items": top_items,
        "countries": dict(countries),
        "anomalies": anomalies,
        "average_basket": round(revenue / len(confirmed), 2) if confirmed else 0,
        "total_bookings": len(bookings),
    }


def monthly_revenue(session: Session) -> pd.DataFrame:
    rows = []
    for b in session.scalars(select(Booking)).all():
        if b.status not in {"confirmed", "deposit_received", "completed"}:
            continue
        if not b.created_at:
            continue
        rows.append({"mois": b.created_at.strftime("%Y-%m"), "montant": b.total_amount or 0})
    if not rows:
        return pd.DataFrame(columns=["mois", "montant"])
    df = pd.DataFrame(rows)
    return df.groupby("mois", as_index=False)["montant"].sum().sort_values("mois")


def booking_funnel(session: Session) -> pd.DataFrame:
    bookings = list(session.scalars(select(Booking)).all())
    statuses = Counter(b.status for b in bookings)
    order = [
        ("pending", "En attente"),
        ("confirmed", "Confirmées"),
        ("deposit_received", "Acompte reçu"),
        ("completed", "Terminées"),
        ("cancelled", "Annulées"),
    ]
    return pd.DataFrame([{"statut": label, "nombre": statuses.get(code, 0)} for code, label in order])


def top_activities(session: Session) -> pd.DataFrame:
    rows = []
    items = list(session.scalars(select(BookingItem).where(BookingItem.catalog_item_id.is_not(None))).all())
    counts = Counter(i.catalog_item_id for i in items)
    for item_id, count in counts.most_common(10):
        item = session.get(CatalogItem, item_id)
        if item:
            rows.append({"activité": (item.name or {}).get("fr", item.slug), "réservations": count, "type": item.kind})
    return pd.DataFrame(rows)


def nationality_breakdown(session: Session) -> pd.DataFrame:
    customers = list(session.scalars(select(Customer)).all())
    counts = Counter(c.country or "Inconnu" for c in customers)
    return pd.DataFrame([{"pays": k, "clients": v} for k, v in counts.most_common(10)])


def satisfaction_over_time(session: Session) -> pd.DataFrame:
    reviews = list(session.scalars(select(Review)).all())
    data = monthly_satisfaction(reviews)
    return pd.DataFrame([{"mois": k, "note": v} for k, v in data.items()])


def provider_bookings(session: Session, provider_id: int) -> list[BookingItem]:
    from src.db.models import CatalogItem
    return list(session.scalars(
        select(BookingItem).join(CatalogItem, BookingItem.catalog_item_id == CatalogItem.id)
        .where(CatalogItem.provider_id == provider_id)
    ).all())


def today_road_sheet(session: Session) -> list[dict]:
    today = date.today()
    assignments = list(session.scalars(select(TransportAssignment)).all())
    result = []
    for assignment in assignments:
        item = session.get(BookingItem, assignment.booking_item_id)
        if not item or item.service_date != today:
            continue
        result.append({
            "heure": assignment.pickup_at.strftime("%H:%M") if assignment.pickup_at else "à confirmer",
            "client": item.booking.customer.first_name if item.booking and item.booking.customer else "—",
            "prestation": (item.catalog.name or {}).get("fr", item.catalog.slug) if item.catalog else "—",
            "statut": assignment.status, "retard_min": assignment.delay_minutes or 0,
        })
    return sorted(result, key=lambda x: x["heure"])
