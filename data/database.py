"""
Initialisation et configuration de la base de données SQLite avec SQLAlchemy
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from dotenv import load_dotenv

load_dotenv()

# Configuration de la base de données
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///azul_agadir.db")

# Pour SQLite en mémoire ou fichier local
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    """Fournit une session de base de données"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialise la base de données - crée toutes les tables"""
    from data.models import Base
    Base.metadata.create_all(bind=engine)
    print("✅ Base de données initialisée avec succès")

def drop_all():
    """Supprime toutes les tables (attention: données perdues)"""
    from data.models import Base
    Base.metadata.drop_all(bind=engine)
    print("⚠️ Toutes les tables ont été supprimées")
