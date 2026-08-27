import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.deps import get_current_user
from app.db import get_db
from app.models.user import User
from app.models.memo import Memo
from app.models.workflow_template import WorkflowTemplate
from app.models.workflow import WorkflowInstance
from app.models.enums import MemoStatus, UserRole
from app.schemas.memo import (
    MemoCreate, MemoUpdate, MemoOut, MemoDetailOut, MemoSubmit, ResubmitRequest,
    ActionRequest, CommentCreate, CommentOut,
)
from app.services.scoping import get_org_scoped_or_404
from app.services.authorization import assert_can_view_memo
from app.services.memo_number import generate_memo_number
from app.services.audit import log_event
from app.services import workflow_engine
from app.models.comment import Comment
from app.models.enums import CommentType

router = APIRouter(prefix="/api/memos", tags=["memos"])


def _load_memo(db: Session, memo_id: uuid.UUID) -> Memo | None:
    return db.execute(
        select(Memo)
        .options(
            selectinload(Memo.workflow_instance).selectinload(WorkflowInstance.steps),
            selectinload(Memo.comments),
            selectinload(Memo.versions),
        )
        .where(Memo.id == memo_id)
    ).scalars().first()


@router.post("", response_model=MemoOut, status_code=status.HTTP_201_CREATED)
def create_draft(payload: MemoCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    memo = Memo(
        organization_id=current_user.organization_id,
        memo_number=generate_memo_number(db, current_user.organization_id),
        author_id=current_user.id,
        status=MemoStatus.draft,
        **payload.model_dump(),
    )
    db.add(memo)
    log_event(db, organization_id=current_user.organization_id, user_id=current_user.id,
              event_type="memo_created", description=f"Draft memo '{memo.subject}' created",
              entity_type="Memo", entity_id=str(memo.id))
    db.commit()
    db.refresh(memo)
    return memo


@router.get("/mine", response_model=list[MemoOut])
def list_my_memos(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.execute(
        select(Memo)
        .where(Memo.organization_id == current_user.organization_id, Memo.author_id == current_user.id)
        .order_by(Memo.created_at.desc())
    ).scalars().all()


@router.get("/{memo_id}", response_model=MemoDetailOut)
def get_memo(memo_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    memo = _load_memo(db, memo_id)
    if memo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memo not found")
    assert_can_view_memo(current_user, memo)
    return memo


@router.patch("/{memo_id}", response_model=MemoOut)
def update_draft(
    memo_id: uuid.UUID,
    payload: MemoUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    memo = get_org_scoped_or_404(db, Memo, memo_id, current_user.organization_id)
    if memo.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the author may edit this memo")
    if memo.status != MemoStatus.draft:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only draft memos may be edited directly")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(memo, field, value)
    db.commit()
    db.refresh(memo)
    return memo


@router.delete("/{memo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_draft(memo_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    memo = get_org_scoped_or_404(db, Memo, memo_id, current_user.organization_id)
    if memo.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the author may delete this memo")
    if memo.status != MemoStatus.draft:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only draft memos may be deleted")
    db.delete(memo)
    db.commit()


@router.post("/{memo_id}/submit", response_model=MemoDetailOut)
def submit_memo(
    memo_id: uuid.UUID,
    payload: MemoSubmit,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    memo = get_org_scoped_or_404(db, Memo, memo_id, current_user.organization_id)
    if memo.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the author may submit this memo")
    if memo.status != MemoStatus.draft:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Memo has already been submitted")
    if not memo.subject.strip() or not memo.body.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Subject and body are required before submitting")

    if payload.template_id:
        get_org_scoped_or_404(db, WorkflowTemplate, payload.template_id, current_user.organization_id)

    org_user_ids = set(
        db.execute(select(User.id).where(User.organization_id == current_user.organization_id)).scalars().all()
    )
    ordered = sorted(payload.participants, key=lambda p: p.position_index)
    participants = []
    for p in ordered:
        if p.user_id not in org_user_ids:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="All workflow participants must belong to your organization")
        participants.append((p.user_id, p.label))

    workflow_engine.start_workflow(db, memo, participants)
    log_event(db, organization_id=current_user.organization_id, user_id=current_user.id,
              event_type="memo_submitted", description=f"Memo {memo.memo_number} submitted",
              entity_type="Memo", entity_id=str(memo.id))
    db.commit()
    return _load_memo(db, memo.id)


def _load_actionable_memo(db: Session, memo_id: uuid.UUID, current_user: User) -> Memo:
    memo = _load_memo(db, memo_id)
    if memo is None or memo.organization_id != current_user.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memo not found")
    if memo.workflow_instance is None or memo.status not in (MemoStatus.pending_approval,):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Memo is not currently awaiting a workflow action")
    return memo


@router.post("/{memo_id}/approve", response_model=MemoDetailOut)
def approve_memo(
    memo_id: uuid.UUID,
    payload: ActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    memo = _load_actionable_memo(db, memo_id, current_user)
    workflow_engine.approve_step(db, memo, current_user, payload.comment)
    log_event(db, organization_id=current_user.organization_id, user_id=current_user.id,
              event_type="memo_approved_step", description=f"{current_user.email} approved memo {memo.memo_number}",
              entity_type="Memo", entity_id=str(memo.id))
    db.commit()
    return _load_memo(db, memo.id)


@router.post("/{memo_id}/reject", response_model=MemoDetailOut)
def reject_memo(
    memo_id: uuid.UUID,
    payload: ActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    memo = _load_actionable_memo(db, memo_id, current_user)
    workflow_engine.reject_step(db, memo, current_user, payload.comment or "")
    log_event(db, organization_id=current_user.organization_id, user_id=current_user.id,
              event_type="memo_rejected", description=f"{current_user.email} rejected memo {memo.memo_number}",
              entity_type="Memo", entity_id=str(memo.id))
    db.commit()
    return _load_memo(db, memo.id)


@router.post("/{memo_id}/request-changes", response_model=MemoDetailOut)
def request_changes_on_memo(
    memo_id: uuid.UUID,
    payload: ActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    memo = _load_actionable_memo(db, memo_id, current_user)
    workflow_engine.request_changes(db, memo, current_user, payload.comment or "")
    log_event(db, organization_id=current_user.organization_id, user_id=current_user.id,
              event_type="memo_changes_requested", description=f"{current_user.email} requested changes on memo {memo.memo_number}",
              entity_type="Memo", entity_id=str(memo.id))
    db.commit()
    return _load_memo(db, memo.id)


@router.post("/{memo_id}/resubmit", response_model=MemoDetailOut)
def resubmit_memo(
    memo_id: uuid.UUID,
    payload: ResubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    memo = _load_memo(db, memo_id)
    if memo is None or memo.organization_id != current_user.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memo not found")
    workflow_engine.resubmit_after_changes(db, memo, current_user, payload.subject, payload.body)
    log_event(db, organization_id=current_user.organization_id, user_id=current_user.id,
              event_type="memo_resubmitted", description=f"Memo {memo.memo_number} resubmitted",
              entity_type="Memo", entity_id=str(memo.id))
    db.commit()
    return _load_memo(db, memo.id)


@router.post("/{memo_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def add_comment(
    memo_id: uuid.UUID,
    payload: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    memo = _load_memo(db, memo_id)
    if memo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memo not found")
    assert_can_view_memo(current_user, memo)
    if not payload.text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Comment text is required")

    comment = Comment(
        memo_id=memo.id,
        author_id=current_user.id,
        comment_type=CommentType.general,
        text=payload.text,
    )
    db.add(comment)
    log_event(db, organization_id=current_user.organization_id, user_id=current_user.id,
              event_type="comment_added", description=f"Comment added on memo {memo.memo_number}",
              entity_type="Memo", entity_id=str(memo.id))
    db.commit()
    db.refresh(comment)
    return comment
