"""
Database connection and session management
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

# Create async SQLAlchemy engine with appropriate configuration
engine_kwargs = {
    "pool_pre_ping": True,
    "echo": settings.ENVIRONMENT == "development",
}

# Add PostgreSQL-specific settings only if not using SQLite
if not settings.DATABASE_URL.startswith("sqlite"):
    engine_kwargs.update({
        "pool_recycle": 300,
        "pool_size": 10,
        "max_overflow": 20,
    })
else:
    # SQLite specific settings
    engine_kwargs.update({
        "connect_args": {"check_same_thread": False},
    })

engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)

# Create async SessionLocal class
SessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Create Base class for models
Base = declarative_base()


async def get_db():
    """
    Async dependency to get database session
    """
    async with SessionLocal() as session:
        yield session