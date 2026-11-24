from fastapi import APIRouter
from app.api.v1.endpoints import health, repair, workflows

api_v1_router = APIRouter()

# Include endpoint routers
api_v1_router.include_router(health.router, tags=["Health"])
api_v1_router.include_router(workflows.router, prefix="/workflows", tags=["Workflows"])
api_v1_router.include_router(repair.router, prefix="/repair", tags=["Repair"])
