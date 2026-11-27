import hmac
from typing import Optional, List
from fastapi import Header, HTTPException, status, Depends
from pydantic import BaseModel, Field
from app.core.config import settings


class HostPrincipal(BaseModel):
    """Authenticated host principal context."""

    principal_id: str = Field(..., description="Unique principal / user identifier")
    username: Optional[str] = None
    roles: List[str] = Field(default_factory=lambda: ["user"])
    is_authenticated: bool = True

    @property
    def is_admin(self) -> bool:
        return "admin" in self.roles


def get_current_principal(
    x_principal_id: Optional[str] = Header(None, alias="X-Principal-ID"),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> HostPrincipal:
    """Resolve and authenticate host principal from incoming request context.
    
    Coordinates authentication integration across Member 4 and Member 6.
    Provides backward-compatible fallback for local UI development.
    """
    # 1. Verify API Key if global protection is active
    if settings.REQUIRE_API_KEY:
        if not settings.API_KEY:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Server API key protection is misconfigured.",
            )
        if not x_api_key or not hmac.compare_digest(x_api_key, settings.API_KEY):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API Key. Provide valid 'X-API-Key' header.",
            )

    # 2. Extract principal from explicit principal headers
    principal_id = x_principal_id or x_user_id

    # 3. Extract principal from Bearer token if provided
    if not principal_id and authorization and authorization.startswith("Bearer "):
        token = authorization.split("Bearer ", 1)[1].strip()
        if token.startswith("user:"):
            principal_id = token.split("user:", 1)[1]
        elif token:
            principal_id = f"principal-{token[:16]}"

    # 4. Fallback to default owner for development & local frontend compatibility
    if not principal_id:
        principal_id = "default-owner"

    roles = ["user"]
    if principal_id in ("admin", "system", "host-admin"):
        roles.append("admin")

    return HostPrincipal(
        principal_id=principal_id,
        username=principal_id,
        roles=roles,
        is_authenticated=True,
    )


def verify_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> Optional[str]:
    """Backward-compatible API key validator."""
    if not settings.REQUIRE_API_KEY:
        return x_api_key

    if not settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server API key protection is misconfigured.",
        )

    if not x_api_key or not hmac.compare_digest(x_api_key, settings.API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key. Provide valid 'X-API-Key' header.",
        )

    return x_api_key


def authorize_workflow_owner(workflow, principal: HostPrincipal) -> None:
    """Enforce workflow-level authorization and prevent cross-owner access."""
    if principal.is_admin:
        return
    # Default owner or creator matches principal
    if workflow.owner_id and workflow.owner_id != "default-owner" and workflow.owner_id != principal.principal_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: you do not have permission to access workflow '{workflow.id}'.",
        )
