"""
Test Prometheus endpoints
"""
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.factories import create_superuser, create_user, get_superuser_token_headers, get_user_token_headers
from tests.utils import APITestHelper, MockServices


class TestPrometheusHealthCheck:
    """Test Prometheus health check endpoint"""
    
    def test_health_check_success(self, client: TestClient, db: Session, api_helper: APITestHelper):
        """Test successful Prometheus health check"""
        superuser = api_helper.create_test_superuser()
        headers = api_helper.get_auth_headers(superuser)
        
        with patch('app.services.prometheus.prometheus_service.health_check') as mock_health:
            mock_health.return_value = {"status": "healthy", "version": "2.40.0"}
            
            response = client.get("/api/v1/prometheus/health", headers=headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "version" in data
            mock_health.assert_called_once()
    
    def test_health_check_service_down(self, client: TestClient, db: Session, api_helper: APITestHelper):
        """Test health check when Prometheus service is down"""
        superuser = api_helper.create_test_superuser()
        headers = api_helper.get_auth_headers(superuser)
        
        with patch('app.services.prometheus.prometheus_service.health_check') as mock_health:
            mock_health.side_effect = Exception("Connection refused")
            
            response = client.get("/api/v1/prometheus/health", headers=headers)
            
            assert response.status_code == 500
    
    def test_health_check_unauthorized(self, client: TestClient, db: Session, api_helper: APITestHelper):
        """Test health check without authentication"""
        response = client.get("/api/v1/prometheus/health")
        assert response.status_code == 401
    
    def test_health_check_regular_user_forbidden(self, client: TestClient, db: Session, api_helper: APITestHelper):
        """Test health check as regular user (should be forbidden)"""
        user = api_helper.create_test_user(email="user@example.com")
        headers = api_helper.get_auth_headers(user)
        
        response = client.get("/api/v1/prometheus/health", headers=headers)
        assert response.status_code == 400  # Not enough privileges


class TestPrometheusQueries:
    """Test Prometheus query endpoints"""
    
    def test_instant_query_success(self, client: TestClient, db: Session, api_helper: APITestHelper):
        """Test successful instant query"""
        superuser = api_helper.create_test_superuser()
        headers = api_helper.get_auth_headers(superuser)
        
        mock_result = {
            "status": "success",
            "data": {
                "resultType": "vector",
                "result": [
                    {
                        "metric": {"__name__": "up", "instance": "localhost:8000"},
                        "value": [1640995200, "1"]
                    }
                ]
            }
        }
        
        with patch('app.services.prometheus.prometheus_service.query_instant') as mock_query:
            mock_query.return_value = mock_result
            
            response = client.get(
                "/api/v1/prometheus/query", 
                headers=headers,
                params={"query": "up"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "data" in data
            mock_query.assert_called_once_with("up", None)
    
    def test_instant_query_with_time(self, client: TestClient, db: Session, api_helper: APITestHelper):
        """Test instant query with specific time"""
        superuser = api_helper.create_test_superuser()
        headers = api_helper.get_auth_headers(superuser)
        
        with patch('app.services.prometheus.prometheus_service.query_instant') as mock_query:
            mock_query.return_value = {"status": "success", "data": {"result": []}}
            
            response = client.get(
                "/api/v1/prometheus/query",
                headers=headers,
                params={"query": "up", "time": "1640995200"}
            )
            
            assert response.status_code == 200
            mock_query.assert_called_once_with("up", "1640995200")
    
    def test_range_query_success(self, client: TestClient, db: Session, api_helper: APITestHelper):
        """Test successful range query"""
        superuser = api_helper.create_test_superuser()
        headers = api_helper.get_auth_headers(superuser)
        
        mock_result = {
            "status": "success",
            "data": {
                "resultType": "matrix",
                "result": [
                    {
                        "metric": {"__name__": "up"},
                        "values": [
                            [1640995200, "1"],
                            [1640995260, "1"]
                        ]
                    }
                ]
            }
        }
        
        with patch('app.services.prometheus.prometheus_service.query_range') as mock_query:
            mock_query.return_value = mock_result
            
            response = client.get(
                "/api/v1/prometheus/query_range",
                headers=headers,
                params={
                    "query": "up",
                    "start": "1640995200",
                    "end": "1640995500",
                    "step": "60"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            mock_query.assert_called_once_with("up", "1640995200", "1640995500", "60")
    
    def test_query_missing_parameters(self, client: TestClient, db: Session, api_helper: APITestHelper):
        """Test query with missing required parameters"""
        superuser = api_helper.create_test_superuser()
        headers = api_helper.get_auth_headers(superuser)
        
        # Missing query parameter
        response = client.get("/api/v1/prometheus/query", headers=headers)
        assert response.status_code == 422
        
        # Missing range query parameters
        response = client.get(
            "/api/v1/prometheus/query_range",
            headers=headers,
            params={"query": "up"}  # Missing start, end, step
        )
        assert response.status_code == 422


class TestPrometheusMetrics:
    """Test Prometheus metrics endpoints"""
    
    def test_get_metrics_list_success(self, client: TestClient, db: Session, api_helper: APITestHelper):
        """Test getting metrics list"""
        superuser = api_helper.create_test_superuser()
        headers = api_helper.get_auth_headers(superuser)
        
        mock_metrics = [
            "http_requests_total",
            "http_request_duration_seconds",
            "up",
            "process_cpu_seconds_total"
        ]
        
        with patch('app.services.prometheus.prometheus_service.get_metrics_list') as mock_list:
            mock_list.return_value = mock_metrics
            
            response = client.get("/api/v1/prometheus/metrics", headers=headers)
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == len(mock_metrics)
            assert "up" in data
            mock_list.assert_called_once()
    
    def test_get_application_metrics_success(self, client: TestClient, db: Session, api_helper: APITestHelper):
        """Test getting application-specific metrics"""
        superuser = api_helper.create_test_superuser()
        headers = api_helper.get_auth_headers(superuser)
        
        mock_app_metrics = {
            "http_requests_total": {
                "status": "success",
                "data": {"result": [{"value": [1640995200, "100"]}]}
            },
            "http_request_duration_seconds": {
                "status": "success", 
                "data": {"result": [{"value": [1640995200, "0.5"]}]}
            }
        }
        
        with patch('app.services.prometheus.prometheus_service.get_application_metrics') as mock_app:
            mock_app.return_value = mock_app_metrics
            
            response = client.get("/api/v1/prometheus/metrics/application", headers=headers)
            
            assert response.status_code == 200
            data = response.json()
            assert "http_requests_total" in data
            assert "http_request_duration_seconds" in data
            mock_app.assert_called_once()
    
    def test_get_system_metrics_success(self, client: TestClient, db: Session, api_helper: APITestHelper):
        """Test getting system metrics"""
        superuser = api_helper.create_test_superuser()
        headers = api_helper.get_auth_headers(superuser)
        
        mock_system_metrics = {
            "cpu_usage": {"status": "success", "data": {"result": [{"value": [1640995200, "75.5"]}]}},
            "memory_usage": {"status": "success", "data": {"result": [{"value": [1640995200, "2048"]}]}},
            "disk_usage": {"status": "success", "data": {"result": [{"value": [1640995200, "50.0"]}]}}
        }
        
        with patch('app.services.prometheus.prometheus_service.get_system_metrics') as mock_system:
            mock_system.return_value = mock_system_metrics
            
            response = client.get("/api/v1/prometheus/metrics/system", headers=headers)
            
            assert response.status_code == 200
            data = response.json()
            assert "cpu_usage" in data
            assert "memory_usage" in data
            assert "disk_usage" in data
            mock_system.assert_called_once()


class TestPrometheusTargets:
    """Test Prometheus targets endpoint"""
    
    def test_get_targets_success(self, client: TestClient, db: Session, api_helper: APITestHelper):
        """Test getting Prometheus targets"""
        superuser = api_helper.create_test_superuser()
        headers = api_helper.get_auth_headers(superuser)
        
        mock_targets = {
            "status": "success",
            "data": {
                "activeTargets": [
                    {
                        "discoveredLabels": {"__address__": "localhost:8000"},
                        "labels": {"instance": "localhost:8000", "job": "fastapi"},
                        "scrapePool": "fastapi",
                        "scrapeUrl": "http://localhost:8000/metrics",
                        "health": "up",
                        "lastScrape": "2023-01-01T10:00:00Z"
                    }
                ]
            }
        }
        
        with patch('app.services.prometheus.prometheus_service.get_targets') as mock_targets_call:
            mock_targets_call.return_value = mock_targets
            
            response = client.get("/api/v1/prometheus/targets", headers=headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "data" in data
            assert "activeTargets" in data["data"]
            mock_targets_call.assert_called_once()


class TestPrometheusErrorHandling:
    """Test Prometheus error handling"""
    
    def test_service_unavailable_error(self, client: TestClient, db: Session, api_helper: APITestHelper):
        """Test handling when Prometheus service is unavailable"""
        superuser = api_helper.create_test_superuser()
        headers = api_helper.get_auth_headers(superuser)
        
        with patch('app.services.prometheus.prometheus_service.query_instant') as mock_query:
            mock_query.side_effect = Exception("Connection refused")
            
            response = client.get(
                "/api/v1/prometheus/query",
                headers=headers,
                params={"query": "up"}
            )
            
            assert response.status_code == 500
    
    def test_invalid_query_error(self, client: TestClient, db: Session, api_helper: APITestHelper):
        """Test handling invalid Prometheus query"""
        superuser = api_helper.create_test_superuser()
        headers = api_helper.get_auth_headers(superuser)
        
        error_result = {
            "status": "error",
            "errorType": "bad_data",
            "error": "invalid query syntax"
        }
        
        with patch('app.services.prometheus.prometheus_service.query_instant') as mock_query:
            mock_query.return_value = error_result
            
            response = client.get(
                "/api/v1/prometheus/query",
                headers=headers,
                params={"query": "invalid{query"}
            )
            
            assert response.status_code == 200  # Prometheus returns error in body
            data = response.json()
            assert data["status"] == "error"
            assert "error" in data


class TestPrometheusPermissions:
    """Test Prometheus endpoint permissions"""
    
    @pytest.mark.parametrize("endpoint", [
        "/api/v1/prometheus/health",
        "/api/v1/prometheus/query?query=up",
        "/api/v1/prometheus/query_range?query=up&start=1&end=2&step=1",
        "/api/v1/prometheus/metrics",
        "/api/v1/prometheus/metrics/application",
        "/api/v1/prometheus/metrics/system",
        "/api/v1/prometheus/targets"
    ])
    def test_endpoint_requires_superuser(self, client: TestClient, db: Session, 
                                       api_helper: APITestHelper, endpoint: str):
        """Test that Prometheus endpoints require superuser privileges"""
        user = api_helper.create_test_user(email="user@example.com")
        headers = api_helper.get_auth_headers(user)
        
        response = client.get(endpoint, headers=headers)
        assert response.status_code == 400  # Not enough privileges
    
    @pytest.mark.parametrize("endpoint", [
        "/api/v1/prometheus/health",
        "/api/v1/prometheus/query?query=up",
        "/api/v1/prometheus/metrics"
    ])
    def test_endpoint_requires_authentication(self, client: TestClient, endpoint: str):
        """Test that Prometheus endpoints require authentication"""
        response = client.get(endpoint)
        assert response.status_code == 401