"""Connexion SQLAlchemy et initialisation de la base."""
from __future__ import annotations

from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from src.config import DATABASE_URL, IS_DEMO
from .base import Base
from . import models  # noqa: F401  (enregistre les tables)

_engine = None
_SessionLocal = None


def configure_database(url: str | None = None):
    """Configure un moteur. Utilisé au démarrage et par les tests."""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    db_url = url or DATABASE_URL
    connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
    _engine = create_engine(db_url, connect_args=connect_args, future=True)

    if db_url.startswith("sqlite"):
        @event.listens_for(_engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, _connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA busy_timeout=5000")
            cursor.close()

    _SessionLocal = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False, future=True)
    return _engine


def get_engine():
    if _engine is None:
        configure_database()
    return _engine


def get_session():
    if _SessionLocal is None:
        configure_database()
    return _SessionLocal()


@contextmanager
def session_scope():
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_database(seed: bool | None = None):
    """Crée le schéma et, en mode démo, les données fictives."""
    engine = get_engine()
    Base.metadata.create_all(engine)
    if seed is None:
        seed = IS_DEMO
    if seed:
        from .seed import seed_if_empty
        seed_if_empty()
