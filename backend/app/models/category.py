import uuid

from sqlalchemy import String, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.base import UUIDMixin, TimestampMixin
from app.models.enums import CategoryStatus


class MemoCategory(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "memo_categories"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000))
    status: Mapped[CategoryStatus] = mapped_column(
        SAEnum(CategoryStatus, name="category_status"), default=CategoryStatus.active
    )
