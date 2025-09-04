"""
User schemas (Pydantic models)
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


# Shared properties
class UserBase(BaseModel):
    """Base user schema"""
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False
    first_name: Optional[str] = None
    last_name: Optional[str] = None


# Properties to receive via API on creation
class UserCreate(UserBase):
    """Schema for creating a user"""
    email: EmailStr
    password: str


# Properties to receive via API on update
class UserUpdate(UserBase):
    """Schema for updating a user"""
    password: Optional[str] = None


class UserInDBBase(UserBase):
    """Base schema for users in database"""
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Additional properties to return via API
class User(UserInDBBase):
    """Schema for returning user data"""
    pass


# Additional properties stored in DB
class UserInDB(UserInDBBase):
    """Schema for user data in database"""
    hashed_password: str