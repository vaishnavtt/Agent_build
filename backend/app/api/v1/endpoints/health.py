from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.config import settings
from app.database.session import get_db
from app.schemas.health import HealthCheckResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Service Health Check",
    description="Returns backend operational status and SQLite database connectivity verification.",
)
def get_health(db: Session = Depends(get_db)) -> HealthCheckResponse:
    """Verifies that FastAPI and SQLite are healthy and responding."""
    db_status = "connected"
    try:
        # Check SQLite connectivity
        db.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"unhealthy: {str(exc)}"

    return HealthCheckResponse(
        status="ok" if db_status == "connected" else "degraded",
        service=settings.PROJECT_NAME,
        version=settings.VERSION,
        timestamp=datetime.now(timezone.utc),
        database=db_status,
        details={
            "environment": settings.ENVIRONMENT,
            "supported_nodes_count": 7,
            "docs_url": "/docs",
        },
    )

