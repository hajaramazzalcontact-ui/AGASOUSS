"""Assistant conversationnel fondé sur le catalogue."""
from __future__ import annotations

import re

from sqlalchemy.orm import Session

from src.db.models import CatalogItem
from src.services.catalog import (
    all_items,
    display_price,
    localized,
    search_items,
    traveler_context,
)
from .client import complete, is_available, model_name
from .guardrails import guard_answer, no_information, redact_pii

SYSTEM_PROMPT = """Tu es l'assistant d'Azul AGADIR, application touristique d'AgadirGO.
Tu réponds dans la langue de l'utilisateur, avec un ton chaleureux et concis.
RÈGLES ABSOLUES :
- Tu ne réponds qu'à partir du CONTEXTE CATALOGUE fourni.
- Tu n'inventes jamais un prix, un horaire, une durée, une adresse ou une consigne de sécurité.
- Si l'information manque, tu dis clairement que tu ne sais pas et invites à confirmer avec l'équipe.
- Tu ne promets jamais une disponibilité non indiquée.
- Tu ne traites aucune donnée personnelle et tu n'en demandes pas.
- Tu proposes au maximum 3 options et tu termines par une question utile.
"""


def _keywords(message: str) -> list[str]:
    words = re.findall(r"[a-zA-ZÀ-ÿ\u0600-\u06FF]{3,}", (message or "").lower())
    stop = {"les", "des", "une", "pour", "avec", "dans", "quoi", "quel", "quelle", "est", "sont",
            "the", "and", "with", "what", "where", "que", "los", "las", "una", "para", "qué"}
    return [w for w in words if w not in stop][:8]


def local_answer(session: Session, message: str, locale: str = "fr") -> tuple[str, list[CatalogItem]]:
    msg = (message or "").lower()
    kind = None
    if any(k in msg for k in ("restaurant", "manger", "table", "dîner", "diner", "طعام", "مطعم", "comer")):
        kind = "restaurant"
    elif any(k in msg for k in ("hôtel", "hotel", "hébergement", "dormir", "riad", "إقامة", "الفندق", "alojamiento")):
        kind = "accommodation"
    elif any(k in msg for k in ("transport", "taxi", "transfert", "navette", "نقل", "سيارة")):
        kind = "transport"
    elif any(k in msg for k in ("plage", "spot", "surf", "mer", "شاطئ", "playa")):
        kind = "spot"
    elif any(k in msg for k in ("activité", "activite", "faire", "visiter", "نشاط", "actividad")):
        kind = "activity"

    words = _keywords(message)
    results = search_items(session, kind=kind, query=" ".join(words) if words else "", locale=locale)
    if not results:
        results = all_items(session, kind)[:6]
    results = sorted(results, key=lambda x: (x.rating_avg or 0), reverse=True)
    picks = results[:3]
    if not picks:
        return no_information(locale), []

    if any(k in msg for k in ("prix", "tarif", "combien", "coût", "cout", "price", "سعر", "precio")):
        lines = []
        for item in picks:
            if item.price_from is None:
                lines.append(f"• {localized(item.name, locale)} : tarif non renseigné, à confirmer.")
            else:
                lines.append(f"• {localized(item.name, locale)} : {display_price(item, locale)}.")
        prefix = {
            "fr": "Voici ce que le catalogue indique réellement :",
            "en": "Here is what the catalogue actually says:",
            "ar": "هذا ما يذكره الكتالوج فعلاً:",
            "es": "Esto es lo que indica realmente el catálogo:",
        }.get(locale, "")
        return prefix + "\n" + "\n".join(lines) + "\n" + no_information(locale), picks

    lines = []
    for item in picks:
        name = localized(item.name, locale)
        desc = localized(item.short_description, locale)
        price = display_price(item, locale)
        rating = f"{item.rating_avg:.1f}/5" if item.rating_avg else "—"
        lines.append(f"• {name} — {desc} ({price}, note {rating})")
    intro = {
        "fr": "Voici trois pistes issues du catalogue :",
        "en": "Here are three options from the catalogue:",
        "ar": "إليك ثلاثة خيارات من الكتالوج:",
        "es": "Aquí tienes tres opciones del catálogo:",
    }.get(locale, "")
    outro = {
        "fr": "Dites-moi si vous préférez plutôt la mer, la culture ou la famille, et je précise.",
        "en": "Tell me if you prefer the sea, culture or family time, and I'll refine.",
        "ar": "أخبرني إن كنت تفضل البحر أو الثقافة أو العائلة وسأوضح أكثر.",
        "es": "Dime si prefieres mar, cultura o familia y afinaré.",
    }.get(locale, "")
    return intro + "\n" + "\n".join(lines) + "\n" + outro, picks


def answer(
    session: Session,
    message: str,
    locale: str = "fr",
    history: list[dict] | None = None,
) -> dict:
    clean = redact_pii(message)
    local_text, picks = local_answer(session, clean, locale)
    if not is_available():
        return {"answer": local_text, "items": picks, "model": "moteur local Azul", "guardrail": "local"}

    context = "\n".join(traveler_context(session, item, locale) for item in all_items(session)[:40])
    history_txt = ""
    if history:
        history_txt = "\n".join(f"{m.get('role')}: {m.get('content')}" for m in history[-6:])
    prompt = (
        f"LANGUE DE RÉPONSE: {locale}\n"
        f"HISTORIQUE RÉCENT:\n{history_txt}\n\n"
        f"CONTEXTE CATALOGUE (données DÉMO marquées):\n{context}\n\n"
        f"QUESTION: {clean}\n\n"
        "Réponds uniquement avec les informations du contexte. "
        "Si un prix ou un horaire manque, dis-le. Maximum 180 mots."
    )
    generated = complete(SYSTEM_PROMPT, prompt)
    if not generated:
        return {"answer": local_text, "items": picks, "model": "moteur local Azul", "guardrail": "fallback"}
    allowed = {float(item.price_from) for item in all_items(session) if item.price_from is not None}
    safe, status = guard_answer(generated, allowed)
    return {"answer": safe, "items": picks, "model": model_name(), "guardrail": status}
