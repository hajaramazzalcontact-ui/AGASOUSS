"""Journal d'accès et d'actions sensibles."""
from __future__ import annotations

from sqlalchemy.orm import Session

from src.db.models import AuditLog


def log_action(
    session: Session,
    actor_id: int | None,
    action: str,
    entity_type: str | None = None,
    entity_id: int | None = None,
    details: dict | None = None,
    ip_hash: str | None = None,
) -> AuditLog:
    row = AuditLog(
        actor_id=actor_id, action=action, entity_type=entity_type,
        entity_id=entity_id, details=details or {}, ip_hash=ip_hash,
    )
    session.add(row)
    session.flush()
    return row
