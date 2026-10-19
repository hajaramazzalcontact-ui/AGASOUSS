"""Gestion du mode démonstration isolé."""
from __future__ import annotations

from pathlib import Path

from src.config import DB_PATH, IS_DEMO


def reset_demo_database() -> None:
    if not IS_DEMO:
        raise RuntimeError("La remise à zéro est disponible uniquement en mode démonstration.")
    from src.db.session import configure_database, get_engine, init_database
    engine = get_engine()
    engine.dispose()
    for suffix in ("", "-wal", "-shm"):
        path = Path(str(DB_PATH) + suffix)
        if path.exists():
            try:
                path.unlink()
            except OSError as exc:
                raise RuntimeError(f"Impossible de supprimer {path}: {exc}") from exc
    configure_database()
    init_database(seed=True)
