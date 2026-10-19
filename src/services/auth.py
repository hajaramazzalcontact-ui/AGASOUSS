"""Authentification du back-office et contrôle des rôles."""
from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.base import utcnow
from src.db.models import User
from src.services.audit import log_action
from src.services.security import decrypt_text, encrypt_text, hash_identifier, hash_password, verify_password

ROLE_LABELS = {
    "admin": "Administrateur",
    "manager": "Gestionnaire",
    "provider": "Prestataire",
    "driver": "Chauffeur",
}


class AuthError(ValueError):
    pass


def authenticate(session: Session, email: str, password: str) -> User:
    email_hash = hash_identifier(email)
    user = session.scalar(select(User).where(User.email_hash == email_hash))
    if not user or not user.is_active:
        raise AuthError("Identifiants invalides.")
    if user.locked_until and user.locked_until > utcnow():
        raise AuthError("Compte temporairement verrouillé. Réessayez plus tard.")
    if not verify_password(password or "", user.password_hash):
        user.failed_attempts = (user.failed_attempts or 0) + 1
        if user.failed_attempts >= 5:
            user.locked_until = utcnow() + timedelta(minutes=15)
        session.flush()
        raise AuthError("Identifiants invalides.")
    user.failed_attempts = 0
    user.locked_until = None
    user.last_login_at = utcnow()
    log_action(session, user.id, "login", "user", user.id)
    session.flush()
    return user


def create_user(
    session: Session,
    *,
    email: str,
    password: str,
    full_name: str,
    role: str = "manager",
    provider_id: int | None = None,
    driver_id: int | None = None,
    locale: str = "fr",
) -> User:
    if role not in ROLE_LABELS:
        raise AuthError("Rôle inconnu.")
    if len(password or "") < 8:
        raise AuthError("Le mot de passe doit contenir au moins 8 caractères.")
    if session.scalar(select(User).where(User.email_hash == hash_identifier(email))):
        raise AuthError("Un compte existe déjà avec cet email.")
    user = User(
        email_hash=hash_identifier(email),
        email_enc=encrypt_text(email),
        password_hash=hash_password(password),
        full_name=full_name.strip()[:160],
        role=role, provider_id=provider_id, driver_id=driver_id, locale=locale,
    )
    session.add(user)
    session.flush()
    return user


def user_email(user: User) -> str:
    return decrypt_text(user.email_enc) or "—"


def can_manage(user: User | None, section: str = "") -> bool:
    if user is None:
        return False
    if user.role in {"admin", "manager"}:
        return True
    if user.role == "provider":
        return section in {"catalogue", "reservations", "transport", "avis"}
    if user.role == "driver":
        return section in {"transport"}
    return False
