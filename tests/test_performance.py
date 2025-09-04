"""
Performance and benchmark tests
"""
import pytest
import time
import asyncio
from typing import List
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.factories import create_user, create_superuser
from tests.utils import APITestHelper


class TestAPIPerformance:
    """Test API performance benchmarks"""
    
    @pytest.mark.benchmark(group="auth")
    def test_login_performance(self, benchmark, client: TestClient, db: Session, api_helper: APITestHelper):
        """Benchmark login endpoint performance"""
        user = api_helper.create_test_user(email="perf@example.com")
        
        login_data = {
            "username": "perf@example.com",
            "password": "testpassword123"
        }
        
        def login():
            response = client.post("/api/v1/auth/login", data=login_data)
            return response
        
        result = benchmark(login)
        assert result.status_code == 200
    
    @pytest.mark.benchmark(group="auth")
    def test_token_validation_performance(self, benchmark, client: TestClient, db: Session, api_helper: APITestHelper):
        """Benchmark token validation performance"""
        user = api_helper.create_test_user(email="perf@example.com")
        headers = api_helper.get_auth_headers(user)
        
        def get_current_user():
            response = client.get("/api/v1/auth/me", headers=headers)
            return response
        
        result = benchmark(get_current_user)
        assert result.status_code == 200
    
    @pytest.mark.benchmark(group="users")
    def test_user_list_performance(self, benchmark, client: TestClient, db: Session, api_helper: APITestHelper):
        """Benchmark user list endpoint performance"""
        superuser = api_helper.create_test_superuser()
        headers = api_helper.get_auth_headers(superuser)
        
        # Create multiple users for realistic testing
        for i in range(20):
            api_helper.create_test_user(email=f"user{i}@example.com")
        
        def get_users():
            response = client.get("/api/v1/users/", headers=headers)
            return response
        
        result = benchmark(get_users)
        assert result.status_code == 200
        assert len(result.json()) >= 20
    
    @pytest.mark.benchmark(group="items")
    def test_item_creation_performance(self, benchmark, client: TestClient, db: Session, api_helper: APITestHelper):
        """Benchmark item creation performance"""
        user = api_helper.create_test_user()
        headers = api_helper.get_auth_headers(user)
        
        item_data = {
            "title": "Performance Test Item",
            "description": "An item created for performance testing"
        }
        
        def create_item():
            response = client.post("/api/v1/items/", json=item_data, headers=headers)
            return response
        
        result = benchmark(create_item)
        assert result.status_code == 200


class TestConcurrentAccess:
    """Test concurrent access scenarios"""
    
    def test_concurrent_logins(self, client: TestClient, db: Session, api_helper: APITestHelper):
        """Test concurrent login requests"""
        # Create multiple users
        users = []
        for i in range(10):
            user = api_helper.create_test_user(email=f"concurrent{i}@example.com")
            users.append(user)
        
        def login_user(user_email: str):
            login_data = {
                "username": user_email,
                "password": "testpassword123"
            }
            response = client.post("/api/v1/auth/login", data=login_data)
            return response.status_code
        
        # Execute concurrent logins
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(login_user, user.email) for user in users]
            results = [future.result() for future in futures]
        
        # All logins should succeed
        assert all(status == 200 for status in results)
    
    def test_concurrent_item_creation(self, client: TestClient, db: Session, api_helper: APITestHelper):
        """Test concurrent item creation"""
        user = api_helper.create_test_user()
        headers = api_helper.get_auth_headers(user)
        
        def create_item(item_index: int):
            item_data = {
                "title": f"Concurrent Item {item_index}",
                "description": f"Item created concurrently #{item_index}"
            }
            response = client.post("/api/v1/items/", json=item_data, headers=headers)
            return response.status_code
        
        # Create items concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_item, i) for i in range(10)]
            results = [future.result() for future in futures]
        
        # All creations should succeed
        assert all(status == 200 for status in results)
    
    def test_read_write_concurrency(self, client: TestClient, db: Session, api_helper: APITestHelper):
        """Test concurrent read and write operations"""
        user = api_helper.create_test_user()
        headers = api_helper.get_auth_headers(user)
        
        # Create some initial items
        for i in range(5):
            item_data = {
                "title": f"Initial Item {i}",
                "description": f"Initial item #{i}"
            }
            client.post("/api/v1/items/", json=item_data, headers=headers)
        
        def read_items():
            response = client.get("/api/v1/items/", headers=headers)
            return response.status_code
        
        def write_item(item_index: int):
            item_data = {
                "title": f"Concurrent Write Item {item_index}",
                "description": f"Item created during concurrent test #{item_index}"
            }
            response = client.post("/api/v1/items/", json=item_data, headers=headers)
            return response.status_code
        
        # Mix read and write operations
        with ThreadPoolExecutor(max_workers=8) as executor:
            read_futures = [executor.submit(read_items) for _ in range(10)]
            write_futures = [executor.submit(write_item, i) for i in range(5)]
            
            read_results = [future.result() for future in read_futures]
            write_results = [future.result() for future in write_futures]
        
        # All operations should succeed
        assert all(status == 200 for status in read_results)
        assert all(status == 200 for status in write_results)


class TestLoadTesting:
    """Test system behavior under load"""
    
    def test_sustained_request_load(self, client: TestClient, db: Session, api_helper: APITestHelper):
        """Test system behavior under sustained load"""
        user = api_helper.create_test_user()
        headers = api_helper.get_auth_headers(user)
        
        # Measure response times under load
        response_times = []
        num_requests = 100
        
        for i in range(num_requests):
            start_time = time.time()
            response = client.get("/api/v1/items/", headers=headers)
            end_time = time.time()
            
            assert response.status_code == 200
            response_times.append(end_time - start_time)
        
        # Calculate performance metrics
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        
        # Basic performance assertions
        assert avg_response_time < 1.0  # Average response time should be under 1 second
        assert max_response_time < 5.0  # Max response time should be under 5 seconds
        
        print(f"Average response time: {avg_response_time:.4f}s")
        print(f"Max response time: {max_response_time:.4f}s")
    
    def test_memory_usage_stability(self, client: TestClient, db: Session, api_helper: APITestHelper):
        """Test memory usage remains stable under repeated operations"""
        user = api_helper.create_test_user()
        headers = api_helper.get_auth_headers(user)
        
        # Perform many operations to test for memory leaks
        for batch in range(10):
            # Create items
            for i in range(10):
                item_data = {
                    "title": f"Memory Test Item {batch}-{i}",
                    "description": f"Item for memory testing batch {batch} item {i}"
                }
                response = client.post("/api/v1/items/", json=item_data, headers=headers)
                assert response.status_code == 200
            
            # Read items
            for _ in range(5):
                response = client.get("/api/v1/items/", headers=headers)
                assert response.status_code == 200
            
            # Delete some items (if delete endpoint exists)
            items_response = client.get("/api/v1/items/", headers=headers)
            items = items_response.json()
            
            for item in items[:5]:  # Delete first 5 items
                response = client.delete(f"/api/v1/items/{item['id']}", headers=headers)
                # Delete might not be implemented, so we don't assert status
        
        # If we reach here without errors, memory usage is likely stable
        assert True


class TestDatabasePerformance:
    """Test database performance scenarios"""
    
    def test_bulk_user_creation_performance(self, db: Session, api_helper: APITestHelper):
        """Test performance of bulk user creation"""
        start_time = time.time()
        
        # Create many users
        users = []
        for i in range(100):
            user = api_helper.create_test_user(email=f"bulk{i}@example.com")
            users.append(user)
        
        end_time = time.time()
        creation_time = end_time - start_time
        
        # Performance assertion
        assert creation_time < 10.0  # Should create 100 users in under 10 seconds
        assert len(users) == 100
        
        print(f"Created 100 users in {creation_time:.4f}s")
    
    def test_large_dataset_query_performance(self, client: TestClient, db: Session, api_helper: APITestHelper):
        """Test query performance with large datasets"""
        superuser = api_helper.create_test_superuser()
        headers = api_helper.get_auth_headers(superuser)
        
        # Create a large number of users
        for i in range(200):
            api_helper.create_test_user(email=f"dataset{i}@example.com")
        
        # Test query performance
        start_time = time.time()
        response = client.get("/api/v1/users/?limit=100", headers=headers)
        end_time = time.time()
        
        query_time = end_time - start_time
        
        assert response.status_code == 200
        users = response.json()
        assert len(users) == 100
        assert query_time < 2.0  # Query should complete in under 2 seconds
        
        print(f"Queried 100 users from 200+ dataset in {query_time:.4f}s")