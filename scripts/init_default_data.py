#!/usr/bin/env python3
"""
Simple script to initialize default data
"""
import asyncio
from app.db.crud import init_default_data
from app.db.database import SessionLocal

async def main():
    async with SessionLocal() as db:
        await init_default_data(db)
        print("✅ Default data initialized successfully!")

if __name__ == "__main__":
    asyncio.run(main())