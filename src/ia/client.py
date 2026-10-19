"""Client Anthropic optionnel, avec délai et repli local."""
from __future__ import annotations

from src.config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL

_client = None


def is_available() -> bool:
    return bool(ANTHROPIC_API_KEY)


def model_name() -> str:
    return ANTHROPIC_MODEL if is_available() else "moteur local Azul"


def complete(system: str, prompt: str, *, max_tokens: int = 700, temperature: float = 0.2) -> str | None:
    """Retourne None si l'IA n'est pas configurée ou échoue.

    Aucune exception réseau ne doit empêcher le parcours de réservation.
    """
    global _client
    if not is_available():
        return None
    try:
        if _client is None:
            from anthropic import Anthropic
            _client = Anthropic(api_key=ANTHROPIC_API_KEY, timeout=20.0)
        response = _client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        parts = [block.text for block in response.content if getattr(block, "type", "") == "text"]
        return "\n".join(parts).strip() or None
    except Exception:
        return None
