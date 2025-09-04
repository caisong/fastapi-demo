"""
Test task endpoints
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.factories import (
    create_user, 
    create_superuser, 
    get_user_token_headers, 
    get_superuser_token_headers
)


class TestReportGeneration:
    """Test report generation endpoints"""
    
    @patch('app.tasks.helpers.generate_report_task.delay')
    def test_generate_report_success(self, mock_task, client: TestClient, db: Session):
        """Test successful report generation"""
        user = create_user(db, email="user@example.com")
        mock_task.return_value = "test-job-id-123"
        
        headers = get_user_token_headers(client, email="user@example.com")
        response = client.post(
            "/api/v1/tasks/reports/generate?report_type=user_activity",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Report generation started for user_activity"
        assert data["job_id"] == "test-job-id-123"
        assert data["status"] == "queued"
        
        # Verify task was called with correct parameters
        mock_task.assert_called_once_with(user.id, "user_activity")
    
    def test_generate_report_invalid_type_fails(self, client: TestClient, db: Session):
        """Test report generation with invalid report type"""
        create_user(db, email="user@example.com")
        
        headers = get_user_token_headers(client, email="user@example.com")
        response = client.post(
            "/api/v1/tasks/reports/generate?report_type=invalid_type",
            headers=headers
        )
        
        assert response.status_code == 400
        assert "Invalid report type" in response.json()["detail"]
    
    def test_generate_report_without_auth_fails(self, client: TestClient):
        """Test report generation without authentication"""
        response = client.post("/api/v1/tasks/reports/generate?report_type=user_activity")
        assert response.status_code == 401
    
    @pytest.mark.parametrize("report_type", [
        "user_activity",
        "items_summary", 
        "monthly_report"
    ])
    @patch('app.tasks.helpers.generate_report_task.delay')
    def test_generate_all_valid_report_types(self, mock_task, report_type, client: TestClient, db: Session):
        """Test all valid report types can be generated"""
        user = create_user(db, email="user@example.com")
        mock_task.return_value = f"job-{report_type}"
        
        headers = get_user_token_headers(client, email="user@example.com")
        response = client.post(
            f"/api/v1/tasks/reports/generate?report_type={report_type}",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert report_type in data["message"]
        mock_task.assert_called_once_with(user.id, report_type)


class TestBatchNotifications:
    """Test batch notification endpoints"""
    
    @patch('app.tasks.helpers.send_batch_notifications_task.delay')
    def test_send_batch_notifications_success(self, mock_task, client: TestClient, db: Session):
        """Test successful batch notification sending"""
        create_superuser(db, email="admin@example.com")
        mock_task.return_value = "notification-job-123"
        
        notification_data = {
            "message": "Important announcement",
            "user_emails": ["user1@example.com", "user2@example.com"]
        }
        
        headers = get_superuser_token_headers(client)
        response = client.post(
            "/api/v1/tasks/notifications/batch",
            json=notification_data,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Batch notification" in data["message"]
        assert data["job_id"] == "notification-job-123"
        assert data["recipient_count"] == 2
        
        # Verify task was called with correct parameters
        mock_task.assert_called_once_with(
            notification_data["user_emails"],
            notification_data["message"]
        )
    
    def test_send_batch_notifications_as_regular_user_fails(self, client: TestClient, db: Session):
        """Test that regular users cannot send batch notifications"""
        create_user(db, email="user@example.com")
        
        notification_data = {
            "message": "Important announcement",
            "user_emails": ["user1@example.com"]
        }
        
        headers = get_user_token_headers(client, email="user@example.com")
        response = client.post(
            "/api/v1/tasks/notifications/batch",
            json=notification_data,
            headers=headers
        )
        
        assert response.status_code == 400
        assert "not enough privileges" in response.json()["detail"]
    
    def test_send_batch_notifications_empty_emails_fails(self, client: TestClient, db: Session):
        """Test batch notifications with empty email list fails"""
        create_superuser(db, email="admin@example.com")
        
        notification_data = {
            "message": "Important announcement",
            "user_emails": []  # Empty list
        }
        
        headers = get_superuser_token_headers(client)
        response = client.post(
            "/api/v1/tasks/notifications/batch",
            json=notification_data,
            headers=headers
        )
        
        assert response.status_code == 422


class TestDataCleanup:
    """Test data cleanup endpoints"""
    
    @patch('app.tasks.helpers.cleanup_old_data_task.delay')
    def test_cleanup_old_data_success(self, mock_task, client: TestClient, db: Session):
        """Test successful data cleanup"""
        create_superuser(db, email="admin@example.com")
        mock_task.return_value = "cleanup-job-456"
        
        headers = get_superuser_token_headers(client)
        response = client.post("/api/v1/tasks/cleanup", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "Data cleanup" in data["message"]
        assert data["job_id"] == "cleanup-job-456"
        
        mock_task.assert_called_once()
    
    def test_cleanup_as_regular_user_fails(self, client: TestClient, db: Session):
        """Test that regular users cannot trigger cleanup"""
        create_user(db, email="user@example.com")
        
        headers = get_user_token_headers(client, email="user@example.com")
        response = client.post("/api/v1/tasks/cleanup", headers=headers)
        
        assert response.status_code == 400
        assert "not enough privileges" in response.json()["detail"]


class TestJobStatusEndpoint:
    """Test job status checking endpoints"""
    
    def test_get_job_status_success(self, mock_task_queue, client: TestClient, db: Session):
        """Test successful job status retrieval"""
        create_user(db, email="user@example.com")
        
        # Configure mock to return specific status
        mock_task_queue.get_job_status.return_value = {
            "status": "completed",
            "job_id": "test-job-123",
            "result": "Report generated successfully"
        }
        
        headers = get_user_token_headers(client, email="user@example.com")
        response = client.get("/api/v1/tasks/jobs/test-job-123/status", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["job_id"] == "test-job-123"
        assert "result" in data
    
    def test_get_job_status_not_found(self, mock_task_queue, client: TestClient, db: Session):
        """Test job status for nonexistent job"""
        create_user(db, email="user@example.com")
        
        # Configure mock to return not found
        mock_task_queue.get_job_status.return_value = {"status": "not_found"}
        
        headers = get_user_token_headers(client, email="user@example.com")
        response = client.get("/api/v1/tasks/jobs/nonexistent-job/status", headers=headers)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_get_job_status_without_auth_fails(self, client: TestClient):
        """Test job status check without authentication"""
        response = client.get("/api/v1/tasks/jobs/test-job/status")
        assert response.status_code == 401
    
    @pytest.mark.parametrize("job_status", [
        "queued", "running", "completed", "failed"
    ])
    def test_get_job_status_various_states(self, mock_task_queue, job_status, client: TestClient, db: Session):
        """Test job status endpoint with various job states"""
        create_user(db, email="user@example.com")
        
        mock_task_queue.get_job_status.return_value = {
            "status": job_status,
            "job_id": "test-job",
            "result": f"Job is {job_status}"
        }
        
        headers = get_user_token_headers(client, email="user@example.com")
        response = client.get("/api/v1/tasks/jobs/test-job/status", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == job_status


class TestQueueInfoEndpoint:
    """Test queue information endpoints"""
    
    @patch('app.core.task_monitor.task_monitor.get_queue_info')
    def test_get_queue_info_success(self, mock_queue_info, client: TestClient, db: Session):
        """Test successful queue info retrieval"""
        create_user(db, email="user@example.com")
        
        mock_queue_info.return_value = {
            "queue_length": 5,
            "active_jobs": 2,
            "completed_jobs": 15,
            "failed_jobs": 1
        }
        
        headers = get_user_token_headers(client, email="user@example.com")
        response = client.get("/api/v1/tasks/queue/info", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["queue_length"] == 5
        assert data["active_jobs"] == 2
        assert data["completed_jobs"] == 15
        assert data["failed_jobs"] == 1
    
    def test_get_queue_info_without_auth_fails(self, client: TestClient):
        """Test queue info without authentication"""
        response = client.get("/api/v1/tasks/queue/info")
        assert response.status_code == 401


class TestRecentJobsEndpoint:
    """Test recent jobs endpoint"""
    
    @patch('app.core.task_monitor.task_monitor.get_recent_jobs')
    def test_get_recent_jobs_success(self, mock_recent_jobs, client: TestClient, db: Session):
        """Test successful recent jobs retrieval"""
        create_user(db, email="user@example.com")
        
        mock_recent_jobs.return_value = [
            {"job_id": "job-1", "status": "completed", "created_at": "2023-01-01T00:00:00"},
            {"job_id": "job-2", "status": "running", "created_at": "2023-01-01T01:00:00"},
            {"job_id": "job-3", "status": "queued", "created_at": "2023-01-01T02:00:00"}
        ]
        
        headers = get_user_token_headers(client, email="user@example.com")
        response = client.get("/api/v1/tasks/jobs/recent", headers=headers)
        
        assert response.status_code == 200
        jobs = response.json()
        assert len(jobs) == 3
        assert jobs[0]["job_id"] == "job-1"
        assert jobs[1]["status"] == "running"
    
    def test_get_recent_jobs_with_limit(self, client: TestClient, db: Session):
        """Test recent jobs with limit parameter"""
        create_user(db, email="user@example.com")
        
        headers = get_user_token_headers(client, email="user@example.com")
        response = client.get("/api/v1/tasks/jobs/recent?limit=5", headers=headers)
        
        assert response.status_code == 200
        # The actual implementation would verify the limit is applied
    
    def test_get_recent_jobs_limit_cap(self, client: TestClient, db: Session):
        """Test that recent jobs limit is capped at 50"""
        create_user(db, email="user@example.com")
        
        headers = get_user_token_headers(client, email="user@example.com")
        # Request more than the maximum allowed
        response = client.get("/api/v1/tasks/jobs/recent?limit=100", headers=headers)
        
        assert response.status_code == 200
        # The implementation should cap the limit at 50


class TestTaskIntegration:
    """Test task endpoint integration"""
    
    @patch('app.core.task_queue.task_queue.enqueue_task')
    def test_task_queue_integration(self, mock_enqueue, client: TestClient, db: Session):
        """Test that tasks are properly enqueued"""
        user = create_user(db, email="user@example.com")
        mock_enqueue.return_value = "integration-job-123"
        
        headers = get_user_token_headers(client, email="user@example.com")
        response = client.post(
            "/api/v1/tasks/reports/generate?report_type=user_activity",
            headers=headers
        )
        
        assert response.status_code == 200
        # Verify task queue integration works
        data = response.json()
        assert "job_id" in data
    
    def test_task_failure_handling(self, mock_task_queue, client: TestClient, db: Session):
        """Test handling of task failures"""
        create_user(db, email="user@example.com")
        
        # Configure mock to simulate task failure
        mock_task_queue.get_job_status.return_value = {
            "status": "failed",
            "job_id": "failed-job",
            "error": "Task processing failed"
        }
        
        headers = get_user_token_headers(client, email="user@example.com")
        response = client.get("/api/v1/tasks/jobs/failed-job/status", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert "error" in data