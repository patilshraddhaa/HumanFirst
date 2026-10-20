from fastapi.testclient import TestClient

from app.db.models import Comment, Post


def test_list_posts_returns_only_published_items_in_descending_publish_order(
    client: TestClient,
    seeded_data: dict[str, str],
) -> None:
    response = client.get("/api/posts")

    assert response.status_code == 200
    items = response.json()["items"]
    assert [item["slug"] for item in items] == ["second-post", "published-post"]
    assert all("draft_id" not in item for item in items)
    assert items[0]["provenance"]["total_sections"] == 1
    assert items[1]["provenance"]["has_ai_content"] is True


def test_get_post_by_slug_returns_public_detail_with_ordered_sections_and_comments(
    client: TestClient,
    published_post_factory,
    db_session_factory,
) -> None:
    published_post = published_post_factory()

    import asyncio

    async def seed_comments() -> None:
        async with db_session_factory() as session:
            root = Comment(
                post_id=published_post["post_id"],
                author_name="Reader",
                author_email="reader@example.com",
                body="Top level comment",
            )
            session.add(root)
            await session.flush()
            reply = Comment(
                post_id=published_post["post_id"],
                parent_id=root.id,
                author_name="Replier",
                author_email="reply@example.com",
                body="Nested reply",
            )
            session.add(reply)
            post = await session.get(Post, published_post["post_id"])
            assert post is not None
            post.comment_count = 2
            await session.commit()

    asyncio.run(seed_comments())

    response = client.get(f"/api/posts/{published_post['slug']}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["slug"] == published_post["slug"]
    assert "draft_id" not in payload
    assert [section["ordinal"] for section in payload["sections"]] == [1, 2]
    assert payload["provenance"]["human_sections"] == 1
    assert payload["provenance"]["ai_sections"] == 1
    assert len(payload["comments"]) == 1
    assert payload["comments"][0]["replies"][0]["body"] == "Nested reply"
    assert "author_email" not in payload["comments"][0]


def test_get_post_by_slug_returns_404_for_unknown_or_unpublished_post(
    client: TestClient,
    seeded_data: dict[str, str],
) -> None:
    missing_response = client.get("/api/posts/missing")
    unpublished_response = client.get("/api/posts/draft-post")

    for response in [missing_response, unpublished_response]:
        assert response.status_code == 404
        assert response.json() == {
            "error": {"code": "post_not_found", "message": "Post was not found."}
        }


def test_patch_post_updates_title_for_owner_only(
    client: TestClient,
    auth_headers: dict[str, str],
    foreign_auth_headers: dict[str, str],
    published_post_factory,
) -> None:
    published_post = published_post_factory()

    response = client.patch(
        f"/api/posts/{published_post['post_id']}",
        json={"title": "Updated title"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Updated title"

    foreign_response = client.patch(
        f"/api/posts/{published_post['post_id']}",
        json={"title": "Foreign edit"},
        headers=foreign_auth_headers,
    )
    assert foreign_response.status_code == 404
    assert foreign_response.json() == {
        "error": {"code": "post_not_found", "message": "Post was not found."}
    }


def test_patch_post_rejects_empty_payload(
    client: TestClient,
    auth_headers: dict[str, str],
    published_post_factory,
) -> None:
    published_post = published_post_factory()

    response = client.patch(
        f"/api/posts/{published_post['post_id']}",
        json={},
        headers=auth_headers,
    )

    assert response.status_code == 400
    assert response.json() == {
        "error": {"code": "empty_patch", "message": "At least one field must be supplied."}
    }


def test_patch_post_requires_authentication(
    client: TestClient,
    published_post_factory,
) -> None:
    published_post = published_post_factory()

    response = client.patch(f"/api/posts/{published_post['post_id']}", json={"title": "Nope"})

    assert response.status_code == 401
    assert response.json() == {
        "error": {"code": "unauthorized", "message": "Authentication is required."}
    }


def test_patch_post_rejects_unsigned_owner_claim(
    client: TestClient,
    published_post_factory,
) -> None:
    published_post = published_post_factory()

    response = client.patch(
        f"/api/posts/{published_post['post_id']}",
        json={"title": "Spoofed"},
        headers={"Authorization": "Bearer author-1|Owner Author"},
    )

    assert response.status_code == 401
    assert response.json() == {
        "error": {"code": "unauthorized", "message": "Bearer token is malformed."}
    }


def test_patch_post_rejects_signed_token_for_unknown_user(
    client: TestClient,
    published_post_factory,
    unknown_user_auth_headers: dict[str, str],
) -> None:
    published_post = published_post_factory()

    response = client.patch(
        f"/api/posts/{published_post['post_id']}",
        json={"title": "Ghost edit"},
        headers=unknown_user_auth_headers,
    )

    assert response.status_code == 401
    assert response.json() == {
        "error": {"code": "unauthorized", "message": "Authenticated user was not found."}
    }


def test_patch_ai_section_updates_content_for_owner(
    client: TestClient,
    auth_headers: dict[str, str],
    published_post_factory,
) -> None:
    published_post = published_post_factory()

    response = client.patch(
        f"/api/posts/{published_post['post_id']}/sections/{published_post['ai_section_id']}",
        json={"content": "AI section updated with fresh supporting detail", "content_type": "CASE_STUDY"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ai_word_count"] == 7
    assert payload["provenance"]["ai_word_count"] == 7
    ai_section = next(section for section in payload["sections"] if section["id"] == published_post["ai_section_id"])
    assert ai_section["content"] == "AI section updated with fresh supporting detail"
    assert ai_section["content_type"] == "CASE_STUDY"


def test_patch_ai_section_requires_authentication(
    client: TestClient,
    published_post_factory,
) -> None:
    published_post = published_post_factory()

    response = client.patch(
        f"/api/posts/{published_post['post_id']}/sections/{published_post['ai_section_id']}",
        json={"content": "No auth"},
    )

    assert response.status_code == 401
    assert response.json() == {
        "error": {"code": "unauthorized", "message": "Authentication is required."}
    }


def test_patch_ai_section_returns_404_for_foreign_owner(
    client: TestClient,
    foreign_auth_headers: dict[str, str],
    published_post_factory,
) -> None:
    published_post = published_post_factory()

    response = client.patch(
        f"/api/posts/{published_post['post_id']}/sections/{published_post['ai_section_id']}",
        json={"content": "Foreign rewrite"},
        headers=foreign_auth_headers,
    )

    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "post_not_found", "message": "Post was not found."}
    }


def test_patch_human_section_returns_409_human_section_immutable(
    client: TestClient,
    auth_headers: dict[str, str],
    published_post_factory,
) -> None:
    published_post = published_post_factory()

    response = client.patch(
        f"/api/posts/{published_post['post_id']}/sections/{published_post['human_section_id']}",
        json={"content": "Attempted rewrite"},
        headers=auth_headers,
    )

    assert response.status_code == 409
    assert response.json() == {
        "error": {
            "code": "human_section_immutable",
            "message": "Human sections are locked after draft lock/materialization.",
        }
    }


def test_delete_ai_section_removes_row_and_refreshes_provenance(
    client: TestClient,
    auth_headers: dict[str, str],
    published_post_factory,
) -> None:
    published_post = published_post_factory()

    response = client.delete(
        f"/api/posts/{published_post['post_id']}/sections/{published_post['ai_section_id']}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ai_word_count"] == 0
    assert payload["provenance"]["ai_sections"] == 0
    assert [section["id"] for section in payload["sections"]] == [published_post["human_section_id"]]


def test_delete_ai_section_requires_authentication(
    client: TestClient,
    published_post_factory,
) -> None:
    published_post = published_post_factory()

    response = client.delete(
        f"/api/posts/{published_post['post_id']}/sections/{published_post['ai_section_id']}",
    )

    assert response.status_code == 401
    assert response.json() == {
        "error": {"code": "unauthorized", "message": "Authentication is required."}
    }


def test_delete_ai_section_rejects_unsigned_owner_claim(
    client: TestClient,
    published_post_factory,
) -> None:
    published_post = published_post_factory()

    response = client.delete(
        f"/api/posts/{published_post['post_id']}/sections/{published_post['ai_section_id']}",
        headers={"Authorization": "Bearer author-1|Owner Author"},
    )

    assert response.status_code == 401
    assert response.json() == {
        "error": {"code": "unauthorized", "message": "Bearer token is malformed."}
    }


def test_delete_human_section_returns_409_human_section_immutable(
    client: TestClient,
    auth_headers: dict[str, str],
    published_post_factory,
) -> None:
    published_post = published_post_factory()

    response = client.delete(
        f"/api/posts/{published_post['post_id']}/sections/{published_post['human_section_id']}",
        headers=auth_headers,
    )

    assert response.status_code == 409
    assert response.json() == {
        "error": {
            "code": "human_section_immutable",
            "message": "Human sections are locked after draft lock/materialization.",
        }
    }


def test_export_post_returns_complete_html_document(
    client: TestClient,
    published_post_factory,
) -> None:
    published_post = published_post_factory()

    response = client.get(f"/api/posts/{published_post['slug']}/export")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "<!DOCTYPE html>" in response.text
    assert "<html" in response.text
    assert "<article>" in response.text
    assert "<style>" in response.text
    assert "Published post" in response.text
    assert "<script src=" not in response.text
    assert "<link rel=" not in response.text


def test_export_post_renders_human_and_ai_sections_differently(
    client: TestClient,
    published_post_factory,
) -> None:
    published_post = published_post_factory()

    response = client.get(f"/api/posts/{published_post['slug']}/export")

    assert 'class="section section-human"' in response.text
    assert 'class="section section-ai"' in response.text
    assert "AI Example" in response.text


def test_export_post_includes_provenance_footer(
    client: TestClient,
    published_post_factory,
) -> None:
    published_post = published_post_factory()

    response = client.get(f"/api/posts/{published_post['slug']}/export")

    assert "Provenance" in response.text
    assert "Human sections were locked at draft lock/materialization." in response.text
    assert f"Slug: {published_post['slug']}" in response.text
    assert "Human sections: 1" in response.text
    assert "AI sections: 1" in response.text


def test_export_post_returns_404_for_unknown_slug(client: TestClient) -> None:
    response = client.get("/api/posts/unknown/export")

    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "post_not_found", "message": "Post was not found."}
    }
