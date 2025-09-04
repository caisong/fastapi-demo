#!/usr/bin/env python3
"""
Database initialization script
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import SessionLocal, engine
from app.db.crud import init_db
from app.db.database import Base


async def init() -> None:
    """Initialize the database"""
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Initialize with default data
    async with SessionLocal() as db:
        try:
            await init_db(db)
            print("Database initialized successfully!")
        except Exception as e:
            print(f"Error initializing database: {e}")


if __name__ == "__main__":
    print("Initializing database...")
    asyncio.run(init())
    print("Database initialization complete.")