"""
FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.sessions import SessionMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import settings
from app.core.application import create_app, run_app
from app.core.middleware import add_middleware
from app.admin.admin import setup_admin
from app.core.task_queue import task_queue

# Create FastAPI app using the application factory
app = create_app()

# Add session middleware for admin authentication
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    max_age=3600  # 1 hour
)

# Set up CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add trusted host middleware - this needs to be added after create_app()
# but before other middlewares to ensure proper order
if settings.ALLOWED_HOSTS and settings.ENVIRONMENT != "testing":
    allowed_hosts = settings.ALLOWED_HOSTS.copy()
    
    # Remove any existing TrustedHostMiddleware first
    app.user_middleware = [m for m in app.user_middleware if m.cls != TrustedHostMiddleware]
    
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=allowed_hosts,
    )
elif settings.ENVIRONMENT == "testing":
    # In testing environment, remove TrustedHostMiddleware completely
    app.user_middleware = [m for m in app.user_middleware if m.cls != TrustedHostMiddleware]

# Add custom middleware
# Set enable_auth_middleware=True to use middleware-based authentication
# instead of Depends (Depends is recommended for most use cases)
add_middleware(app, enable_auth_middleware=False)

# Setup Prometheus metrics
if settings.ENABLE_METRICS:
    instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_respect_env_var=True,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/metrics"],  # Don't monitor the metrics endpoint itself
        env_var_name="ENABLE_METRICS",
        inprogress_name="inprogress",
        inprogress_labels=True,
    )
    instrumentator.instrument(app).expose(app)

# Setup admin interface
setup_admin(app)


@app.on_event("startup")
async def startup_event():
    """Initialize task queue on startup"""
    await task_queue.startup()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup task queue on shutdown"""
    await task_queue.shutdown()


if __name__ == "__main__":
    # Run the application
    run_app()