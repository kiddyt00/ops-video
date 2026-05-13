"""
Application configuration
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings"""

    # Project
    PROJECT_NAME: str = "Ops-Video"
    VERSION: str = "0.1.0"

    # Database
    DATABASE_URL: str = Field(
        default="postgresql://ops:***@localhost:5432/ops_video",
        description="PostgreSQL connection URL"
    )

    # LLM configuration is now managed via the database (AIModel with category='llm' and is_active=True)
    # See: /api/ai-models endpoints

    # Storage
    STORAGE_PATH: str = "./storage"

    @property
    def storage_path(self) -> Path:
        return Path(self.STORAGE_PATH).resolve()

    # CORS
    FRONTEND_URL: str = "http://localhost:3000"

    @property
    def cors_origins(self) -> list[str]:
        return [
            self.FRONTEND_URL,
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]

    # Redis (optional)
    REDIS_URL: str = Field(
        default="",
        description="Redis connection URL (redis://localhost:6379/0)"
    )

    # Image Generation Provider
    # Options: DASHSCOPE (通义万相), SILICONFLOW (FLUX.1)
    IMAGE_PROVIDER: str = "DASHSCOPE"

    # DashScope (通义万相) API
    DASHSCOPE_API_KEY: str = "sk-26a410fc4042497187fd5401f786c155"
    DASHSCOPE_MODEL: str = "wan2.6-t2i"  # wan2.6 同步调用，推荐

    # SiliconFlow API (OpenAI-compatible /images/generations)
    SILICONFLOW_API_KEY: str = ""
    SILICONFLOW_MODEL: str = "black-forest-labs/FLUX.1-schnell"

    # Mock Mode — skip real API calls, return fake data
    MOCK_MODE: bool = False

    # Graph provider (sqlite | neo4j)
    GRAPH_PROVIDER: str = "sqlite"
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or text
    LOG_DIR: str = "./logs"

    @property
    def log_path(self) -> Path:
        return Path(self.LOG_DIR).resolve()

    # JWT Authentication
    JWT_SECRET_KEY: str = Field(
        default="change-this-secret-key-in-production",
        description="Secret key for JWT token signing"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="allow")


settings = Settings()

# Ensure storage directories exist
STORAGE_DIRS = {
    "images": settings.storage_path / "images",
    "audio": settings.storage_path / "audio",
    "video": settings.storage_path / "video",
    "scripts": settings.storage_path / "scripts",
    "storyboards": settings.storage_path / "storyboards",
}

for dir_path in STORAGE_DIRS.values():
    dir_path.mkdir(parents=True, exist_ok=True)
