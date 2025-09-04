#!/usr/bin/env python3
"""
Create sample data for testing admin interface
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import SessionLocal
from app.models.user import User
from app.models.item import Item
from app.core.security import get_password_hash


async def create_sample_data():
    """Create sample users and items"""
    async with SessionLocal() as db:
        try:
            # Check if sample data already exists
            result = await db.execute(select(User).filter(User.email == "user1@example.com"))
            if result.scalar_one_or_none():
                print("Sample data already exists, skipping...")
                return
            
            # Create sample users
            users_data = [
                {
                    "email": "user1@example.com",
                    "hashed_password": get_password_hash("password123"),
                    "first_name": "John",
                    "last_name": "Doe",
                    "is_active": True,
                    "is_superuser": False,
                },
                {
                    "email": "user2@example.com", 
                    "hashed_password": get_password_hash("password123"),
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "is_active": True,
                    "is_superuser": False,
                },
                {
                    "email": "inactive@example.com",
                    "hashed_password": get_password_hash("password123"),
                    "first_name": "Inactive",
                    "last_name": "User",
                    "is_active": False,
                    "is_superuser": False,
                },
            ]
            
            sample_users = []
            for user_data in users_data:
                user = User(**user_data)
                db.add(user)
                sample_users.append(user)
            
            await db.commit()
            
            # Refresh to get IDs
            for user in sample_users:
                await db.refresh(user)
            
            # Create sample items
            items_data = [
                {
                    "title": "Sample Item 1",
                    "description": "This is a sample item for testing the admin interface",
                    "owner_id": sample_users[0].id,
                    "is_active": True,
                },
                {
                    "title": "Another Item",
                    "description": "Another sample item with different content",
                    "owner_id": sample_users[1].id,
                    "is_active": True,
                },
                {
                    "title": "Inactive Item",
                    "description": "This item is inactive",
                    "owner_id": sample_users[0].id,
                    "is_active": False,
                },
                {
                    "title": "Long Title Item for Testing Search Functionality",
                    "description": "This item has a very long title to test the search and display functionality in the admin interface. It should wrap properly and be searchable.",
                    "owner_id": sample_users[1].id,
                    "is_active": True,
                },
            ]
            
            for item_data in items_data:
                item = Item(**item_data)
                db.add(item)
            
            await db.commit()
            
            print("Sample data created successfully!")
            print(f"Created {len(users_data)} users and {len(items_data)} items")
            print("\nSample users:")
            for user_data in users_data:
                print(f"  - {user_data['first_name']} {user_data['last_name']} ({user_data['email']})")
            
        except Exception as e:
            print(f"Error creating sample data: {e}")
            await db.rollback()


if __name__ == "__main__":
    print("Creating sample data...")
    asyncio.run(create_sample_data())
    print("Sample data creation complete.")