"""
Base service class for business logic
"""
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from fastapi import HTTPException

from app.db.crud import CRUDBase

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base service class that wraps CRUD operations with business logic"""
    
    def __init__(self, crud: CRUDBase[ModelType, CreateSchemaType, UpdateSchemaType]):
        self.crud = crud
    
    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """Get a single record by ID with business logic validation"""
        obj = await self.crud.get(db, id=id)
        if not obj:
            raise HTTPException(status_code=404, detail="Item not found")
        return obj
    
    async def get_multi(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[ModelType]:
        """Get multiple records with pagination and business logic"""
        if limit > 100:
            limit = 100  # Enforce maximum limit
        return await self.crud.get_multi(db, skip=skip, limit=limit)
    
    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record with business logic validation"""
        # Subclasses can override this to add validation
        return await self.crud.create(db, obj_in=obj_in)
    
    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """Update an existing record with business logic validation"""
        # Subclasses can override this to add validation
        return await self.crud.update(db, db_obj=db_obj, obj_in=obj_in)
    
    async def remove(self, db: AsyncSession, *, id: int) -> ModelType:
        """Delete a record with business logic validation"""
        obj = await self.crud.get(db, id=id)
        if not obj:
            raise HTTPException(status_code=404, detail="Item not found")
        return await self.crud.remove(db, id=id)