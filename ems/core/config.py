# app/core/config.py
import secrets
import os
from typing import Any, Dict, List, Optional, Union

from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, field_validator, ConfigDict

class Settings(BaseSettings):
    model_config = ConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra='allow'
    )
    
    API_V1_STR: str = "/api"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    # 60 minutes * 24 hours * 7 days = 7 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days
    SERVER_NAME: str = "Event Management System"
    SERVER_HOST: AnyHttpUrl = "http://localhost:8000"
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    # Database settings
    POSTGRES_SERVER: str = os.getenv("PGHOST", "localhost")
    POSTGRES_USER: str = os.getenv("PGUSER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("PGPASSWORD", "password") 
    POSTGRES_DB: str = os.getenv("PGDATABASE", "ems")
    DATABASE_URI: str = os.getenv("DATABASE_URI", "postgresql://postgres:password@localhost:5432/ems")  # Changed from PostgresDsn to str

    # Authentication settings
    JWT_ALGORITHM: str = "HS256"
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

settings = Settings()