"""add MCP provenance fields to sections

Revision ID: 0002_section_mcp_provenance
Revises: 0001_humanfirst_baseline
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_section_mcp_provenance"
down_revision = "0001_humanfirst_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sections", sa.Column("type", sa.String(length=64), nullable=True))
    op.add_column("sections", sa.Column("source_selection", sa.Text(), nullable=True))
    op.add_column("sections", sa.Column("author_prompt", sa.Text(), nullable=True))
    op.add_column(
        "sections",
        sa.Column("position_after_paragraph", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_check_constraint(
        "ck_sections_position_after_paragraph_non_negative",
        "sections",
        "position_after_paragraph >= 0",
    )


def downgrade() -> None:
    op.drop_constraint("ck_sections_position_after_paragraph_non_negative", "sections")
    op.drop_column("sections", "position_after_paragraph")
    op.drop_column("sections", "author_prompt")
    op.drop_column("sections", "source_selection")
    op.drop_column("sections", "type")
