"""Configuration centrale d'Azul AGADIR.

Aucun secret n'est écrit dans le code. Les valeurs sensibles viennent de
l'environnement ou d'un fichier .env local ignoré par Git.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
BACKUP_DIR = DATA_DIR / "backups"
ASSETS_DIR = BASE_DIR / "assets"

for _d in (DATA_DIR, UPLOAD_DIR, BACKUP_DIR):
    _d.mkdir(parents=True, exist_ok=True)

MODE = os.getenv("AZUL_MODE", "demo").strip().lower()
IS_DEMO = MODE != "production"
DB_PATH = DATA_DIR / ("azul_demo.db" if IS_DEMO else "azul.db")
DATABASE_URL = os.getenv("AZUL_DATABASE_URL", f"sqlite:///{DB_PATH.as_posix()}")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6").strip()

ADMIN_EMAIL = os.getenv("AZUL_ADMIN_EMAIL", "admin@azul.local").strip().lower()
ADMIN_PASSWORD = os.getenv("AZUL_ADMIN_PASSWORD", "AzulDemo2026!")

APP_NAME = "AZUL AGADIR"
APP_EDITOR = "AgadirGO"
CURRENCY = "MAD"
CENTER_LAT = 30.4278
CENTER_LNG = -9.5981

# Politique commerciale de démonstration. En production, ces textes doivent
# être validés par le gérant et un juriste.
CANCELLATION_POLICY = (
    "Annulation gratuite jusqu'à 48 h avant le début de la prestation. "
    "À moins de 48 h, l'acompte peut être retenu. Les conditions définitives "
    "sont affichées sur chaque fiche et reprises dans la confirmation."
)


def ensure_fernet_key() -> bytes:
    """Retourne la clé Fernet, générée localement si absente.

    En production, définir AZUL_FERNET_KEY et sauvegarder cette clé hors du
    serveur applicatif. Sans elle, les champs chiffrés sont illisibles.
    """
    from cryptography.fernet import Fernet

    env_key = os.getenv("AZUL_FERNET_KEY", "").strip()
    if env_key:
        return env_key.encode("utf-8")

    key_file = DATA_DIR / ".secret.key"
    if key_file.exists():
        return key_file.read_bytes().strip()
    key = Fernet.generate_key()
    key_file.write_bytes(key)
    try:
        key_file.chmod(0o600)
    except OSError:
        pass
    return key


def is_demo() -> bool:
    return IS_DEMO
