"""
Custom middleware for the FastAPI application
"""
import time
from typing import Callable, Optional

from fastapi import FastAPI, Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from jose import jwt
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.auth import TokenPayload


class ProcessTimeMiddleware(BaseHTTPMiddleware):
    """Middleware to add process time header"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log requests"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Log request
        print(f"Request: {request.method} {request.url}")
        
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        print(
            f"Response: {response.status_code} - "
            f"Time: {process_time:.4f}s - "
            f"Path: {request.url.path}"
        )
        
        return response


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Optional authentication middleware for global JWT validation
    This can be used as an alternative to Depends for certain routes
    """
    
    def __init__(self, app, skip_paths: Optional[list] = None):
        super().__init__(app)
        self.skip_paths = skip_paths or [
            "/docs",
            "/redoc", 
            "/openapi.json",
            "/health",
            "/metrics",
            "/api/v1/auth/register",
            "/api/v1/auth/login",
            "/api/v1/auth/login-json",
            "/api/v1/auth/refresh",
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip authentication for certain paths
        if any(request.url.path.startswith(path) for path in self.skip_paths):
            return await call_next(request)
        
        # Check for Authorization header
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            # For API routes, return 401; for others, continue
            if request.url.path.startswith("/api/"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return await call_next(request)
        
        # Validate JWT token
        token = authorization.split(" ")[1]
        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=[settings.ALGORITHM]
            )
            token_data = TokenPayload(**payload)
            # Store user info in request state for use in endpoints
            request.state.user_id = int(token_data.sub)
        except (jwt.JWTError, ValidationError):
            if request.url.path.startswith("/api/"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        
        return await call_next(request)


def add_middleware(app: FastAPI, enable_auth_middleware: bool = False) -> None:
    """
    Add all custom middleware to the FastAPI app
    
    Args:
        app: FastAPI application instance
        enable_auth_middleware: Whether to enable authentication middleware
                               (Depends is recommended for most use cases)
    """
    
    # Add process time middleware
    app.add_middleware(ProcessTimeMiddleware)
    
    # Add request logging middleware (only in development)
    from app.core.config import settings
    if settings.ENVIRONMENT == "development":
        app.add_middleware(RequestLoggingMiddleware)
    
    # Add authentication middleware (optional)
    if enable_auth_middleware:
        app.add_middleware(AuthenticationMiddleware)