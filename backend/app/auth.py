from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from uuid import UUID

import jwt
from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import User
from app.db.session import get_session

_AUTH_SECRET = os.environ.get("APP_AUTH_TOKEN_SECRET", "dev-auth-token-secret")


@dataclass(slots=True)
class CurrentUser:
    id: UUID
    display_name: str | None = None


def _unauthorized(message: str) -> HTTPException:
    return HTTPException(
        status_code=401,
        detail={"error": "unauthorized", "message": message},
    )


def _urlsafe_b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _urlsafe_b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}")


def _sign(encoded_payload: str) -> str:
    digest = hmac.new(_AUTH_SECRET.encode("utf-8"), encoded_payload.encode("ascii"), hashlib.sha256).digest()
    return _urlsafe_b64encode(digest)


def create_access_token(user_id: str | UUID, display_name: str | None = None) -> str:
    payload = {"sub": str(user_id)}
    if display_name:
        payload["name"] = display_name
    encoded_payload = _urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    return f"{encoded_payload}.{_sign(encoded_payload)}"


def _decode_legacy_token(token: str) -> tuple[UUID, str | None]:
    encoded_payload, separator, signature = token.partition(".")
    if not separator or not encoded_payload or not signature:
        raise _unauthorized("Bearer token is malformed.")
    expected_signature = _sign(encoded_payload)
    if not hmac.compare_digest(signature, expected_signature):
        raise _unauthorized("Bearer token is invalid.")
    try:
        payload = json.loads(_urlsafe_b64decode(encoded_payload))
    except (ValueError, json.JSONDecodeError) as exc:
        raise _unauthorized("Bearer token is malformed.") from exc
    raw_user_id = payload.get("sub")
    if not isinstance(raw_user_id, str) or not raw_user_id.strip():
        raise _unauthorized("Bearer token must include a user id.")
    try:
        user_id = UUID(raw_user_id.strip())
    except ValueError as exc:
        raise _unauthorized("Bearer token must include a valid user id.") from exc
    display_name = payload.get("name")
    if display_name is not None and not isinstance(display_name, str):
        raise _unauthorized("Bearer token is malformed.")
    cleaned_display_name = display_name.strip() or None if isinstance(display_name, str) else None
    return user_id, cleaned_display_name


def _decode_jwt_token(token: str) -> tuple[UUID, str | None]:
    try:
        claims = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.PyJWTError as exc:
        raise _unauthorized("Bearer token is invalid.") from exc

    raw_user_id = claims.get("user_id")
    if not isinstance(raw_user_id, str) or not raw_user_id.strip():
        raise _unauthorized("Bearer token must include a user id.")
    try:
        user_id = UUID(raw_user_id.strip())
    except ValueError as exc:
        raise _unauthorized("Bearer token must include a valid user id.") from exc
    display_name = claims.get("name")
    if display_name is not None and not isinstance(display_name, str):
        raise _unauthorized("Bearer token is malformed.")
    cleaned_display_name = display_name.strip() or None if isinstance(display_name, str) else None
    return user_id, cleaned_display_name


def _decode_token(token: str) -> tuple[UUID, str | None]:
    segments = token.count(".")
    if segments == 2:
        return _decode_jwt_token(token)
    if segments == 1:
        return _decode_legacy_token(token)
    raise _unauthorized("Bearer token is malformed.")


async def get_current_user(
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
) -> CurrentUser:
    if not authorization:
        raise _unauthorized("Authentication is required.")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise _unauthorized("Authorization must use a bearer token.")
    user_id, claimed_display_name = _decode_token(token)
    user = await session.get(User, user_id)
    if user is None:
        raise _unauthorized("Authenticated user was not found.")
    display_name = user.display_name or user.name or claimed_display_name
    return CurrentUser(id=user.id, display_name=display_name)
