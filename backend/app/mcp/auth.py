from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from fastmcp import Context
from fastmcp.server.dependencies import get_http_headers
from fastmcp.server.middleware import Middleware, MiddlewareContext
from sqlalchemy import select

from app.db import session as db_session
from app.db.models import User

MCP_USER_STATE_KEY = "current_user"


@dataclass(slots=True)
class MCPError(Exception):
    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


def raise_auth_required() -> None:
    raise MCPError(code="auth_required", message="Authorization header is required.")


def extract_bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise_auth_required()

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token or not token.startswith("hf_"):
        raise MCPError(code="invalid_token", message="Expected Authorization: Bearer hf_....")
    return token


async def resolve_mcp_user_from_token(token: str) -> User:
    async with db_session.AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.mcp_token == token))
        user = result.scalar_one_or_none()
    if user is None:
        raise MCPError(code="invalid_token", message="Bearer token is unknown.")
    return user


async def resolve_mcp_user_from_headers(headers: Mapping[str, str]) -> User:
    token = extract_bearer_token(headers.get("authorization"))
    return await resolve_mcp_user_from_token(token)


def require_mcp_user(ctx: Context) -> User:
    user = ctx.get_state(MCP_USER_STATE_KEY)
    if not isinstance(user, User):
        raise_auth_required()
    return user


class BearerTokenAuthMiddleware(Middleware):
    async def on_call_tool(self, context: MiddlewareContext, call_next):
        fastmcp_context = context.fastmcp_context
        if fastmcp_context is None:
            raise_auth_required()

        headers = get_http_headers(include={"authorization"})
        user = await resolve_mcp_user_from_headers(headers)
        fastmcp_context.set_state(MCP_USER_STATE_KEY, user, serializable=False)
        return await call_next(context)
