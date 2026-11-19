from fastapi import APIRouter
from app.api.v1.endpoints import health, workflows

api_v1_router = APIRouter()

# Include endpoint routers
api_v1_router.include_router(health.router, tags=["Health"])
api_v1_router.include_router(workflows.router, prefix="/workflows", tags=["Workflows"])
