from __future__ import annotations

from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.enums import (
    SectionAuthorType,
    SectionContentType,
    SectionCreationSource,
    section_author_type_enum,
    section_content_type_enum,
    section_creation_source_enum,
)
from app.db.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Section(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sections"

    draft_id: Mapped[UUID] = mapped_column(
        ForeignKey("drafts.id", ondelete="CASCADE"),
        nullable=False,
    )
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    author_type: Mapped[SectionAuthorType] = mapped_column(section_author_type_enum, nullable=False)
    content_type: Mapped[SectionContentType] = mapped_column(section_content_type_enum, nullable=False)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    anchor_human_section_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("sections.id"),
        nullable=True,
    )
    created_via: Mapped[SectionCreationSource] = mapped_column(
        section_creation_source_enum,
        nullable=False,
    )
    # MCP-specific fields
    type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_selection: Mapped[str | None] = mapped_column(Text, nullable=True)
    author_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    position_after_paragraph: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    draft: Mapped[object] = relationship("Draft", back_populates="sections")
    anchor_human_section: Mapped[object | None] = relationship(
        "Section",
        remote_side="Section.id",
        back_populates="ai_sections",
    )
    ai_sections: Mapped[list[object]] = relationship("Section", back_populates="anchor_human_section")

    __table_args__ = (
        UniqueConstraint("draft_id", "ordinal", name="uq_sections_draft_ordinal"),
        CheckConstraint("ordinal >= 0", name="ck_sections_ordinal_non_negative"),
        CheckConstraint("word_count >= 0", name="ck_sections_word_count_non_negative"),
        CheckConstraint("position_after_paragraph >= 0", name="ck_sections_position_after_paragraph_non_negative"),
        CheckConstraint(
            "(author_type != 'HUMAN') OR anchor_human_section_id IS NULL",
            name="ck_sections_human_anchor_null",
        ),
        CheckConstraint(
            "(author_type != 'AI') OR anchor_human_section_id IS NOT NULL",
            name="ck_sections_ai_anchor_required",
        ),
    )

    def get_mcp_content_type(self) -> str:
        """Return MCP-compatible content_type string (ai/human)."""
        return "ai" if self.author_type == SectionAuthorType.AI else "human"
