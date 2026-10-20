from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import create_access_token, require_current_user
from app.core.security import generate_mcp_token, hash_password, verify_password
from app.db.models import User
from app.db.session import get_session
from app.routes.schemas import (
    AuthLoginRequest,
    AuthMeResponse,
    AuthRegisterRequest,
    AuthSessionResponse,
    UserResponse,
)

router = APIRouter()


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _serialize_user(user: User) -> UserResponse:
    return UserResponse.model_validate(user)


@router.post(
    "/register",
    response_model=AuthSessionResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="registerAuthUser",
)
async def register(
    payload: AuthRegisterRequest,
    session: AsyncSession = Depends(get_session),
) -> AuthSessionResponse:
    email = _normalize_email(str(payload.email))
    existing_user = await session.scalar(select(User).where(User.email == email))
    if existing_user is not None:
        raise HTTPException(
            status_code=409,
            detail={"error": "email_taken", "message": "Email is already registered."},
        )

    user = User(
        name=payload.name.strip(),
        display_name=payload.name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
        mcp_token=generate_mcp_token(),
        mcp_token_issued_at=datetime.now(timezone.utc),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return AuthSessionResponse(
        access_token=create_access_token(subject=user.email, user_id=user.id),
        user=_serialize_user(user),
    )


@router.post(
    "/login",
    response_model=AuthSessionResponse,
    operation_id="loginAuthUser",
)
async def login(
    payload: AuthLoginRequest,
    session: AsyncSession = Depends(get_session),
) -> AuthSessionResponse:
    email = _normalize_email(str(payload.email))
    user = await session.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail={
                "error": "invalid_credentials",
                "message": "Invalid email or password.",
            },
        )

    return AuthSessionResponse(
        access_token=create_access_token(subject=user.email, user_id=user.id),
        user=_serialize_user(user),
    )


@router.get(
    "/me",
    response_model=AuthMeResponse,
    operation_id="getCurrentAuthUser",
)
async def me(current_user: User = Depends(require_current_user)) -> AuthMeResponse:
    return AuthMeResponse(user=_serialize_user(current_user))
