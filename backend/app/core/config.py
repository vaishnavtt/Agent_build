from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application runtime settings and environment variables."""

    PROJECT_NAME: str = "AgentForge AI"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database Configuration (SQLite default)
    DATABASE_URL: str = "sqlite:///./agentforge.db"

    # CORS configuration
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    # AI Configuration (Placeholders for Member 3 & Member 5)
    GEMINI_API_KEY: str = ""
    GEMINI_DEFAULT_MODEL: str = "gemini-1.5-pro"

    # Execution Engine Configuration (Member 5 & Member 6)
    DEFAULT_TIMEOUT_SECONDS: int = 300
    AUTO_REPAIR_MAX_ATTEMPTS: int = 3

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()

