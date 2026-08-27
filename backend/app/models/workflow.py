import uuid
from datetime import datetime

from sqlalchemy import String, Text, ForeignKey, Enum as SAEnum, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base import UUIDMixin, TimestampMixin
from app.models.enums import WorkflowInstanceStatus, WorkflowStepStatus


class WorkflowInstance(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "workflow_instances"

    memo_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("memos.id"), nullable=False, unique=True)
    current_step_index: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[WorkflowInstanceStatus] = mapped_column(
        SAEnum(WorkflowInstanceStatus, name="workflow_instance_status"),
        default=WorkflowInstanceStatus.in_progress,
    )

    memo = relationship("Memo", back_populates="workflow_instance")
    steps = relationship(
        "WorkflowStep",
        back_populates="workflow_instance",
        order_by="WorkflowStep.position_index",
        cascade="all, delete-orphan",
    )


class WorkflowStep(UUIDMixin, Base):
    __tablename__ = "workflow_steps"

    workflow_instance_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflow_instances.id"), nullable=False, index=True
    )
    position_index: Mapped[int] = mapped_column(Integer, nullable=False)
    label: Mapped[str | None] = mapped_column(String(150))
    assigned_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status: Mapped[WorkflowStepStatus] = mapped_column(
        SAEnum(WorkflowStepStatus, name="workflow_step_status"), default=WorkflowStepStatus.pending
    )
    acted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acted_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    comment: Mapped[str | None] = mapped_column(Text)

    workflow_instance = relationship("WorkflowInstance", back_populates="steps")
