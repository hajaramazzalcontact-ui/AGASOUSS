"""Score de priorisation d'une demande de réservation (0–100).

Le score est déterministe et explicable. Il ne remplace jamais la décision
humaine : il sert à ordonner la file de confirmation et de relance.
"""
from __future__ import annotations

from typing import Any


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def score_booking_request(
    amount: float | None,
    lead_days: int | None,
    group_size: int | None,
    completed_bookings: int = 0,
    cancelled_bookings: int = 0,
) -> tuple[int, str]:
    """Calcule un score et une phrase d'explication.

    Pondérations : montant 25, proximité de la date 30, taille du groupe 20,
    historique 25. Les valeurs manquantes sont traitées comme neutres.
    """
    amount = max(0.0, float(amount or 0))
    lead = max(0, int(lead_days if lead_days is not None else 7))
    group = max(1, int(group_size or 1))
    completed = max(0, int(completed_bookings or 0))
    cancelled = max(0, int(cancelled_bookings or 0))

    amount_points = _clamp((amount / 4000.0) * 25.0, 0.0, 25.0)
    if lead <= 1:
        urgency_points = 30.0
    elif lead <= 3:
        urgency_points = 25.0
    elif lead <= 7:
        urgency_points = 18.0
    elif lead <= 14:
        urgency_points = 11.0
    elif lead <= 30:
        urgency_points = 6.0
    else:
        urgency_points = 2.0
    group_points = _clamp((group - 1) * 3.0, 0.0, 20.0)
    history_points = _clamp(completed * 5.0 - cancelled * 6.0, 0.0, 25.0)
    if completed == 0 and cancelled == 0:
        history_points = 6.0  # nouveau client : neutre, jamais pénalisé

    total = int(round(_clamp(
        amount_points + urgency_points + group_points + history_points, 0, 100
    )))
    amount_txt = f"{amount:,.0f} MAD".replace(",", " ")
    explanation = (
        f"Score {total}/100 : montant {amount_txt} ({int(round(amount_points))} pts), "
        f"départ dans {lead} j ({int(round(urgency_points))} pts), "
        f"{group} voyageur(s) ({int(round(group_points))} pts), "
        f"{completed} séjour(s) terminé(s) et {cancelled} annulation(s) "
        f"({int(round(history_points))} pts)."
    )
    return total, explanation


def score_from_booking(booking: Any, completed: int = 0, cancelled: int = 0) -> tuple[int, str]:
    lead = 7
    try:
        target = None
        if getattr(booking, "items", None):
            dates = [i.service_date for i in booking.items if i.service_date]
            target = min(dates) if dates else None
        if target:
            from datetime import date
            lead = (target - date.today()).days
    except Exception:
        lead = 7
    group = 1
    try:
        if getattr(booking, "items", None):
            item = booking.items[0]
            group = max(1, (item.adults or 1) + (item.children or 0))
    except Exception:
        pass
    return score_booking_request(
        getattr(booking, "total_amount", None), lead, group, completed, cancelled
    )
