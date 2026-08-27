import uuid

from sqlalchemy import String, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base import UUIDMixin, TimestampMixin


class WorkflowTemplate(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "workflow_templates"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)

    positions = relationship(
        "WorkflowTemplatePosition",
        back_populates="template",
        order_by="WorkflowTemplatePosition.position_index",
        cascade="all, delete-orphan",
    )


class WorkflowTemplatePosition(UUIDMixin, Base):
    __tablename__ = "workflow_template_positions"

    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflow_templates.id"), nullable=False, index=True
    )
    position_index: Mapped[int] = mapped_column(Integer, nullable=False)
    label: Mapped[str] = mapped_column(String(150), nullable=False)

    template = relationship("WorkflowTemplate", back_populates="positions")
