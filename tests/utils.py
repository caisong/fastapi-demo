"""
Test utilities and helper functions
"""
import pytest
import asyncio
from typing import Dict, Any, Optional, List
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.user import User
from app.models.item import Item
from tests.factories import create_user, create_superuser


class APITestHelper:
    """Helper class for API testing with common utilities"""
    
    def __init__(self, client: TestClient, db: Session):
        self.client = client
        self.db = db
        self._cached_tokens = {}
    
    def get_auth_headers(self, user: User) -> Dict[str, str]:
        """Get authentication headers for a user"""
        if user.email not in self._cached_tokens:
            access_token = create_access_token(subject=str(user.id))
            self._cached_tokens[user.email] = access_token
        
        return {"Authorization": f"Bearer {self._cached_tokens[user.email]}"}
    
    def create_test_user(self, **kwargs) -> User:
        """Create a test user with default values"""
        defaults = {
            "email": "testuser@example.com",
            "password": "TestPassword123",
            "first_name": "Test",
            "last_name": "User"
        }
        defaults.update(kwargs)
        return create_user(self.db, **defaults)
    
    def create_test_superuser(self, **kwargs) -> User:
        """Create a test superuser with default values"""
        defaults = {
            "email": "admin@example.com",
            "first_name": "Admin",
            "last_name": "User"
        }
        defaults.update(kwargs)
        return create_superuser(self.db, **defaults)
    
    def assert_response_structure(self, response_data: Dict[str, Any], 
                                expected_keys: List[str], 
                                forbidden_keys: Optional[List[str]] = None):
        """Assert response has expected structure"""
        for key in expected_keys:
            assert key in response_data, f"Expected key '{key}' not found in response"
        
        if forbidden_keys:
            for key in forbidden_keys:
                assert key not in response_data, f"Forbidden key '{key}' found in response"
    
    def assert_user_response_structure(self, user_data: Dict[str, Any]):
        """Assert user response has correct structure"""
        expected_keys = ["id", "email", "first_name", "last_name", "is_active", "is_superuser"]
        forbidden_keys = ["password", "hashed_password"]
        self.assert_response_structure(user_data, expected_keys, forbidden_keys)
    
    def assert_item_response_structure(self, item_data: Dict[str, Any]):
        """Assert item response has correct structure"""
        expected_keys = ["id", "title", "description", "owner_id", "created_at", "updated_at"]
        self.assert_response_structure(item_data, expected_keys)


class MockServices:
    """Collection of mock services for testing"""
    
    @staticmethod
    def mock_email_service():
        """Mock email service"""
        mock_service = MagicMock()
        mock_service.send_welcome_email.return_value = "email-sent"
        mock_service.send_password_reset.return_value = "reset-sent"
        return mock_service
    
    @staticmethod
    def mock_task_queue():
        """Mock ARQ task queue"""
        mock_queue = AsyncMock()
        mock_queue.enqueue_task.return_value = "mock-job-id"
        mock_queue.get_job_status.return_value = {
            "status": "completed",
            "job_id": "mock-job-id",
            "result": "mock-result"
        }
        mock_queue.get_queue_info.return_value = {
            "pending_jobs": 0,
            "in_progress_jobs": 0,
            "completed_jobs": 10
        }
        return mock_queue
    
    @staticmethod
    def mock_prometheus_service():
        """Mock Prometheus service"""
        mock_service = AsyncMock()
        mock_service.health_check.return_value = {"status": "healthy"}
        mock_service.query_instant.return_value = {
            "status": "success",
            "data": {
                "resultType": "vector",
                "result": [
                    {
                        "metric": {"__name__": "test_metric"},
                        "value": [1640995200, "42"]
                    }
                ]
            }
        }
        mock_service.query_range.return_value = {
            "status": "success",
            "data": {
                "resultType": "matrix",
                "result": [
                    {
                        "metric": {"__name__": "test_metric"},
                        "values": [
                            [1640995200, "42"],
                            [1640995260, "43"]
                        ]
                    }
                ]
            }
        }
        mock_service.get_metrics_list.return_value = ["test_metric", "another_metric"]
        return mock_service
    
    @staticmethod
    def mock_redis_service():
        """Mock Redis service"""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = '{"cached": "data"}'
        mock_redis.set.return_value = True
        mock_redis.delete.return_value = 1
        mock_redis.exists.return_value = True
        return mock_redis


class DatabaseTestHelper:
    """Helper for database-related testing"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_test_items(self, user: User, count: int = 3) -> List[Item]:
        """Create multiple test items for a user"""
        items = []
        for i in range(count):
            item_data = {
                "title": f"Test Item {i+1}",
                "description": f"Description for test item {i+1}",
                "owner_id": user.id
            }
            item = Item(**item_data)
            self.db.add(item)
            items.append(item)
        
        self.db.commit()
        for item in items:
            self.db.refresh(item)
        
        return items
    
    def count_users(self) -> int:
        """Count total users in database"""
        return self.db.query(User).count()
    
    def count_items(self) -> int:
        """Count total items in database"""
        return self.db.query(Item).count()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()


class AsyncTestHelper:
    """Helper for async testing"""
    
    @staticmethod
    async def async_api_test_helper(async_client: AsyncClient, 
                                  method: str, 
                                  url: str, 
                                  headers: Optional[Dict[str, str]] = None,
                                  json_data: Optional[Dict[str, Any]] = None):
        """Helper for making async API calls"""
        if method.upper() == "GET":
            response = await async_client.get(url, headers=headers)
        elif method.upper() == "POST":
            response = await async_client.post(url, headers=headers, json=json_data)
        elif method.upper() == "PUT":
            response = await async_client.put(url, headers=headers, json=json_data)
        elif method.upper() == "DELETE":
            response = await async_client.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        return response


@pytest.fixture
def api_helper(client: TestClient, db: Session) -> APITestHelper:
    """Fixture for API test helper"""
    return APITestHelper(client, db)


@pytest.fixture
def mock_services() -> MockServices:
    """Fixture for mock services"""
    return MockServices()


@pytest.fixture
def db_helper(db: Session) -> DatabaseTestHelper:
    """Fixture for database test helper"""
    return DatabaseTestHelper(db)


@pytest.fixture
def async_helper() -> AsyncTestHelper:
    """Fixture for async test helper"""
    return AsyncTestHelper()


def parametrize_user_types():
    """Decorator for parametrizing tests with different user types"""
    return pytest.mark.parametrize("user_type,expected_status", [
        ("superuser", 200),
        ("regular_user", 400),
        ("unauthenticated", 401)
    ])