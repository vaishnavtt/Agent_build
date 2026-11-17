from datetime import datetime
from typing import Dict, Any
from pydantic import BaseModel, Field


class HealthCheckResponse(BaseModel):
    """Health check status response schema."""

    status: str = Field(default="ok", example="ok")
    service: str = Field(default="AgentForge AI Backend", example="AgentForge AI Backend")
    version: str = Field(default="1.0.0", example="1.0.0")
    timestamp: datetime = Field(description="Server UTC timestamp")
    database: str = Field(default="connected", example="connected")
    details: Dict[str, Any] = Field(default_factory=dict)

