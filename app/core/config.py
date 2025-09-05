"""
Application Configuration Settings
"""
import secrets
import os
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, EmailStr, field_validator, model_validator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


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
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8080,http://localhost:8010,http://10.1.19.51:8010,http://0.0.0.0:8010,http://127.0.0.1:8010"
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "10.1.19.51", "0.0.0.0"]
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="after")
    @classmethod
    def assemble_cors_origins(cls, v):
        if v is None:
            return "http://localhost:3000,http://localhost:8080"
        
        if isinstance(v, str):
            # Handle empty string
            if not v.strip():
                return "http://localhost:3000,http://localhost:8080"
            
            # Return as is for comma-separated values
            return v
        
        if isinstance(v, list):
            return ",".join(v)
        
        return "http://localhost:3000,http://localhost:8080"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list"""
        if not self.BACKEND_CORS_ORIGINS:
            return ["http://localhost:3000", "http://localhost:8080"]
        
        origins = [item.strip() for item in self.BACKEND_CORS_ORIGINS.split(',') if item.strip()]
        return origins if origins else ["http://localhost:3000", "http://localhost:8080"]
    
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
    
    # Logging configuration
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(default="json", description="Log format (json/text)")
    LOG_FILE: Optional[str] = Field(default=None, description="Log file path")
    
    # Middleware configuration
    ENABLE_CORS: bool = Field(default=True, description="Enable CORS middleware")
    ENABLE_RATE_LIMIT: bool = Field(default=True, description="Enable rate limiting")
    RATE_LIMIT_REQUESTS: int = Field(default=100, description="Rate limit requests per minute")
    RATE_LIMIT_WINDOW: int = Field(default=60, description="Rate limit window in seconds")
    
    # Security configuration
    ENABLE_SECURITY_HEADERS: bool = Field(default=True, description="Enable security headers")
    ENABLE_HTTPS_REDIRECT: bool = Field(default=False, description="Enable HTTPS redirect")
    
    # Plugin configuration
    ENABLE_PLUGINS: bool = Field(default=True, description="Enable plugin system")
    PLUGIN_DIRECTORY: str = Field(default="app/plugins", description="Plugin directory")
    
    # Dependency injection configuration
    ENABLE_DI: bool = Field(default=True, description="Enable dependency injection")
    
    # Monitoring configuration
    ENABLE_HEALTH_CHECKS: bool = Field(default=True, description="Enable health checks")
    HEALTH_CHECK_INTERVAL: int = Field(default=30, description="Health check interval in seconds")
    
    # Cache configuration
    CACHE_TTL: int = Field(default=300, description="Default cache TTL in seconds")
    CACHE_MAX_SIZE: int = Field(default=1000, description="Maximum cache size")
    
    # Task queue configuration
    TASK_QUEUE_MAX_JOBS: int = Field(default=10, description="Maximum concurrent jobs")
    TASK_QUEUE_TIMEOUT: int = Field(default=300, description="Task timeout in seconds")
    TASK_QUEUE_RETRY_ATTEMPTS: int = Field(default=3, description="Task retry attempts")
    
    # API configuration
    API_TITLE: str = Field(default="FastAPI Framework", description="API title")
    API_VERSION: str = Field(default="1.0.0", description="API version")
    API_DESCRIPTION: str = Field(default="A scalable FastAPI framework", description="API description")
    API_DOCS_URL: str = Field(default="/docs", description="API docs URL")
    API_REDOC_URL: str = Field(default="/redoc", description="API ReDoc URL")
    
    # Pagination configuration
    DEFAULT_PAGE_SIZE: int = Field(default=20, description="Default page size")
    MAX_PAGE_SIZE: int = Field(default=100, description="Maximum page size")
    
    # File upload configuration
    MAX_FILE_SIZE: int = Field(default=10 * 1024 * 1024, description="Maximum file size in bytes")
    ALLOWED_FILE_TYPES: List[str] = Field(default=["image/jpeg", "image/png", "image/gif"], description="Allowed file types")
    UPLOAD_DIRECTORY: str = Field(default="uploads", description="Upload directory")
    
    # Email configuration
    SMTP_TLS: bool = Field(default=True, description="Use TLS for SMTP")
    SMTP_SSL: bool = Field(default=False, description="Use SSL for SMTP")
    SMTP_PORT: int = Field(default=587, description="SMTP port")
    SMTP_USERNAME: Optional[str] = Field(default=None, description="SMTP username")
    SMTP_PASSWORD: Optional[str] = Field(default=None, description="SMTP password")
    SMTP_HOST: Optional[str] = Field(default=None, description="SMTP host")
    
    # Third-party API configuration
    THIRD_PARTY_API_TIMEOUT: int = Field(default=30, description="Third-party API timeout")
    THIRD_PARTY_API_RETRIES: int = Field(default=3, description="Third-party API retries")
    THIRD_PARTY_API_RATE_LIMIT: int = Field(default=100, description="Third-party API rate limit")
    
    # Development configuration
    DEBUG: bool = Field(default=False, description="Debug mode")
    RELOAD: bool = Field(default=False, description="Auto-reload on changes")
    WORKERS: int = Field(default=1, description="Number of worker processes")
    
    # Testing configuration
    TESTING: bool = Field(default=False, description="Testing mode")
    TEST_DATABASE_URL: Optional[str] = Field(default=None, description="Test database URL")
    
    # Environment
    ENVIRONMENT: str = Field(default="development", description="Environment (development/staging/production)")
    
    # Project paths
    PROJECT_ROOT: Path = Field(default=Path(__file__).parent.parent.parent, description="Project root directory")
    LOGS_DIR: Path = Field(default=Path("logs"), description="Logs directory")
    UPLOADS_DIR: Path = Field(default=Path("uploads"), description="Uploads directory")
    PLUGINS_DIR: Path = Field(default=Path("app/plugins"), description="Plugins directory")


# Create settings instance
settings = Settings()