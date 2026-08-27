import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db import get_db
from app.models.user import User
from app.models.delegation import Delegation
from app.models.enums import DelegationStatus
from app.schemas.misc import DelegationCreate, DelegationOut
from app.services.scoping import get_org_scoped_or_404

router = APIRouter(prefix="/api/delegations", tags=["delegations"])


@router.get("", response_model=list[DelegationOut])
def list_my_delegations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.execute(
        select(Delegation).where(
            Delegation.organization_id == current_user.organization_id,
            or_(Delegation.delegating_user_id == current_user.id, Delegation.delegate_user_id == current_user.id),
        )
    ).scalars().all()


@router.post("", response_model=DelegationOut, status_code=status.HTTP_201_CREATED)
def create_delegation(
    payload: DelegationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    delegate = get_org_scoped_or_404(db, User, payload.delegate_user_id, current_user.organization_id)
    if delegate.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot delegate to yourself")
    if payload.end_date < payload.start_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="End date must be on or after the start date")

    delegation = Delegation(
        organization_id=current_user.organization_id,
        delegating_user_id=current_user.id,
        delegate_user_id=delegate.id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        reason=payload.reason,
    )
    db.add(delegation)
    db.commit()
    db.refresh(delegation)
    return delegation


@router.post("/{delegation_id}/revoke", response_model=DelegationOut)
def revoke_delegation(delegation_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    delegation = get_org_scoped_or_404(db, Delegation, delegation_id, current_user.organization_id)
    if delegation.delegating_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the delegating user may revoke this delegation")
    delegation.status = DelegationStatus.revoked
    db.commit()
    db.refresh(delegation)
    return delegation
