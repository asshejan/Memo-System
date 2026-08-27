import uuid

from sqlalchemy.orm import Session

from app.models.notification import Notification


def notify(
    db: Session,
    *,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    event_type: str,
    message: str,
    memo_id: uuid.UUID | None = None,
) -> None:
    db.add(
        Notification(
            organization_id=organization_id,
            user_id=user_id,
            memo_id=memo_id,
            event_type=event_type,
            message=message,
        )
    )
