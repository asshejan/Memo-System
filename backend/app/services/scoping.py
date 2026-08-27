import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session


def get_org_scoped_or_404(db: Session, model, object_id: uuid.UUID, organization_id: uuid.UUID):
    """Fetch a row by id and verify it belongs to the caller's organization.

    Always use this (or an equivalent explicit organization_id filter) instead of a bare
    db.get()/query().filter(id=...) for any tenant-scoped model — a bare id lookup would let
    a valid, authenticated user reach another organization's row just by guessing/enumerating
    ids, which is exactly the isolation failure the spec calls out as unacceptable.
    """
    obj = db.get(model, object_id)
    if obj is None or getattr(obj, "organization_id", None) != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{model.__name__} not found")
    return obj
