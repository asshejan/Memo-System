import uuid

from sqlalchemy import Text, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base import UUIDMixin, TimestampMixin
from app.models.enums import CommentType


class Comment(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "comments"

    memo_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("memos.id"), nullable=False, index=True)
    author_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    on_behalf_of_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    comment_type: Mapped[CommentType] = mapped_column(
        SAEnum(CommentType, name="comment_type"), default=CommentType.general
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)

    memo = relationship("Memo", back_populates="comments")
