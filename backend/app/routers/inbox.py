import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.deps import get_current_user
from app.db import get_db
from app.models.user import User
from app.models.memo import Memo
from app.models.workflow import WorkflowInstance, WorkflowStep
from app.models.delegation import Delegation
from app.models.enums import MemoStatus, WorkflowStepStatus, DelegationStatus
from app.schemas.memo import MemoOut

router = APIRouter(prefix="/api", tags=["inbox"])


def _acting_user_ids(db: Session, current_user: User) -> set[uuid.UUID]:
    """The user's own id plus anyone currently delegating to them."""
    today = date.today()
    delegators = db.execute(
        select(Delegation.delegating_user_id).where(
            Delegation.delegate_user_id == current_user.id,
            Delegation.status == DelegationStatus.active,
            Delegation.start_date <= today,
            Delegation.end_date >= today,
        )
    ).scalars().all()
    return {current_user.id, *delegators}


@router.get("/inbox", response_model=list[MemoOut])
def get_inbox(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    actor_ids = _acting_user_ids(db, current_user)
    memo_ids = db.execute(
        select(WorkflowStep.workflow_instance_id)
        .where(WorkflowStep.status == WorkflowStepStatus.current, WorkflowStep.assigned_user_id.in_(actor_ids))
    ).scalars().all()
    if not memo_ids:
        return []
    instances = db.execute(
        select(WorkflowInstance.memo_id).where(WorkflowInstance.id.in_(memo_ids))
    ).scalars().all()
    return db.execute(
        select(Memo)
        .where(
            Memo.organization_id == current_user.organization_id,
            Memo.id.in_(instances),
            Memo.status == MemoStatus.pending_approval,
        )
        .order_by(Memo.priority.desc(), Memo.submitted_at.asc())
    ).scalars().all()


@router.get("/memos-completed", response_model=list[MemoOut])
def get_completed(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    actor_ids = _acting_user_ids(db, current_user)
    step_memo_instance_ids = db.execute(
        select(WorkflowStep.workflow_instance_id).where(WorkflowStep.assigned_user_id.in_(actor_ids))
    ).scalars().all()
    participant_memo_ids = set(
        db.execute(select(WorkflowInstance.memo_id).where(WorkflowInstance.id.in_(step_memo_instance_ids))).scalars().all()
    )
    authored_memo_ids = set(
        db.execute(
            select(Memo.id).where(Memo.organization_id == current_user.organization_id, Memo.author_id == current_user.id)
        ).scalars().all()
    )
    visible_ids = participant_memo_ids | authored_memo_ids
    if current_user.role.value == "org_admin":
        return db.execute(
            select(Memo)
            .where(Memo.organization_id == current_user.organization_id, Memo.status.in_([MemoStatus.approved, MemoStatus.rejected]))
            .order_by(Memo.created_at.desc())
        ).scalars().all()
    if not visible_ids:
        return []
    return db.execute(
        select(Memo)
        .where(
            Memo.organization_id == current_user.organization_id,
            Memo.id.in_(visible_ids),
            Memo.status.in_([MemoStatus.approved, MemoStatus.rejected]),
        )
        .order_by(Memo.created_at.desc())
    ).scalars().all()


@router.get("/dashboard")
def get_dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    inbox = get_inbox(current_user, db)
    my_memos = db.execute(
        select(Memo).where(Memo.organization_id == current_user.organization_id, Memo.author_id == current_user.id)
    ).scalars().all()
    completed = get_completed(current_user, db)
    urgent = [m for m in inbox if m.priority.value == "urgent"]

    counts_by_status: dict[str, int] = {}
    for m in my_memos:
        counts_by_status[m.status.value] = counts_by_status.get(m.status.value, 0) + 1

    return {
        "awaiting_action": [MemoOut.model_validate(m) for m in inbox],
        "my_memos": [MemoOut.model_validate(m) for m in my_memos],
        "recently_completed": [MemoOut.model_validate(m) for m in completed[:10]],
        "urgent_memos": [MemoOut.model_validate(m) for m in urgent],
        "memo_counts_by_status": counts_by_status,
    }
