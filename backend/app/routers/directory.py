from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db import get_db
from app.models.user import User
from app.models.department import Department
from app.models.category import MemoCategory
from app.models.enums import DepartmentStatus, CategoryStatus
from app.schemas.auth import UserOut
from app.schemas.org_admin import DepartmentOut, CategoryOut

router = APIRouter(prefix="/api/directory", tags=["directory"])


@router.get("/users", response_model=list[UserOut])
def list_org_users(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """All users in the caller's own organization (including inactive) — used both to populate
    workflow-participant pickers (frontend filters to status == active for that case) and to
    resolve names for historical memos that reference a since-deactivated user."""
    return db.execute(
        select(User).where(User.organization_id == current_user.organization_id)
    ).scalars().all()


@router.get("/departments", response_model=list[DepartmentOut])
def list_active_departments(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.execute(
        select(Department).where(
            Department.organization_id == current_user.organization_id, Department.status == DepartmentStatus.active
        )
    ).scalars().all()


@router.get("/categories", response_model=list[CategoryOut])
def list_active_categories(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.execute(
        select(MemoCategory).where(
            MemoCategory.organization_id == current_user.organization_id, MemoCategory.status == CategoryStatus.active
        )
    ).scalars().all()
