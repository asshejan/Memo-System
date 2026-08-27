import uuid

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user
from app.db import get_db
from app.models.user import User
from app.models.memo import Memo
from app.models.attachment import Attachment
from app.schemas.misc import AttachmentOut
from app.services.authorization import assert_can_view_memo
from app.services.audit import log_event

router = APIRouter(prefix="/api/memos/{memo_id}/attachments", tags=["attachments"])

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "image/png",
    "image/jpeg",
    "text/plain",
    "text/csv",
}


def _get_memo_for_user(db: Session, memo_id: uuid.UUID, user: User) -> Memo:
    memo = db.get(Memo, memo_id)
    if memo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memo not found")
    assert_can_view_memo(user, memo)
    return memo


@router.get("", response_model=list[AttachmentOut])
def list_attachments(memo_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_memo_for_user(db, memo_id, current_user)
    return db.execute(select(Attachment).where(Attachment.memo_id == memo_id)).scalars().all()


@router.post("", response_model=AttachmentOut, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    memo_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    memo = _get_memo_for_user(db, memo_id, current_user)
    if memo.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the author may attach files to this memo")

    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File type is not permitted")

    data = await file.read()
    if len(data) > settings.attachment_max_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File exceeds the maximum allowed size")

    attachment = Attachment(
        memo_id=memo.id,
        filename=file.filename or "attachment",
        mime_type=file.content_type,
        size_bytes=len(data),
        data=data,
        uploaded_by_id=current_user.id,
    )
    db.add(attachment)
    log_event(db, organization_id=current_user.organization_id, user_id=current_user.id,
              event_type="attachment_uploaded", description=f"Attachment '{attachment.filename}' uploaded to memo {memo.memo_number}",
              entity_type="Memo", entity_id=str(memo.id))
    db.commit()
    db.refresh(attachment)
    return attachment


@router.get("/{attachment_id}/download")
def download_attachment(
    memo_id: uuid.UUID,
    attachment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_memo_for_user(db, memo_id, current_user)
    attachment = db.get(Attachment, attachment_id)
    if attachment is None or attachment.memo_id != memo_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")

    log_event(db, organization_id=current_user.organization_id, user_id=current_user.id,
              event_type="attachment_downloaded", description=f"Attachment '{attachment.filename}' downloaded",
              entity_type="Attachment", entity_id=str(attachment.id))
    db.commit()

    return Response(
        content=attachment.data,
        media_type=attachment.mime_type,
        headers={"Content-Disposition": f'attachment; filename="{attachment.filename}"'},
    )


@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment(
    memo_id: uuid.UUID,
    attachment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    memo = _get_memo_for_user(db, memo_id, current_user)
    attachment = db.get(Attachment, attachment_id)
    if attachment is None or attachment.memo_id != memo_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")
    if memo.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the author may delete attachments")

    log_event(db, organization_id=current_user.organization_id, user_id=current_user.id,
              event_type="attachment_deleted", description=f"Attachment '{attachment.filename}' deleted",
              entity_type="Attachment", entity_id=str(attachment.id))
    db.delete(attachment)
    db.commit()
