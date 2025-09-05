"""
Application constants and enums
"""
from enum import Enum
from typing import Dict, Any


class Environment(str, Enum):
    """Environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class LogLevel(str, Enum):
    """Log levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class HTTPStatus(str, Enum):
    """HTTP status codes"""
    OK = "200"
    CREATED = "201"
    NO_CONTENT = "204"
    BAD_REQUEST = "400"
    UNAUTHORIZED = "401"
    FORBIDDEN = "403"
    NOT_FOUND = "404"
    CONFLICT = "409"
    UNPROCESSABLE_ENTITY = "422"
    INTERNAL_SERVER_ERROR = "500"


class TaskStatus(str, Enum):
    """Task status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ServiceType(str, Enum):
    """Service types"""
    WEB = "web"
    WORKER = "worker"
    PROMETHEUS = "prometheus"
    PUSHGATEWAY = "pushgateway"
    REDIS = "redis"


# Application metadata
APP_METADATA = {
    "name": "FastAPI Framework",
    "version": "1.0.0",
    "description": "A scalable FastAPI framework with monitoring and task management",
    "author": "Development Team",
    "license": "MIT",
    "homepage": "https://github.com/your-org/fastapi-framework",
}

# API configuration
API_CONFIG = {
    "title": "FastAPI Framework API",
    "version": "1.0.0",
    "description": "A comprehensive FastAPI framework with monitoring capabilities",
    "terms_of_service": "https://example.com/terms/",
    "contact": {
        "name": "API Support",
        "url": "https://example.com/contact/",
        "email": "support@example.com",
    },
    "license_info": {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
}

# Default pagination settings
PAGINATION_CONFIG = {
    "default_page_size": 20,
    "max_page_size": 100,
    "page_size_param": "page_size",
    "page_param": "page",
}

# Cache configuration
CACHE_CONFIG = {
    "default_ttl": 300,  # 5 minutes
    "max_ttl": 3600,     # 1 hour
    "key_prefix": "fastapi:",
}

# Rate limiting configuration
RATE_LIMIT_CONFIG = {
    "default_requests": 100,
    "default_window": 60,  # seconds
    "burst_requests": 200,
    "burst_window": 60,
}

# Monitoring configuration
MONITORING_CONFIG = {
    "metrics_enabled": True,
    "health_check_interval": 30,
    "prometheus_port": 9090,
    "pushgateway_port": 9091,
    "log_level": "INFO",
}

# Database configuration
DATABASE_CONFIG = {
    "pool_size": 10,
    "max_overflow": 20,
    "pool_timeout": 30,
    "pool_recycle": 3600,
    "echo": False,
}

# Security configuration
SECURITY_CONFIG = {
    "jwt_algorithm": "HS256",
    "access_token_expire_minutes": 30,
    "refresh_token_expire_days": 7,
    "password_min_length": 8,
    "password_require_uppercase": True,
    "password_require_lowercase": True,
    "password_require_digits": True,
    "password_require_special": False,
}

# Task queue configuration
TASK_QUEUE_CONFIG = {
    "max_jobs": 10,
    "job_timeout": 300,
    "keep_result": 3600,
    "retry_attempts": 3,
    "retry_delay": 60,
}

# Third-party API configuration
THIRD_PARTY_API_CONFIG = {
    "default_timeout": 30,
    "max_retries": 3,
    "retry_delay": 1,
    "rate_limit_requests": 100,
    "rate_limit_window": 60,
}

# Error codes
ERROR_CODES = {
    "VALIDATION_ERROR": "VALIDATION_ERROR",
    "AUTHENTICATION_ERROR": "AUTHENTICATION_ERROR",
    "AUTHORIZATION_ERROR": "AUTHORIZATION_ERROR",
    "NOT_FOUND_ERROR": "NOT_FOUND_ERROR",
    "CONFLICT_ERROR": "CONFLICT_ERROR",
    "INTERNAL_ERROR": "INTERNAL_ERROR",
    "EXTERNAL_SERVICE_ERROR": "EXTERNAL_SERVICE_ERROR",
    "RATE_LIMIT_ERROR": "RATE_LIMIT_ERROR",
    "TASK_ERROR": "TASK_ERROR",
    "DATABASE_ERROR": "DATABASE_ERROR",
}

# Service endpoints
SERVICE_ENDPOINTS = {
    "health": "/health",
    "metrics": "/metrics",
    "docs": "/docs",
    "redoc": "/redoc",
    "openapi": "/openapi.json",
    "admin": "/admin",
    "api": "/api/v1",
}

# Default response messages
RESPONSE_MESSAGES = {
    "success": "Operation completed successfully",
    "created": "Resource created successfully",
    "updated": "Resource updated successfully",
    "deleted": "Resource deleted successfully",
    "not_found": "Resource not found",
    "unauthorized": "Authentication required",
    "forbidden": "Access denied",
    "validation_error": "Validation error",
    "internal_error": "Internal server error",
}