from fastapi.testclient import TestClient


def test_get_draft(client: TestClient) -> None:
    response = client.get("/api/drafts/1")

    assert response.status_code == 200
    assert response.json()["title"] == "MCP onboarding note"
    assert response.json()["locked_at"] is None


def test_patch_updates_unlocked_draft(
    client: TestClient,
    get_draft_row,
) -> None:
    response = client.patch(
        "/api/drafts/1",
        json={"title": "Edited title", "body_text": "Fresh copy"},
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Edited title"
    assert response.json()["body_text"] == "Fresh copy"

    draft = get_draft_row(1)
    assert draft is not None
    assert draft.title == "Edited title"
    assert draft.body_text == "Fresh copy"


def test_patch_rejects_locked_draft(client: TestClient) -> None:
    lock_response = client.post("/api/drafts/1/lock")
    assert lock_response.status_code == 200

    response = client.patch("/api/drafts/1", json={"title": "Cannot edit"})

    assert response.status_code == 409
    assert response.json() == {
        "error": {
            "code": "draft_locked",
            "message": "Draft is already locked.",
        }
    }


def test_lock_sets_locked_at_and_preserves_redirect_flag(
    client: TestClient,
    get_draft_row,
) -> None:
    response = client.post("/api/drafts/1/lock")

    assert response.status_code == 200
    body = response.json()
    assert body["locked_at"] is not None
    assert body["requires_mcp_setup"] is True

    draft = get_draft_row(1)
    assert draft is not None
    assert draft.locked_at is not None


def test_lock_rejects_already_locked_draft(client: TestClient) -> None:
    first = client.post("/api/drafts/2/lock")
    assert first.status_code == 200

    second = client.post("/api/drafts/2/lock")

    assert second.status_code == 409
    assert second.json() == {
        "error": {
            "code": "draft_locked",
            "message": "Draft is already locked.",
        }
    }


def test_missing_draft_returns_not_found(client: TestClient) -> None:
    response = client.get("/api/drafts/999")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "draft_not_found",
            "message": "Draft not found.",
        }
    }
import asyncio
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.auth import create_access_token
from app.db.models import Post, Section, SectionAuthorType, SectionContentType


def _auth_headers_for_user(user) -> dict[str, str]:
    token = create_access_token(subject=user.email, user_id=user.id)
    return {"Authorization": f"Bearer {token}"}


def test_create_draft_returns_201_and_persists_defaults(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.post("/api/drafts", headers=auth_headers, json={"title": "First draft"})

    assert response.status_code == 201
    payload = response.json()
    assert payload["title"] == "First draft"
    assert payload["body"] == ""
    assert payload["status"] == "DRAFT"
    assert payload["word_count"] == 0
    assert payload["keystroke_count"] == 0
    assert payload["session_duration_seconds"] == 0
    assert payload["pause_events"] == 0
    assert payload["paste_attempts"] == 0
    assert payload["reading_time_minutes"] == 0
    assert payload["locked_at"] is None


def test_list_drafts_returns_only_current_author_unlocked_drafts_in_recency_order(
    client: TestClient,
    user_factory,
    draft_factory,
) -> None:
    author = user_factory(email="author@example.com")
    other = user_factory(email="other@example.com")
    headers = _auth_headers_for_user(author)

    older = draft_factory(
        author.id,
        title="older",
        updated_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    newer = draft_factory(author.id, title="newer")
    draft_factory(other.id, title="foreign")
    draft_factory(author.id, title="locked", locked_at=datetime.now(timezone.utc))

    response = client.get("/api/drafts", headers=headers)

    assert response.status_code == 200
    items = response.json()["items"]
    assert [item["id"] for item in items] == [str(newer.id), str(older.id)]


def test_get_draft_returns_owned_unlocked_draft(
    client: TestClient,
    user_factory,
    draft_factory,
) -> None:
    author = user_factory(email="author@example.com")
    headers = _auth_headers_for_user(author)
    draft = draft_factory(author.id, title="owned draft", body="hello")

    response = client.get(f"/api/drafts/{draft.id}", headers=headers)

    assert response.status_code == 200
    assert response.json()["title"] == "owned draft"
    assert response.json()["body"] == "hello"


def test_get_draft_returns_404_for_foreign_or_locked_draft(
    client: TestClient,
    user_factory,
    draft_factory,
) -> None:
    author = user_factory(email="author@example.com")
    headers = _auth_headers_for_user(author)
    other = user_factory(email="other@example.com")
    foreign = draft_factory(other.id, title="foreign")
    locked = draft_factory(author.id, title="locked", locked_at=datetime.now(timezone.utc))

    foreign_response = client.get(f"/api/drafts/{foreign.id}", headers=headers)
    locked_response = client.get(f"/api/drafts/{locked.id}", headers=headers)

    assert foreign_response.status_code == 404
    assert foreign_response.json() == {
        "error": {"code": "draft_not_found", "message": "Draft not found"}
    }
    assert locked_response.status_code == 404
    assert locked_response.json() == {
        "error": {"code": "draft_not_found", "message": "Draft not found"}
    }


def test_patch_draft_updates_body_and_editor_metrics(
    client: TestClient,
    user_factory,
    draft_factory,
) -> None:
    author = user_factory(email="author@example.com")
    headers = _auth_headers_for_user(author)
    draft = draft_factory(author.id, title="before")

    response = client.patch(
        f"/api/drafts/{draft.id}",
        headers=headers,
        json={
            "title": "after",
            "body": "Updated body",
            "word_count": 2,
            "keystroke_count": 14,
            "session_duration_seconds": 30,
            "pause_events": 1,
            "paste_attempts": 0,
            "reading_time_minutes": 1,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["title"] == "after"
    assert payload["body"] == "Updated body"
    assert payload["word_count"] == 2
    assert payload["keystroke_count"] == 14
    assert payload["session_duration_seconds"] == 30
    assert payload["pause_events"] == 1
    assert payload["paste_attempts"] == 0
    assert payload["reading_time_minutes"] == 1


def test_patch_draft_rejects_empty_payload_with_400(
    client: TestClient,
    user_factory,
    draft_factory,
) -> None:
    author = user_factory(email="author@example.com")
    headers = _auth_headers_for_user(author)
    draft = draft_factory(author.id, title="before")

    response = client.patch(f"/api/drafts/{draft.id}", headers=headers, json={})

    assert response.status_code == 400
    assert response.json() == {
        "error": {"code": "empty_patch", "message": "Patch payload cannot be empty"}
    }


def test_patch_draft_rejects_negative_metrics_with_422(
    client: TestClient,
    user_factory,
    draft_factory,
) -> None:
    author = user_factory(email="author@example.com")
    headers = _auth_headers_for_user(author)
    draft = draft_factory(author.id, title="before")

    response = client.patch(
        f"/api/drafts/{draft.id}",
        headers=headers,
        json={"word_count": -1},
    )

    assert response.status_code == 422
    assert response.json() == {
        "error": {
            "code": "validation_error",
            "message": "Request validation failed",
        }
    }


def test_lock_draft_materializes_ordered_human_sections_and_hides_draft(
    client: TestClient,
    user_factory,
    draft_factory,
    list_sections_for_draft,
) -> None:
    author = user_factory(email="author@example.com")
    headers = _auth_headers_for_user(author)
    draft = draft_factory(
        author.id,
        title="Lock me",
        body_text="First paragraph.\nline two.\n\nSecond paragraph.\n\n  Third paragraph  ",
        word_count=8,
    )

    response = client.post(f"/api/drafts/{draft.id}/lock", headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(draft.id)
    assert payload["title"] == "Lock me"
    assert payload["locked_at"] is not None

    sections = list_sections_for_draft(draft.id)
    assert [(section.ordinal, section.content) for section in sections] == [
        (1, "First paragraph.\nline two."),
        (2, "Second paragraph."),
        (3, "Third paragraph"),
    ]
    assert [section.author_type for section in sections] == [
        SectionAuthorType.HUMAN.value,
        SectionAuthorType.HUMAN.value,
        SectionAuthorType.HUMAN.value,
    ]
    assert [section.content_type for section in sections] == [
        SectionContentType.BODY_PARAGRAPH.value,
        SectionContentType.BODY_PARAGRAPH.value,
        SectionContentType.BODY_PARAGRAPH.value,
    ]
    assert [section.word_count for section in sections] == [4, 2, 2]

    get_response = client.get(f"/api/drafts/{draft.id}", headers=headers)
    list_response = client.get("/api/drafts", headers=headers)

    assert get_response.status_code == 404
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()["items"]] == []


def test_lock_draft_allows_whitespace_only_body_without_sections(
    client: TestClient,
    user_factory,
    draft_factory,
    list_sections_for_draft,
) -> None:
    author = user_factory(email="author@example.com")
    headers = _auth_headers_for_user(author)
    draft = draft_factory(author.id, body_text=" \n\n\t ")

    response = client.post(f"/api/drafts/{draft.id}/lock", headers=headers)

    assert response.status_code == 200
    assert response.json()["locked_at"] is not None
    assert list_sections_for_draft(draft.id) == []


def test_lock_draft_rejects_relock_for_owned_locked_draft(
    client: TestClient,
    user_factory,
    draft_factory,
) -> None:
    author = user_factory(email="author@example.com")
    headers = _auth_headers_for_user(author)
    draft = draft_factory(author.id, locked_at=datetime.now(timezone.utc))

    response = client.post(f"/api/drafts/{draft.id}/lock", headers=headers)

    assert response.status_code == 409
    assert response.json() == {
        "error": {
            "code": "draft_locked",
            "message": "Draft is already locked",
        }
    }


def test_lock_draft_rejects_existing_sections_conflict(
    client: TestClient,
    user_factory,
    draft_factory,
    section_factory,
    list_sections_for_draft,
) -> None:
    author = user_factory(email="author@example.com")
    headers = _auth_headers_for_user(author)
    draft = draft_factory(author.id, body_text="Fresh body text")

    section_factory(
        draft.id,
        ordinal=1,
        author_type=SectionAuthorType.HUMAN.value,
        content="Existing section",
    )

    response = client.post(f"/api/drafts/{draft.id}/lock", headers=headers)

    assert response.status_code == 409
    assert response.json() == {
        "error": {
            "code": "draft_sections_exist",
            "message": "Draft sections already exist for this draft",
        }
    }
    sections = list_sections_for_draft(draft.id)
    assert len(sections) == 1
    assert sections[0].content == "Existing section"


def test_lock_draft_returns_404_for_missing_or_foreign_draft(
    client: TestClient,
    user_factory,
    draft_factory,
) -> None:
    author = user_factory(email="author@example.com")
    other = user_factory(email="other@example.com")
    headers = _auth_headers_for_user(author)
    foreign = draft_factory(other.id)

    missing_response = client.post("/api/drafts/missing/lock", headers=headers)
    foreign_response = client.post(f"/api/drafts/{foreign.id}/lock", headers=headers)

    for response in [missing_response, foreign_response]:
        assert response.status_code == 404
        assert response.json() == {
            "error": {"code": "draft_not_found", "message": "Draft not found"}
        }


def test_publish_locked_draft_creates_unique_slugged_post_with_ordered_sections(
    client: TestClient,
    user_factory,
    draft_factory,
    section_factory,
    db_session_factory,
    app_modules,
) -> None:
    author = user_factory(email="author@example.com", name="Author Name")
    headers = _auth_headers_for_user(author)
    draft = draft_factory(
        author.id,
        title="My Publishable Draft",
        locked_at=datetime.now(timezone.utc),
    )
    human_section = section_factory(
        draft.id,
        ordinal=1,
        author_type=SectionAuthorType.HUMAN.value,
        content="Human written opening paragraph",
    )
    ai_section = section_factory(
        draft.id,
        ordinal=2,
        author_type=SectionAuthorType.AI.value,
        content="AI generated supporting example",
        content_type="EXAMPLE",
        anchor_human_section_id=human_section.id,
    )

    response = client.post(f"/api/drafts/{draft.id}/publish", headers=headers)

    assert response.status_code == 201
    payload = response.json()
    assert payload["draft_id"] == str(draft.id)
    assert payload["slug"] == "my-publishable-draft"
    assert payload["title"] == "My Publishable Draft"
    assert [section["id"] for section in payload["sections"]] == [str(human_section.id), str(ai_section.id)]
    assert payload["provenance"]["human_sections"] == 1
    assert payload["provenance"]["ai_sections"] == 1
    assert payload["comment_count"] == 0
    assert payload["comments"] == []

    async def assert_db() -> None:
        async with db_session_factory() as session:
            posts = (
                await session.execute(select(app_modules.models.Post).where(app_modules.models.Post.draft_id == draft.id))
            ).scalars().all()
            assert len(posts) == 1
            assert posts[0].author_id == author.id
            assert posts[0].slug == "my-publishable-draft"
            assert posts[0].published_at is not None

    asyncio.run(assert_db())


def test_publish_generates_unique_slug_for_duplicate_titles(
    client: TestClient,
    auth_headers: dict[str, str],
    draft_factory,
    section_factory,
    owner_user,
) -> None:
    first_draft = draft_factory(
        owner_user.id,
        title="Published Post",
        locked_at=datetime.now(timezone.utc),
    )
    draft = draft_factory(
        owner_user.id,
        title="Published Post",
        locked_at=datetime.now(timezone.utc),
    )
    section_factory(
        first_draft.id,
        ordinal=1,
        author_type=SectionAuthorType.HUMAN.value,
        content="Original section",
    )
    section_factory(
        draft.id,
        ordinal=1,
        author_type=SectionAuthorType.HUMAN.value,
        content="Fresh human section",
    )
    first_response = client.post(f"/api/drafts/{first_draft.id}/publish", headers=auth_headers)
    assert first_response.status_code == 201

    response = client.post(f"/api/drafts/{draft.id}/publish", headers=auth_headers)

    assert response.status_code == 201
    assert response.json()["slug"] == "published-post-2"


def test_publish_returns_404_for_foreign_or_missing_draft(
    client: TestClient,
    auth_headers: dict[str, str],
    draft_factory,
    foreign_user,
) -> None:
    foreign = draft_factory(foreign_user.id, title="foreign", locked_at=datetime.now(timezone.utc))

    foreign_response = client.post(f"/api/drafts/{foreign.id}/publish", headers=auth_headers)
    missing_response = client.post("/api/drafts/missing/publish", headers=auth_headers)

    for response in [foreign_response, missing_response]:
        assert response.status_code == 404
        assert response.json() == {
            "error": {"code": "draft_not_found", "message": "Draft not found"}
        }


def test_publish_returns_409_for_unlocked_empty_or_already_published_draft(
    client: TestClient,
    auth_headers: dict[str, str],
    draft_factory,
    section_factory,
    owner_user,
) -> None:
    unlocked = draft_factory(owner_user.id, title="Unlocked")
    empty_locked = draft_factory(owner_user.id, title="Empty", locked_at=datetime.now(timezone.utc))
    already_published = draft_factory(
        owner_user.id,
        title="Already Published",
        locked_at=datetime.now(timezone.utc),
    )
    section_factory(
        already_published.id,
        ordinal=1,
        author_type=SectionAuthorType.HUMAN.value,
        content="Section content",
    )
    first_publish = client.post(f"/api/drafts/{already_published.id}/publish", headers=auth_headers)
    assert first_publish.status_code == 201

    for draft_id in [unlocked.id, empty_locked.id, already_published.id]:
        response = client.post(f"/api/drafts/{draft_id}/publish", headers=auth_headers)
        assert response.status_code == 409
        assert response.json() == {
            "error": {
                "code": "draft_not_publishable",
                "message": "Draft is not publishable",
            }
        }


def test_patch_draft_rejects_owned_locked_draft_with_409(
    client: TestClient,
    user_factory,
    draft_factory,
) -> None:
    author = user_factory(email="author@example.com")
    headers = _auth_headers_for_user(author)
    draft = draft_factory(author.id, locked_at=datetime.now(timezone.utc))

    response = client.patch(
        f"/api/drafts/{draft.id}",
        headers=headers,
        json={"title": "after"},
    )

    assert response.status_code == 409
    assert response.json() == {
        "error": {
            "code": "draft_locked",
            "message": "Draft is already locked",
        }
    }


def test_all_draft_routes_require_auth(client: TestClient) -> None:
    create_response = client.post("/api/drafts", json={})
    list_response = client.get("/api/drafts")
    get_response = client.get("/api/drafts/missing")
    patch_response = client.patch("/api/drafts/missing", json={"title": "x"})
    publish_response = client.post("/api/drafts/missing/publish")
    lock_response = client.post("/api/drafts/missing/lock")

    for response in [
        create_response,
        list_response,
        get_response,
        patch_response,
        publish_response,
        lock_response,
    ]:
        assert response.status_code == 401
        assert response.json() == {
            "error": {"code": "auth_required", "message": "Authentication required."}
        }
