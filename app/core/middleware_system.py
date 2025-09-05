"""
Enhanced middleware system
"""
from typing import Any, Callable, Optional, Dict, List
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
import time
import uuid
from contextvars import ContextVar

from .logging import get_logger, log_request, log_response, log_error
from .exceptions import BaseAPIException, handle_exception
from .response import create_error_response
from .constants import SERVICE_ENDPOINTS

logger = get_logger(__name__)

# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)


class MiddlewareChain:
    """Middleware chain for managing middleware execution order"""
    
    def __init__(self):
        self.middlewares: List[BaseHTTPMiddleware] = []
        self.logger = get_logger("middleware_chain")
    
    def add_middleware(self, middleware: BaseHTTPMiddleware) -> None:
        """Add middleware to chain"""
        self.middlewares.append(middleware)
        self.logger.debug(f"Added middleware: {middleware.__class__.__name__}")
    
    def remove_middleware(self, middleware_class: type) -> None:
        """Remove middleware from chain"""
        self.middlewares = [m for m in self.middlewares if not isinstance(m, middleware_class)]
        self.logger.debug(f"Removed middleware: {middleware_class.__name__}")
    
    def get_middlewares(self) -> List[BaseHTTPMiddleware]:
        """Get all middlewares"""
        return self.middlewares.copy()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request logging"""
    
    def __init__(self, app, exclude_paths: Optional[List[str]] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            SERVICE_ENDPOINTS["health"],
            SERVICE_ENDPOINTS["metrics"],
            "/favicon.ico"
        ]
        self.logger = get_logger("request_logging")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and response"""
        # Skip logging for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Generate request ID
        request_id = str(uuid.uuid4())
        request_id_var.set(request_id)
        
        # Log request
        start_time = time.time()
        log_request(
            self.logger,
            request_id=request_id,
            method=request.method,
            url=request.url,
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            content_length=request.headers.get("content-length")
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Log response
            duration = time.time() - start_time
            log_response(
                self.logger,
                request_id=request_id,
                status_code=response.status_code,
                duration=duration,
                content_length=response.headers.get("content-length")
            )
            
            return response
            
        except Exception as e:
            # Log error
            duration = time.time() - start_time
            log_error(
                self.logger,
                request_id=request_id,
                error=e,
                duration=duration
            )
            raise


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for error handling"""
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = get_logger("error_handling")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle errors and return standardized responses"""
        try:
            return await call_next(request)
        except BaseAPIException as e:
            # Handle custom API exceptions
            self.logger.error(f"API Exception: {e.message}", extra={
                "error_code": e.error_code,
                "details": e.details,
                "request_id": request_id_var.get()
            })
            return create_error_response(
                message=e.message,
                error_code=e.error_code,
                details=e.details,
                status_code=e.status_code
            )
        except Exception as e:
            # Handle unexpected exceptions
            self.logger.error(f"Unexpected error: {str(e)}", exc_info=True, extra={
                "request_id": request_id_var.get()
            })
            
            # Convert to API exception
            api_exception = handle_exception(e)
            return create_error_response(
                message=api_exception.message,
                error_code=api_exception.error_code,
                details=api_exception.details,
                status_code=api_exception.status_code
            )


class CORSMiddleware(BaseHTTPMiddleware):
    """Enhanced CORS middleware"""
    
    def __init__(
        self,
        app,
        allow_origins: Optional[List[str]] = None,
        allow_methods: Optional[List[str]] = None,
        allow_headers: Optional[List[str]] = None,
        allow_credentials: bool = True,
        max_age: int = 600
    ):
        super().__init__(app)
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.allow_headers = allow_headers or ["*"]
        self.allow_credentials = allow_credentials
        self.max_age = max_age
        self.logger = get_logger("cors")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle CORS"""
        origin = request.headers.get("origin")
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            response = Response()
            self._add_cors_headers(response, origin)
            return response
        
        # Process request
        response = await call_next(request)
        
        # Add CORS headers
        self._add_cors_headers(response, origin)
        
        return response
    
    def _add_cors_headers(self, response: Response, origin: Optional[str]) -> None:
        """Add CORS headers to response"""
        if origin and (origin in self.allow_origins or "*" in self.allow_origins):
            response.headers["Access-Control-Allow-Origin"] = origin
        elif "*" in self.allow_origins:
            response.headers["Access-Control-Allow-Origin"] = "*"
        
        response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
        response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)
        response.headers["Access-Control-Allow-Credentials"] = str(self.allow_credentials).lower()
        response.headers["Access-Control-Max-Age"] = str(self.max_age)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""
    
    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        burst_requests: int = 100,
        window_size: int = 60
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_requests = burst_requests
        self.window_size = window_size
        self.requests: Dict[str, List[float]] = {}
        self.logger = get_logger("rate_limit")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check rate limit"""
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Clean old requests
        if client_ip in self.requests:
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if current_time - req_time < self.window_size
            ]
        else:
            self.requests[client_ip] = []
        
        # Check rate limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            self.logger.warning(f"Rate limit exceeded for {client_ip}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "RATE_LIMIT_ERROR",
                    "message": "Rate limit exceeded",
                    "details": {
                        "limit": self.requests_per_minute,
                        "window": self.window_size
                    }
                }
            )
        
        # Add current request
        self.requests[client_ip].append(current_time)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            self.requests_per_minute - len(self.requests[client_ip])
        )
        response.headers["X-RateLimit-Reset"] = str(
            int(current_time + self.window_size)
        )
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Security headers middleware"""
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = get_logger("security_headers")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers"""
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response


class MiddlewareManager:
    """Middleware manager for managing middleware lifecycle"""
    
    def __init__(self):
        self.chain = MiddlewareChain()
        self.logger = get_logger("middleware_manager")
    
    def add_middleware(self, middleware: BaseHTTPMiddleware) -> None:
        """Add middleware to chain"""
        self.chain.add_middleware(middleware)
    
    def remove_middleware(self, middleware_class: type) -> None:
        """Remove middleware from chain"""
        self.chain.remove_middleware(middleware_class)
    
    def setup_default_middlewares(self, app: Any) -> None:
        """Setup default middlewares"""
        # Add middlewares in order
        self.add_middleware(SecurityHeadersMiddleware(app))
        self.add_middleware(CORSMiddleware(app))
        self.add_middleware(RateLimitMiddleware(app))
        self.add_middleware(RequestLoggingMiddleware(app))
        self.add_middleware(ErrorHandlingMiddleware(app))
        
        self.logger.info("Setup default middlewares")
    
    def apply_middlewares(self, app: Any) -> None:
        """Apply all middlewares to app"""
        for middleware in self.chain.get_middlewares():
            app.add_middleware(middleware.__class__)
        
        self.logger.info(f"Applied {len(self.chain.get_middlewares())} middlewares")


# Global middleware manager
middleware_manager = MiddlewareManager()


def setup_middlewares(app: Any) -> None:
    """Setup all middlewares"""
    middleware_manager.setup_default_middlewares(app)
    middleware_manager.apply_middlewares(app)


def add_middleware(middleware: BaseHTTPMiddleware) -> None:
    """Add custom middleware"""
    middleware_manager.add_middleware(middleware)


def remove_middleware(middleware_class: type) -> None:
    """Remove middleware"""
    middleware_manager.remove_middleware(middleware_class)