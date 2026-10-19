"""Sécurité : mots de passe, chiffrement des contacts, références, QR signés."""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timezone

from cryptography.fernet import Fernet, InvalidToken

from src.config import ensure_fernet_key

_SCRYPT_N = 2 ** 14
_SCRYPT_R = 8
_SCRYPT_P = 1


def hash_password(password: str) -> str:
    """Hache un mot de passe avec scrypt et un sel aléatoire."""
    if not password:
        raise ValueError("Le mot de passe ne peut pas être vide.")
    salt = os.urandom(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P, dklen=32
    )
    return "scrypt${}${}${}${}${}".format(
        _SCRYPT_N,
        _SCRYPT_R,
        _SCRYPT_P,
        base64.b64encode(salt).decode(),
        base64.b64encode(digest).decode(),
    )


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, n, r, p, salt_b64, digest_b64 = stored.split("$")
        if scheme != "scrypt":
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)
        actual = hashlib.scrypt(
            password.encode("utf-8"), salt=salt, n=int(n), r=int(r), p=int(p), dklen=len(expected)
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def _fernet() -> Fernet:
    return Fernet(ensure_fernet_key())


def encrypt_text(value: str | None) -> str | None:
    if value is None or str(value).strip() == "":
        return None
    return _fernet().encrypt(str(value).strip().encode("utf-8")).decode("utf-8")


def decrypt_text(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return _fernet().decrypt(value.encode("utf-8")).decode("utf-8")
    except (InvalidToken, ValueError):
        return None


def hash_identifier(value: str | None) -> str | None:
    normalized = (value or "").strip().lower()
    if not normalized:
        return None
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def mask_email(email: str | None) -> str:
    if not email or "@" not in email:
        return "—"
    local, domain = email.split("@", 1)
    visible = local[:2] if len(local) > 2 else local[:1]
    return f"{visible}***@{domain}"


def mask_phone(phone: str | None) -> str:
    if not phone:
        return "—"
    digits = "".join(c for c in phone if c.isdigit())
    return f"***{digits[-3:]}" if digits else "—"


def new_public_reference(prefix: str = "AZ") -> str:
    stamp = datetime.now(timezone.utc).strftime("%y%m%d")
    return f"{prefix}-{stamp}-{secrets.token_hex(3).upper()}"


def new_cart_token() -> str:
    return secrets.token_urlsafe(24)


def sign_ticket_payload(booking_reference: str) -> str:
    """Jeton compact, sans donnée personnelle, vérifiable par HMAC."""
    key = _fernet()._signing_key  # uniquement comme matériau de signature local
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    nonce = secrets.token_hex(4)
    base = f"AZUL|{booking_reference}|{stamp}|{nonce}"
    signature = hmac.new(key, base.encode("utf-8"), hashlib.sha256).hexdigest()[:24].upper()
    return f"{base}|{signature}"


def verify_ticket_payload(payload: str) -> bool:
    try:
        base, signature = payload.rsplit("|", 1)
        key = _fernet()._signing_key
        expected = hmac.new(key, base.encode("utf-8"), hashlib.sha256).hexdigest()[:24].upper()
        return hmac.compare_digest(signature, expected)
    except (ValueError, AttributeError):
        return False
