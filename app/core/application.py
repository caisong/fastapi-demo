"""
Application factory and lifecycle management
"""
from typing import Any, Optional, Dict, List
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager

from .config import settings
from .logging import init_logging, get_logger
from .middleware_system import setup_middlewares
from .plugins import initialize_plugins, cleanup_plugins
from .dependency_injection import init_dependency_injection, cleanup_dependency_injection
from .exceptions import BaseAPIException, create_http_exception
from .response import create_error_response
from .constants import APP_METADATA, API_CONFIG

logger = get_logger(__name__)


class ApplicationManager:
    """Application manager for lifecycle management"""
    
    def __init__(self):
        self.app: Optional[FastAPI] = None
        self.logger = get_logger("application_manager")
    
    def create_app(
        self,
        title: str = None,
        description: str = None,
        version: str = None,
        debug: bool = None,
        **kwargs
    ) -> FastAPI:
        """Create FastAPI application with all configurations"""
        
        # Initialize logging first
        init_logging()
        
        # Use provided values or fallback to settings
        app_title = title or settings.API_TITLE
        app_description = description or settings.API_DESCRIPTION
        app_version = version or settings.API_VERSION
        app_debug = debug if debug is not None else settings.DEBUG
        
        # Create FastAPI app
        self.app = FastAPI(
            title=app_title,
            description=app_description,
            version=app_version,
            debug=app_debug,
            docs_url=settings.API_DOCS_URL if not app_debug else None,
            redoc_url=settings.API_REDOC_URL if not app_debug else None,
            openapi_url="/openapi.json" if not app_debug else None,
            **kwargs
        )
        
        # Setup application lifecycle
        self._setup_lifecycle()
        
        # Setup middleware
        self._setup_middleware()
        
        # Setup exception handlers
        self._setup_exception_handlers()
        
        # Setup plugins
        if settings.ENABLE_PLUGINS:
            self._setup_plugins()
        
        # Setup dependency injection
        if settings.ENABLE_DI:
            self._setup_dependency_injection()
        
        # Setup routes
        self._setup_routes()
        
        self.logger.info(f"Application created: {app_title} v{app_version}")
        return self.app
    
    def _setup_lifecycle(self) -> None:
        """Setup application lifecycle events"""
        
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            """Application lifespan manager"""
            # Startup
            self.logger.info("Starting application...")
            yield
            # Shutdown
            self.logger.info("Shutting down application...")
            await self._cleanup()
        
        self.app.router.lifespan_context = lifespan
    
    def _setup_middleware(self) -> None:
        """Setup middleware"""
        if settings.ENABLE_CORS:
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=settings.cors_origins_list,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
        
        # TrustedHostMiddleware is handled in main.py
        # if settings.ENABLE_SECURITY_HEADERS:
        #     # Add testserver for testing
        #     allowed_hosts = ["*"] if settings.DEBUG else settings.ALLOWED_HOSTS + ["testserver"]
        #     self.app.add_middleware(
        #         TrustedHostMiddleware,
        #         allowed_hosts=allowed_hosts
        #     )
        
        # Setup custom middlewares
        setup_middlewares(self.app)
    
    def _setup_exception_handlers(self) -> None:
        """Setup exception handlers"""
        
        @self.app.exception_handler(BaseAPIException)
        async def api_exception_handler(request: Request, exc: BaseAPIException) -> JSONResponse:
            """Handle custom API exceptions"""
            return create_error_response(
                message=exc.message,
                error_code=exc.error_code,
                details=exc.details,
                status_code=exc.status_code
            )
        
        @self.app.exception_handler(Exception)
        async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
            """Handle general exceptions"""
            self.logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
            return create_error_response(
                message="Internal server error",
                error_code="INTERNAL_ERROR",
                details={"original_error": type(exc).__name__},
                status_code=500
            )
    
    def _setup_plugins(self) -> None:
        """Setup plugins"""
        try:
            initialize_plugins()
            self.logger.info("Plugins initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize plugins: {str(e)}")
    
    def _setup_dependency_injection(self) -> None:
        """Setup dependency injection"""
        try:
            init_dependency_injection()
            self.logger.info("Dependency injection initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize dependency injection: {str(e)}")
    
    def _setup_routes(self) -> None:
        """Setup application routes"""
        # Health check endpoint
        @self.app.get("/health", tags=["health"])
        async def health_check() -> Dict[str, Any]:
            """Health check endpoint"""
            return {
                "status": "healthy",
                "service": settings.PROJECT_NAME,
                "version": settings.API_VERSION,
                "environment": settings.ENVIRONMENT
            }
        
        # Root endpoint
        @self.app.get("/", tags=["root"])
        async def root() -> Dict[str, Any]:
            """Root endpoint"""
            return {
                "message": f"Welcome to {settings.PROJECT_NAME}",
                "version": settings.API_VERSION,
                "docs": settings.API_DOCS_URL,
                "health": "/health"
            }
        
        # Include API routes
        from app.api.v1.api import api_router
        self.app.include_router(api_router, prefix=settings.API_V1_STR)
        
        self.logger.info("Routes configured")
    
    async def _cleanup(self) -> None:
        """Cleanup application resources"""
        try:
            if settings.ENABLE_PLUGINS:
                cleanup_plugins()
            
            if settings.ENABLE_DI:
                cleanup_dependency_injection()
            
            self.logger.info("Application cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
    
    def run(
        self,
        host: str = "0.0.0.0",
        port: int = 8000,
        reload: bool = None,
        workers: int = None,
        **kwargs
    ) -> None:
        """Run the application"""
        if not self.app:
            raise ValueError("Application not created. Call create_app() first.")
        
        # Use provided values or fallback to settings
        app_reload = reload if reload is not None else settings.RELOAD
        app_workers = workers if workers is not None else settings.WORKERS
        
        self.logger.info(f"Starting server on {host}:{port}")
        self.logger.info(f"Environment: {settings.ENVIRONMENT}")
        self.logger.info(f"Debug mode: {settings.DEBUG}")
        self.logger.info(f"Reload: {app_reload}")
        self.logger.info(f"Workers: {app_workers}")
        
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=app_reload,
            workers=app_workers if not app_reload else 1,
            log_level=settings.LOG_LEVEL.lower(),
            **kwargs
        )


# Global application manager
app_manager = ApplicationManager()


def create_app(**kwargs) -> FastAPI:
    """Create FastAPI application"""
    return app_manager.create_app(**kwargs)


def get_app() -> Optional[FastAPI]:
    """Get current application instance"""
    return app_manager.app


def run_app(**kwargs) -> None:
    """Run the application"""
    app_manager.run(**kwargs)


# Application instance
app = create_app()