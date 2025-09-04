"""
Custom middleware for the FastAPI application
"""
import time
from typing import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


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


def add_middleware(app: FastAPI) -> None:
    """Add all custom middleware to the FastAPI app"""
    
    # Add process time middleware
    app.add_middleware(ProcessTimeMiddleware)
    
    # Add request logging middleware (only in development)
    from app.core.config import settings
    if settings.ENVIRONMENT == "development":
        app.add_middleware(RequestLoggingMiddleware)