from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, JSON, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


json_document = JSON().with_variant(JSONB, "postgresql")


class Post(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "posts"

    draft_id: Mapped[UUID] = mapped_column(ForeignKey("drafts.id"), nullable=False, unique=True)
    author_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    author_display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    slug: Mapped[str] = mapped_column(String(180), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    human_word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    ai_word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    like_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    comment_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    provenance_summary: Mapped[dict[str, object]] = mapped_column(
        json_document,
        nullable=False,
        default=dict,
        server_default=text("'{}'"),
    )

    draft: Mapped[object] = relationship("Draft", back_populates="post")
    author: Mapped[object] = relationship("User", back_populates="posts")
    comments: Mapped[list[object]] = relationship(
        "Comment",
        back_populates="post",
        cascade="all, delete-orphan",
    )
    likes: Mapped[list[object]] = relationship(
        "Like",
        back_populates="post",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint("human_word_count >= 0", name="ck_posts_human_word_count_non_negative"),
        CheckConstraint("ai_word_count >= 0", name="ck_posts_ai_word_count_non_negative"),
        CheckConstraint("like_count >= 0", name="ck_posts_like_count_non_negative"),
        CheckConstraint("comment_count >= 0", name="ck_posts_comment_count_non_negative"),
    )
