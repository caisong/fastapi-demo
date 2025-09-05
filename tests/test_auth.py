"""
Test authentication endpoints
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import verify_password, create_access_token
from tests.factories import create_user, create_superuser


class TestUserRegistration:
    """Test user registration endpoints"""
    
    def test_register_new_user_success(self, client: TestClient):
        """Test successful user registration"""
        user_data = {
            "email": "newuser@example.com",
            "password": "NewPassword123",
            "first_name": "New",
            "last_name": "User"
        }
        
        with patch('app.services.user.send_welcome_email_task.delay') as mock_email:
            mock_email.return_value = "mock-job-id"
            response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["first_name"] == user_data["first_name"]
        assert data["last_name"] == user_data["last_name"]
        assert data["is_active"] is True
        assert data["is_superuser"] is False
        assert "id" in data
        # Verify welcome email task was called
        mock_email.assert_called_once()
    
    def test_register_duplicate_email_fails(self, client: TestClient, db: Session):
        """Test registration with duplicate email fails"""
        # Create existing user
        create_user(db, email="existing@example.com")
        
        user_data = {
            "email": "existing@example.com",
            "password": "NewPassword123",
            "first_name": "New",
            "last_name": "User"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    def test_register_invalid_email_fails(self, client: TestClient):
        """Test registration with invalid email fails"""
        user_data = {
            "email": "invalid-email",
            "password": "newpassword123",
            "first_name": "New",
            "last_name": "User"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422
    
    def test_register_weak_password_fails(self, client: TestClient):
        """Test registration with weak password fails"""
        user_data = {
            "email": "newuser@example.com",
            "password": "123",  # Too short
            "first_name": "New",
            "last_name": "User"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422


class TestUserLogin:
    """Test user login endpoints"""
    
    def test_login_success(self, client: TestClient, db: Session):
        """Test successful login"""
        user = create_user(db, email="test@example.com")
        
        login_data = {
            "username": "test@example.com",
            "password": "testpassword123"
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        
        tokens = response.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"
    
    def test_login_json_endpoint_success(self, client: TestClient, db: Session):
        """Test JSON login endpoint"""
        user = create_user(db, email="test@example.com")
        
        login_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        
        response = client.post("/api/v1/auth/login-json", json=login_data)
        assert response.status_code == 200
        
        tokens = response.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"
        assert "user" in tokens
    
    def test_login_incorrect_email(self, client: TestClient):
        """Test login with incorrect email"""
        login_data = {
            "username": "wrong@example.com",
            "password": "testpassword123"
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect email or password"
    
    def test_login_incorrect_password(self, client: TestClient, db: Session):
        """Test login with incorrect password"""
        create_user(db, email="test@example.com")
        
        login_data = {
            "username": "test@example.com",
            "password": "wrongpassword"
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect email or password"
    
    def test_login_inactive_user(self, client: TestClient, db: Session):
        """Test login with inactive user"""
        create_user(db, email="test@example.com", is_active=False)
        
        login_data = {
            "username": "test@example.com",
            "password": "testpassword123"
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 401
        assert "inactive" in response.json()["detail"].lower()


class TestTokenRefresh:
    """Test token refresh functionality"""
    
    def test_refresh_token_success(self, client: TestClient, db: Session):
        """Test successful token refresh"""
        user = create_user(db, email="test@example.com")
        
        # First login to get tokens
        login_data = {
            "username": "test@example.com",
            "password": "testpassword123"
        }
        
        login_response = client.post("/api/v1/auth/login", data=login_data)
        tokens = login_response.json()
        refresh_token = tokens["refresh_token"]
        
        # Use refresh token to get new access token
        refresh_data = {"refresh_token": refresh_token}
        response = client.post("/api/v1/auth/refresh", json=refresh_data)
        
        assert response.status_code == 200
        new_tokens = response.json()
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens
        assert new_tokens["token_type"] == "bearer"
    
    def test_refresh_token_invalid(self, client: TestClient):
        """Test refresh with invalid token"""
        refresh_data = {"refresh_token": "invalid-token"}
        response = client.post("/api/v1/auth/refresh", json=refresh_data)
        
        assert response.status_code == 401
    
    @patch('app.core.security.jwt.decode')
    def test_refresh_token_expired(self, mock_decode, client: TestClient):
        """Test refresh with expired token"""
        from jose import jwt
        mock_decode.side_effect = jwt.ExpiredSignatureError()
        
        refresh_data = {"refresh_token": "expired-token"}
        response = client.post("/api/v1/auth/refresh", json=refresh_data)
        
        assert response.status_code == 401


class TestCurrentUser:
    """Test current user endpoint"""
    
    def test_get_current_user_success(self, client: TestClient, db: Session):
        """Test getting current user with valid token"""
        user = create_user(db, email="test@example.com")
        
        # Login to get token
        login_data = {
            "username": "test@example.com",
            "password": "testpassword123"
        }
        
        login_response = client.post("/api/v1/auth/login", data=login_data)
        tokens = login_response.json()
        access_token = tokens["access_token"]
        
        # Get current user
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/api/v1/users/me", headers=headers)
        
        assert response.status_code == 200
        user_data = response.json()
        assert user_data["email"] == user.email
        assert user_data["id"] == user.id
    
    def test_get_current_user_no_token(self, client: TestClient):
        """Test getting current user without token"""
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401
    
    def test_get_current_user_invalid_token(self, client: TestClient):
        """Test getting current user with invalid token"""
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 401


class TestAuthenticationSecurity:
    """Test authentication security aspects"""
    
    @patch('app.core.security.pwd_context.verify')
    def test_password_verification_called(self, mock_verify, client: TestClient, db: Session):
        """Test that password verification is called during login"""
        create_user(db, email="test@example.com")
        mock_verify.return_value = True
        
        login_data = {
            "username": "test@example.com",
            "password": "testpassword123"
        }
        
        client.post("/api/v1/auth/login", data=login_data)
        mock_verify.assert_called_once()
    
    def test_password_not_returned_in_response(self, client: TestClient, db: Session):
        """Test that password is never returned in API responses"""
        user = create_user(db, email="test@example.com")
        
        login_data = {
            "username": "test@example.com",
            "password": "testpassword123"
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        response_data = response.json()
        
        # Check that password fields are not in response
        assert "password" not in str(response_data)
        assert "hashed_password" not in str(response_data)
    
    def test_rate_limiting_headers(self, client: TestClient):
        """Test that rate limiting headers are present"""
        # This would test rate limiting if implemented
        response = client.get("/api/v1/auth/me")
        # Add assertions for rate limiting headers if implemented