import hmac
from typing import Optional
from fastapi import Header, HTTPException, status
from app.core.config import settings


def verify_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> Optional[str]:
    """Validate API key if REQUIRE_API_KEY is enabled.
    
    Safe comparison using constant-time comparison to avoid timing attacks.
    Never exposes configured secret or client keys in errors or logs.
    """
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

