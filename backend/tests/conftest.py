import asyncio
import importlib
import os
import sys
from collections.abc import AsyncIterator, Callable, Iterator
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.db.models.draft import Draft
from app.db.session import AsyncSessionLocal
from app.main import app


@pytest.fixture(scope="function")
def client() -> TestClient:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function", autouse=True)
def reset_demo_drafts(client: TestClient) -> None:
    async def _reset() -> None:
        async with AsyncSessionLocal() as session:
            await session.execute(delete(Draft))
            session.add_all(
                [
                    Draft(
                        id=1,
                        title="MCP onboarding note",
                        body_text=(
                            "Summarize the draft goal.\n\n"
                            "Capture the main reasoning steps.\n\n"
                            "Leave the final handoff clean."
                        ),
                        requires_mcp_setup=True,
                    ),
                    Draft(
                        id=2,
                        title="Release preview note",
                        body_text=(
                            "Locking should freeze writing.\n\n"
                            "Preview should stay available after the transition."
                        ),
                        requires_mcp_setup=False,
                    ),
                ]
            )
            await session.commit()

    import asyncio

    asyncio.run(_reset())


@pytest.fixture(scope="function")
def run_db() -> callable:
    def _run(coro):
        import asyncio

        return asyncio.run(coro)

    return _run


@pytest.fixture(scope="function")
def get_draft_row(run_db):
    def _get_draft_row(draft_id: int) -> Draft | None:
        async def _load() -> Draft | None:
            async with AsyncSessionLocal() as session:
                return await session.get(Draft, draft_id)

        return run_db(_load())

    return _get_draft_row
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

os.environ.setdefault(
    "JWT_SECRET_KEY",
    "test-jwt-secret-key-for-backend-tests-only-123456",
)

from app.core.auth import create_access_token
from app.core.security import generate_mcp_token, hash_password


@pytest.fixture(scope="function")
def app_modules(monkeypatch: pytest.MonkeyPatch, tmp_path) -> Iterator[SimpleNamespace]:
    database_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{database_path}")
    monkeypatch.setenv("DATABASE_ECHO", "false")

    for module_name in list(sys.modules):
        if module_name == "app" or module_name.startswith("app."):
            sys.modules.pop(module_name, None)

    main_module = importlib.import_module("app.main")
    base_module = importlib.import_module("app.db.base")
    models_module = importlib.import_module("app.db.models")
    session_module = importlib.import_module("app.db.session")

    modules = SimpleNamespace(
        app=main_module.app,
        base=base_module,
        models=models_module,
        session=session_module,
    )
    yield modules
    asyncio.run(modules.session.engine.dispose())


@pytest_asyncio.fixture
async def db_schema(app_modules: SimpleNamespace) -> AsyncIterator[None]:
    await app_modules.base.create_all_for_test()
    try:
        yield
    finally:
        await app_modules.base.drop_all_for_test()


@pytest.fixture(scope="function")
def client(app_modules: SimpleNamespace, db_schema: None) -> Iterator[TestClient]:
    with TestClient(app_modules.app) as test_client:
        yield test_client
    app_modules.app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def async_session(
    app_modules: SimpleNamespace,
    db_schema: None,
) -> AsyncIterator[object]:
    async with app_modules.session.AsyncSessionLocal() as session:
        yield session


@pytest.fixture(scope="function")
def test_session_maker(app_modules: SimpleNamespace, db_schema: None):
    return app_modules.session.AsyncSessionLocal


@pytest.fixture(scope="function")
def db_session_factory(app_modules: SimpleNamespace, db_schema: None):
    return app_modules.session.AsyncSessionLocal


@pytest.fixture(scope="function")
def registered_user_payload() -> dict[str, str]:
    return {
        "name": "Test User",
        "email": "test@example.com",
        "password": "super-secret-password",
    }


@pytest.fixture(scope="function")
def user_factory(app_modules: SimpleNamespace, db_schema: None):
    async def create_user(**overrides):
        name = overrides.pop("name", None)
        display_name = overrides.pop("display_name", name or "User")
        values = {
            "name": name,
            "email": "user@example.com",
            "password_hash": hash_password("super-secret-password"),
            "display_name": display_name,
            "mcp_token": generate_mcp_token("hf_test_"),
            "mcp_token_issued_at": datetime.now(timezone.utc),
        }
        values.update(overrides)

        async with app_modules.session.AsyncSessionLocal() as session:
            user = app_modules.models.User(**values)
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

    def factory(**overrides):
        return asyncio.run(create_user(**overrides))

    return factory


@pytest.fixture(scope="function")
def owner_user(user_factory):
    return user_factory(
        email="author1@example.com",
        name="Owner Author",
        display_name="Owner Author",
    )


@pytest.fixture(scope="function")
def foreign_user(user_factory):
    return user_factory(
        email="author2@example.com",
        name="Foreign Author",
        display_name="Foreign Author",
    )


@pytest.fixture(scope="function")
def auth_headers(owner_user) -> dict[str, str]:
    token = create_access_token(subject=owner_user.email, user_id=owner_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def foreign_auth_headers(foreign_user) -> dict[str, str]:
    token = create_access_token(subject=foreign_user.email, user_id=foreign_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def unknown_user_auth_headers() -> dict[str, str]:
    token = create_access_token(subject="ghost@example.com", user_id=uuid4())
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def author_headers(auth_headers: dict[str, str]) -> dict[str, str]:
    return auth_headers


@pytest.fixture(scope="function")
def draft_factory(app_modules: SimpleNamespace, db_schema: None):
    async def create_draft(author_id, **overrides):
        body_text = overrides.pop("body_text", None)
        if body_text is not None and "body" not in overrides:
            overrides["body"] = body_text

        draft_values = {
            "author_id": UUID(str(author_id)),
            "title": "",
            "body": "",
            "status": app_modules.models.DraftStatus.DRAFT,
            "word_count": 0,
            "keystroke_count": 0,
            "session_duration_seconds": 0,
            "pause_events": 0,
            "paste_attempts": 0,
            "reading_time_minutes": 0,
        }
        draft_values.update(overrides)

        async with app_modules.session.AsyncSessionLocal() as session:
            draft = app_modules.models.Draft(**draft_values)
            session.add(draft)
            await session.commit()
            if "updated_at" in overrides:
                draft.updated_at = overrides["updated_at"]
                await session.commit()
            await session.refresh(draft)
            return draft

    def factory(author_id, **overrides):
        return asyncio.run(create_draft(author_id, **overrides))

    return factory


@pytest.fixture(scope="function")
def section_factory(
    app_modules: SimpleNamespace,
    test_session_maker: async_sessionmaker[AsyncSession],
) -> Callable[..., object]:
    def factory(
        draft_id: UUID | str,
        *,
        ordinal: int,
        author_type: str,
        content: str,
        content_type: str = "BODY_PARAGRAPH",
        anchor_human_section_id: UUID | str | None = None,
    ):
        async def create_section():
            resolved_content_type = "BODY_PARAGRAPH" if content_type == "BODY" else content_type
            author_enum = app_modules.models.SectionAuthorType(author_type)
            content_enum = app_modules.models.SectionContentType(resolved_content_type)
            created_via = (
                app_modules.models.SectionCreationSource.LOCK_MATERIALIZATION
                if author_enum == app_modules.models.SectionAuthorType.HUMAN
                else app_modules.models.SectionCreationSource.MCP
            )
            async with test_session_maker() as session:
                section = app_modules.models.Section(
                    draft_id=UUID(str(draft_id)),
                    ordinal=ordinal,
                    author_type=author_enum,
                    content_type=content_enum,
                    content=content,
                    anchor_human_section_id=(
                        None if anchor_human_section_id is None else UUID(str(anchor_human_section_id))
                    ),
                    word_count=len(content.split()),
                    created_via=created_via,
                )
                session.add(section)
                await session.commit()
                await session.refresh(section)
                return section

        return asyncio.run(create_section())

    return factory


@pytest.fixture(scope="function")
def like_payload() -> dict[str, str]:
    return {"fingerprint": "browser-fingerprint-123"}


@pytest.fixture(scope="function")
def seeded_data(
    app_modules: SimpleNamespace,
    db_schema: None,
    owner_user,
) -> dict[str, str]:
    async def seed() -> dict[str, str]:
        async with app_modules.session.AsyncSessionLocal() as session:
            published_draft = app_modules.models.Draft(author_id=owner_user.id, title="Published draft")
            second_draft = app_modules.models.Draft(author_id=owner_user.id, title="Second draft")
            draft_for_publish = app_modules.models.Draft(author_id=owner_user.id, title="Draft to publish")
            session.add_all([published_draft, second_draft, draft_for_publish])
            await session.flush()

            published_post = app_modules.models.Post(
                draft_id=published_draft.id,
                author_id=owner_user.id,
                author_display_name=owner_user.display_name,
                slug="published-post",
                title="Published post",
                published_at=datetime.now(timezone.utc),
                human_word_count=4,
                ai_word_count=3,
                provenance_summary={
                    "total_sections": 2,
                    "human_sections": 1,
                    "ai_sections": 1,
                    "human_word_count": 4,
                    "ai_word_count": 3,
                    "total_word_count": 7,
                    "has_ai_content": True,
                    "by_author_type": [
                        {"key": "AI", "count": 1, "word_count": 3},
                        {"key": "HUMAN", "count": 1, "word_count": 4},
                    ],
                    "by_content_type": [
                        {"key": "BODY_PARAGRAPH", "count": 1, "word_count": 4},
                        {"key": "EXAMPLE", "count": 1, "word_count": 3},
                    ],
                },
            )
            second_published_post = app_modules.models.Post(
                draft_id=second_draft.id,
                author_id=owner_user.id,
                author_display_name=owner_user.display_name,
                slug="second-post",
                title="Second published post",
                published_at=datetime.now(timezone.utc),
                human_word_count=2,
                ai_word_count=0,
                provenance_summary={
                    "total_sections": 1,
                    "human_sections": 1,
                    "ai_sections": 0,
                    "human_word_count": 2,
                    "ai_word_count": 0,
                    "total_word_count": 2,
                    "has_ai_content": False,
                    "by_author_type": [{"key": "HUMAN", "count": 1, "word_count": 2}],
                    "by_content_type": [{"key": "BODY_PARAGRAPH", "count": 1, "word_count": 2}],
                },
            )
            draft_post = app_modules.models.Post(
                draft_id=draft_for_publish.id,
                author_id=owner_user.id,
                author_display_name=owner_user.display_name,
                slug="draft-post",
                title="Draft post",
            )
            session.add_all([published_post, second_published_post, draft_post])
            await session.flush()

            root_comment = app_modules.models.Comment(
                post_id=published_post.id,
                author_name="Root Author",
                author_email="root@example.com",
                body="Root comment",
            )
            other_root_comment = app_modules.models.Comment(
                post_id=second_published_post.id,
                author_name="Other Root",
                author_email="other@example.com",
                body="Other post root comment",
            )
            session.add_all([root_comment, other_root_comment])
            await session.flush()

            reply_comment = app_modules.models.Comment(
                post_id=published_post.id,
                parent_id=root_comment.id,
                author_name="Reply Author",
                author_email="reply@example.com",
                body="Reply comment",
            )
            session.add(reply_comment)
            await session.flush()

            published_post.comment_count = 2
            second_published_post.comment_count = 1
            await session.commit()

            return {
                "published_post_id": str(published_post.id),
                "published_post_slug": published_post.slug,
                "second_published_post_id": str(second_published_post.id),
                "draft_post_id": str(draft_post.id),
                "root_comment_id": str(root_comment.id),
                "reply_comment_id": str(reply_comment.id),
                "other_root_comment_id": str(other_root_comment.id),
            }

    return asyncio.run(seed())


@pytest.fixture(scope="function")
def published_post_factory(
    app_modules: SimpleNamespace,
    db_schema: None,
    owner_user,
):
    def create(
        *,
        author_id: UUID | str | None = None,
        author_display_name: str | None = None,
    ) -> dict[str, str]:
        resolved_author_id = UUID(str(author_id or owner_user.id))
        resolved_display_name = author_display_name or owner_user.display_name
        post_id = uuid4()
        draft_id = uuid4()
        human_section_id = uuid4()
        ai_section_id = uuid4()
        published_at = datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc)
        slug = f"post-{post_id.hex[:8]}"
        human_content = "Human section locked forever"
        ai_content = "AI helper draft with extra insight"
        human_word_count = len(human_content.split())
        ai_word_count = len(ai_content.split())

        async def seed() -> None:
            async with app_modules.session.AsyncSessionLocal() as session:
                draft = app_modules.models.Draft(
                    id=draft_id,
                    author_id=resolved_author_id,
                    title="Published draft",
                    status=app_modules.models.DraftStatus.LOCKED,
                    locked_at=published_at,
                )
                post = app_modules.models.Post(
                    id=post_id,
                    draft_id=draft_id,
                    author_id=resolved_author_id,
                    author_display_name=resolved_display_name,
                    slug=slug,
                    title="Published post",
                    published_at=published_at,
                    human_word_count=human_word_count,
                    ai_word_count=ai_word_count,
                    provenance_summary={
                        "total_sections": 2,
                        "human_sections": 1,
                        "ai_sections": 1,
                        "human_word_count": human_word_count,
                        "ai_word_count": ai_word_count,
                        "total_word_count": human_word_count + ai_word_count,
                        "has_ai_content": True,
                        "by_author_type": [
                            {"key": "AI", "count": 1, "word_count": ai_word_count},
                            {"key": "HUMAN", "count": 1, "word_count": human_word_count},
                        ],
                        "by_content_type": [
                            {"key": "BODY_PARAGRAPH", "count": 1, "word_count": human_word_count},
                            {"key": "EXAMPLE", "count": 1, "word_count": ai_word_count},
                        ],
                    },
                )
                human_section = app_modules.models.Section(
                    id=human_section_id,
                    draft_id=draft_id,
                    ordinal=1,
                    author_type=app_modules.models.SectionAuthorType.HUMAN,
                    content_type=app_modules.models.SectionContentType.BODY_PARAGRAPH,
                    content=human_content,
                    word_count=human_word_count,
                    created_via=app_modules.models.SectionCreationSource.LOCK_MATERIALIZATION,
                )
                ai_section = app_modules.models.Section(
                    id=ai_section_id,
                    draft_id=draft_id,
                    ordinal=2,
                    author_type=app_modules.models.SectionAuthorType.AI,
                    content_type=app_modules.models.SectionContentType.EXAMPLE,
                    content=ai_content,
                    word_count=ai_word_count,
                    anchor_human_section_id=human_section_id,
                    created_via=app_modules.models.SectionCreationSource.MCP,
                )
                session.add_all([draft, post, human_section, ai_section])
                await session.commit()

        asyncio.run(seed())

        return {
            "post_id": str(post_id),
            "draft_id": str(draft_id),
            "slug": slug,
            "human_section_id": str(human_section_id),
            "ai_section_id": str(ai_section_id),
        }

    return create


@pytest.fixture(scope="function")
def list_sections_for_draft(
    db_session_factory: async_sessionmaker[AsyncSession],
) -> Callable[[str], list[object]]:
    def list_for_draft(draft_id: str) -> list[object]:
        async def read_sections() -> list[object]:
            async with db_session_factory() as session:
                from app.db.models import Section

                result = await session.execute(
                    select(Section)
                    .where(Section.draft_id == UUID(str(draft_id)))
                    .order_by(Section.ordinal.asc(), Section.created_at.asc(), Section.id.asc())
                )
                return list(result.scalars().all())

        return asyncio.run(read_sections())

    return list_for_draft
