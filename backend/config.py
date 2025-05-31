# Configuration module for environment variables and app settings
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./chat.db"

    # Auth
    admin_username: str
    admin_password: str
    secret_key: str

    # AI Provider
    openai_provider: str = "openai"  # "openai" or "azure"
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"

    # Azure-specific
    azure_openai_endpoint: Optional[str] = None
    azure_openai_deployment: Optional[str] = None
    azure_openai_api_key: Optional[str] = None
    azure_openai_api_version: str = "2025-04-01-preview"

    # App settings
    max_tokens: int = 2048
    temperature: float = 0.7
    stream_chunk_size: int = 512

    # Security
    cors_origins: list = ["http://localhost:5173"]
    session_expire_minutes: int = 1440  # 24 hours

    # Server
    server_host: str = "0.0.0.0"
    server_port: int = 8000

    @validator("database_url")
    def configure_sqlite_wal(cls, v):
        if v.startswith("sqlite"):
            return v + "?mode=wal"
        return v

    class Config:
        # Resolve the .env file relative to this module's directory.
        # Allows starting the app from any working directory.
        env_file = os.path.join(os.path.dirname(__file__), ".env")
        env_file_encoding = "utf-8"
        # Map uppercase env names like ADMIN_USERNAME -> admin_username
        case_sensitive = False


settings = Settings()
