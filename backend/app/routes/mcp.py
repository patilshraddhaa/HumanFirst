from fastapi import APIRouter, Depends

from app.core.auth import require_current_user
from app.db.models import User
from app.routes.schemas import AuthMeResponse, UserResponse

router = APIRouter(prefix="/mcp", tags=["mcp"])


@router.get("/me", response_model=AuthMeResponse, operation_id="getMcpCurrentUser")
async def mcp_me(current_user: User = Depends(require_current_user)) -> AuthMeResponse:
    return AuthMeResponse(user=UserResponse.model_validate(current_user))
