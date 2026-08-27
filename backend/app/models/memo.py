import uuid
from datetime import datetime

from sqlalchemy import String, Text, ForeignKey, Enum as SAEnum, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base import UUIDMixin, TimestampMixin
from app.models.enums import MemoPriority, MemoStatus


class Memo(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "memos"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    memo_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    author_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    department_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id"))
    category_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("memo_categories.id"))
    priority: Mapped[MemoPriority] = mapped_column(
        SAEnum(MemoPriority, name="memo_priority"), default=MemoPriority.normal
    )
    status: Mapped[MemoStatus] = mapped_column(
        SAEnum(MemoStatus, name="memo_status"), default=MemoStatus.draft, index=True
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    versions = relationship(
        "MemoVersion", back_populates="memo", order_by="MemoVersion.version_number", cascade="all, delete-orphan"
    )
    workflow_instance = relationship(
        "WorkflowInstance", back_populates="memo", uselist=False, cascade="all, delete-orphan"
    )
    comments = relationship("Comment", back_populates="memo", cascade="all, delete-orphan")
    attachments = relationship("Attachment", back_populates="memo", cascade="all, delete-orphan")


class MemoVersion(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "memo_versions"

    memo_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("memos.id"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    editor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    subject: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")

    memo = relationship("Memo", back_populates="versions")
