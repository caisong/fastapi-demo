"""
Enhanced testing framework
"""
import asyncio
import pytest
from typing import Any, Dict, Optional, Callable, Generator
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient

from .config import settings
from .database import get_db, Base
from .application import create_app
from .logging import setup_logging, LogLevel, Environment


class TestConfig:
    """Test configuration"""
    
    # Database
    TEST_DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"
    
    # API
    API_BASE_URL: str = "http://testserver"
    
    # Authentication
    TEST_USER_EMAIL: str = "test@example.com"
    TEST_USER_PASSWORD: str = "TestPassword123"
    TEST_ADMIN_EMAIL: str = "admin@example.com"
    TEST_ADMIN_PASSWORD: str = "AdminPassword123"
    
    # Test data
    TEST_DATA: Dict[str, Any] = {
        "users": [],
        "items": [],
        "tasks": []
    }


class TestDatabase:
    """Test database manager"""
    
    def __init__(self, database_url: str = TestConfig.TEST_DATABASE_URL):
        self.database_url = database_url
        self.engine = create_async_engine(
            database_url,
            echo=False,
            future=True
        )
        self.async_session = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def create_tables(self) -> None:
        """Create test tables"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def drop_tables(self) -> None:
        """Drop test tables"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    
    async def get_session(self) -> AsyncSession:
        """Get test database session"""
        return self.async_session()
    
    async def cleanup(self) -> None:
        """Cleanup test database"""
        await self.drop_tables()
        await self.engine.dispose()


class TestClientManager:
    """Test client manager"""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.client: Optional[TestClient] = None
        self.async_client: Optional[AsyncClient] = None
    
    def get_sync_client(self) -> TestClient:
        """Get synchronous test client"""
        if not self.client:
            self.client = TestClient(self.app)
        return self.client
    
    async def get_async_client(self) -> AsyncClient:
        """Get asynchronous test client"""
        if not self.async_client:
            self.async_client = AsyncClient(app=self.app, base_url=TestConfig.API_BASE_URL)
        return self.async_client
    
    async def cleanup(self) -> None:
        """Cleanup test clients"""
        if self.async_client:
            await self.async_client.aclose()


class TestDataManager:
    """Test data manager"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.data: Dict[str, Any] = {}
    
    async def create_test_user(self, email: str = TestConfig.TEST_USER_EMAIL, **kwargs) -> Dict[str, Any]:
        """Create test user"""
        from app.models.user import User
        from app.core.security import get_password_hash
        
        user_data = {
            "email": email,
            "hashed_password": get_password_hash(TestConfig.TEST_USER_PASSWORD),
            "is_active": True,
            "is_superuser": False,
            **kwargs
        }
        
        user = User(**user_data)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        self.data["user"] = user
        return user
    
    async def create_test_admin(self, email: str = TestConfig.TEST_ADMIN_EMAIL, **kwargs) -> Dict[str, Any]:
        """Create test admin user"""
        return await self.create_test_user(
            email=email,
            is_superuser=True,
            **kwargs
        )
    
    async def create_test_item(self, owner_id: int, **kwargs) -> Dict[str, Any]:
        """Create test item"""
        from app.models.item import Item
        
        item_data = {
            "title": "Test Item",
            "description": "Test Description",
            "owner_id": owner_id,
            **kwargs
        }
        
        item = Item(**item_data)
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        
        self.data["item"] = item
        return item
    
    async def cleanup(self) -> None:
        """Cleanup test data"""
        # Delete in reverse order to handle foreign key constraints
        for model_name in ["item", "user"]:
            if model_name in self.data:
                await self.db.delete(self.data[model_name])
                await self.db.commit()


class TestFixtureManager:
    """Test fixture manager"""
    
    def __init__(self):
        self.database: Optional[TestDatabase] = None
        self.app: Optional[FastAPI] = None
        self.client_manager: Optional[TestClientManager] = None
        self.data_manager: Optional[TestDataManager] = None
    
    async def setup(self) -> None:
        """Setup test environment"""
        # Setup logging
        setup_logging(
            level=LogLevel.DEBUG,
            environment=Environment.TESTING,
            json_format=False
        )
        
        # Setup database
        self.database = TestDatabase()
        await self.database.create_tables()
        
        # Setup app
        self.app = create_app()
        
        # Override database dependency
        async def override_get_db():
            async with self.database.async_session() as session:
                yield session
        
        self.app.dependency_overrides[get_db] = override_get_db
        
        # Setup client manager
        self.client_manager = TestClientManager(self.app)
    
    async def cleanup(self) -> None:
        """Cleanup test environment"""
        if self.data_manager:
            await self.data_manager.cleanup()
        
        if self.client_manager:
            await self.client_manager.cleanup()
        
        if self.database:
            await self.database.cleanup()
    
    def get_sync_client(self) -> TestClient:
        """Get synchronous test client"""
        if not self.client_manager:
            raise RuntimeError("Test environment not setup")
        return self.client_manager.get_sync_client()
    
    async def get_async_client(self) -> AsyncClient:
        """Get asynchronous test client"""
        if not self.client_manager:
            raise RuntimeError("Test environment not setup")
        return await self.client_manager.get_async_client()
    
    async def get_data_manager(self) -> TestDataManager:
        """Get test data manager"""
        if not self.database:
            raise RuntimeError("Test environment not setup")
        
        if not self.data_manager:
            session = await self.database.get_session()
            self.data_manager = TestDataManager(session)
        
        return self.data_manager


# Global test fixture manager
test_fixture_manager = TestFixtureManager()


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_setup():
    """Setup test environment"""
    await test_fixture_manager.setup()
    yield test_fixture_manager
    await test_fixture_manager.cleanup()


@pytest.fixture
async def test_db(test_setup):
    """Get test database session"""
    return await test_setup.database.get_session()


@pytest.fixture
def test_client(test_setup):
    """Get synchronous test client"""
    return test_setup.get_sync_client()


@pytest.fixture
async def async_test_client(test_setup):
    """Get asynchronous test client"""
    return await test_setup.get_async_client()


@pytest.fixture
async def test_data_manager(test_setup):
    """Get test data manager"""
    return await test_setup.get_data_manager()


@pytest.fixture
async def test_user(test_data_manager):
    """Create test user"""
    return await test_data_manager.create_test_user()


@pytest.fixture
async def test_admin(test_data_manager):
    """Create test admin user"""
    return await test_data_manager.create_test_admin()


@pytest.fixture
async def test_item(test_data_manager, test_user):
    """Create test item"""
    return await test_data_manager.create_test_item(owner_id=test_user.id)


# Test utilities
class TestUtils:
    """Test utilities"""
    
    @staticmethod
    def create_auth_headers(token: str) -> Dict[str, str]:
        """Create authentication headers"""
        return {"Authorization": f"Bearer {token}"}
    
    @staticmethod
    def assert_response_status(response, expected_status: int) -> None:
        """Assert response status"""
        assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}"
    
    @staticmethod
    def assert_response_json(response, expected_keys: list) -> None:
        """Assert response JSON structure"""
        data = response.json()
        for key in expected_keys:
            assert key in data, f"Expected key '{key}' not found in response"
    
    @staticmethod
    def assert_pagination(response) -> None:
        """Assert pagination structure"""
        data = response.json()
        assert "pagination" in data
        pagination = data["pagination"]
        assert "page" in pagination
        assert "page_size" in pagination
        assert "total" in pagination
        assert "total_pages" in pagination


# Test decorators
def async_test(func: Callable) -> Callable:
    """Decorator for async test functions"""
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))
    return wrapper


def test_with_data(*data_fixtures):
    """Decorator for tests that need specific data"""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Setup data fixtures
            for fixture in data_fixtures:
                # This would be implemented based on specific needs
                pass
            return func(*args, **kwargs)
        return wrapper
    return decorator


def test_with_auth(required_permissions: list = None):
    """Decorator for tests that require authentication"""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Setup authentication
            # This would be implemented based on specific needs
            return func(*args, **kwargs)
        return wrapper
    return decorator