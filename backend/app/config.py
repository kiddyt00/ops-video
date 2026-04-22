"""
Application configuration
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings"""

    # Project
    PROJECT_NAME: str = "Ops-Video"
    VERSION: str = "0.1.0"

    # Database
    DATABASE_URL: str = Field(
        default="postgresql://ops:ops_password@localhost:5432/ops_video",
        description="PostgreSQL connection URL"
    )

    # ComfyUI
    COMFYUI_HOST: str = "localhost"
    COMFYUI_PORT: int = 8188

    @property
    def comfyui_url(self) -> str:
        return f"http://{self.COMFYUI_HOST}:{self.COMFYUI_PORT}"

    # LLM (optional)
    LLM_API_KEY: str = ""
    LLM_API_BASE_URL: str = "http://localhost:11434/v1"
    LLM_MODEL: str = "qwen:7b"

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
    # Options: COMFYUI (local), DASHSCOPE (通义万相), SILICONFLOW (FLUX.1)
    IMAGE_PROVIDER: str = "COMFYUI"

    # DashScope (通义万相) API
    DASHSCOPE_API_KEY: str = ""
    DASHSCOPE_MODEL: str = "wanx-v1"  # wanx-v1 or wanx-v2

    # SiliconFlow API (OpenAI-compatible /images/generations)
    SILICONFLOW_API_KEY: str = ""
    SILICONFLOW_MODEL: str = "black-forest-labs/FLUX.1-schnell"

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

    class Config:
        env_file = ".env"
        case_sensitive = True


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
