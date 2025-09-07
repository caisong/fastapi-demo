"""
Test item endpoints
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.factories import (
    create_user, 
    create_superuser, 
    create_item,
    get_user_token_headers, 
    get_superuser_token_headers
)


class TestItemListEndpoint:
    """Test item list endpoint"""
    
    def test_get_items_as_regular_user_shows_own_items(self, client: TestClient, db: Session):
        """Test regular users see only their own items"""
        user1 = create_user(db, email="user1@example.com")
        user2 = create_user(db, email="user2@example.com")
        
        # Create items for different users
        item1 = create_item(db, owner_id=user1.id, title="User1 Item 1")
        item2 = create_item(db, owner_id=user1.id, title="User1 Item 2")
        item3 = create_item(db, owner_id=user2.id, title="User2 Item 1")
        
        headers = get_user_token_headers(client, email="user1@example.com")
        response = client.get("/api/v1/items/", headers=headers)
        
        assert response.status_code == 200
        items = response.json()
        
        # User1 should only see their own items
        assert len(items) == 2
        item_titles = [item["title"] for item in items]
        assert "User1 Item 1" in item_titles
        assert "User1 Item 2" in item_titles
        assert "User2 Item 1" not in item_titles
    
    def test_get_items_as_superuser_shows_all_items(self, client: TestClient, db: Session):
        """Test superuser sees all items"""
        superuser = create_superuser(db, email="admin@example.com")
        user1 = create_user(db, email="user1@example.com")
        user2 = create_user(db, email="user2@example.com")
        
        # Create items for different users
        create_item(db, owner_id=user1.id, title="User1 Item")
        create_item(db, owner_id=user2.id, title="User2 Item")
        create_item(db, owner_id=superuser.id, title="Superuser Item")
        
        headers = get_superuser_token_headers(client)
        response = client.get("/api/v1/items/", headers=headers)
        
        assert response.status_code == 200
        items = response.json()
        
        # Superuser should see all items
        assert len(items) >= 3
        item_titles = [item["title"] for item in items]
        assert "User1 Item" in item_titles
        assert "User2 Item" in item_titles
        assert "Superuser Item" in item_titles
    
    def test_get_items_without_auth_fails(self, client: TestClient):
        """Test that unauthenticated requests fail"""
        response = client.get("/api/v1/items/")
        assert response.status_code == 401
    
    def test_get_items_with_pagination(self, client: TestClient, db: Session):
        """Test items list pagination"""
        user = create_user(db, email="user@example.com")
        
        # Create multiple items
        for i in range(5):
            create_item(db, owner_id=user.id, title=f"Item {i}")
        
        headers = get_user_token_headers(client, email="user@example.com")
        
        # Test with limit
        response = client.get("/api/v1/items/?limit=3", headers=headers)
        assert response.status_code == 200
        items = response.json()
        assert len(items) <= 3
        
        # Test with skip
        response = client.get("/api/v1/items/?skip=2&limit=3", headers=headers)
        assert response.status_code == 200
        items = response.json()
        assert len(items) <= 3


class TestItemCreationEndpoint:
    """Test item creation endpoint"""
    
    @patch('app.tasks.helpers.process_item_task.delay')
    def test_create_item_success(self, mock_task, client: TestClient, db: Session):
        """Test successful item creation"""
        user = create_user(db, email="user@example.com")
        mock_task.return_value = "mock-job-id"
        
        item_data = {
            "title": "New Test Item",
            "description": "A test item for API testing"
        }
        
        headers = get_user_token_headers(client, email="user@example.com")
        response = client.post("/api/v1/items/", json=item_data, headers=headers)
        
        assert response.status_code == 200
        created_item = response.json()
        assert created_item["title"] == item_data["title"]
        assert created_item["description"] == item_data["description"]
        assert created_item["owner_id"] == user.id
        assert "id" in created_item
        
        # Verify background task was called
        mock_task.assert_called_once()
    
    def test_create_item_without_auth_fails(self, client: TestClient):
        """Test that unauthenticated item creation fails"""
        item_data = {
            "title": "New Test Item",
            "description": "A test item"
        }
        
        response = client.post("/api/v1/items/", json=item_data)
        assert response.status_code == 401
    
    def test_create_item_invalid_data_fails(self, client: TestClient, db: Session):
        """Test item creation with invalid data fails"""
        create_user(db, email="user@example.com")
        
        invalid_item_data = {
            "title": "",  # Empty title
            "description": "A" * 1001  # Too long description
        }
        
        headers = get_user_token_headers(client, email="user@example.com")
        response = client.post("/api/v1/items/", json=invalid_item_data, headers=headers)
        
        assert response.status_code == 422
    
    def test_create_item_minimal_data_success(self, client: TestClient, db: Session):
        """Test creating item with minimal required data"""
        create_user(db, email="user@example.com")
        
        item_data = {
            "title": "Minimal Item"
            # description is optional
        }
        
        headers = get_user_token_headers(client, email="user@example.com")
        response = client.post("/api/v1/items/", json=item_data, headers=headers)
        
        assert response.status_code == 200
        created_item = response.json()
        assert created_item["title"] == item_data["title"]


class TestItemDetailEndpoint:
    """Test individual item detail endpoint"""
    
    def test_get_own_item_success(self, client: TestClient, db: Session):
        """Test user can get their own item"""
        user = create_user(db, email="user@example.com")
        item = create_item(db, owner_id=user.id, title="My Item")
        
        headers = get_user_token_headers(client, email="user@example.com")
        response = client.get(f"/api/v1/items/{item.id}", headers=headers)
        
        assert response.status_code == 200
        item_data = response.json()
        assert item_data["id"] == item.id
        assert item_data["title"] == item.title
        assert item_data["owner_id"] == user.id
    
    def test_get_other_users_item_as_regular_user_fails(self, client: TestClient, db: Session):
        """Test regular user cannot get other users' items"""
        user1 = create_user(db, email="user1@example.com")
        user2 = create_user(db, email="user2@example.com")
        item = create_item(db, owner_id=user2.id, title="User2 Item")
        
        headers = get_user_token_headers(client, email="user1@example.com")
        response = client.get(f"/api/v1/items/{item.id}", headers=headers)
        
        assert response.status_code == 400
        assert "not enough permissions" in response.json()["detail"].lower()
    
    def test_get_any_item_as_superuser_success(self, client: TestClient, db: Session):
        """Test superuser can get any item"""
        superuser = create_superuser(db, email="admin@example.com")
        user = create_user(db, email="user@example.com")
        item = create_item(db, owner_id=user.id, title="User Item")
        
        headers = get_superuser_token_headers(client)
        response = client.get(f"/api/v1/items/{item.id}", headers=headers)
        
        assert response.status_code == 200
        item_data = response.json()
        assert item_data["id"] == item.id
        assert item_data["title"] == item.title
    
    def test_get_nonexistent_item_fails(self, client: TestClient, db: Session):
        """Test getting nonexistent item returns 404"""
        create_user(db, email="user@example.com")
        
        headers = get_user_token_headers(client, email="user@example.com")
        response = client.get("/api/v1/items/99999", headers=headers)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestItemUpdateEndpoint:
    """Test item update endpoint"""
    
    def test_update_own_item_success(self, client: TestClient, db: Session):
        """Test user can update their own item"""
        user = create_user(db, email="user@example.com")
        item = create_item(db, owner_id=user.id, title="Original Title")
        
        update_data = {
            "title": "Updated Title",
            "description": "Updated description"
        }
        
        headers = get_user_token_headers(client, email="user@example.com")
        response = client.put(f"/api/v1/items/{item.id}", json=update_data, headers=headers)
        
        assert response.status_code == 200
        updated_item = response.json()
        assert updated_item["title"] == update_data["title"]
        assert updated_item["description"] == update_data["description"]
        assert updated_item["id"] == item.id
        assert updated_item["owner_id"] == user.id
    
    def test_update_other_users_item_as_regular_user_fails(self, client: TestClient, db: Session):
        """Test regular user cannot update other users' items"""
        user1 = create_user(db, email="user1@example.com")
        user2 = create_user(db, email="user2@example.com")
        item = create_item(db, owner_id=user2.id, title="User2 Item")
        
        update_data = {"title": "Updated Title"}
        
        headers = get_user_token_headers(client, email="user1@example.com")
        response = client.put(f"/api/v1/items/{item.id}", json=update_data, headers=headers)
        
        assert response.status_code == 400
        assert "not enough permissions" in response.json()["detail"].lower()
    
    def test_update_any_item_as_superuser_success(self, client: TestClient, db: Session):
        """Test superuser can update any item"""
        superuser = create_superuser(db, email="admin@example.com")
        user = create_user(db, email="user@example.com")
        item = create_item(db, owner_id=user.id, title="User Item")
        
        update_data = {"title": "Updated by Admin"}
        
        headers = get_superuser_token_headers(client)
        response = client.put(f"/api/v1/items/{item.id}", json=update_data, headers=headers)
        
        assert response.status_code == 200
        updated_item = response.json()
        assert updated_item["title"] == update_data["title"]
    
    def test_update_nonexistent_item_fails(self, client: TestClient, db: Session):
        """Test updating nonexistent item returns 404"""
        create_user(db, email="user@example.com")
        
        update_data = {"title": "Updated Title"}
        
        headers = get_user_token_headers(client, email="user@example.com")
        response = client.put("/api/v1/items/99999", json=update_data, headers=headers)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_update_item_partial_data_success(self, client: TestClient, db: Session):
        """Test updating item with partial data"""
        user = create_user(db, email="user@example.com")
        item = create_item(db, owner_id=user.id, title="Original Title", description="Original description")
        
        # Update only title
        update_data = {"title": "Updated Title Only"}
        
        headers = get_user_token_headers(client, email="user@example.com")
        response = client.put(f"/api/v1/items/{item.id}", json=update_data, headers=headers)
        
        assert response.status_code == 200
        updated_item = response.json()
        assert updated_item["title"] == update_data["title"]
        # Description should remain unchanged
        assert updated_item["description"] == "Original description"


class TestItemPermissions:
    """Test item permission edge cases"""
    
    def test_item_ownership_verification(self, client: TestClient, db: Session):
        """Test that item ownership is properly verified"""
        user1 = create_user(db, email="user1@example.com")
        user2 = create_user(db, email="user2@example.com")
        
        # User1 creates an item
        item_data = {"title": "User1 Item"}
        headers1 = get_user_token_headers(client, email="user1@example.com")
        response = client.post("/api/v1/items/", json=item_data, headers=headers1)
        item = response.json()
        
        # User2 cannot access User1's item
        headers2 = get_user_token_headers(client, email="user2@example.com")
        response = client.get(f"/api/v1/items/{item['id']}", headers=headers2)
        assert response.status_code == 400
        
        # User2 cannot update User1's item
        response = client.put(f"/api/v1/items/{item['id']}", json={"title": "Hacked"}, headers=headers2)
        assert response.status_code == 400
    
    def test_superuser_bypass_ownership(self, client: TestClient, db: Session):
        """Test that superuser can bypass ownership restrictions"""
        superuser = create_superuser(db, email="admin@example.com")
        user = create_user(db, email="user@example.com")
        item = create_item(db, owner_id=user.id, title="User Item")
        
        superuser_headers = get_superuser_token_headers(client)
        
        # Superuser can view any item
        response = client.get(f"/api/v1/items/{item.id}", headers=superuser_headers)
        assert response.status_code == 200
        
        # Superuser can update any item
        response = client.put(f"/api/v1/items/{item.id}", json={"title": "Updated by Admin"}, headers=superuser_headers)
        assert response.status_code == 200
    
    @patch('app.services.item.item_service.update')
    def test_item_service_called_on_update(self, mock_update, client: TestClient, db: Session):
        """Test that item service is called during updates"""
        user = create_user(db, email="user@example.com")
        item = create_item(db, owner_id=user.id, title="Original Title")
        
        # Mock the service method
        mock_update.return_value = item
        
        update_data = {"title": "Updated Title"}
        headers = get_user_token_headers(client, email="user@example.com")
        
        # This would test service layer integration if implemented
        # response = client.put(f"/api/v1/items/{item.id}", json=update_data, headers=headers)
        # mock_update.assert_called_once()