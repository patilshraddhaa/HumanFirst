from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.config import settings
from app.db.models import User
from app.db.session import get_session

bearer_scheme = HTTPBearer(auto_error=False)


def create_access_token(
    *,
    subject: str,
    user_id: str | UUID,
    expires_delta: timedelta | None = None,
) -> str:
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + (
        expires_delta or timedelta(minutes=settings.jwt_access_token_ttl_minutes)
    )
    payload = {
        "sub": subject,
        "user_id": str(user_id),
        "iat": issued_at,
        "exp": expires_at,
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        claims = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=401,
            detail={"error": "invalid_token", "message": "Invalid access token."},
        ) from exc

    if not claims.get("sub") or not claims.get("user_id"):
        raise HTTPException(
            status_code=401,
            detail={"error": "invalid_token", "message": "Invalid access token."},
        )
    return claims


async def get_current_user(
    session: AsyncSession = Depends(get_session),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> User:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=401,
            detail={"error": "auth_required", "message": "Authentication required."},
        )

    claims = decode_access_token(credentials.credentials)
    try:
        user_id = UUID(str(claims["user_id"]))
    except ValueError as exc:
        raise HTTPException(
            status_code=401,
            detail={"error": "invalid_token", "message": "Invalid access token."},
        ) from exc

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=401,
            detail={"error": "user_not_found", "message": "User no longer exists."},
        )
    return user


async def require_current_user(user: User = Depends(get_current_user)) -> User:
    return user
