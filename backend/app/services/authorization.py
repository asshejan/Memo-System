from fastapi import HTTPException, status

from app.models.memo import Memo
from app.models.user import User
from app.models.enums import UserRole


def assert_can_view_memo(user: User, memo: Memo) -> None:
    """A memo is visible to its author, its org admins, and anyone who is (or was) a
    workflow participant on it. Everyone else — including same-org users with no
    connection to the memo — gets a 404, matching "view memos they are authorized to access".
    """
    if memo.organization_id != user.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memo not found")
    if memo.author_id == user.id or user.role == UserRole.org_admin:
        return
    if memo.workflow_instance:
        participant_ids = {step.assigned_user_id for step in memo.workflow_instance.steps}
        if user.id in participant_ids:
            return
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memo not found")
