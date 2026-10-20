"""humanfirst baseline

Revision ID: 0001_humanfirst_baseline
Revises:
Create Date: 2026-05-27 17:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_humanfirst_baseline"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


draft_status = postgresql.ENUM("DRAFT", "LOCKED", name="draft_status")
draft_status_existing = postgresql.ENUM(
    "DRAFT",
    "LOCKED",
    name="draft_status",
    create_type=False,
)
section_author_type = postgresql.ENUM("HUMAN", "AI", name="section_author_type")
section_author_type_existing = postgresql.ENUM(
    "HUMAN",
    "AI",
    name="section_author_type",
    create_type=False,
)
section_content_type = postgresql.ENUM(
    "BODY_PARAGRAPH",
    "EXAMPLE",
    "REPHRASE",
    "CASE_STUDY",
    "KEY_TAKEAWAYS",
    "VISUALISE",
    name="section_content_type",
)
section_content_type_existing = postgresql.ENUM(
    "BODY_PARAGRAPH",
    "EXAMPLE",
    "REPHRASE",
    "CASE_STUDY",
    "KEY_TAKEAWAYS",
    "VISUALISE",
    name="section_content_type",
    create_type=False,
)
section_creation_source = postgresql.ENUM(
    "LOCK_MATERIALIZATION",
    "MCP",
    "AUTHOR_EDIT",
    name="section_creation_source",
)
section_creation_source_existing = postgresql.ENUM(
    "LOCK_MATERIALIZATION",
    "MCP",
    "AUTHOR_EDIT",
    name="section_creation_source",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    draft_status.create(bind, checkfirst=True)
    section_author_type.create(bind, checkfirst=True)
    section_content_type.create(bind, checkfirst=True)
    section_creation_source.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=True),
        sa.Column("mcp_token", sa.String(length=80), nullable=False),
        sa.Column("mcp_token_issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("mcp_last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("mcp_token", name="uq_users_mcp_token"),
    )
    op.create_index("uq_users_email_lower", "users", [sa.text("lower(email)")], unique=True)

    op.create_table(
        "drafts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.Text(), nullable=False, server_default=""),
        sa.Column("body", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", draft_status_existing, nullable=False, server_default="DRAFT"),
        sa.Column("keystroke_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("session_duration_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pause_events", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("paste_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("word_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reading_time_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("keystroke_count >= 0", name="ck_drafts_keystroke_count_non_negative"),
        sa.CheckConstraint(
            "session_duration_seconds >= 0",
            name="ck_drafts_session_duration_seconds_non_negative",
        ),
        sa.CheckConstraint("pause_events >= 0", name="ck_drafts_pause_events_non_negative"),
        sa.CheckConstraint("paste_attempts >= 0", name="ck_drafts_paste_attempts_non_negative"),
        sa.CheckConstraint("word_count >= 0", name="ck_drafts_word_count_non_negative"),
        sa.CheckConstraint(
            "reading_time_minutes >= 0",
            name="ck_drafts_reading_time_minutes_non_negative",
        ),
    )
    op.create_index("ix_drafts_author_created_at", "drafts", ["author_id", "created_at"], unique=False)

    op.create_table(
        "sections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "draft_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("drafts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("author_type", section_author_type_existing, nullable=False),
        sa.Column("content_type", section_content_type_existing, nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("word_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "anchor_human_section_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sections.id"),
            nullable=True,
        ),
        sa.Column("created_via", section_creation_source_existing, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("draft_id", "ordinal", name="uq_sections_draft_ordinal"),
        sa.CheckConstraint("ordinal >= 0", name="ck_sections_ordinal_non_negative"),
        sa.CheckConstraint("word_count >= 0", name="ck_sections_word_count_non_negative"),
        sa.CheckConstraint(
            "(author_type != 'HUMAN') OR anchor_human_section_id IS NULL",
            name="ck_sections_human_anchor_null",
        ),
        sa.CheckConstraint(
            "(author_type != 'AI') OR anchor_human_section_id IS NOT NULL",
            name="ck_sections_ai_anchor_required",
        ),
    )

    op.create_table(
        "posts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("draft_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("drafts.id"), nullable=False),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("author_display_name", sa.String(length=120), nullable=True),
        sa.Column("slug", sa.String(length=180), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("human_word_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ai_word_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("like_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("comment_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "provenance_summary",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("draft_id", name="uq_posts_draft_id"),
        sa.UniqueConstraint("slug", name="uq_posts_slug"),
        sa.CheckConstraint("human_word_count >= 0", name="ck_posts_human_word_count_non_negative"),
        sa.CheckConstraint("ai_word_count >= 0", name="ck_posts_ai_word_count_non_negative"),
        sa.CheckConstraint("like_count >= 0", name="ck_posts_like_count_non_negative"),
        sa.CheckConstraint("comment_count >= 0", name="ck_posts_comment_count_non_negative"),
    )

    op.create_table(
        "comments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "post_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("posts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "parent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("comments.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("author_name", sa.String(length=120), nullable=False),
        sa.Column("author_email", sa.String(length=320), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_comments_post_created_at", "comments", ["post_id", "created_at"], unique=False)

    op.create_table(
        "likes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "post_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("posts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("fingerprint_hash", sa.String(length=128), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("post_id", "fingerprint_hash", name="uq_likes_post_fingerprint_hash"),
    )
    op.create_index("ix_likes_post_id", "likes", ["post_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_likes_post_id", table_name="likes")
    op.drop_table("likes")
    op.drop_index("ix_comments_post_created_at", table_name="comments")
    op.drop_table("comments")
    op.drop_table("posts")
    op.drop_table("sections")
    op.drop_index("ix_drafts_author_created_at", table_name="drafts")
    op.drop_table("drafts")
    op.drop_index("uq_users_email_lower", table_name="users")
    op.drop_table("users")

    bind = op.get_bind()
    section_creation_source.drop(bind, checkfirst=True)
    section_content_type.drop(bind, checkfirst=True)
    section_author_type.drop(bind, checkfirst=True)
    draft_status.drop(bind, checkfirst=True)
