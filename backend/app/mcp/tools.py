from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Any

from fastmcp import Context, FastMCP
from fastmcp.exceptions import ToolError
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db import session as db_session
from app.db.models import Draft, Section
from app.mcp.auth import MCPError, require_mcp_user

ALLOWED_SECTION_TYPES = {
    "example",
    "rephrase",
    "case_study",
    "key_takeaways",
    "visualise",
}


def count_words(text: str) -> int:
    return len(text.split())


def isoformat(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def section_to_payload(section: Section) -> dict[str, Any]:
    return {
        "id": str(section.id),
        "draft_id": str(section.draft_id),
        "content_type": section.get_mcp_content_type(),
        "type": section.type,
        "content": section.content,
        "source_selection": section.source_selection,
        "author_prompt": section.author_prompt,
        "position_after_paragraph": section.position_after_paragraph,
        "word_count": section.word_count,
        "created_at": isoformat(section.created_at),
    }


def ordered_sections(sections: Sequence[Section]) -> list[Section]:
    return sorted(
        sections,
        key=lambda section: (
            section.position_after_paragraph,
            section.created_at,
            section.id,
        ),
    )


def validate_section_type(section_type: str) -> None:
    if section_type not in ALLOWED_SECTION_TYPES:
        raise MCPError(
            code="invalid_section_type",
            message=f"Unsupported section type: {section_type}",
        )


def ensure_draft_ready_for_ai(draft: Draft) -> None:
    if not draft.is_locked:
        raise MCPError(
            code="draft_not_ready_for_ai",
            message="Draft must be locked before saving AI sections.",
        )


def validate_section_position(draft: Draft, position_after_paragraph: int) -> None:
    from app.db.models.enums import SectionAuthorType

    human_positions = {
        section.position_after_paragraph
        for section in draft.sections
        if section.author_type == SectionAuthorType.HUMAN
    }
    if position_after_paragraph not in human_positions:
        raise MCPError(
            code="invalid_section_position",
            message="Position must match an existing human paragraph boundary.",
        )


async def get_owned_draft(session, *, draft_id: str, author_id: object) -> Draft:
    from uuid import UUID

    result = await session.execute(
        select(Draft)
        .where(Draft.id == UUID(draft_id), Draft.author_id == author_id)
        .options(selectinload(Draft.sections))
    )
    draft = result.scalar_one_or_none()
    if draft is None:
        raise MCPError(code="draft_not_found", message="Draft was not found.")
    return draft


async def get_owned_ai_section(session, *, section_id: str, author_id: object) -> Section:
    from uuid import UUID

    result = await session.execute(
        select(Section)
        .join(Section.draft)
        .where(Section.id == UUID(section_id), Draft.author_id == author_id)
        .options(selectinload(Section.draft).selectinload(Draft.sections))
    )
    section = result.scalar_one_or_none()
    if section is None:
        raise MCPError(code="section_not_found", message="Section was not found.")
    return section


async def ping_for_user(user) -> dict[str, Any]:
    return {
        "ok": True,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
        },
    }


async def list_drafts_for_user(user) -> dict[str, Any]:
    from app.db.models.enums import SectionAuthorType

    async with db_session.AsyncSessionLocal() as session:
        result = await session.execute(
            select(Draft)
            .where(Draft.author_id == user.id)
            .order_by(Draft.updated_at.desc(), Draft.id.desc())
            .options(selectinload(Draft.sections))
        )
        drafts = result.scalars().all()

    items = []
    for draft in drafts:
        ai_section_count = sum(1 for section in draft.sections if section.author_type == SectionAuthorType.AI)
        items.append(
            {
                "id": str(draft.id),
                "title": draft.title,
                "status": draft.mcp_status,
                "word_count": draft.word_count,
                "created_at": isoformat(draft.created_at),
                "updated_at": isoformat(draft.updated_at),
                "section_count": len(draft.sections),
                "ai_section_count": ai_section_count,
            }
        )
    return {"items": items}


async def get_draft_for_user(user, draft_id: str) -> dict[str, Any]:
    async with db_session.AsyncSessionLocal() as session:
        draft = await get_owned_draft(session, draft_id=draft_id, author_id=user.id)
        sections = ordered_sections(draft.sections)

    return {
        "id": str(draft.id),
        "title": draft.title,
        "status": draft.mcp_status,
        "word_count": draft.word_count,
        "body_text": draft.body_text,
        "sections": [section_to_payload(section) for section in sections],
    }


async def save_section_for_user(
    user,
    *,
    draft_id: str,
    type: str,
    content: str,
    source_selection: str | None,
    author_prompt: str | None,
    position_after_paragraph: int,
) -> dict[str, Any]:
    from app.db.models.enums import SectionAuthorType, SectionContentType, SectionCreationSource

    validate_section_type(type)

    async with db_session.AsyncSessionLocal() as session:
        draft = await get_owned_draft(session, draft_id=draft_id, author_id=user.id)
        ensure_draft_ready_for_ai(draft)
        validate_section_position(draft, position_after_paragraph)

        # Calculate next ordinal: max existing ordinal + 1, or 1 if no sections exist
        max_ordinal = max((s.ordinal for s in draft.sections), default=0)
        next_ordinal = max_ordinal + 1

        # Map MCP type to SectionContentType enum
        content_type_map = {
            "example": SectionContentType.EXAMPLE,
            "rephrase": SectionContentType.REPHRASE,
            "case_study": SectionContentType.CASE_STUDY,
            "key_takeaways": SectionContentType.KEY_TAKEAWAYS,
            "visualise": SectionContentType.VISUALISE,
        }
        content_type_enum = content_type_map.get(type, SectionContentType.BODY_PARAGRAPH)

        # Find an anchor human section at the given position
        anchor_section = next(
            (s for s in draft.sections
             if s.author_type == SectionAuthorType.HUMAN and s.position_after_paragraph == position_after_paragraph),
            None
        )

        section = Section(
            draft_id=draft.id,
            ordinal=next_ordinal,
            author_type=SectionAuthorType.AI,
            content_type=content_type_enum,
            type=type,
            content=content,
            anchor_human_section_id=anchor_section.id if anchor_section else None,
            source_selection=source_selection,
            author_prompt=author_prompt,
            position_after_paragraph=position_after_paragraph,
            word_count=count_words(content),
            created_via=SectionCreationSource.MCP,
        )
        draft.updated_at = datetime.now(timezone.utc)
        session.add(section)
        await session.commit()
        await session.refresh(section)

    return {"ok": True, "section": section_to_payload(section)}


async def delete_section_for_user(user, *, section_id: str) -> dict[str, Any]:
    from app.db.models.enums import SectionAuthorType

    async with db_session.AsyncSessionLocal() as session:
        section = await get_owned_ai_section(session, section_id=section_id, author_id=user.id)
        if section.author_type != SectionAuthorType.AI:
            raise MCPError(
                code="section_not_deletable",
                message="Only AI sections can be deleted.",
            )

        section.draft.updated_at = datetime.now(timezone.utc)
        await session.delete(section)
        await session.commit()

    return {"ok": True}


def as_tool_error(error: MCPError) -> ToolError:
    return ToolError(f"{error.code}: {error.message}")


async def ping_tool(ctx: Context) -> dict[str, Any]:
    user = require_mcp_user(ctx)
    return await ping_for_user(user)


async def list_drafts_tool(ctx: Context) -> dict[str, Any]:
    user = require_mcp_user(ctx)
    return await list_drafts_for_user(user)


async def get_draft_tool(draft_id: str, ctx: Context) -> dict[str, Any]:
    user = require_mcp_user(ctx)
    return await get_draft_for_user(user, draft_id)


async def save_section_tool(
    draft_id: str,
    type: str,
    content: str,
    source_selection: str | None,
    author_prompt: str | None,
    position_after_paragraph: int,
    word_count: int | None,
    ctx: Context,
) -> dict[str, Any]:
    del word_count
    user = require_mcp_user(ctx)
    return await save_section_for_user(
        user,
        draft_id=draft_id,
        type=type,
        content=content,
        source_selection=source_selection,
        author_prompt=author_prompt,
        position_after_paragraph=position_after_paragraph,
    )


async def delete_section_tool(section_id: str, ctx: Context) -> dict[str, Any]:
    user = require_mcp_user(ctx)
    return await delete_section_for_user(user, section_id=section_id)


def register_tools(mcp: FastMCP) -> None:
    @mcp.tool(name="ping")
    async def ping_registered(ctx: Context) -> dict[str, Any]:
        try:
            return await ping_tool(ctx)
        except MCPError as error:
            raise as_tool_error(error) from error

    @mcp.tool(name="list_drafts")
    async def list_drafts_registered(ctx: Context) -> dict[str, Any]:
        try:
            return await list_drafts_tool(ctx)
        except MCPError as error:
            raise as_tool_error(error) from error

    @mcp.tool(name="get_draft")
    async def get_draft_registered(draft_id: str, ctx: Context) -> dict[str, Any]:
        try:
            return await get_draft_tool(draft_id, ctx)
        except MCPError as error:
            raise as_tool_error(error) from error

    @mcp.tool(name="save_section")
    async def save_section_registered(
        draft_id: str,
        type: str,
        content: str,
        source_selection: str | None = None,
        author_prompt: str | None = None,
        position_after_paragraph: int = 0,
        word_count: int | None = None,
        *,
        ctx: Context,
    ) -> dict[str, Any]:
        try:
            return await save_section_tool(
                draft_id=draft_id,
                type=type,
                content=content,
                source_selection=source_selection,
                author_prompt=author_prompt,
                position_after_paragraph=position_after_paragraph,
                word_count=word_count,
                ctx=ctx,
            )
        except MCPError as error:
            raise as_tool_error(error) from error

    @mcp.tool(name="delete_section")
    async def delete_section_registered(section_id: str, ctx: Context) -> dict[str, Any]:
        try:
            return await delete_section_tool(section_id, ctx)
        except MCPError as error:
            raise as_tool_error(error) from error
