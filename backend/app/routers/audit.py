from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import require_org_admin
from app.db import get_db
from app.models.user import User
from app.models.audit import AuditLog
from app.schemas.misc import AuditLogOut

router = APIRouter(prefix="/api/audit-log", tags=["audit"])


@router.get("", response_model=list[AuditLogOut])
def list_audit_log(current_user: User = Depends(require_org_admin), db: Session = Depends(get_db)):
    return db.execute(
        select(AuditLog)
        .where(AuditLog.organization_id == current_user.organization_id)
        .order_by(AuditLog.created_at.desc())
        .limit(500)
    ).scalars().all()
