"""Planificateur de séjour jour par jour.

Le programme est construit localement à partir du catalogue et des
disponibilités, puis éventuellement reformulé par l'IA. L'IA ne choisit pas
les prix et n'invente pas les horaires.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from src.db.models import CatalogItem, Itinerary, ItineraryDay, ItineraryItem
from src.services.catalog import (
    all_items,
    display_price,
    localized,
    slots_for,
    variants_for,
)
from src.services.weather import get_weather_sea
from .client import complete, is_available, model_name


def _pick_activity(pool: list[CatalogItem], used: set[int], interests: list[str], rainy_or_windy: bool):
    scored = []
    for item in pool:
        if item.id in used:
            continue
        overlap = len(set(item.vibes or []).intersection(interests))
        score = overlap * 10 + (item.rating_avg or 0)
        if rainy_or_windy and "culture" not in (item.vibes or []):
            score -= 4
        if not rainy_or_windy and "mer" in (item.vibes or []):
            score += 2
        scored.append((score, item))
    if not scored:
        return None
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]


def _pick_restaurant(pool: list[CatalogItem], used: set[int], family: bool):
    candidates = [r for r in pool if r.id not in used]
    if family:
        candidates = [r for r in candidates if any("famille" in (r.tags or []) for _ in [0])] or candidates
    candidates.sort(key=lambda x: (x.rating_avg or 0), reverse=True)
    return candidates[0] if candidates else None


def _ref_for(item: CatalogItem, preferred_date: date):
    variants = variants_for(None, item.id) if False else []
    return None, None


def build_plan(
    session: Session,
    *,
    days: int = 3,
    budget: float | None = None,
    adults: int = 2,
    children: int = 0,
    interests: list[str] | None = None,
    start_date: date | None = None,
    locale: str = "fr",
) -> dict:
    days = max(1, min(7, int(days)))
    start_date = start_date or date.today() + timedelta(days=1)
    interests = interests or ["mer", "culture", "gastronomie"]
    weather = get_weather_sea()
    wave = weather.get("wave_height") or 0
    rainy_or_windy = bool(weather.get("weather_code") in {61, 63, 65, 80, 81, 82, 95, 96, 99} or wave > 1.5)

    activities = all_items(session, "activity")
    restaurants = all_items(session, "restaurant")
    transports = all_items(session, "transport")
    used_act: set[int] = set()
    used_rest: set[int] = set()
    plan_days: list[dict] = []
    total = 0.0
    unknown = 0

    for day_index in range(days):
        current_date = start_date + timedelta(days=day_index)
        act = _pick_activity(activities, used_act, interests, rainy_or_windy)
        rest = _pick_restaurant(restaurants, used_rest, children > 0)
        if act:
            used_act.add(act.id)
        if rest:
            used_rest.add(rest.id)
        transport = transports[day_index % len(transports)] if transports else None
        items = []
        if act:
            variants = variants_for(session, act.id)
            variant = variants[0] if variants else None
            slots = slots_for(session, variant.id, days=90) if variant else []
            slot = next((s for s in slots if s.start_at.date() == current_date), None)
            price = (slot.price_override if slot and slot.price_override is not None else
                     (variant.price if variant else act.price_from))
            pax = max(1, adults + children)
            if price is None:
                unknown += 1
            else:
                total += price * pax
            items.append({
                "type": "activity", "item": act, "variant": variant, "slot": slot,
                "start_time": slot.start_at.strftime("%H:%M") if slot else "à confirmer",
                "end_time": slot.end_at.strftime("%H:%M") if slot else "à confirmer",
                "price": price, "price_status": ("demo" if act.price_status == "demo" else
                                                 ("confirmed" if price is not None else "missing")),
            })
        if rest:
            price = rest.price_from
            if price is not None:
                total += price * max(1, adults)
            items.append({
                "type": "restaurant", "item": rest, "variant": None, "slot": None,
                "start_time": "19:00", "end_time": "20:30",
                "price": price, "price_status": ("demo" if rest.price_status == "demo" and price is not None
                                                 else ("confirmed" if price is not None else "missing")),
            })
        if transport and day_index == 0:
            variants = variants_for(session, transport.id)
            variant = variants[0] if variants else None
            price = variant.price if variant else transport.price_from
            if price is not None:
                total += price
            items.append({
                "type": "transport", "item": transport, "variant": variant, "slot": None,
                "start_time": "09:00", "end_time": "09:45",
                "price": price, "price_status": ("demo" if transport.price_status == "demo" and price is not None
                                                 else ("confirmed" if price is not None else "missing")),
            })
        backup = (
            "Plan B météo : atelier culturel, médina ou café couvert. "
            "Les disponibilités et horaires doivent être confirmés par l'équipe."
            if not rainy_or_windy else
            "Plan B météo : activité intérieure ou culturelle. Les horaires réels doivent être confirmés."
        )
        plan_days.append({
            "day": day_index + 1,
            "date": current_date,
            "items": items,
            "weather": weather.get("summary", "Météo à confirmer"),
            "backup": backup,
        })

    budget_note = None
    if budget is not None and total > budget:
        budget_note = (
            f"Le total connu ({total:,.0f} MAD DÉMO) dépasse le budget indiqué. "
            "Réduisez une option ou demandez un devis à l'équipe."
        ).replace(",", " ")

    model = "moteur local Azul"
    summary_text = (
        f"Un programme de {days} jour(s) entre océan, culture et gastronomie, "
        "construit à partir des fiches et disponibilités du catalogue. "
        "Les prix et horaires marqués à confirmer doivent être validés par l'équipe."
    )
    if is_available():
        summary_prompt = _summary_prompt(plan_days, days, budget, adults, children, interests, locale)
        ai_text = complete(
            "Tu rédiges un court résumé de séjour. Tu n'inventes aucun prix, horaire ou fait. "
            "Tu reprends uniquement les éléments fournis.",
            summary_prompt, max_tokens=280,
        )
        if ai_text:
            model = model_name()
            summary_text = ai_text
    return {
        "summary": summary_text,
        "days": plan_days,
        "start_date": start_date,
        "duration_days": days,
        "adults": adults,
        "children": children,
        "interests": interests,
        "weather": weather,
        "total_known": round(total, 2),
        "unknown_prices": unknown,
        "budget_note": budget_note,
        "model": model,
        "generated_at": datetime.now(),
    }


def _summary_prompt(plan_days, days, budget, adults, children, interests, locale) -> str:
    lines = [f"Langue: {locale}", f"Durée: {days} jours", f"Voyageurs: {adults} adultes, {children} enfants",
             f"Intérêts: {', '.join(interests)}", "Programme:"]
    for day in plan_days:
        names = [localized(i["item"].name, locale) for i in day["items"]]
        lines.append(f"Jour {day['day']} ({day['date']}): " + " | ".join(names))
    return "\n".join(lines) + "\nRédige 3 phrases maximum, sans ajouter de prix ni d'horaire."


def save_plan(session: Session, plan: dict, customer_id: int | None, locale: str = "fr") -> Itinerary:
    itinerary = Itinerary(
        customer_id=customer_id, title=f"Programme de {plan['duration_days']} jours",
        start_date=plan["start_date"], duration_days=plan["duration_days"],
        budget=None, group_json={"adults": plan["adults"], "children": plan["children"]},
        interests=plan["interests"], locale=locale, status="draft",
        ai_model=plan["model"], prompt_version="azul-1", is_demo=True,
    )
    session.add(itinerary)
    session.flush()
    for day in plan["days"]:
        row = ItineraryDay(
            itinerary_id=itinerary.id, day_number=day["day"], day_date=day["date"],
            weather_snapshot={"summary": day["weather"], "demo": True},
            backup_plan=day["backup"],
        )
        session.add(row)
        session.flush()
        for item in day["items"]:
            session.add(ItineraryItem(
                day_id=row.id, catalog_item_id=item["item"].id,
                variant_id=item["variant"].id if item.get("variant") else None,
                start_time=item["start_time"], end_time=item["end_time"],
                estimated_price=item["price"], price_status=item["price_status"],
                notes="Proposition de démonstration, à confirmer.",
            ))
    session.flush()
    return itinerary
