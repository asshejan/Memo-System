import uuid
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db import get_db
from app.models.user import User
from app.models.memo import Memo
from app.models.workflow import WorkflowInstance, WorkflowStep
from app.models.enums import MemoStatus, MemoPriority, UserRole
from app.schemas.memo import MemoOut

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("/memos", response_model=list[MemoOut])
def search_memos(
    q: str | None = None,
    author_id: uuid.UUID | None = None,
    department_id: uuid.UUID | None = None,
    category_id: uuid.UUID | None = None,
    status_filter: MemoStatus | None = None,
    priority: MemoPriority | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Always scoped to the caller's organization — never cross-tenant, regardless of filters supplied.
    query = select(Memo).where(Memo.organization_id == current_user.organization_id)

    if current_user.role != UserRole.org_admin:
        step_instance_ids = db.execute(
            select(WorkflowStep.workflow_instance_id).where(WorkflowStep.assigned_user_id == current_user.id)
        ).scalars().all()
        participant_memo_ids = set(
            db.execute(select(WorkflowInstance.memo_id).where(WorkflowInstance.id.in_(step_instance_ids))).scalars().all()
        )
        query = query.where(or_(Memo.author_id == current_user.id, Memo.id.in_(participant_memo_ids)))

    if q:
        like = f"%{q}%"
        query = query.where(or_(Memo.subject.ilike(like), Memo.body.ilike(like), Memo.memo_number.ilike(like)))
    if author_id:
        query = query.where(Memo.author_id == author_id)
    if department_id:
        query = query.where(Memo.department_id == department_id)
    if category_id:
        query = query.where(Memo.category_id == category_id)
    if status_filter:
        query = query.where(Memo.status == status_filter)
    if priority:
        query = query.where(Memo.priority == priority)
    if date_from:
        query = query.where(Memo.created_at >= date_from)
    if date_to:
        query = query.where(Memo.created_at <= date_to)

    query = query.order_by(Memo.created_at.desc()).limit(200)
    return db.execute(query).scalars().all()
