from fastapi import APIRouter
from app.api.v1.endpoints import health, regression, reliability, testing, validation, workflows

api_v1_router = APIRouter()

# Include endpoint routers
api_v1_router.include_router(health.router, tags=["Health"])
api_v1_router.include_router(workflows.router, prefix="/workflows", tags=["Workflows"])
api_v1_router.include_router(validation.router, prefix="/workflows", tags=["Validation"])
api_v1_router.include_router(testing.router, prefix="/workflows", tags=["Testing"])
api_v1_router.include_router(reliability.router, prefix="/workflows", tags=["Reliability Lab"])
api_v1_router.include_router(regression.router, prefix="/workflows", tags=["Regression"])
