import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_org_admin
from app.core.security import hash_password
from app.db import get_db
from app.models.user import User
from app.models.department import Department
from app.models.category import MemoCategory
from app.models.workflow_template import WorkflowTemplate, WorkflowTemplatePosition
from app.models.organization import Organization
from app.models.memo import Memo
from app.models.workflow import WorkflowInstance
from app.models.enums import MemoStatus, WorkflowInstanceStatus
from app.schemas.auth import UserOut, OrganizationOut
from app.schemas.org_admin import (
    DepartmentCreate, DepartmentUpdate, DepartmentOut,
    UserInvite, UserUpdate,
    CategoryCreate, CategoryUpdate, CategoryOut,
    TemplateCreate, TemplateOut,
    OrganizationUpdate,
)
from app.services.scoping import get_org_scoped_or_404
from app.services.audit import log_event

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ---- Organization ----

@router.get("/organization", response_model=OrganizationOut)
def get_organization(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.get(Organization, current_user.organization_id)


@router.patch("/organization", response_model=OrganizationOut)
def update_organization(
    payload: OrganizationUpdate,
    current_user: User = Depends(require_org_admin),
    db: Session = Depends(get_db),
):
    org = db.get(Organization, current_user.organization_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(org, field, value)
    db.commit()
    db.refresh(org)
    return org


@router.get("/stats")
def get_org_stats(current_user: User = Depends(require_org_admin), db: Session = Depends(get_db)):
    org_id = current_user.organization_id
    user_count = db.execute(select(func.count()).select_from(User).where(User.organization_id == org_id)).scalar_one()
    active_user_count = db.execute(
        select(func.count()).select_from(User).where(User.organization_id == org_id, User.status == "active")
    ).scalar_one()
    dept_count = db.execute(
        select(func.count()).select_from(Department).where(Department.organization_id == org_id)
    ).scalar_one()
    memo_count = db.execute(select(func.count()).select_from(Memo).where(Memo.organization_id == org_id)).scalar_one()
    pending = db.execute(
        select(func.count()).select_from(WorkflowInstance).join(Memo).where(
            Memo.organization_id == org_id, WorkflowInstance.status == WorkflowInstanceStatus.in_progress
        )
    ).scalar_one()
    completed = db.execute(
        select(func.count()).select_from(WorkflowInstance).join(Memo).where(
            Memo.organization_id == org_id, WorkflowInstance.status == WorkflowInstanceStatus.approved
        )
    ).scalar_one()
    rejected = db.execute(
        select(func.count()).select_from(WorkflowInstance).join(Memo).where(
            Memo.organization_id == org_id, WorkflowInstance.status == WorkflowInstanceStatus.rejected
        )
    ).scalar_one()
    return {
        "user_count": user_count,
        "active_user_count": active_user_count,
        "department_count": dept_count,
        "memo_count": memo_count,
        "pending_workflows": pending,
        "completed_workflows": completed,
        "rejected_workflows": rejected,
    }


# ---- Departments ----

@router.get("/departments", response_model=list[DepartmentOut])
def list_departments(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.execute(
        select(Department).where(Department.organization_id == current_user.organization_id)
    ).scalars().all()


@router.post("/departments", response_model=DepartmentOut, status_code=status.HTTP_201_CREATED)
def create_department(
    payload: DepartmentCreate,
    current_user: User = Depends(require_org_admin),
    db: Session = Depends(get_db),
):
    dept = Department(organization_id=current_user.organization_id, **payload.model_dump())
    db.add(dept)
    log_event(db, organization_id=current_user.organization_id, user_id=current_user.id,
              event_type="department_created", description=f"Department '{dept.name}' created",
              entity_type="Department", entity_id=str(dept.id))
    db.commit()
    db.refresh(dept)
    return dept


@router.patch("/departments/{department_id}", response_model=DepartmentOut)
def update_department(
    department_id: uuid.UUID,
    payload: DepartmentUpdate,
    current_user: User = Depends(require_org_admin),
    db: Session = Depends(get_db),
):
    dept = get_org_scoped_or_404(db, Department, department_id, current_user.organization_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(dept, field, value)
    log_event(db, organization_id=current_user.organization_id, user_id=current_user.id,
              event_type="department_updated", description=f"Department '{dept.name}' updated",
              entity_type="Department", entity_id=str(dept.id))
    db.commit()
    db.refresh(dept)
    return dept


# ---- Users ----

@router.get("/users", response_model=list[UserOut])
def list_users(current_user: User = Depends(require_org_admin), db: Session = Depends(get_db)):
    return db.execute(select(User).where(User.organization_id == current_user.organization_id)).scalars().all()


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def invite_user(
    payload: UserInvite,
    current_user: User = Depends(require_org_admin),
    db: Session = Depends(get_db),
):
    existing = db.execute(select(User).where(User.email == payload.email)).scalars().first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already registered")
    if payload.department_id:
        get_org_scoped_or_404(db, Department, payload.department_id, current_user.organization_id)

    user = User(
        organization_id=current_user.organization_id,
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        designation=payload.designation,
        department_id=payload.department_id,
        role=payload.role,
    )
    db.add(user)
    log_event(db, organization_id=current_user.organization_id, user_id=current_user.id,
              event_type="user_created", description=f"User '{user.email}' created",
              entity_type="User", entity_id=str(user.id))
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    current_user: User = Depends(require_org_admin),
    db: Session = Depends(get_db),
):
    user = get_org_scoped_or_404(db, User, user_id, current_user.organization_id)
    if payload.department_id:
        get_org_scoped_or_404(db, Department, payload.department_id, current_user.organization_id)
    prior_status = user.status
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    if payload.status is not None and payload.status != prior_status:
        log_event(db, organization_id=current_user.organization_id, user_id=current_user.id,
                   event_type="user_status_changed",
                   description=f"User '{user.email}' status changed to {payload.status.value}",
                   entity_type="User", entity_id=str(user.id))
    db.commit()
    db.refresh(user)
    return user


# ---- Memo Categories ----

@router.get("/categories", response_model=list[CategoryOut])
def list_categories(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.execute(
        select(MemoCategory).where(MemoCategory.organization_id == current_user.organization_id)
    ).scalars().all()


@router.post("/categories", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    current_user: User = Depends(require_org_admin),
    db: Session = Depends(get_db),
):
    category = MemoCategory(organization_id=current_user.organization_id, **payload.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.patch("/categories/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: uuid.UUID,
    payload: CategoryUpdate,
    current_user: User = Depends(require_org_admin),
    db: Session = Depends(get_db),
):
    category = get_org_scoped_or_404(db, MemoCategory, category_id, current_user.organization_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    db.commit()
    db.refresh(category)
    return category


# ---- Workflow Templates ----

@router.get("/templates", response_model=list[TemplateOut])
def list_templates(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.execute(
        select(WorkflowTemplate).where(WorkflowTemplate.organization_id == current_user.organization_id)
    ).scalars().all()


@router.post("/templates", response_model=TemplateOut, status_code=status.HTTP_201_CREATED)
def create_template(
    payload: TemplateCreate,
    current_user: User = Depends(require_org_admin),
    db: Session = Depends(get_db),
):
    template = WorkflowTemplate(organization_id=current_user.organization_id, name=payload.name)
    template.positions = [
        WorkflowTemplatePosition(position_index=p.position_index, label=p.label) for p in payload.positions
    ]
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: uuid.UUID,
    current_user: User = Depends(require_org_admin),
    db: Session = Depends(get_db),
):
    template = get_org_scoped_or_404(db, WorkflowTemplate, template_id, current_user.organization_id)
    db.delete(template)
    db.commit()
