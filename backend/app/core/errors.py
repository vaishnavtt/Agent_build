from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class APIErrorResponse(BaseModel):
    """Standardized API error response schema."""

    detail: str
    error_code: str = Field(default="INTERNAL_ERROR")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    details: Optional[Dict[str, Any]] = None

