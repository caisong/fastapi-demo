"""
Integration tests for the entire application
"""
import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.factories import create_user, create_superuser
from tests.utils import APITestHelper, MockServices


class TestUserItemWorkflow:
    """Test complete user and item workflow"""
    
    def test_complete_user_item_lifecycle(self, client: TestClient, db: Session, api_helper: APITestHelper):
        """Test complete lifecycle: register -> login -> create items -> manage items"""
        
        # 1. Register a new user
        user_data = {
            "email": "lifecycle@example.com",
            "password": "Password123",  # Updated to meet validation requirements
            "first_name": "Lifecycle",
            "last_name": "User"
        }
        
        with patch('app.tasks.helpers.send_welcome_email_task.delay') as mock_email:
            mock_email.return_value = "mock-job-id"
            register_response = client.post("/api/v1/auth/register", json=user_data)
        
        assert register_response.status_code == 200
        user_info = register_response.json()
        user_id = user_info["id"]
        
        # 2. Login with the new user
        login_data = {
            "username": "lifecycle@example.com",
            "password": "Password123"
        }
        
        login_response = client.post("/api/v1/auth/login", data=login_data)
        assert login_response.status_code == 200
        
        tokens = login_response.json()
        access_token = tokens["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # 3. Verify user can access protected endpoints
        me_response = client.post("/api/v1/auth/test-token", headers=headers)
        assert me_response.status_code == 200
        me_data = me_response.json()
        assert me_data["user_id"] == user_id
        
        # 4. Create multiple items
        items_created = []
        for i in range(3):
            item_data = {
                "title": f"Lifecycle Item {i+1}",
                "description": f"Item created during lifecycle test #{i+1}"
            }
            
            item_response = client.post("/api/v1/items/", json=item_data, headers=headers)
            assert item_response.status_code == 200
            
            item_info = item_response.json()
            items_created.append(item_info)
            assert item_info["title"] == item_data["title"]
            assert item_info["owner_id"] == user_id
        
        # 5. List user's items
        items_list_response = client.get("/api/v1/items/", headers=headers)
        assert items_list_response.status_code == 200
        
        items_list = items_list_response.json()
        assert len(items_list) == 3
        
        # 6. Update an item
        item_to_update = items_created[0]
        update_data = {
            "title": "Updated Lifecycle Item",
            "description": "Updated description"
        }
        
        update_response = client.put(
            f"/api/v1/items/{item_to_update['id']}", 
            json=update_data, 
            headers=headers
        )
        assert update_response.status_code == 200
        
        updated_item = update_response.json()
        assert updated_item["title"] == update_data["title"]
        assert updated_item["description"] == update_data["description"]
        
        # 7. Get specific item
        get_item_response = client.get(f"/api/v1/items/{item_to_update['id']}", headers=headers)
        assert get_item_response.status_code == 200
        
        retrieved_item = get_item_response.json()
        assert retrieved_item["title"] == update_data["title"]
        
        # 8. Delete an item
        delete_response = client.delete(f"/api/v1/items/{items_created[1]['id']}", headers=headers)
        assert delete_response.status_code == 200
        
        # 9. Verify item was deleted
        final_items_response = client.get("/api/v1/items/", headers=headers)
        assert final_items_response.status_code == 200
        
        final_items = final_items_response.json()
        assert len(final_items) == 2  # One item was deleted
        
        deleted_item_ids = [item["id"] for item in final_items]
        assert items_created[1]["id"] not in deleted_item_ids


class TestAdminUserManagement:
    """Test admin user management workflows"""
    
    def test_superuser_complete_user_management(self, client: TestClient, db: Session, api_helper: APITestHelper):
        """Test complete user management by superuser"""
        
        # 1. Create superuser
        superuser = api_helper.create_test_superuser()
        superuser_headers = api_helper.get_auth_headers(superuser)
        
        # 2. Create users via admin endpoint
        user_data = {
            "email": "managed@example.com",
            "password": "Password123",
            "first_name": "Managed",
            "last_name": "User",
            "is_active": True,
            "is_superuser": False
        }
        
        create_user_response = client.post("/api/v1/users/", json=user_data, headers=superuser_headers)
        assert create_user_response.status_code == 200
        
        created_user = create_user_response.json()
        user_id = created_user["id"]
        
        # 3. List all users
        users_list_response = client.get("/api/v1/users/", headers=superuser_headers)
        assert users_list_response.status_code == 200
        
        users_list = users_list_response.json()
        assert len(users_list) >= 2  # At least superuser and created user
        
        # 4. Get specific user
        get_user_response = client.get(f"/api/v1/users/{user_id}", headers=superuser_headers)
        assert get_user_response.status_code == 200
        
        user_details = get_user_response.json()
        assert user_details["email"] == "managed@example.com"
        
        # 5. Update user
        update_data = {
            "first_name": "Updated",
            "last_name": "Name",
            "is_active": False
        }
        
        update_response = client.put(f"/api/v1/users/{user_id}", json=update_data, headers=superuser_headers)
        assert update_response.status_code == 200
        
        updated_user = update_response.json()
        assert updated_user["first_name"] == "Updated"
        assert updated_user["last_name"] == "Name"
        assert updated_user["is_active"] is False
        
        # 6. Verify updated user cannot login (inactive)
        login_data = {
            "username": "managed@example.com",
            "password": "Password123"
        }
        
        login_response = client.post("/api/v1/auth/login", data=login_data)
        assert login_response.status_code == 401
        assert "inactive" in login_response.json()["detail"].lower()


class TestTaskIntegration:
    """Test task queue integration"""
    
    def test_background_task_workflow(self, client: TestClient, db: Session, api_helper: APITestHelper, mock_task_queue):
        """Test complete background task workflow"""
        
        # 1. Create superuser for task access
        superuser = api_helper.create_test_superuser()
        headers = api_helper.get_auth_headers(superuser)
        
        # 2. Generate report task (use query parameter instead of JSON body)
        report_response = client.post("/api/v1/tasks/reports/generate?report_type=user_activity", headers=headers)
        assert report_response.status_code == 200
        
        report_result = report_response.json()
        assert "job_id" in report_result
        job_id = report_result["job_id"]
        
        # 3. Check job status
        status_response = client.get(f"/api/v1/tasks/jobs/{job_id}/status", headers=headers)
        assert status_response.status_code == 200
        
        status_result = status_response.json()
        assert status_result["job_id"] == job_id
        assert "status" in status_result
        
        # 4. Send batch notifications  
        notification_data = {
            "message": "Test notification",
            "user_emails": ["user1@example.com", "user2@example.com", "user3@example.com"]
        }
        
        notification_response = client.post("/api/v1/tasks/notifications/batch", json=notification_data, headers=headers)
        assert notification_response.status_code == 200
        
        # 5. Perform data cleanup (fix endpoint path)
        cleanup_response = client.post("/api/v1/tasks/cleanup", headers=headers)
        assert cleanup_response.status_code == 200
        
        # 6. Get queue information
        queue_info_response = client.get("/api/v1/tasks/queue/info", headers=headers)
        assert queue_info_response.status_code == 200
        
        queue_info = queue_info_response.json()
        assert "queue_length" in queue_info
        assert "active_workers" in queue_info
        assert "redis_connected" in queue_info
        
        # 7. Get recent jobs
        recent_jobs_response = client.get("/api/v1/tasks/jobs/recent", headers=headers)
        assert recent_jobs_response.status_code == 200
        
        recent_jobs = recent_jobs_response.json()
        assert isinstance(recent_jobs, list)


class TestPrometheusIntegration:
    """Test Prometheus integration workflow"""
    
    def test_prometheus_monitoring_workflow(self, client: TestClient, db: Session, api_helper: APITestHelper):
        """Test complete Prometheus monitoring workflow"""
        
        # 1. Create superuser for Prometheus access
        superuser = api_helper.create_test_superuser()
        headers = api_helper.get_auth_headers(superuser)
        
        # 2. Check Prometheus health
        with patch('app.services.prometheus.prometheus_service.health_check') as mock_health:
            mock_health.return_value = {"status": "healthy", "version": "2.40.0"}
            
            health_response = client.get("/api/v1/prometheus/health", headers=headers)
            assert health_response.status_code == 200
            
            health_data = health_response.json()
            assert health_data["status"] == "healthy"
        
        # 3. Query application metrics
        with patch('app.services.prometheus.prometheus_service.get_application_metrics') as mock_app_metrics:
            mock_app_metrics.return_value = {
                "status": "success",
                "application_metrics": {
                    "http_requests_total": {
                        "status": "success",
                        "result": [{"value": [1640995200, "100"]}]
                    }
                },
                "timestamp": "2023-12-31T00:00:00"
            }
            
            app_metrics_response = client.get("/api/v1/prometheus/application_metrics", headers=headers)
            assert app_metrics_response.status_code == 200
            
            app_metrics = app_metrics_response.json()
            assert "application_metrics" in app_metrics
            assert "http_requests_total" in app_metrics["application_metrics"]
        
        # 4. Query system metrics
        with patch('app.services.prometheus.prometheus_service.get_system_metrics') as mock_system_metrics:
            mock_system_metrics.return_value = {
                "status": "success",
                "system_metrics": {
                    "cpu_usage": {
                        "status": "success", 
                        "result": [{"value": [1640995200, "75.5"]}]
                    }
                },
                "timestamp": "2023-12-31T00:00:00"
            }
            
            system_metrics_response = client.get("/api/v1/prometheus/system_metrics", headers=headers)
            assert system_metrics_response.status_code == 200
            
            system_metrics = system_metrics_response.json()
            assert "system_metrics" in system_metrics
            assert "cpu_usage" in system_metrics["system_metrics"]
        
        # 5. Get targets information
        with patch('app.services.prometheus.prometheus_service.get_targets') as mock_targets:
            mock_targets.return_value = {
                "status": "success",
                "targets": {"activeTargets": []}
            }
            
            targets_response = client.get("/api/v1/prometheus/targets", headers=headers)
            assert targets_response.status_code == 200
            
            targets_data = targets_response.json()
            assert targets_data["status"] == "success"
            assert "targets" in targets_data
        
        # 6. Perform custom query
        with patch('app.services.prometheus.prometheus_service.query_instant') as mock_query:
            mock_query.return_value = {
                "status": "success",
                "data": {"result": [{"value": [1640995200, "1"]}]}
            }
            
            query_response = client.get(
                "/api/v1/prometheus/query",
                headers=headers,
                params={"query": "up"}
            )
            assert query_response.status_code == 200
            
            query_data = query_response.json()
            assert query_data["status"] == "success"


class TestSecurityIntegration:
    """Test security-related integration scenarios"""
    
    def test_authentication_security_workflow(self, client: TestClient, db: Session, api_helper: APITestHelper):
        """Test complete authentication security workflow"""
        
        # 1. Register user
        user_data = {
            "email": "security@example.com",
            "password": "SecurePassword123",
            "first_name": "Security",
            "last_name": "User"
        }
        
        with patch('app.tasks.helpers.send_welcome_email_task.delay'):
            register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 200
        
        # 2. Login and get tokens
        login_data = {
            "username": "security@example.com",
            "password": "SecurePassword123"
        }
        
        login_response = client.post("/api/v1/auth/login", data=login_data)
        assert login_response.status_code == 200
        
        tokens = login_response.json()
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
        
        # 3. Use access token for protected endpoints
        headers = {"Authorization": f"Bearer {access_token}"}
        
        me_response = client.post("/api/v1/auth/test-token", headers=headers)
        assert me_response.status_code == 200
        
        # 4. Test invalid token scenarios
        invalid_headers = {"Authorization": "Bearer invalid-token"}
        invalid_response = client.post("/api/v1/auth/test-token", headers=invalid_headers)
        assert invalid_response.status_code == 401
        
        # 5. Refresh access token
        refresh_data = {"refresh_token": refresh_token}
        refresh_response = client.post("/api/v1/auth/refresh", json=refresh_data)
        assert refresh_response.status_code == 200
        
        new_tokens = refresh_response.json()
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens
        
        # 6. Use new access token
        new_headers = {"Authorization": f"Bearer {new_tokens['access_token']}"}
        new_me_response = client.post("/api/v1/auth/test-token", headers=new_headers)
        assert new_me_response.status_code == 200
        
        # 7. Test permission boundaries
        regular_user_headers = new_headers
        
        # Regular user should not access admin endpoints
        users_response = client.get("/api/v1/users/", headers=regular_user_headers)
        assert users_response.status_code == 400  # Not enough privileges
        
        prometheus_response = client.get("/api/v1/prometheus/health")  # Public endpoint
        assert prometheus_response.status_code == 200  # Public access allowed


class TestErrorHandlingIntegration:
    """Test error handling across different components"""
    
    def test_cascading_error_handling(self, client: TestClient, db: Session, api_helper: APITestHelper):
        """Test how errors cascade through different layers"""
        
        user = api_helper.create_test_user()
        headers = api_helper.get_auth_headers(user)
        
        # 1. Test non-existent resource
        response = client.get("/api/v1/items/99999", headers=headers)
        assert response.status_code == 404
        
        # 2. Test invalid data validation
        invalid_item_data = {
            "title": "",  # Empty title should fail validation
            "description": ""
        }
        
        response = client.post("/api/v1/items/", json=invalid_item_data, headers=headers)
        assert response.status_code == 422
        
        # 3. Test permission errors
        response = client.get("/api/v1/users/")  # No auth
        assert response.status_code == 401
        
        response = client.get("/api/v1/users/", headers=headers)  # Wrong permission
        assert response.status_code == 400
        
        # 4. Test server errors (mocked)
        with patch('app.db.database.AsyncSession.execute') as mock_execute:
            mock_execute.side_effect = Exception("Database connection error")
            
            response = client.get("/api/v1/items/", headers=headers)
            assert response.status_code == 500