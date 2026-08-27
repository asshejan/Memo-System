import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import DelegationStatus


class AttachmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    memo_id: uuid.UUID
    filename: str
    mime_type: str
    size_bytes: int
    uploaded_by_id: uuid.UUID
    created_at: datetime


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    memo_id: uuid.UUID | None
    event_type: str
    message: str
    read_at: datetime | None
    created_at: datetime


class DelegationCreate(BaseModel):
    delegate_user_id: uuid.UUID
    start_date: date
    end_date: date
    reason: str | None = None


class DelegationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    delegating_user_id: uuid.UUID
    delegate_user_id: uuid.UUID
    start_date: date
    end_date: date
    reason: str | None
    status: DelegationStatus


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: uuid.UUID | None
    event_type: str
    entity_type: str | None
    entity_id: str | None
    description: str
    created_at: datetime
