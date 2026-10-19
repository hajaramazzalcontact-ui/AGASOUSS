"""Garde-fous communs aux fonctions IA.

- Aucune donnée personnelle n'est envoyée au modèle.
- Aucun prix, horaire ou engagement de sécurité ne doit être inventé.
- En cas de doute, la réponse est « je ne sais pas » ou « à confirmer ».
"""
from __future__ import annotations

import re

EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b", re.IGNORECASE)
PHONE_RE = re.compile(r"(\+?\d[\d\s().-]{7,}\d)")


def redact_pii(text: str) -> str:
    text = EMAIL_RE.sub("[email masqué]", text or "")
    text = PHONE_RE.sub("[téléphone masqué]", text)
    return text


def unsupported_prices(answer: str, allowed_values: set[float]) -> list[str]:
    """Repère des montants cités qui ne figurent pas dans le contexte autorisé."""
    found = []
    for raw in re.findall(r"(\d[\d\s]{1,8})\s*(?:MAD|DH|dirhams?)", answer or "", flags=re.IGNORECASE):
        try:
            value = float(raw.replace(" ", ""))
        except ValueError:
            continue
        if value not in allowed_values:
            found.append(f"{value:.0f} MAD")
    return found


def guard_answer(answer: str, allowed_prices: set[float] | None = None) -> tuple[str, str]:
    """Retourne (texte, statut). Ne masque jamais une information utile."""
    text = (answer or "").strip()
    if not text:
        return "Je ne sais pas. Cette information n'est pas disponible dans le catalogue.", "fallback"
    if allowed_prices is not None:
        bad = unsupported_prices(text, allowed_prices)
        if bad:
            return (
                "Je ne peux pas confirmer ce tarif : il n'est pas renseigné dans le catalogue. "
                "Le prix exact doit être confirmé par l'équipe Azul AGADIR.",
                "blocked_unsupported_price",
            )
    return text, "ok"


def no_information(locale: str = "fr") -> str:
    return {
        "fr": "Je ne sais pas : cette information n'est pas disponible dans le catalogue Azul AGADIR. L'équipe peut la confirmer.",
        "en": "I don't know: this information is not available in the Azul AGADIR catalogue. The team can confirm it.",
        "ar": "لا أعرف: هذه المعلومة غير متوفرة في كتالوج أزول أكادير. يمكن للفريق تأكيدها.",
        "es": "No lo sé: esta información no está disponible en el catálogo de Azul AGADIR. El equipo puede confirmarla.",
    }.get(locale, "Je ne sais pas.")


def safety_note(locale: str = "fr") -> str:
    return {
        "fr": "Les conditions de sécurité et de baignade doivent être confirmées sur place.",
        "en": "Safety and swimming conditions must be confirmed on site.",
        "ar": "يجب تأكيد ظروف السلامة والسباحة في المكان.",
        "es": "Las condiciones de seguridad y baño deben confirmarse en el lugar.",
    }.get(locale, "")
