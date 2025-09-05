"""
Custom exceptions for the application
"""
from typing import Any, Dict, Optional
from fastapi import HTTPException, status
from .constants import ERROR_CODES


class BaseAPIException(Exception):
    """Base exception for all API exceptions"""
    
    def __init__(
        self,
        message: str,
        error_code: str = ERROR_CODES["INTERNAL_ERROR"],
        details: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary"""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details,
            "status_code": self.status_code
        }


class ValidationError(BaseAPIException):
    """Validation error exception"""
    
    def __init__(
        self,
        message: str = "Validation error",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=ERROR_CODES["VALIDATION_ERROR"],
            details=details,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


class AuthenticationError(BaseAPIException):
    """Authentication error exception"""
    
    def __init__(
        self,
        message: str = "Authentication required",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=ERROR_CODES["AUTHENTICATION_ERROR"],
            details=details,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class AuthorizationError(BaseAPIException):
    """Authorization error exception"""
    
    def __init__(
        self,
        message: str = "Access denied",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=ERROR_CODES["AUTHORIZATION_ERROR"],
            details=details,
            status_code=status.HTTP_403_FORBIDDEN
        )


class NotFoundError(BaseAPIException):
    """Not found error exception"""
    
    def __init__(
        self,
        message: str = "Resource not found",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=ERROR_CODES["NOT_FOUND_ERROR"],
            details=details,
            status_code=status.HTTP_404_NOT_FOUND
        )


class ConflictError(BaseAPIException):
    """Conflict error exception"""
    
    def __init__(
        self,
        message: str = "Resource conflict",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=ERROR_CODES["CONFLICT_ERROR"],
            details=details,
            status_code=status.HTTP_409_CONFLICT
        )


class ExternalServiceError(BaseAPIException):
    """External service error exception"""
    
    def __init__(
        self,
        message: str = "External service error",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=ERROR_CODES["EXTERNAL_SERVICE_ERROR"],
            details=details,
            status_code=status.HTTP_502_BAD_GATEWAY
        )


class RateLimitError(BaseAPIException):
    """Rate limit error exception"""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=ERROR_CODES["RATE_LIMIT_ERROR"],
            details=details,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )


class TaskError(BaseAPIException):
    """Task error exception"""
    
    def __init__(
        self,
        message: str = "Task execution error",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=ERROR_CODES["TASK_ERROR"],
            details=details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class DatabaseError(BaseAPIException):
    """Database error exception"""
    
    def __init__(
        self,
        message: str = "Database error",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=ERROR_CODES["DATABASE_ERROR"],
            details=details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def create_http_exception(exception: BaseAPIException) -> HTTPException:
    """Convert custom exception to HTTPException"""
    return HTTPException(
        status_code=exception.status_code,
        detail=exception.to_dict()
    )


def handle_exception(exception: Exception) -> BaseAPIException:
    """Handle and convert generic exceptions to custom exceptions"""
    if isinstance(exception, BaseAPIException):
        return exception
    
    # Convert common exceptions
    if isinstance(exception, ValueError):
        return ValidationError(
            message=str(exception),
            details={"original_error": type(exception).__name__}
        )
    
    if isinstance(exception, KeyError):
        return ValidationError(
            message=f"Missing required field: {exception}",
            details={"original_error": type(exception).__name__}
        )
    
    if isinstance(exception, PermissionError):
        return AuthorizationError(
            message="Permission denied",
            details={"original_error": type(exception).__name__}
        )
    
    if isinstance(exception, FileNotFoundError):
        return NotFoundError(
            message="Resource not found",
            details={"original_error": type(exception).__name__}
        )
    
    # Default to internal error
    return BaseAPIException(
        message="Internal server error",
        details={
            "original_error": type(exception).__name__,
            "original_message": str(exception)
        }
    )