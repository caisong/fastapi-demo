"""
Test user endpoints
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.factories import (
    create_user, 
    create_superuser, 
    get_user_token_headers, 
    get_superuser_token_headers
)


class TestUserListEndpoint:
    """Test user list endpoint"""
    
    def test_get_users_as_superuser_success(self, client: TestClient, db: Session):
        """Test getting users list as superuser"""
        superuser = create_superuser(db, email="admin@example.com")
        create_user(db, email="user1@example.com")
        create_user(db, email="user2@example.com")
        
        headers = get_superuser_token_headers(client)
        response = client.get("/api/v1/users/", headers=headers)
        
        assert response.status_code == 200
        users = response.json()
        assert len(users) >= 3  # At least the superuser and 2 test users
        
        # Verify user data structure
        for user in users:
            assert "id" in user
            assert "email" in user
            assert "first_name" in user
            assert "last_name" in user
            assert "is_active" in user
            assert "is_superuser" in user
            # Ensure password fields are not exposed
            assert "password" not in user
            assert "hashed_password" not in user
    
    def test_get_users_as_regular_user_fails(self, client: TestClient, db: Session):
        """Test that regular users cannot access users list"""
        create_user(db, email="user@example.com")
        
        headers = get_user_token_headers(client, email="user@example.com")
        response = client.get("/api/v1/users/", headers=headers)
        
        assert response.status_code == 400
        assert "not enough privileges" in response.json()["detail"]
    
    def test_get_users_without_auth_fails(self, client: TestClient):
        """Test that unauthenticated requests fail"""
        response = client.get("/api/v1/users/")
        assert response.status_code == 401
    
    def test_get_users_with_pagination(self, client: TestClient, db: Session):
        """Test users list pagination"""
        create_superuser(db, email="admin@example.com")
        
        # Create multiple test users
        for i in range(5):
            create_user(db, email=f"user{i}@example.com")
        
        headers = get_superuser_token_headers(client)
        
        # Test with limit
        response = client.get("/api/v1/users/?limit=3", headers=headers)
        assert response.status_code == 200
        users = response.json()
        assert len(users) <= 3
        
        # Test with skip
        response = client.get("/api/v1/users/?skip=2&limit=3", headers=headers)
        assert response.status_code == 200
        users = response.json()
        assert len(users) <= 3


class TestUserCreationEndpoint:
    """Test user creation endpoint"""
    
    def test_create_user_as_superuser_success(self, client: TestClient, db: Session):
        """Test successful user creation by superuser"""
        create_superuser(db, email="admin@example.com")
        
        user_data = {
            "email": "newuser@example.com",
            "password": "newpassword123",
            "first_name": "New",
            "last_name": "User",
            "is_active": True,
            "is_superuser": False
        }
        
        headers = get_superuser_token_headers(client)
        response = client.post("/api/v1/users/", json=user_data, headers=headers)
        
        assert response.status_code == 200
        created_user = response.json()
        assert created_user["email"] == user_data["email"]
        assert created_user["first_name"] == user_data["first_name"] 
        assert created_user["last_name"] == user_data["last_name"]
        assert created_user["is_active"] == user_data["is_active"]
        assert created_user["is_superuser"] == user_data["is_superuser"]
        assert "password" not in created_user
        assert "hashed_password" not in created_user
    
    def test_create_user_duplicate_email_fails(self, client: TestClient, db: Session):
        """Test creating user with duplicate email fails"""
        create_superuser(db, email="admin@example.com")
        create_user(db, email="existing@example.com")
        
        user_data = {
            "email": "existing@example.com",  # Duplicate email
            "password": "newpassword123",
            "first_name": "New",
            "last_name": "User"
        }
        
        headers = get_superuser_token_headers(client)
        response = client.post("/api/v1/users/", json=user_data, headers=headers)
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    def test_create_user_as_regular_user_fails(self, client: TestClient, db: Session):
        """Test that regular users cannot create users"""
        create_user(db, email="user@example.com")
        
        user_data = {
            "email": "newuser@example.com",
            "password": "newpassword123",
            "first_name": "New",
            "last_name": "User"
        }
        
        headers = get_user_token_headers(client, email="user@example.com")
        response = client.post("/api/v1/users/", json=user_data, headers=headers)
        
        assert response.status_code == 400
        assert "not enough privileges" in response.json()["detail"]
    
    def test_create_user_invalid_data_fails(self, client: TestClient, db: Session):
        """Test user creation with invalid data fails"""
        create_superuser(db, email="admin@example.com")
        
        invalid_user_data = {
            "email": "invalid-email",  # Invalid email format
            "password": "123",  # Too short password
            "first_name": "",  # Empty name
            "last_name": ""
        }
        
        headers = get_superuser_token_headers(client)
        response = client.post("/api/v1/users/", json=invalid_user_data, headers=headers)
        
        assert response.status_code == 422


class TestUserDetailEndpoint:
    """Test individual user detail endpoint"""
    
    def test_get_own_user_details_success(self, client: TestClient, db: Session):
        """Test user can get their own details"""
        user = create_user(db, email="user@example.com")
        
        headers = get_user_token_headers(client, email="user@example.com")
        response = client.get(f"/api/v1/users/{user.id}", headers=headers)
        
        assert response.status_code == 200
        user_data = response.json()
        assert user_data["id"] == user.id
        assert user_data["email"] == user.email
    
    def test_get_other_user_as_superuser_success(self, client: TestClient, db: Session):
        """Test superuser can get any user's details"""
        create_superuser(db, email="admin@example.com")
        target_user = create_user(db, email="user@example.com")
        
        headers = get_superuser_token_headers(client)
        response = client.get(f"/api/v1/users/{target_user.id}", headers=headers)
        
        assert response.status_code == 200
        user_data = response.json()
        assert user_data["id"] == target_user.id
        assert user_data["email"] == target_user.email
    
    def test_get_other_user_as_regular_user_fails(self, client: TestClient, db: Session):
        """Test regular user cannot get other users' details"""
        create_user(db, email="user1@example.com")
        target_user = create_user(db, email="user2@example.com")
        
        headers = get_user_token_headers(client, email="user1@example.com")
        response = client.get(f"/api/v1/users/{target_user.id}", headers=headers)
        
        assert response.status_code == 400
        assert "not enough privileges" in response.json()["detail"]
    
    def test_get_nonexistent_user_fails(self, client: TestClient, db: Session):
        """Test getting nonexistent user returns 404"""
        create_superuser(db, email="admin@example.com")
        
        headers = get_superuser_token_headers(client)
        response = client.get("/api/v1/users/99999", headers=headers)
        
        assert response.status_code == 404


class TestUserUpdateEndpoint:
    """Test user update endpoint"""
    
    def test_update_user_as_superuser_success(self, client: TestClient, db: Session):
        """Test successful user update by superuser"""
        create_superuser(db, email="admin@example.com")
        target_user = create_user(db, email="user@example.com")
        
        update_data = {
            "first_name": "Updated",
            "last_name": "Name",
            "is_active": False
        }
        
        headers = get_superuser_token_headers(client)
        response = client.put(f"/api/v1/users/{target_user.id}", json=update_data, headers=headers)
        
        assert response.status_code == 200
        updated_user = response.json()
        assert updated_user["first_name"] == update_data["first_name"]
        assert updated_user["last_name"] == update_data["last_name"]
        assert updated_user["is_active"] == update_data["is_active"]
    
    def test_update_user_password(self, client: TestClient, db: Session):
        """Test updating user password"""
        create_superuser(db, email="admin@example.com")
        target_user = create_user(db, email="user@example.com")
        
        update_data = {
            "password": "newpassword123"
        }
        
        headers = get_superuser_token_headers(client)
        response = client.put(f"/api/v1/users/{target_user.id}", json=update_data, headers=headers)
        
        assert response.status_code == 200
        # Password should not be in response
        updated_user = response.json()
        assert "password" not in updated_user
        assert "hashed_password" not in updated_user
    
    def test_update_user_as_regular_user_fails(self, client: TestClient, db: Session):
        """Test that regular users cannot update users"""
        create_user(db, email="user1@example.com")
        target_user = create_user(db, email="user2@example.com")
        
        update_data = {"first_name": "Updated"}
        
        headers = get_user_token_headers(client, email="user1@example.com")
        response = client.put(f"/api/v1/users/{target_user.id}", json=update_data, headers=headers)
        
        assert response.status_code == 400
        assert "not enough privileges" in response.json()["detail"]
    
    def test_update_nonexistent_user_fails(self, client: TestClient, db: Session):
        """Test updating nonexistent user returns 404"""
        create_superuser(db, email="admin@example.com")
        
        update_data = {"first_name": "Updated"}
        
        headers = get_superuser_token_headers(client)
        response = client.put("/api/v1/users/99999", json=update_data, headers=headers)
        
        assert response.status_code == 404
        assert "does not exist" in response.json()["detail"]


class TestUserPermissions:
    """Test user permission edge cases"""
    
    def test_superuser_can_access_all_endpoints(self, client: TestClient, db: Session):
        """Test that superuser has access to all user endpoints"""
        superuser = create_superuser(db, email="admin@example.com")
        regular_user = create_user(db, email="user@example.com")
        
        headers = get_superuser_token_headers(client)
        
        # Can list users
        response = client.get("/api/v1/users/", headers=headers)
        assert response.status_code == 200
        
        # Can create users  
        user_data = {
            "email": "newuser@example.com",
            "password": "newpassword123",
            "first_name": "New",
            "last_name": "User"
        }
        response = client.post("/api/v1/users/", json=user_data, headers=headers)
        assert response.status_code == 200
        
        # Can view any user
        response = client.get(f"/api/v1/users/{regular_user.id}", headers=headers)
        assert response.status_code == 200
        
        # Can update any user
        update_data = {"first_name": "Updated"}
        response = client.put(f"/api/v1/users/{regular_user.id}", json=update_data, headers=headers)
        assert response.status_code == 200
    
    @patch('app.core.security.get_password_hash')
    def test_password_hashing_called_on_create(self, mock_hash, client: TestClient, db: Session):
        """Test that password is properly hashed when creating user"""
        create_superuser(db, email="admin@example.com")
        mock_hash.return_value = "hashed_password"
        
        user_data = {
            "email": "newuser@example.com",
            "password": "plaintext_password",
            "first_name": "New",
            "last_name": "User"
        }
        
        headers = get_superuser_token_headers(client)
        response = client.post("/api/v1/users/", json=user_data, headers=headers)
        
        assert response.status_code == 200
        mock_hash.assert_called_once_with("plaintext_password")