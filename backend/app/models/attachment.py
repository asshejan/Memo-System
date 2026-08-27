import uuid

from sqlalchemy import String, Integer, ForeignKey, LargeBinary
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base import UUIDMixin, TimestampMixin


class Attachment(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "attachments"

    memo_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("memos.id"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(150), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    uploaded_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    memo = relationship("Memo", back_populates="attachments")
