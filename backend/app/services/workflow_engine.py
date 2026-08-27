import uuid
from datetime import date, datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.memo import Memo, MemoVersion
from app.models.workflow import WorkflowInstance, WorkflowStep
from app.models.enums import (
    MemoStatus,
    WorkflowInstanceStatus,
    WorkflowStepStatus,
    CommentType,
)
from app.models.comment import Comment
from app.models.delegation import Delegation
from app.models.enums import DelegationStatus
from app.models.user import User
from app.services.notify import notify


def _active_delegate_source(db: Session, acting_user_id: uuid.UUID) -> uuid.UUID | None:
    """If acting_user is currently an active delegate for someone, return that someone's id."""
    today = date.today()
    delegation = db.execute(
        select(Delegation).where(
            Delegation.delegate_user_id == acting_user_id,
            Delegation.status == DelegationStatus.active,
            Delegation.start_date <= today,
            Delegation.end_date >= today,
        )
    ).scalars().first()
    return delegation.delegating_user_id if delegation else None


def resolve_actor_for_step(db: Session, step: WorkflowStep, acting_user: User) -> uuid.UUID:
    """Return the id the action should be recorded as being performed on behalf of.

    Raises 403 if acting_user is neither the assignee nor their active delegate.
    """
    if step.assigned_user_id == acting_user.id:
        return acting_user.id
    delegated_from = _active_delegate_source(db, acting_user.id)
    if delegated_from == step.assigned_user_id:
        return step.assigned_user_id
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="It is not your turn to act on this memo",
    )


def start_workflow(
    db: Session,
    memo: Memo,
    participants: list[tuple[uuid.UUID, str | None]],
) -> WorkflowInstance:
    if not participants:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one workflow participant is required")

    instance = memo.workflow_instance
    if instance is None:
        instance = WorkflowInstance(memo_id=memo.id)
        db.add(instance)
    instance.current_step_index = 0
    instance.status = WorkflowInstanceStatus.in_progress
    instance.steps = [
        WorkflowStep(
            position_index=idx,
            label=label,
            assigned_user_id=user_id,
            status=WorkflowStepStatus.current if idx == 0 else WorkflowStepStatus.pending,
        )
        for idx, (user_id, label) in enumerate(participants)
    ]
    memo.status = MemoStatus.pending_approval
    memo.submitted_at = datetime.now(timezone.utc)

    first = instance.steps[0]
    notify(
        db,
        organization_id=memo.organization_id,
        user_id=first.assigned_user_id,
        event_type="assigned",
        message=f"Memo {memo.memo_number} — {memo.subject} requires your action",
        memo_id=memo.id,
    )
    return instance


def _current_step(instance: WorkflowInstance) -> WorkflowStep:
    return instance.steps[instance.current_step_index]


def approve_step(db: Session, memo: Memo, acting_user: User, comment_text: str | None) -> None:
    instance = memo.workflow_instance
    step = _current_step(instance)
    on_behalf_of = resolve_actor_for_step(db, step, acting_user)

    step.status = WorkflowStepStatus.approved
    step.acted_at = datetime.now(timezone.utc)
    step.acted_by_id = acting_user.id
    step.comment = comment_text

    if comment_text:
        db.add(
            Comment(
                memo_id=memo.id,
                author_id=acting_user.id,
                on_behalf_of_id=on_behalf_of if on_behalf_of != acting_user.id else None,
                comment_type=CommentType.approval,
                text=comment_text,
            )
        )

    is_last = instance.current_step_index == len(instance.steps) - 1
    if is_last:
        instance.status = WorkflowInstanceStatus.approved
        memo.status = MemoStatus.approved
        notify(
            db,
            organization_id=memo.organization_id,
            user_id=memo.author_id,
            event_type="approved",
            message=f"Memo {memo.memo_number} — {memo.subject} has been fully approved",
            memo_id=memo.id,
        )
    else:
        instance.current_step_index += 1
        next_step = _current_step(instance)
        next_step.status = WorkflowStepStatus.current
        notify(
            db,
            organization_id=memo.organization_id,
            user_id=next_step.assigned_user_id,
            event_type="assigned",
            message=f"Memo {memo.memo_number} — {memo.subject} requires your action",
            memo_id=memo.id,
        )
        notify(
            db,
            organization_id=memo.organization_id,
            user_id=memo.author_id,
            event_type="forwarded",
            message=f"Memo {memo.memo_number} was approved by a participant and forwarded",
            memo_id=memo.id,
        )


def reject_step(db: Session, memo: Memo, acting_user: User, reason: str) -> None:
    if not reason or not reason.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A rejection reason is required")
    instance = memo.workflow_instance
    step = _current_step(instance)
    on_behalf_of = resolve_actor_for_step(db, step, acting_user)

    step.status = WorkflowStepStatus.rejected
    step.acted_at = datetime.now(timezone.utc)
    step.acted_by_id = acting_user.id
    step.comment = reason

    instance.status = WorkflowInstanceStatus.rejected
    memo.status = MemoStatus.rejected

    db.add(
        Comment(
            memo_id=memo.id,
            author_id=acting_user.id,
            on_behalf_of_id=on_behalf_of if on_behalf_of != acting_user.id else None,
            comment_type=CommentType.rejection,
            text=reason,
        )
    )
    notify(
        db,
        organization_id=memo.organization_id,
        user_id=memo.author_id,
        event_type="rejected",
        message=f"Memo {memo.memo_number} — {memo.subject} was rejected",
        memo_id=memo.id,
    )


def request_changes(db: Session, memo: Memo, acting_user: User, reason: str) -> None:
    if not reason or not reason.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A comment explaining the requested changes is required")
    instance = memo.workflow_instance
    step = _current_step(instance)
    on_behalf_of = resolve_actor_for_step(db, step, acting_user)

    step.status = WorkflowStepStatus.changes_requested
    step.acted_at = datetime.now(timezone.utc)
    step.acted_by_id = acting_user.id
    step.comment = reason

    instance.status = WorkflowInstanceStatus.changes_requested
    memo.status = MemoStatus.changes_requested

    db.add(
        Comment(
            memo_id=memo.id,
            author_id=acting_user.id,
            on_behalf_of_id=on_behalf_of if on_behalf_of != acting_user.id else None,
            comment_type=CommentType.change_request,
            text=reason,
        )
    )
    notify(
        db,
        organization_id=memo.organization_id,
        user_id=memo.author_id,
        event_type="changes_requested",
        message=f"Changes were requested on memo {memo.memo_number} — {memo.subject}",
        memo_id=memo.id,
    )


def resubmit_after_changes(db: Session, memo: Memo, author: User, new_subject: str, new_body: str) -> None:
    if memo.author_id != author.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the author may resubmit this memo")
    if memo.status != MemoStatus.changes_requested:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Memo is not awaiting changes")

    existing_versions = len(memo.versions)
    db.add(
        MemoVersion(
            memo_id=memo.id,
            version_number=existing_versions + 1,
            editor_id=author.id,
            subject=memo.subject,
            body=memo.body,
        )
    )

    memo.subject = new_subject
    memo.body = new_body

    instance = memo.workflow_instance
    instance.current_step_index = 0
    instance.status = WorkflowInstanceStatus.in_progress
    for idx, step in enumerate(instance.steps):
        step.status = WorkflowStepStatus.current if idx == 0 else WorkflowStepStatus.pending
        step.acted_at = None
        step.acted_by_id = None
        step.comment = None
    memo.status = MemoStatus.pending_approval

    first = instance.steps[0]
    notify(
        db,
        organization_id=memo.organization_id,
        user_id=first.assigned_user_id,
        event_type="resubmitted",
        message=f"Memo {memo.memo_number} — {memo.subject} was resubmitted and requires your action",
        memo_id=memo.id,
    )
