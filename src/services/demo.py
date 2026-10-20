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
    if IS_DEMO:
        # Re-illustration des fiches après un reset (silencieux sans réseau).
        session = get_session()
        try:
            from src.services.photos import apply_real_photos
            apply_real_photos(session)
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()
