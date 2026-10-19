"""Base SQLAlchemy et conventions communes."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import declarative_base

Base = declarative_base()


def utcnow() -> datetime:
    """Horodatage UTC naïf, compatible SQLite."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
