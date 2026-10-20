from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.dialects import postgresql

from app.routes.posts import _build_like_insert_statement, _hash_fingerprint
from app.usecases.posts import build_comment_tree


def test_hash_fingerprint_normalizes_input() -> None:
    assert _hash_fingerprint(" fingerprint ") == _hash_fingerprint("fingerprint")


def test_build_comment_tree_returns_two_levels_only(app_modules) -> None:
    root_id = uuid4()
    reply_id = uuid4()
    post_id = uuid4()
    root = app_modules.models.Comment(
        id=root_id,
        post_id=post_id,
        parent_id=None,
        author_name="Root",
        author_email="root@example.com",
        body="Root body",
        created_at=datetime.now(timezone.utc),
    )
    reply = app_modules.models.Comment(
        id=reply_id,
        post_id=post_id,
        parent_id=root_id,
        author_name="Reply",
        author_email="reply@example.com",
        body="Reply body",
        created_at=datetime.now(timezone.utc),
    )

    tree = build_comment_tree([root, reply])

    assert len(tree) == 1
    assert tree[0].id == root_id
    assert [item.id for item in tree[0].replies] == [reply_id]


def test_like_upsert_compiles_for_postgresql() -> None:
    statement = _build_like_insert_statement(uuid4(), "fingerprint-hash", "postgresql")
    compiled = str(statement.compile(dialect=postgresql.dialect()))

    assert "ON CONFLICT" in compiled


def test_like_is_public_and_idempotent_per_fingerprint(
    client: TestClient,
    seeded_data: dict[str, str],
    like_payload: dict[str, str],
    db_session_factory,
    app_modules,
) -> None:
    post_id = seeded_data["published_post_id"]
    parsed_post_id = UUID(post_id)

    first = client.post(f"/api/posts/{post_id}/likes", json=like_payload)
    second = client.post(f"/api/posts/{post_id}/likes", json=like_payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["liked"] is True
    assert second.json()["like_count"] == 1

    async def assert_db() -> None:
        async with db_session_factory() as session:
            likes = (
                await session.execute(select(app_modules.models.Like).where(app_modules.models.Like.post_id == parsed_post_id))
            ).scalars().all()
            post = await session.get(app_modules.models.Post, parsed_post_id)
            assert len(likes) == 1
            assert post is not None
            assert post.like_count == 1

    import asyncio

    asyncio.run(assert_db())


def test_unlike_is_public_and_idempotent_per_fingerprint(
    client: TestClient,
    seeded_data: dict[str, str],
    like_payload: dict[str, str],
    db_session_factory,
    app_modules,
) -> None:
    post_id = seeded_data["published_post_id"]
    parsed_post_id = UUID(post_id)
    client.post(f"/api/posts/{post_id}/likes", json=like_payload)

    first = client.request("DELETE", f"/api/posts/{post_id}/likes", json=like_payload)
    second = client.request("DELETE", f"/api/posts/{post_id}/likes", json=like_payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["liked"] is False
    assert second.json()["like_count"] == 0

    async def assert_db() -> None:
        async with db_session_factory() as session:
            likes = (
                await session.execute(select(app_modules.models.Like).where(app_modules.models.Like.post_id == parsed_post_id))
            ).scalars().all()
            post = await session.get(app_modules.models.Post, parsed_post_id)
            assert likes == []
            assert post is not None
            assert post.like_count == 0

    import asyncio

    asyncio.run(assert_db())


def test_like_rejects_unknown_post(client: TestClient, like_payload: dict[str, str]) -> None:
    response = client.post(f"/api/posts/{uuid4()}/likes", json=like_payload)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "post_not_found"


def test_create_root_comment_increments_comment_count(
    client: TestClient,
    seeded_data: dict[str, str],
) -> None:
    post_id = seeded_data["published_post_id"]

    response = client.post(
        f"/api/posts/{post_id}/comments",
        json={
            "author_name": " New Author ",
            "author_email": "new@example.com",
            "body": " New comment body ",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["comment"]["parent_id"] is None
    assert payload["comment"]["author_name"] == "New Author"
    assert payload["comment"]["body"] == "New comment body"
    assert "author_email" not in payload["comment"]
    assert payload["comment_count"] == 3


def test_create_reply_comment_increments_comment_count(
    client: TestClient,
    seeded_data: dict[str, str],
) -> None:
    post_id = seeded_data["published_post_id"]
    root_comment_id = seeded_data["root_comment_id"]

    response = client.post(
        f"/api/posts/{post_id}/comments",
        json={
            "author_name": "Reply Author",
            "author_email": "reply2@example.com",
            "body": "Another reply",
            "parent_id": root_comment_id,
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["comment"]["parent_id"] == root_comment_id
    assert payload["comment_count"] == 3


def test_reply_to_reply_is_rejected(client: TestClient, seeded_data: dict[str, str]) -> None:
    post_id = seeded_data["published_post_id"]
    reply_comment_id = seeded_data["reply_comment_id"]

    response = client.post(
        f"/api/posts/{post_id}/comments",
        json={
            "author_name": "Nested",
            "author_email": "nested@example.com",
            "body": "Should fail",
            "parent_id": reply_comment_id,
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "reply_depth_exceeded"


def test_reply_parent_must_belong_to_same_post(client: TestClient, seeded_data: dict[str, str]) -> None:
    post_id = seeded_data["published_post_id"]
    other_root_comment_id = seeded_data["other_root_comment_id"]

    response = client.post(
        f"/api/posts/{post_id}/comments",
        json={
            "author_name": "Cross Post",
            "author_email": "cross@example.com",
            "body": "Wrong parent",
            "parent_id": other_root_comment_id,
        },
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "cross_post_parent"


def test_list_comments_returns_one_level_thread_tree(
    client: TestClient,
    seeded_data: dict[str, str],
) -> None:
    post_id = seeded_data["published_post_id"]

    response = client.get(f"/api/posts/{post_id}/comments")

    assert response.status_code == 200
    payload = response.json()
    assert payload["comment_count"] == 2
    assert len(payload["comments"]) == 1
    root = payload["comments"][0]
    assert root["id"] == seeded_data["root_comment_id"]
    assert len(root["replies"]) == 1
    assert root["replies"][0]["id"] == seeded_data["reply_comment_id"]
    assert "replies" not in root["replies"][0]


def test_public_engagement_routes_do_not_require_auth(
    client: TestClient,
    seeded_data: dict[str, str],
    like_payload: dict[str, str],
) -> None:
    post_id = seeded_data["published_post_id"]

    like_response = client.post(f"/api/posts/{post_id}/likes", json=like_payload)
    comment_response = client.post(
        f"/api/posts/{post_id}/comments",
        json={
            "author_name": "Public User",
            "author_email": "public@example.com",
            "body": "Public comment",
        },
    )
    list_response = client.get(f"/api/posts/{post_id}/comments")

    assert like_response.status_code == 200
    assert comment_response.status_code == 201
    assert list_response.status_code == 200


def test_author_only_publish_or_edit_routes_still_require_auth(
    client: TestClient,
    draft_factory,
    section_factory,
    author_headers: dict[str, str],
) -> None:
    locked_draft = draft_factory(
        "author-1",
        title="Draft For Publish Auth",
        locked_at=datetime.now(timezone.utc),
    )
    section_factory(
        locked_draft.id,
        ordinal=1,
        author_type="HUMAN",
        content="Publishable draft content",
    )

    unauthorized = client.post(f"/api/drafts/{locked_draft.id}/publish")
    authorized = client.post(f"/api/drafts/{locked_draft.id}/publish", headers=author_headers)

    assert unauthorized.status_code == 401
    assert unauthorized.json()["error"]["code"] == "auth_required"
    assert authorized.status_code == 201
    assert authorized.json()["draft_id"] == str(locked_draft.id)
    assert authorized.json()["published_at"] is not None


def test_like_and_comment_counters_match_row_counts_after_mutations(
    client: TestClient,
    seeded_data: dict[str, str],
    like_payload: dict[str, str],
    db_session_factory,
    app_modules,
) -> None:
    post_id = seeded_data["published_post_id"]
    parsed_post_id = UUID(post_id)

    client.post(f"/api/posts/{post_id}/likes", json=like_payload)
    client.post(
        f"/api/posts/{post_id}/comments",
        json={
            "author_name": "Counter User",
            "author_email": "counter@example.com",
            "body": "Counter comment",
        },
    )

    async def assert_counts() -> None:
        async with db_session_factory() as session:
            post = await session.get(app_modules.models.Post, parsed_post_id)
            like_count = await session.scalar(
                select(func.count(app_modules.models.Like.id)).where(app_modules.models.Like.post_id == parsed_post_id)
            )
            comment_count = await session.scalar(
                select(func.count(app_modules.models.Comment.id)).where(app_modules.models.Comment.post_id == parsed_post_id)
            )
            assert post is not None
            assert post.like_count == (like_count or 0) == 1
            assert post.comment_count == (comment_count or 0) == 3

    import asyncio

    asyncio.run(assert_counts())
