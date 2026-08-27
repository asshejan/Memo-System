import uuid

from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def log_event(
    db: Session,
    *,
    organization_id: uuid.UUID | None,
    user_id: uuid.UUID | None,
    event_type: str,
    description: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
) -> None:
    entry = AuditLog(
        organization_id=organization_id,
        user_id=user_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
    )
    db.add(entry)
