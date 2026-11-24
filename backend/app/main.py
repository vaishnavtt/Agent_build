from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from app.core.config import settings
from app.database.base import Base
from app.database.session import engine, ensure_tables_and_columns
from app.api.v1.router import api_v1_router
from app.api.v1.endpoints import workflows, executions

# Ensure all database tables exist on module load
ensure_tables_and_columns()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events: ensure SQLite tables exist on startup."""
    ensure_tables_and_columns()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AgentForge AI - Autonomous visual workflow builder & execution engine backend.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Set up CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

# Direct /api route aliases for Member 2 REST API specifications
app.include_router(workflows.router, prefix="/api/workflows", tags=["Workflows"])
app.include_router(executions.router, prefix="/api/executions", tags=["Executions"])


@app.get("/", include_in_schema=False)
def root():
    """Redirect root to OpenAPI interactive documentation."""
    return RedirectResponse(url="/docs")
