"""
Application Configuration Settings
"""
import secrets
import os
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, EmailStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""
    
    model_config = SettingsConfigDict(
        env_file=".env.example" if os.getenv("ENVIRONMENT") == "testing" else ".env",
        env_ignore_empty=True,
        extra="ignore",
        case_sensitive=False,
    )
    
    # Project Information
    PROJECT_NAME: str = "FastAPI Application"
    PROJECT_DESCRIPTION: str = "A FastAPI application with modern architecture"
    PROJECT_VERSION: str = "1.0.0"
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    
    # Server Configuration
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    ENVIRONMENT: str = "development"  # development, staging, production
    LOG_LEVEL: str = "INFO"
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days
    ALGORITHM: str = "HS256"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000", 
        "http://localhost:8080",
        "http://localhost:8010",
        "http://10.1.19.51:8010",
        "http://0.0.0.0:8010",
        "http://127.0.0.1:8010"
    ]
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "10.1.19.51", "0.0.0.0"]
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if v is None:
            return ["http://localhost:3000", "http://localhost:8080"]
        
        if isinstance(v, str):
            # Handle empty string
            if not v.strip():
                return ["http://localhost:3000", "http://localhost:8080"]
            
            # Handle comma-separated values
            if ',' in v:
                origins = [item.strip() for item in v.split(',') if item.strip()]
                return origins if origins else ["http://localhost:3000", "http://localhost:8080"]
            
            # Single URL
            return [v.strip()]
        
        if isinstance(v, list):
            return v
        
        # Fallback
        return ["http://localhost:3000", "http://localhost:8080"]
    
    # Database Configuration
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "fastapi_db"
    POSTGRES_PORT: int = 15432
    
    DATABASE_URL: Optional[str] = None
    
    # Testing
    TEST_DATABASE_URL: Optional[str] = None
    
    @model_validator(mode="after")
    def assemble_db_connections(self) -> "Settings":
        # Assemble main database URL
        if not self.DATABASE_URL:
            self.DATABASE_URL = (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
                f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        
        # Assemble test database URL
        if not self.TEST_DATABASE_URL:
            self.TEST_DATABASE_URL = (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
                f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/fastapi_test_db"
            )
        return self
    
    # Redis Configuration (for caching and background tasks)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # ARQ Task Queue Configuration
    ARQ_REDIS_URL: str = "redis://localhost:6379/0"
    ARQ_MAX_JOBS: int = 10
    ARQ_JOB_TIMEOUT: int = 300  # 5 minutes
    ARQ_KEEP_RESULT: int = 3600  # 1 hour
    
    # Email Configuration
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[EmailStr] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    # Admin User
    FIRST_SUPERUSER_EMAIL: EmailStr = "admin@example.com"
    FIRST_SUPERUSER_PASSWORD: str = "admin123"
    
    # Admin Interface
    ADMIN_SECRET_KEY: str = secrets.token_urlsafe(32)
    ADMIN_TITLE: str = "FastAPI Admin"
    ADMIN_LOGO_URL: Optional[str] = None
    
    # File Upload
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_FOLDER: str = "uploads"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # Prometheus Metrics
    ENABLE_METRICS: bool = True
    PROMETHEUS_PORT: int = 9090
    
    # Prometheus Server Configuration
    PROMETHEUS_SERVER_HOST: str = "localhost"
    PROMETHEUS_SERVER_PORT: int = 9091
    PROMETHEUS_SERVER_URL: str = "http://localhost:9091"
    PROMETHEUS_QUERY_TIMEOUT: int = 30


# Create settings instance
settings = Settings()