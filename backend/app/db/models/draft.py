from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.enums import DraftStatus, draft_status_enum
from app.db.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Draft(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "drafts"

    author_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    body: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    status: Mapped[DraftStatus] = mapped_column(
        draft_status_enum,
        nullable=False,
        default=DraftStatus.DRAFT,
        server_default=DraftStatus.DRAFT.value,
    )
    keystroke_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    session_duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    pause_events: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    paste_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    reading_time_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    author: Mapped[object] = relationship("User", back_populates="drafts")
    sections: Mapped[list[object]] = relationship(
        "Section",
        back_populates="draft",
        cascade="all, delete-orphan",
        order_by="Section.ordinal",
    )
    post: Mapped[object | None] = relationship("Post", back_populates="draft", uselist=False)

    __table_args__ = (
        Index("ix_drafts_author_created_at", "author_id", "created_at"),
        CheckConstraint("keystroke_count >= 0", name="ck_drafts_keystroke_count_non_negative"),
        CheckConstraint(
            "session_duration_seconds >= 0",
            name="ck_drafts_session_duration_seconds_non_negative",
        ),
        CheckConstraint("pause_events >= 0", name="ck_drafts_pause_events_non_negative"),
        CheckConstraint("paste_attempts >= 0", name="ck_drafts_paste_attempts_non_negative"),
        CheckConstraint("word_count >= 0", name="ck_drafts_word_count_non_negative"),
        CheckConstraint(
            "reading_time_minutes >= 0",
            name="ck_drafts_reading_time_minutes_non_negative",
        ),
    )

    @property
    def is_locked(self) -> bool:
        return self.locked_at is not None or self.status == DraftStatus.LOCKED

    @property
    def mcp_status(self) -> str:
        return "locked" if self.is_locked else self.status.value.lower()

    @property
    def body_text(self) -> str:
        """Alias for body field for MCP compatibility."""
        return self.body
