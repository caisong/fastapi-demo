"""
Item service with business logic
"""
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.services.base import BaseService
from app.db.crud import CRUDBase
from app.models.item import Item
from app.models.user import User
from app.schemas.item import ItemCreate, ItemUpdate
from app.tasks.helpers import process_item_task, send_item_notification_task


class ItemService(BaseService[Item, ItemCreate, ItemUpdate]):
    """Item service with business logic"""
    
    def __init__(self):
        super().__init__(CRUDBase(Item))
    
    async def create(self, db: AsyncSession, *, obj_in: ItemCreate, owner_id: int) -> Item:
        """Create a new item with business logic validation"""
        # Validate owner exists
        result = await db.execute(select(User).filter(User.id == owner_id))
        owner = result.scalar_one_or_none()
        if not owner:
            raise HTTPException(
                status_code=404,
                detail="Owner not found"
            )
        
        # Create item data
        item_data = obj_in.dict()
        item_data["owner_id"] = owner_id
        
        # Create item
        item = await self.crud.create(db, obj_in=item_data)
        
        # Process item asynchronously (e.g., data validation, enrichment)
        await process_item_task.delay(item.id)
        
        # Send notification to owner
        await send_item_notification_task.delay(
            owner.email, 
            f"Item '{item.title}' created successfully",
            item.id
        )
        
        return item
    
    async def get_user_items(
        self, 
        db: AsyncSession, 
        *, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Item]:
        """Get items owned by a specific user"""
        if limit > 100:
            limit = 100
        
        result = await db.execute(
            select(Item)
            .filter(Item.owner_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def update_with_owner_check(
        self,
        db: AsyncSession,
        *,
        item_id: int,
        owner_id: int,
        obj_in: ItemUpdate
    ) -> Item:
        """Update item with owner validation"""
        item = await self.get(db, id=item_id)
        
        # Check if user owns the item
        if item.owner_id != owner_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to update this item"
            )
        
        return await self.crud.update(db, db_obj=item, obj_in=obj_in)
    
    async def delete_with_owner_check(
        self,
        db: AsyncSession,
        *,
        item_id: int,
        owner_id: int
    ) -> Item:
        """Delete item with owner validation"""
        item = await self.get(db, id=item_id)
        
        # Check if user owns the item
        if item.owner_id != owner_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to delete this item"
            )
        
        return await self.crud.remove(db, id=item_id)
    
    async def get_active_items(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Item]:
        """Get only active items"""
        if limit > 100:
            limit = 100
        
        result = await db.execute(
            select(Item)
            .filter(Item.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()


# Create instance
item_service = ItemService()