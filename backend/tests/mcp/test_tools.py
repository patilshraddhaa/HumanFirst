from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID

import pytest
import pytest_asyncio

from app.core.security import hash_password
from app.mcp.auth import MCPError, extract_bearer_token, resolve_mcp_user_from_headers
from app.mcp.tools import (
    delete_section_for_user,
    get_draft_for_user,
    list_drafts_for_user,
    save_section_for_user,
)


@pytest_asyncio.fixture
async def mcp_server(app_modules: SimpleNamespace):
    from app.mcp.server import create_mcp_server
    return create_mcp_server()


async def seed_user(app_modules: SimpleNamespace, *, email: str, name: str, token: str):
    async with app_modules.session.AsyncSessionLocal() as session:
        user = app_modules.models.User(
            email=email,
            name=name,
            display_name=name,
            password_hash=hash_password("password"),
            mcp_token=token,
            mcp_token_issued_at=datetime.now(timezone.utc),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


async def seed_draft(
    app_modules: SimpleNamespace,
    *,
    author_id: UUID,
    title: str,
    status: str,
    updated_at: datetime,
):
    async with app_modules.session.AsyncSessionLocal() as session:
        status_enum = app_modules.models.DraftStatus.LOCKED if status == "locked" else app_modules.models.DraftStatus.DRAFT
        draft = app_modules.models.Draft(
            author_id=author_id,
            title=title,
            body="Paragraph one.\n\nParagraph two.",
            status=status_enum,
            word_count=4,
        )
        if status == "locked":
            draft.locked_at = datetime.now(timezone.utc)
        session.add(draft)
        await session.commit()
        draft.updated_at = updated_at
        await session.commit()
        await session.refresh(draft)
        return draft


async def seed_section(
    app_modules: SimpleNamespace,
    *,
    draft_id: UUID,
    content_type: str,
    type: str,
    content: str,
    position_after_paragraph: int,
    ordinal: int | None = None,
):
    from sqlalchemy import select

    async with app_modules.session.AsyncSessionLocal() as session:
        author_type_enum = app_modules.models.SectionAuthorType.AI if content_type == "ai" else app_modules.models.SectionAuthorType.HUMAN
        
        # Map type to content_type enum
        content_type_map = {
            "example": app_modules.models.SectionContentType.EXAMPLE,
            "paragraph": app_modules.models.SectionContentType.BODY_PARAGRAPH,
            "rephrase": app_modules.models.SectionContentType.REPHRASE,
        }
        content_type_enum = content_type_map.get(type, app_modules.models.SectionContentType.BODY_PARAGRAPH)

        # Calculate next ordinal if not provided
        if ordinal is None:
            result = await session.execute(
                select(app_modules.models.Section).where(app_modules.models.Section.draft_id == draft_id)
            )
            existing_sections = result.scalars().all()
            max_ordinal = max((s.ordinal for s in existing_sections), default=0)
            ordinal = max_ordinal + 1

        # Find anchor section if AI
        anchor_id = None
        if author_type_enum == app_modules.models.SectionAuthorType.AI:
            result = await session.execute(
                select(app_modules.models.Section).where(
                    app_modules.models.Section.draft_id == draft_id,
                    app_modules.models.Section.author_type == app_modules.models.SectionAuthorType.HUMAN,
                    app_modules.models.Section.position_after_paragraph == position_after_paragraph,
                )
            )
            anchor_section = result.scalars().first()
            if anchor_section:
                anchor_id = anchor_section.id

        created_via = app_modules.models.SectionCreationSource.MCP if author_type_enum == app_modules.models.SectionAuthorType.AI else app_modules.models.SectionCreationSource.LOCK_MATERIALIZATION

        section = app_modules.models.Section(
            draft_id=draft_id,
            ordinal=ordinal,
            author_type=author_type_enum,
            content_type=content_type_enum,
            type=type if author_type_enum == app_modules.models.SectionAuthorType.AI else None,
            content=content,
            position_after_paragraph=position_after_paragraph,
            word_count=len(content.split()),
            anchor_human_section_id=anchor_id,
            created_via=created_via,
        )
        session.add(section)
        await session.commit()
        await session.refresh(section)
        return section


@pytest.mark.asyncio
async def test_resolve_mcp_user_from_headers(app_modules, db_schema) -> None:
    user = await seed_user(app_modules, email="author@example.com", name="Author", token="hf_author")

    resolved = await resolve_mcp_user_from_headers({"authorization": "Bearer hf_author"})

    assert resolved.id == user.id


def test_extract_bearer_token_rejects_invalid_headers() -> None:
    with pytest.raises(MCPError) as missing:
        extract_bearer_token(None)
    assert missing.value.code == "auth_required"

    with pytest.raises(MCPError) as malformed:
        extract_bearer_token("Token hf_nope")
    assert malformed.value.code == "invalid_token"


@pytest.mark.asyncio
async def test_resolve_mcp_user_from_headers_rejects_unknown_token(app_modules, db_schema) -> None:
    with pytest.raises(MCPError) as error:
        await resolve_mcp_user_from_headers({"authorization": "Bearer hf_unknown"})

    assert error.value.code == "invalid_token"


@pytest.mark.asyncio
async def test_server_registers_expected_tools(mcp_server) -> None:
    tool_names = {tool.name for tool in await mcp_server.list_tools(run_middleware=False)}
    assert tool_names == {"ping", "list_drafts", "get_draft", "save_section", "delete_section"}


@pytest.mark.asyncio
async def test_list_drafts_is_author_scoped_and_ordered(app_modules, db_schema) -> None:
    author = await seed_user(app_modules, email="author@example.com", name="Author", token="hf_author")
    other = await seed_user(app_modules, email="other@example.com", name="Other", token="hf_other")

    older = await seed_draft(
        app_modules,
        author_id=author.id,
        title="Older",
        status="locked",
        updated_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    newer = await seed_draft(
        app_modules,
        author_id=author.id,
        title="Newer",
        status="draft",
        updated_at=datetime.now(timezone.utc),
    )
    await seed_draft(
        app_modules,
        author_id=other.id,
        title="Foreign",
        status="locked",
        updated_at=datetime.now(timezone.utc) + timedelta(days=1),
    )

    await seed_section(
        app_modules,
        draft_id=newer.id,
        content_type="human",
        type="paragraph",
        content="Human paragraph",
        position_after_paragraph=0,
    )
    await seed_section(
        app_modules,
        draft_id=newer.id,
        content_type="ai",
        type="example",
        content="AI expansion",
        position_after_paragraph=0,
    )
    await seed_section(
        app_modules,
        draft_id=older.id,
        content_type="human",
        type="paragraph",
        content="Older human paragraph",
        position_after_paragraph=0,
    )

    payload = await list_drafts_for_user(author)

    assert [item["title"] for item in payload["items"]] == ["Newer", "Older"]
    assert payload["items"][0]["section_count"] == 2
    assert payload["items"][0]["ai_section_count"] == 1


@pytest.mark.asyncio
async def test_get_draft_rejects_cross_user_access(app_modules, db_schema) -> None:
    author = await seed_user(app_modules, email="author@example.com", name="Author", token="hf_author")
    other = await seed_user(app_modules, email="other@example.com", name="Other", token="hf_other")
    draft = await seed_draft(
        app_modules,
        author_id=other.id,
        title="Foreign",
        status="locked",
        updated_at=datetime.now(timezone.utc),
    )

    with pytest.raises(MCPError) as error:
        await get_draft_for_user(author, str(draft.id))

    assert error.value.code == "draft_not_found"


@pytest.mark.asyncio
async def test_save_section_creates_ai_sections_and_ignores_cross_user_access(app_modules, db_schema) -> None:
    author = await seed_user(app_modules, email="author@example.com", name="Author", token="hf_author")
    other = await seed_user(app_modules, email="other@example.com", name="Other", token="hf_other")
    draft = await seed_draft(
        app_modules,
        author_id=author.id,
        title="Locked Draft",
        status="locked",
        updated_at=datetime.now(timezone.utc),
    )
    foreign_draft = await seed_draft(
        app_modules,
        author_id=other.id,
        title="Foreign Draft",
        status="locked",
        updated_at=datetime.now(timezone.utc),
    )

    await seed_section(
        app_modules,
        draft_id=draft.id,
        content_type="human",
        type="paragraph",
        content="Paragraph one",
        position_after_paragraph=0,
    )

    payload = await save_section_for_user(
        author,
        draft_id=str(draft.id),
        type="example",
        content="Helpful AI content here",
        source_selection="Paragraph one",
        author_prompt="Expand it",
        position_after_paragraph=0,
    )
    assert payload["ok"] is True
    assert payload["section"]["content_type"] == "ai"
    assert payload["section"]["word_count"] == 4

    with pytest.raises(MCPError) as foreign_error:
        await save_section_for_user(
            author,
            draft_id=str(foreign_draft.id),
            type="example",
            content="No access",
            source_selection=None,
            author_prompt=None,
            position_after_paragraph=0,
        )
    assert foreign_error.value.code == "draft_not_found"


@pytest.mark.asyncio
async def test_save_section_requires_locked_draft_and_valid_position(app_modules, db_schema) -> None:
    author = await seed_user(app_modules, email="author@example.com", name="Author", token="hf_author")
    unlocked = await seed_draft(
        app_modules,
        author_id=author.id,
        title="Unlocked",
        status="draft",
        updated_at=datetime.now(timezone.utc),
    )
    locked = await seed_draft(
        app_modules,
        author_id=author.id,
        title="Locked",
        status="locked",
        updated_at=datetime.now(timezone.utc),
    )
    await seed_section(
        app_modules,
        draft_id=locked.id,
        content_type="human",
        type="paragraph",
        content="Paragraph one",
        position_after_paragraph=1,
    )

    with pytest.raises(MCPError) as unlocked_error:
        await save_section_for_user(
            author,
            draft_id=str(unlocked.id),
            type="example",
            content="Nope",
            source_selection=None,
            author_prompt=None,
            position_after_paragraph=0,
        )
    assert unlocked_error.value.code == "draft_not_ready_for_ai"

    with pytest.raises(MCPError) as position_error:
        await save_section_for_user(
            author,
            draft_id=str(locked.id),
            type="example",
            content="Nope",
            source_selection=None,
            author_prompt=None,
            position_after_paragraph=0,
        )
    assert position_error.value.code == "invalid_section_position"


@pytest.mark.asyncio
async def test_delete_section_only_allows_author_owned_ai_sections(app_modules, db_schema) -> None:
    author = await seed_user(app_modules, email="author@example.com", name="Author", token="hf_author")
    other = await seed_user(app_modules, email="other@example.com", name="Other", token="hf_other")
    draft = await seed_draft(
        app_modules,
        author_id=author.id,
        title="Locked Draft",
        status="locked",
        updated_at=datetime.now(timezone.utc),
    )
    foreign_draft = await seed_draft(
        app_modules,
        author_id=other.id,
        title="Foreign Draft",
        status="locked",
        updated_at=datetime.now(timezone.utc),
    )

    human_section = await seed_section(
        app_modules,
        draft_id=draft.id,
        content_type="human",
        type="paragraph",
        content="Human paragraph",
        position_after_paragraph=0,
    )
    ai_section = await seed_section(
        app_modules,
        draft_id=draft.id,
        content_type="ai",
        type="example",
        content="AI paragraph",
        position_after_paragraph=0,
    )
    foreign_section = await seed_section(
        app_modules,
        draft_id=foreign_draft.id,
        content_type="ai",
        type="example",
        content="Foreign AI paragraph",
        position_after_paragraph=0,
    )

    with pytest.raises(MCPError) as human_error:
        await delete_section_for_user(author, section_id=str(human_section.id))
    assert human_error.value.code == "section_not_deletable"

    with pytest.raises(MCPError) as foreign_error:
        await delete_section_for_user(author, section_id=str(foreign_section.id))
    assert foreign_error.value.code == "section_not_found"

    payload = await delete_section_for_user(author, section_id=str(ai_section.id))
    assert payload == {"ok": True}


def test_humanfirst_command_is_committed_and_mentions_required_tool_flow() -> None:
    command_path = Path(__file__).resolve().parents[2] / ".claude" / "commands" / "humanfirst.md"

    assert command_path.exists()

    command_text = command_path.read_text(encoding="utf-8")
    for expected in (
        "list_drafts",
        "get_draft",
        "save_section",
        "delete_section",
    ):
        assert expected in command_text
