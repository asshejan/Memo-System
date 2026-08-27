import uuid
from datetime import date

from sqlalchemy import String, ForeignKey, Date, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.base import UUIDMixin, TimestampMixin
from app.models.enums import DelegationStatus


class Delegation(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "delegations"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    delegating_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    delegate_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[DelegationStatus] = mapped_column(
        SAEnum(DelegationStatus, name="delegation_status"), default=DelegationStatus.active
    )
