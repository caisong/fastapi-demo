"""
Authentication schemas
"""
from typing import Optional

from pydantic import BaseModel


class Token(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str


class TokenPayload(BaseModel):
    """Token payload schema"""
    sub: Optional[str] = None


class LoginRequest(BaseModel):
    """Login request schema"""
    email: str
    password: str


class LoginResponse(BaseModel):
    """Login response schema"""
    access_token: str
    refresh_token: str
    token_type: str
    user: dict  # User information


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""
    refresh_token: str