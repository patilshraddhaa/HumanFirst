from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError


@pytest.mark.asyncio
async def test_draft_defaults_and_post_relations(
    app_modules: SimpleNamespace,
    async_session,
) -> None:
    user = app_modules.models.User(
        email="author@example.com",
        password_hash="hashed-password",
        display_name="Author",
        mcp_token="hf_author_token",
        mcp_token_issued_at=datetime.now(timezone.utc),
    )
    async_session.add(user)
    await async_session.flush()

    draft = app_modules.models.Draft(author_id=user.id)
    async_session.add(draft)
    await async_session.flush()

    post = app_modules.models.Post(
        draft_id=draft.id,
        author_id=user.id,
        slug="hello-humanfirst",
        title="Hello HumanFirst",
    )
    async_session.add(post)
    await async_session.flush()

    assert draft.status == app_modules.models.DraftStatus.DRAFT
    assert draft.keystroke_count == 0
    assert draft.word_count == 0
    assert post.like_count == 0
    assert post.comment_count == 0
    assert post.provenance_summary == {}


@pytest.mark.asyncio
async def test_section_ai_rows_require_anchor_human_section_id(
    app_modules: SimpleNamespace,
    async_session,
) -> None:
    user = app_modules.models.User(
        email="sections@example.com",
        password_hash="hashed-password",
        mcp_token="hf_sections_token",
        mcp_token_issued_at=datetime.now(timezone.utc),
    )
    async_session.add(user)
    await async_session.flush()

    draft = app_modules.models.Draft(
        author_id=user.id,
        status=app_modules.models.DraftStatus.LOCKED,
        locked_at=datetime.now(timezone.utc),
    )
    async_session.add(draft)
    await async_session.flush()

    invalid_ai_section = app_modules.models.Section(
        draft_id=draft.id,
        ordinal=1,
        author_type=app_modules.models.SectionAuthorType.AI,
        content_type=app_modules.models.SectionContentType.EXAMPLE,
        content="Missing anchor",
        created_via=app_modules.models.SectionCreationSource.MCP,
    )
    async_session.add(invalid_ai_section)

    with pytest.raises(IntegrityError):
        await async_session.flush()
    await async_session.rollback()


@pytest.mark.asyncio
async def test_like_uniqueness_is_scoped_to_post(
    app_modules: SimpleNamespace,
    async_session,
) -> None:
    user = app_modules.models.User(
        email="likes@example.com",
        password_hash="hashed-password",
        mcp_token="hf_likes_token",
        mcp_token_issued_at=datetime.now(timezone.utc),
    )
    async_session.add(user)
    await async_session.flush()

    draft = app_modules.models.Draft(author_id=user.id)
    async_session.add(draft)
    await async_session.flush()

    post = app_modules.models.Post(
        draft_id=draft.id,
        author_id=user.id,
        slug=f"liked-post-{uuid4().hex}",
        title="Liked post",
    )
    async_session.add(post)
    await async_session.flush()

    async_session.add_all(
        [
            app_modules.models.Like(post_id=post.id, fingerprint_hash="dup-fingerprint"),
            app_modules.models.Like(post_id=post.id, fingerprint_hash="dup-fingerprint"),
        ],
    )

    with pytest.raises(IntegrityError):
        await async_session.flush()
    await async_session.rollback()


@pytest.mark.asyncio
async def test_user_email_uniqueness_is_case_insensitive(
    app_modules: SimpleNamespace,
    async_session,
) -> None:
    async_session.add(
        app_modules.models.User(
            email="author@example.com",
            password_hash="hashed-password",
            display_name="Author",
            mcp_token="hf_case_token_1",
            mcp_token_issued_at=datetime.now(timezone.utc),
        )
    )
    await async_session.flush()

    async_session.add(
        app_modules.models.User(
            email="AUTHOR@example.com",
            password_hash="hashed-password",
            display_name="Author Two",
            mcp_token="hf_case_token_2",
            mcp_token_issued_at=datetime.now(timezone.utc),
        )
    )

    with pytest.raises(IntegrityError):
        await async_session.flush()
    await async_session.rollback()
