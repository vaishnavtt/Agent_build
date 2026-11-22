from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.core.config import settings
from app.core.logging import logger
from app.database.session import init_db, engine
from app.api.v1.router import api_v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events: ensure SQLite tables and indexes exist on startup without wiping data."""
    logger.info("Initializing AgentForge AI backend and database tables...")
    init_db(engine)
    logger.info("Database initialized successfully.")
    yield
    logger.info("AgentForge AI backend shutting down.")


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


# -----------------------------------------------------------------------------
# CENTRALIZED EXCEPTION HANDLERS
# -----------------------------------------------------------------------------

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Format HTTP exceptions with consistent error responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error_code": f"HTTP_{exc.status_code}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Format Pydantic schema validation failures with clean details."""
    error_messages = []
    for error in exc.errors():
        loc = " -> ".join(str(p) for p in error.get("loc", []))
        msg = error.get("msg", "Invalid value")
        error_messages.append(f"{loc}: {msg}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "; ".join(error_messages) if error_messages else "Request validation failed.",
            "error_code": "VALIDATION_ERROR",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "errors": exc.errors(),
        },
    )


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Handle database constraint / foreign key integrity violations safely."""
    logger.error("Database integrity error on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "detail": "Database integrity constraint violation or duplicate entry.",
            "error_code": "DATABASE_INTEGRITY_ERROR",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle general database errors without exposing credentials or internal queries."""
    logger.error("Database error on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "A database error occurred while processing the request.",
            "error_code": "DATABASE_ERROR",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Catch-all for unhandled server exceptions."""
    logger.exception("Unhandled server exception on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred.",
            "error_code": "INTERNAL_SERVER_ERROR",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


# Mount API routers
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)


@app.get("/", include_in_schema=False)
def root():
    """Redirect root to OpenAPI interactive documentation."""
    return RedirectResponse(url="/docs")
