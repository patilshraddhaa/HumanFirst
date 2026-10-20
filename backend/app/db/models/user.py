from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    mcp_token: Mapped[str] = mapped_column(String(80), nullable=False)
    mcp_token_issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    mcp_last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    drafts: Mapped[list[object]] = relationship("Draft", back_populates="author")
    posts: Mapped[list[object]] = relationship("Post", back_populates="author")

    __table_args__ = (
        Index("uq_users_email_lower", func.lower(email), unique=True),
        UniqueConstraint("mcp_token", name="uq_users_mcp_token"),
    )
