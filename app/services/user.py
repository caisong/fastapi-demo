"""
User service with business logic
"""
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.services.base import BaseService
from app.db.crud import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password
from app.tasks.helpers import send_welcome_email_task


class UserService(BaseService[User, UserCreate, UserUpdate]):
    """User service with business logic"""
    
    def __init__(self):
        super().__init__(CRUDBase(User))
    
    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        """Create a new user with business logic validation"""
        # Check if user already exists
        result = await db.execute(select(User).filter(User.email == obj_in.email))
        user = result.scalar_one_or_none()
        if user:
            raise HTTPException(
                status_code=400,
                detail="The user with this email already exists in the system.",
            )
        
        # Hash password
        user_data = obj_in.dict()
        user_data["hashed_password"] = get_password_hash(user_data.pop("password"))
        
        # Create user
        user = await self.crud.create(db, obj_in=user_data)
        
        # Send welcome email asynchronously
        await send_welcome_email_task.delay(user.email, user.first_name or "User")
        
        return user
    
    async def authenticate(self, db: AsyncSession, *, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        result = await db.execute(select(User).filter(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    async def update_password(
        self, 
        db: AsyncSession, 
        *, 
        user: User, 
        current_password: str, 
        new_password: str
    ) -> User:
        """Update user password with current password validation"""
        if not verify_password(current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password"
            )
        
        hashed_password = get_password_hash(new_password)
        return await self.crud.update(
            db, db_obj=user, obj_in={"hashed_password": hashed_password}
        )
    
    async def deactivate(self, db: AsyncSession, *, user_id: int) -> User:
        """Deactivate user account"""
        user = await self.get(db, id=user_id)
        return await self.crud.update(db, db_obj=user, obj_in={"is_active": False})
    
    async def activate(self, db: AsyncSession, *, user_id: int) -> User:
        """Activate user account"""
        user = await self.get(db, id=user_id)
        return await self.crud.update(db, db_obj=user, obj_in={"is_active": True})
    
    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        """Get user by email"""
        result = await db.execute(select(User).filter(User.email == email))
        return result.scalar_one_or_none()


# Create instance
user_service = UserService()