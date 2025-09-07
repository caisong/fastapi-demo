"""
Item endpoints
"""
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api import deps
from app.db.crud import CRUDBase
from app.db.database import get_db
from app.models.item import Item
from app.models.user import User
from app.schemas.item import Item as ItemSchema, ItemCreate, ItemUpdate

router = APIRouter()

# Create CRUD instance for Item
item_crud = CRUDBase[Item, ItemCreate, ItemUpdate](Item)


@router.get("/", response_model=List[ItemSchema])
async def read_items(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve items
    """
    if current_user.is_superuser:
        items = await item_crud.get_multi(db, skip=skip, limit=limit)
    else:
        # Regular users can only see their own items
        result = await db.execute(select(Item).filter(Item.owner_id == current_user.id).offset(skip).limit(limit))
        items = result.scalars().all()
    return items


@router.post("/", response_model=ItemSchema)
async def create_item(
    *,
    db: AsyncSession = Depends(get_db),
    item_in: ItemCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new item
    """
    item_data = item_in.model_dump()
    item_data["owner_id"] = current_user.id
    item = Item(**item_data)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    
    # Trigger background task for item processing
    try:
        from app.tasks.helpers import process_item_task
        await process_item_task.delay(item.id)
    except ImportError:
        # Task system not available, skip tasks
        pass
    
    return item


@router.put("/{id}", response_model=ItemSchema)
async def update_item(
    *,
    db: AsyncSession = Depends(get_db),
    id: int,
    item_in: ItemUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update an item
    """
    item = await item_crud.get(db=db, id=id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    item = await item_crud.update(db=db, db_obj=item, obj_in=item_in)
    return item


@router.get("/{id}", response_model=ItemSchema)
async def read_item(
    *,
    db: AsyncSession = Depends(get_db),
    id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get item by ID
    """
    item = await item_crud.get(db=db, id=id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return item


@router.delete("/{id}", response_model=ItemSchema)
async def delete_item(
    *,
    db: AsyncSession = Depends(get_db),
    id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete an item
    """
    item = await item_crud.get(db=db, id=id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    item = await item_crud.remove(db=db, id=id)
    return item