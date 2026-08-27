import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db import get_db
from app.models.user import User
from app.models.notification import Notification
from app.schemas.misc import NotificationOut

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationOut])
def list_notifications(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.execute(
        select(Notification)
        .where(Notification.user_id == current_user.id, Notification.organization_id == current_user.organization_id)
        .order_by(Notification.created_at.desc())
        .limit(100)
    ).scalars().all()


@router.get("/unread-count")
def unread_count(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    count = len(
        db.execute(
            select(Notification.id).where(
                Notification.user_id == current_user.id,
                Notification.organization_id == current_user.organization_id,
                Notification.read_at.is_(None),
            )
        ).scalars().all()
    )
    return {"unread_count": count}


@router.post("/{notification_id}/read", response_model=NotificationOut)
def mark_read(notification_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notification = db.get(Notification, notification_id)
    if notification is None or notification.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    notification.read_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(notification)
    return notification


@router.post("/mark-all-read", status_code=status.HTTP_204_NO_CONTENT)
def mark_all_read(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    unread = db.execute(
        select(Notification).where(
            Notification.user_id == current_user.id,
            Notification.organization_id == current_user.organization_id,
            Notification.read_at.is_(None),
        )
    ).scalars().all()
    now = datetime.now(timezone.utc)
    for n in unread:
        n.read_at = now
    db.commit()
