"""Sauvegardes locales de la base SQLite."""
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from src.config import BACKUP_DIR, DB_PATH
from src.db.models import BackupLog


def create_backup(session=None, actor_id: int | None = None) -> Path:
    """Copie cohérente de la base SQLite, horodatée."""
    if not str(DB_PATH).lower().endswith(".db"):
        raise RuntimeError("La sauvegarde intégrée prend en charge SQLite uniquement.")
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    target = BACKUP_DIR / f"azul-{datetime.now().strftime('%Y%m%d-%H%M%S')}.db"
    source = sqlite3.connect(DB_PATH)
    dest = sqlite3.connect(target)
    try:
        source.backup(dest)
    finally:
        dest.close()
        source.close()
    if session is not None:
        session.add(BackupLog(
            path=str(target), size_bytes=target.stat().st_size,
            created_by=actor_id,
        ))
        session.flush()
    return target
