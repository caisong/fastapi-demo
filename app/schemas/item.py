"""
Item schemas (Pydantic models)
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


# Shared properties
class ItemBase(BaseModel):
    """Base item schema"""
    title: Optional[str] = None
    description: Optional[str] = None


# Properties to receive on item creation
class ItemCreate(ItemBase):
    """Schema for creating an item"""
    title: str
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        """Validate title is not empty"""
        if not v or not v.strip():
            raise ValueError('Title cannot be empty')
        if len(v) > 100:
            raise ValueError('Title cannot exceed 100 characters')
        return v.strip()
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        """Validate description length"""
        if v and len(v) > 1000:
            raise ValueError('Description cannot exceed 1000 characters')
        return v


# Properties to receive on item update
class ItemUpdate(ItemBase):
    """Schema for updating an item"""
    pass


# Properties shared by models stored in DB
class ItemInDBBase(ItemBase):
    """Base schema for items in database"""
    id: int
    title: str
    owner_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Properties to return to client
class Item(ItemInDBBase):
    """Schema for returning item data"""
    pass


# Properties properties stored in DB
class ItemInDB(ItemInDBBase):
    """Schema for item data in database"""
    pass