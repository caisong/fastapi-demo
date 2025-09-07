"""
Test configuration
"""
import pytest
import asyncio
import os
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

# Set test environment before importing anything
# Set test environment before importing anything
os.environ["ENVIRONMENT"] = "testing"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["TEST_DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["ENABLE_METRICS"] = "false"
os.environ["ENABLE_SECURITY_HEADERS"] = "false"
os.environ["ENABLE_RATE_LIMIT"] = "false"
os.environ["RATE_LIMIT_PER_MINUTE"] = "100000"
os.environ["RATE_LIMIT_REQUESTS"] = "100000"
os.environ["RATE_LIMIT_WINDOW"] = "3600"
os.environ["ENABLE_CORS"] = "false"
os.environ["ASYNC_DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["POSTGRES_SERVER"] = "sqlite"
os.environ["POSTGRES_DB"] = "test.db"

from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.database import Base, get_db
from app.core.task_queue import task_queue
from app.services.prometheus import prometheus_service
from main import app

# Import test utilities
from tests.utils import APITestHelper, MockServices, DatabaseTestHelper, AsyncTestHelper

# Test database URLs
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
ASYNC_SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Sync engine for initial setup
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Async engine for async tests
async_engine = create_async_engine(
    ASYNC_SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncTestingSessionLocal = sessionmaker(
    class_=AsyncSession, 
    autocommit=False, 
    autoflush=False, 
    bind=async_engine
)


async def override_get_db():
    """Override async database dependency for testing"""
    async with AsyncTestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for the test session"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create test client with database setup"""
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create async test client"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def db() -> Generator[TestingSessionLocal, None, None]:
    """Create test database session"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
async def async_db() -> AsyncGenerator[AsyncSession, None]:
    """Create async test database session"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncTestingSessionLocal() as session:
        yield session
    
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def mock_task_queue(mocker):
    """Mock task queue for testing"""
    mock_queue = AsyncMock()
    
    def mock_enqueue_task(function_name, *args, **kwargs):
        return f"mock-job-{function_name}"
    
    def mock_get_job_status(job_id):
        return {
            "status": "completed",
            "job_id": job_id,  # Use the actual job_id passed in
            "result": "mock-result"
        }
    
    mock_queue.enqueue_task.side_effect = mock_enqueue_task
    mock_queue.get_job_status.side_effect = mock_get_job_status
    
    mocker.patch.object(task_queue, "enqueue_task", side_effect=mock_enqueue_task)
    mocker.patch.object(task_queue, "get_job_status", side_effect=mock_get_job_status)
    return mock_queue


@pytest.fixture
def mock_prometheus_service(mocker):
    """Mock Prometheus service for testing"""
    mock_service = AsyncMock()
    mock_service.health_check.return_value = {"status": "healthy"}
    mock_service.query_instant.return_value = {
        "status": "success",
        "result": [{"metric": {"__name__": "test_metric"}, "value": [1640995200, "42"]}]
    }
    mocker.patch.object(prometheus_service, "health_check", side_effect=mock_service.health_check)
    mocker.patch.object(prometheus_service, "query_instant", side_effect=mock_service.query_instant)
    return mock_service


@pytest.fixture
def test_user_data():
    """Test user data for creating users"""
    return {
        "email": "test@example.com",
        "password": "testpassword123",
        "first_name": "Test",
        "last_name": "User",
        "is_active": True,
        "is_superuser": False
    }


@pytest.fixture
def test_superuser_data():
    """Test superuser data"""
    return {
        "email": "admin@example.com", 
        "password": "adminpassword123",
        "first_name": "Admin",
        "last_name": "User",
        "is_active": True,
        "is_superuser": True
    }


@pytest.fixture
def test_item_data():
    """Test item data"""
    return {
        "title": "Test Item",
        "description": "A test item for API testing"
    }


@pytest.fixture
def mock_email_service(mocker):
    """Mock email service for testing"""
    mock_service = MagicMock()
    mock_service.send_welcome_email.return_value = "email-sent"
    mock_service.send_password_reset.return_value = "reset-sent"
    
    # Mock the task delays
    mocker.patch('app.services.user.send_welcome_email_task.delay', return_value="mock-job-id")
    mocker.patch('app.services.user.send_password_reset_task.delay', return_value="mock-job-id")
    
    return mock_service


@pytest.fixture
def mock_redis_service(mocker):
    """Mock Redis service for testing"""
    mock_redis = AsyncMock()
    mock_redis.get.return_value = '{"cached": "data"}'
    mock_redis.set.return_value = True
    mock_redis.delete.return_value = 1
    mock_redis.exists.return_value = True
    
    mocker.patch('app.core.cache.redis_client', mock_redis)
    return mock_redis


@pytest.fixture
def mock_all_services(mock_task_queue, mock_prometheus_service, mock_email_service, mock_redis_service):
    """Mock all external services for comprehensive testing"""
    return {
        "task_queue": mock_task_queue,
        "prometheus": mock_prometheus_service,
        "email": mock_email_service,
        "redis": mock_redis_service
    }


@pytest.fixture(scope="session")
def test_settings_fixture():
    """Test settings override"""
    # Settings are already configured via environment variables
    # This fixture is kept for compatibility but doesn't need to do anything
    yield {}


@pytest.fixture(autouse=True)
def override_settings(test_settings_fixture):
    """Automatically override settings for all tests"""
    pass


@pytest.fixture
def api_helper(client: TestClient, db) -> APITestHelper:
    """Fixture for API test helper"""
    return APITestHelper(client, db)


@pytest.fixture
def mock_services() -> MockServices:
    """Fixture for mock services"""
    return MockServices()


@pytest.fixture
def db_helper(db) -> DatabaseTestHelper:
    """Fixture for database test helper"""
    return DatabaseTestHelper(db)


@pytest.fixture
def async_helper() -> AsyncTestHelper:
    """Fixture for async test helper"""
    return AsyncTestHelper()