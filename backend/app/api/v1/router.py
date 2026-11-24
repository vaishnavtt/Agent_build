from fastapi import APIRouter
from app.api.v1.endpoints import health, workflows, agents, executions

api_v1_router = APIRouter()

# Include endpoint routers
api_v1_router.include_router(health.router, tags=["Health"])
api_v1_router.include_router(workflows.router, prefix="/workflows", tags=["Workflows"])
api_v1_router.include_router(executions.router, prefix="/executions", tags=["Executions"])
api_v1_router.include_router(agents.router, prefix="/agents", tags=["Agents"])
