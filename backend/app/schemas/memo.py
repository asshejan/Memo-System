import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import MemoPriority, MemoStatus, WorkflowStepStatus, WorkflowInstanceStatus, CommentType


class MemoCreate(BaseModel):
    subject: str
    body: str = ""
    department_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None
    priority: MemoPriority = MemoPriority.normal


class MemoUpdate(BaseModel):
    subject: str | None = None
    body: str | None = None
    department_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None
    priority: MemoPriority | None = None


class WorkflowParticipantIn(BaseModel):
    position_index: int
    user_id: uuid.UUID
    label: str | None = None


class MemoSubmit(BaseModel):
    template_id: uuid.UUID | None = None
    participants: list[WorkflowParticipantIn]


class ResubmitRequest(BaseModel):
    subject: str
    body: str


class ActionRequest(BaseModel):
    comment: str | None = None


class MemoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    memo_number: str
    subject: str
    body: str
    author_id: uuid.UUID
    department_id: uuid.UUID | None
    category_id: uuid.UUID | None
    priority: MemoPriority
    status: MemoStatus
    created_at: datetime
    submitted_at: datetime | None


class WorkflowStepOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    position_index: int
    label: str | None
    assigned_user_id: uuid.UUID
    status: WorkflowStepStatus
    acted_at: datetime | None
    acted_by_id: uuid.UUID | None
    comment: str | None


class WorkflowInstanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    current_step_index: int
    status: WorkflowInstanceStatus
    steps: list[WorkflowStepOut]


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    author_id: uuid.UUID
    on_behalf_of_id: uuid.UUID | None
    comment_type: CommentType
    text: str
    created_at: datetime


class CommentCreate(BaseModel):
    text: str


class MemoVersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    version_number: int
    editor_id: uuid.UUID
    subject: str
    body: str
    created_at: datetime


class MemoDetailOut(MemoOut):
    workflow_instance: WorkflowInstanceOut | None
    comments: list[CommentOut]
    versions: list[MemoVersionOut]
