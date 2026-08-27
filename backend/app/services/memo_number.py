import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.memo import Memo
from app.models.organization import Organization


def generate_memo_number(db: Session, organization_id: uuid.UUID) -> str:
    org = db.get(Organization, organization_id)
    year = datetime.now(timezone.utc).year
    count = db.execute(
        select(func.count()).select_from(Memo).where(Memo.organization_id == organization_id)
    ).scalar_one()
    sequence = count + 1
    prefix = (org.identifier if org else "MEMO").upper()
    return f"{prefix}-{year}-{sequence:04d}"
