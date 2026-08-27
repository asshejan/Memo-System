from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.deps import require_org_admin
from app.db import get_db
from app.models.user import User
from app.models.memo import Memo
from app.models.enums import MemoStatus
from app.models.workflow import WorkflowStep
from app.models.enums import WorkflowStepStatus

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/summary")
def report_summary(
    date_from: date | None = None,
    date_to: date | None = None,
    department_id: str | None = None,
    category_id: str | None = None,
    current_user: User = Depends(require_org_admin),
    db: Session = Depends(get_db),
):
    query = select(Memo).where(Memo.organization_id == current_user.organization_id)
    if date_from:
        query = query.where(Memo.created_at >= date_from)
    if date_to:
        query = query.where(Memo.created_at <= date_to)
    if department_id:
        query = query.where(Memo.department_id == department_id)
    if category_id:
        query = query.where(Memo.category_id == category_id)

    memos = db.execute(query).scalars().all()

    by_status: dict[str, int] = {}
    by_department: dict[str, int] = {}
    by_category: dict[str, int] = {}
    urgent_count = 0
    completion_seconds: list[float] = []

    for m in memos:
        by_status[m.status.value] = by_status.get(m.status.value, 0) + 1
        if m.department_id:
            key = str(m.department_id)
            by_department[key] = by_department.get(key, 0) + 1
        if m.category_id:
            key = str(m.category_id)
            by_category[key] = by_category.get(key, 0) + 1
        if m.priority.value == "urgent":
            urgent_count += 1
        if m.status == MemoStatus.approved and m.submitted_at:
            last_step = db.execute(
                select(WorkflowStep)
                .join(WorkflowStep.workflow_instance)
                .where(WorkflowStep.status == WorkflowStepStatus.approved)
                .order_by(WorkflowStep.acted_at.desc())
                .limit(1)
            ).scalars().first()
            if last_step and last_step.acted_at:
                completion_seconds.append((last_step.acted_at - m.submitted_at).total_seconds())

    avg_completion_hours = (sum(completion_seconds) / len(completion_seconds) / 3600) if completion_seconds else None

    return {
        "memos_by_status": by_status,
        "memos_by_department": by_department,
        "memos_by_category": by_category,
        "urgent_memo_count": urgent_count,
        "average_workflow_completion_hours": avg_completion_hours,
        "pending_approvals": by_status.get(MemoStatus.pending_approval.value, 0),
        "rejected_count": by_status.get(MemoStatus.rejected.value, 0),
        "change_requests_count": by_status.get(MemoStatus.changes_requested.value, 0),
    }
