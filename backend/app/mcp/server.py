from fastmcp import FastMCP

from app.core.config import settings
from app.mcp.auth import BearerTokenAuthMiddleware
from app.mcp.tools import register_tools


def create_mcp_server() -> FastMCP:
    mcp = FastMCP("humanfirst")
    mcp.add_middleware(BearerTokenAuthMiddleware())
    register_tools(mcp)
    return mcp


def serve() -> None:
    mcp.run(
        transport="http",
        host=settings.mcp_host,
        port=settings.mcp_port,
        path=settings.mcp_public_path,
    )


mcp = create_mcp_server()
