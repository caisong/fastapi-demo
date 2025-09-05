"""
Middleware Configuration Example

This file shows how to configure authentication middleware as an alternative to Depends.
"""

from fastapi import FastAPI
from app.core.middleware import add_middleware
from app.core.config import settings

# Example 1: Standard configuration (Depends only)
def create_app_standard():
    """Create app with standard Depends-based authentication"""
    app = FastAPI(title="Standard Auth App")
    
    # Add middleware without authentication middleware
    add_middleware(app, enable_auth_middleware=False)
    
    return app


# Example 2: With authentication middleware enabled
def create_app_with_middleware():
    """Create app with authentication middleware enabled"""
    app = FastAPI(title="Middleware Auth App")
    
    # Add middleware with authentication middleware
    add_middleware(app, enable_auth_middleware=True)
    
    return app


# Example 3: Custom middleware configuration
def create_app_custom():
    """Create app with custom middleware configuration"""
    app = FastAPI(title="Custom Auth App")
    
    # Add custom authentication middleware with custom skip paths
    from app.core.middleware import AuthenticationMiddleware
    
    custom_skip_paths = [
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health",
        "/metrics",
        "/api/v1/auth/register",
        "/api/v1/auth/login",
        "/api/v1/auth/login-json",
        "/api/v1/auth/refresh",
        "/api/v1/public",  # Custom public endpoint
    ]
    
    app.add_middleware(AuthenticationMiddleware, skip_paths=custom_skip_paths)
    
    # Add other middleware
    add_middleware(app, enable_auth_middleware=False)
    
    return app


# Example 4: Environment-based configuration
def create_app_environment_based():
    """Create app with environment-based middleware configuration"""
    app = FastAPI(title="Environment Auth App")
    
    # Enable authentication middleware based on environment
    enable_auth_middleware = settings.ENVIRONMENT in ["production", "staging"]
    add_middleware(app, enable_auth_middleware=enable_auth_middleware)
    
    return app


# Example 5: Conditional middleware based on settings
def create_app_conditional():
    """Create app with conditional middleware based on settings"""
    app = FastAPI(title="Conditional Auth App")
    
    # Check if authentication middleware should be enabled
    # This could be controlled by environment variables
    enable_auth_middleware = getattr(settings, 'ENABLE_AUTH_MIDDLEWARE', False)
    
    add_middleware(app, enable_auth_middleware=enable_auth_middleware)
    
    return app


# Usage examples:

# For most applications, use Depends (recommended):
# app = create_app_standard()

# For applications that need global authentication:
# app = create_app_with_middleware()

# For applications with custom requirements:
# app = create_app_custom()

# For environment-specific configurations:
# app = create_app_environment_based()

# For settings-controlled configurations:
# app = create_app_conditional()