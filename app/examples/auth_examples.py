"""
Authentication Examples

This file demonstrates different ways to use authentication in FastAPI endpoints.
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_user,
    get_current_active_user,
    get_current_active_superuser,
    get_current_user_optional,
    get_current_user_from_request,
    get_current_user_from_middleware,
)
from app.db.database import get_db
from app.models.user import User

router = APIRouter()


# Example 1: Standard authentication using Depends (Recommended)
@router.get("/protected-standard")
async def protected_standard(
    current_user: User = Depends(get_current_user)
):
    """
    Standard protected endpoint using Depends.
    This is the recommended approach for most use cases.
    """
    return {
        "message": "This is a protected endpoint",
        "user_id": current_user.id,
        "user_email": current_user.email
    }


# Example 2: Active user only
@router.get("/protected-active")
async def protected_active(
    current_user: User = Depends(get_current_active_user)
):
    """
    Protected endpoint that requires an active user.
    """
    return {
        "message": "This endpoint requires an active user",
        "user_id": current_user.id,
        "is_active": current_user.is_active
    }


# Example 3: Superuser only
@router.get("/admin-only")
async def admin_only(
    current_user: User = Depends(get_current_active_superuser)
):
    """
    Protected endpoint that requires superuser privileges.
    """
    return {
        "message": "This endpoint is for superusers only",
        "user_id": current_user.id,
        "is_superuser": current_user.is_superuser
    }


# Example 4: Optional authentication
@router.get("/optional-auth")
async def optional_auth(
    current_user: User = Depends(get_current_user_optional)
):
    """
    Endpoint that works with or without authentication.
    """
    if current_user:
        return {
            "message": "Authenticated user",
            "user_id": current_user.id,
            "user_email": current_user.email
        }
    else:
        return {
            "message": "Anonymous user",
            "user_id": None
        }


# Example 5: Using request-based authentication
@router.get("/request-based")
async def request_based(
    request: Request,
    current_user: User = Depends(get_current_user_from_request)
):
    """
    Authentication using request headers directly.
    Useful for custom authentication schemes.
    """
    return {
        "message": "Authenticated via request headers",
        "user_id": current_user.id,
        "user_email": current_user.email,
        "request_path": request.url.path
    }


# Example 6: Using middleware-based authentication
@router.get("/middleware-based")
async def middleware_based(
    request: Request,
    current_user: User = Depends(get_current_user_from_middleware)
):
    """
    Authentication using middleware state.
    Requires AuthenticationMiddleware to be enabled.
    """
    return {
        "message": "Authenticated via middleware",
        "user_id": current_user.id,
        "user_email": current_user.email,
        "middleware_user_id": getattr(request.state, 'user_id', None)
    }


# Example 7: Multiple authentication levels
@router.get("/multi-level")
async def multi_level(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint that can handle different authentication levels.
    """
    # Check if user is superuser
    if current_user.is_superuser:
        return {
            "message": "Superuser access",
            "level": "admin",
            "user_id": current_user.id
        }
    # Check if user is active
    elif current_user.is_active:
        return {
            "message": "Regular user access",
            "level": "user",
            "user_id": current_user.id
        }
    else:
        return {
            "message": "Inactive user",
            "level": "inactive",
            "user_id": current_user.id
        }


# Example 8: Public endpoint with optional user info
@router.get("/public-with-user-info")
async def public_with_user_info(
    current_user: User = Depends(get_current_user_optional)
):
    """
    Public endpoint that provides additional info if user is authenticated.
    """
    response = {
        "message": "This is a public endpoint",
        "authenticated": current_user is not None
    }
    
    if current_user:
        response.update({
            "user_id": current_user.id,
            "user_email": current_user.email,
            "is_superuser": current_user.is_superuser
        })
    
    return response