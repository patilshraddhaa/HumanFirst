from fastapi.testclient import TestClient


def test_register_creates_user_and_returns_token(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Story Six",
            "email": "story6@example.com",
            "password": "supersecret",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["token"]
    assert data["user"]["email"] == "story6@example.com"
    assert data["user"]["name"] == "Story Six"
    assert data["user"]["mcp_connected"] is False


def test_login_and_me_restore_authenticated_user(client: TestClient) -> None:
    client.post(
        "/api/auth/register",
        json={
            "name": "Author Person",
            "email": "author@example.com",
            "password": "supersecret",
        },
    )

    login_response = client.post(
        "/api/auth/login",
        json={"email": "author@example.com", "password": "supersecret"},
    )

    assert login_response.status_code == 200
    token = login_response.json()["token"]

    me_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["user"]["email"] == "author@example.com"


def test_login_rejects_invalid_credentials(client: TestClient) -> None:
    client.post(
        "/api/auth/register",
        json={
            "name": "Author Person",
            "email": "author@example.com",
            "password": "supersecret",
        },
    )

    response = client.post(
        "/api/auth/login",
        json={"email": "author@example.com", "password": "wrongpass"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_credentials"
import asyncio

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


def _fetch_user_by_email(
    session_maker: async_sessionmaker[AsyncSession],
    user_model,
    email: str,
) -> object | None:
    async def _load() -> object | None:
        async with session_maker() as session:
            return await session.scalar(select(user_model).where(user_model.email == email))

    return asyncio.run(_load())


def test_register_returns_bearer_session_and_stable_mcp_token(
    client: TestClient,
    registered_user_payload: dict[str, str],
) -> None:
    response = client.post("/api/auth/register", json=registered_user_payload)

    assert response.status_code == 201
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["email"] == registered_user_payload["email"]
    assert body["user"]["name"] == registered_user_payload["name"]
    assert body["user"]["mcp_token"].startswith("hf_")


def test_register_rejects_duplicate_email(
    client: TestClient,
    registered_user_payload: dict[str, str],
) -> None:
    first_response = client.post("/api/auth/register", json=registered_user_payload)
    second_response = client.post("/api/auth/register", json=registered_user_payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json() == {
        "error": {
            "code": "email_taken",
            "message": "Email is already registered.",
        }
    }


def test_login_returns_session_for_valid_credentials(
    client: TestClient,
    registered_user_payload: dict[str, str],
) -> None:
    register_response = client.post("/api/auth/register", json=registered_user_payload)
    register_body = register_response.json()

    response = client.post(
        "/api/auth/login",
        json={
            "email": registered_user_payload["email"],
            "password": registered_user_payload["password"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["id"] == register_body["user"]["id"]
    assert body["user"]["mcp_token"] == register_body["user"]["mcp_token"]


def test_login_rejects_invalid_password(
    client: TestClient,
    registered_user_payload: dict[str, str],
) -> None:
    client.post("/api/auth/register", json=registered_user_payload)

    response = client.post(
        "/api/auth/login",
        json={
            "email": registered_user_payload["email"],
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "error": {
            "code": "invalid_credentials",
            "message": "Invalid email or password.",
        }
    }


def test_me_returns_current_user_for_valid_bearer_token(
    client: TestClient,
    registered_user_payload: dict[str, str],
) -> None:
    register_response = client.post("/api/auth/register", json=registered_user_payload)
    register_body = register_response.json()

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {register_body['access_token']}"},
    )

    assert response.status_code == 200
    assert response.json() == {"user": register_body["user"]}


def test_me_rejects_missing_or_invalid_token(client: TestClient) -> None:
    missing_token_response = client.get("/api/auth/me")
    invalid_token_response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer not-a-real-token"},
    )

    assert missing_token_response.status_code == 401
    assert missing_token_response.json() == {
        "error": {
            "code": "auth_required",
            "message": "Authentication required.",
        }
    }
    assert invalid_token_response.status_code == 401
    assert invalid_token_response.json() == {
        "error": {
            "code": "invalid_token",
            "message": "Invalid access token.",
        }
    }


def test_password_is_stored_hashed_not_plaintext(
    client: TestClient,
    registered_user_payload: dict[str, str],
    test_session_maker: async_sessionmaker[AsyncSession],
    app_modules,
) -> None:
    client.post("/api/auth/register", json=registered_user_payload)

    user = _fetch_user_by_email(
        test_session_maker,
        app_modules.models.User,
        registered_user_payload["email"],
    )

    assert user is not None
    assert user.password_hash != registered_user_payload["password"]
    assert user.password_hash.startswith("pbkdf2_sha256$")
