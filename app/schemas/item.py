"""
Item schemas (Pydantic models)
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# Shared properties
class ItemBase(BaseModel):
    """Base item schema"""
    title: Optional[str] = None
    description: Optional[str] = None


# Properties to receive on item creation
class ItemCreate(ItemBase):
    """Schema for creating an item"""
    title: str


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