"""
Standardized response handling
"""
from typing import Any, Dict, Optional, Union, List
from fastapi import status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .constants import RESPONSE_MESSAGES, HTTPStatus
from .exceptions import BaseAPIException


class APIResponse(BaseModel):
    """Standard API response model"""
    
    success: bool = True
    message: str = RESPONSE_MESSAGES["success"]
    data: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    meta: Optional[Dict[str, Any]] = None
    
    class Config:
        json_encoders = {
            # Add custom encoders here if needed
        }


class PaginatedResponse(APIResponse):
    """Paginated API response model"""
    
    data: List[Any] = []
    pagination: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Error response model"""
    
    success: bool = False
    message: str
    error: Dict[str, Any]
    meta: Optional[Dict[str, Any]] = None


def create_response(
    data: Any = None,
    message: str = RESPONSE_MESSAGES["success"],
    status_code: int = status.HTTP_200_OK,
    meta: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Create standardized API response"""
    
    response_data = APIResponse(
        success=True,
        message=message,
        data=data,
        meta=meta
    )
    
    return JSONResponse(
        status_code=status_code,
        content=response_data.dict(exclude_none=True)
    )


def create_error_response(
    message: str,
    error_code: str = "INTERNAL_ERROR",
    details: Optional[Dict[str, Any]] = None,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    meta: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Create standardized error response"""
    
    response_data = ErrorResponse(
        message=message,
        error={
            "code": error_code,
            "details": details or {}
        },
        meta=meta
    )
    
    return JSONResponse(
        status_code=status_code,
        content=response_data.dict(exclude_none=True)
    )


def create_exception_response(exception: BaseAPIException) -> JSONResponse:
    """Create response from custom exception"""
    
    response_data = ErrorResponse(
        message=exception.message,
        error={
            "code": exception.error_code,
            "details": exception.details
        }
    )
    
    return JSONResponse(
        status_code=exception.status_code,
        content=response_data.dict(exclude_none=True)
    )


def create_paginated_response(
    data: List[Any],
    page: int,
    page_size: int,
    total: int,
    message: str = RESPONSE_MESSAGES["success"],
    status_code: int = status.HTTP_200_OK,
    meta: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Create paginated response"""
    
    total_pages = (total + page_size - 1) // page_size
    
    response_data = PaginatedResponse(
        success=True,
        message=message,
        data=data,
        pagination={
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        },
        meta=meta
    )
    
    return JSONResponse(
        status_code=status_code,
        content=response_data.dict(exclude_none=True)
    )


def create_created_response(
    data: Any = None,
    message: str = RESPONSE_MESSAGES["created"],
    meta: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Create created response (201)"""
    return create_response(
        data=data,
        message=message,
        status_code=status.HTTP_201_CREATED,
        meta=meta
    )


def create_updated_response(
    data: Any = None,
    message: str = RESPONSE_MESSAGES["updated"],
    meta: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Create updated response (200)"""
    return create_response(
        data=data,
        message=message,
        status_code=status.HTTP_200_OK,
        meta=meta
    )


def create_deleted_response(
    message: str = RESPONSE_MESSAGES["deleted"],
    meta: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Create deleted response (200)"""
    return create_response(
        data=None,
        message=message,
        status_code=status.HTTP_200_OK,
        meta=meta
    )


def create_not_found_response(
    message: str = RESPONSE_MESSAGES["not_found"],
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Create not found response (404)"""
    return create_error_response(
        message=message,
        error_code="NOT_FOUND_ERROR",
        details=details,
        status_code=status.HTTP_404_NOT_FOUND
    )


def create_unauthorized_response(
    message: str = RESPONSE_MESSAGES["unauthorized"],
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Create unauthorized response (401)"""
    return create_error_response(
        message=message,
        error_code="AUTHENTICATION_ERROR",
        details=details,
        status_code=status.HTTP_401_UNAUTHORIZED
    )


def create_forbidden_response(
    message: str = RESPONSE_MESSAGES["forbidden"],
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Create forbidden response (403)"""
    return create_error_response(
        message=message,
        error_code="AUTHORIZATION_ERROR",
        details=details,
        status_code=status.HTTP_403_FORBIDDEN
    )


def create_validation_error_response(
    message: str = RESPONSE_MESSAGES["validation_error"],
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Create validation error response (422)"""
    return create_error_response(
        message=message,
        error_code="VALIDATION_ERROR",
        details=details,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )


def create_internal_error_response(
    message: str = RESPONSE_MESSAGES["internal_error"],
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Create internal error response (500)"""
    return create_error_response(
        message=message,
        error_code="INTERNAL_ERROR",
        details=details,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


# Response decorators
def success_response(message: str = RESPONSE_MESSAGES["success"]):
    """Decorator for success responses"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            return create_response(data=result, message=message)
        return wrapper
    return decorator


def created_response(message: str = RESPONSE_MESSAGES["created"]):
    """Decorator for created responses"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            return create_created_response(data=result, message=message)
        return wrapper
    return decorator


def updated_response(message: str = RESPONSE_MESSAGES["updated"]):
    """Decorator for updated responses"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            return create_updated_response(data=result, message=message)
        return wrapper
    return decorator


def deleted_response(message: str = RESPONSE_MESSAGES["deleted"]):
    """Decorator for deleted responses"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            func(*args, **kwargs)
            return create_deleted_response(message=message)
        return wrapper
    return decorator