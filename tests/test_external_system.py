"""
外部系统认证服务测试
"""
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.external_system import ExternalSystem, ExternalSystemSession
from app.schemas.external_system import ExternalSystemCreate, ExternalSystemUpdate
from app.services.external_system import external_system_service
from tests.factories import create_user, create_superuser
from tests.utils import APITestHelper


class TestExternalSystemModels:
    """测试外部系统模型"""
    
    def test_external_system_model(self, db: Session):
        """测试外部系统模型创建"""
        system_data = {
            "name": "test_system",
            "display_name": "测试系统",
            "base_url": "https://api.test.com",
            "auth_url": "/auth/login",
            "username": "test_user",
            "password_hash": "hashed_password",
            "auth_type": "username_password",
            "session_timeout": 3600,
            "max_retry_count": 3,
            "is_active": True,
            "auth_status": "inactive"
        }
        
        system = ExternalSystem(**system_data)
        db.add(system)
        db.commit()
        db.refresh(system)
        
        assert system.name == "test_system"
        assert system.display_name == "测试系统"
        assert system.is_active is True
        assert system.auth_status == "inactive"
    
    
    def test_external_system_session_model(self, db: Session):
        """测试外部系统会话模型"""
        # 先创建系统
        system = ExternalSystem(
            name="session_test_system",
            base_url="https://api.test.com",
            username="test_user",
            password_hash="hashed_password"
        )
        db.add(system)
        db.commit()
        db.refresh(system)
        
        # 创建会话
        session_data = {
            "system_id": system.id,
            "session_token": "test_token_12345",
            "session_data": {"user_id": 123, "role": "admin"},
            "is_valid": True,
            "expires_at": datetime.utcnow() + timedelta(hours=1)
        }
        
        session = ExternalSystemSession(**session_data)
        db.add(session)
        db.commit()
        db.refresh(session)
        
        assert session.system_id == system.id
        assert session.session_token == "test_token_12345"
        assert session.is_valid is True
        assert session.request_count == 0


class TestExternalSystemService:
    """测试外部系统服务"""
    
    @pytest.fixture
    def sample_system_data(self) -> Dict[str, Any]:
        """示例外部系统数据"""
        return {
            "name": "weather_api",
            "display_name": "天气API",
            "base_url": "https://api.weather.com",
            "auth_url": "/v1/auth/login",
            "username": "api_user",
            "password": "api_password_123",
            "auth_type": "username_password",
            "session_timeout": 3600,
            "max_retry_count": 3,
            "is_active": True
        }
    
    @pytest.mark.asyncio
    async def test_create_system(self, db):
        """测试创建外部系统"""
        system_in = ExternalSystemCreate(
            name="test_create_system",
            display_name="测试创建系统",
            base_url="https://api.test.com",
            auth_url="/auth/login",
            username="test_user",
            password="test_password",
            auth_type="username_password",
            session_timeout=3600,
            max_retry_count=3,
            is_active=True
        )
        
        system = await external_system_service.create_system(db, system_in=system_in)
        
        assert system.name == "test_create_system"
        assert system.display_name == "测试创建系统"
        assert system.is_active is True
        assert system.password_hash is not None  # 密码应被加密
        
        # 验证密码加密
        from app.core.security import verify_password
        assert verify_password("test_password", system.password_hash)
    
    @pytest.mark.asyncio
    async def test_authenticate_system_success(self, db, sample_system_data):
        """测试外部系统认证成功"""
        # 创建系统
        system_in = ExternalSystemCreate(**sample_system_data)
        system = await external_system_service.create_system(db, system_in=system_in)
        
        # 模拟API调用成功
        with patch('app.core.service_base.ExternalAPIService.post') as mock_post:
            mock_post.return_value = {
                "status_code": 200,
                "data": {
                    "success": True,
                    "token": "mock_auth_token_12345",
                    "expires_in": 3600
                },
                "response_time": 150,
                "headers": {}
            }
            
            # 执行认证
            result = await external_system_service.authenticate_system(db, system_name="weather_api")
            
            assert result.success is True
            assert result.system_name == "weather_api"
            assert result.session_token is not None
    
    @pytest.mark.asyncio
    async def test_authenticate_system_failure(self, db, sample_system_data):
        """测试外部系统认证失败"""
        # 创建系统
        system_in = ExternalSystemCreate(**sample_system_data)
        system = await external_system_service.create_system(db, system_in=system_in)
        
        # 模拟API调用失败
        with patch('app.core.service_base.ExternalAPIService.post') as mock_post:
            mock_post.side_effect = Exception("认证服务器不可用")
            
            # 执行认证
            result = await external_system_service.authenticate_system(db, system_name="weather_api")
            
            assert result.success is False
            assert "认证服务器不可用" in result.message
    
    @pytest.mark.asyncio
    async def test_get_system_status(self, db, sample_system_data):
        """测试获取系统状态"""
        # 创建系统
        system_in = ExternalSystemCreate(**sample_system_data)
        system = await external_system_service.create_system(db, system_in=system_in)
        
        # 获取状态
        status = await external_system_service.get_system_status(db, system_name="weather_api")
        
        assert status is not None
        assert status.system_name == "weather_api"
        assert status.status == "inactive"


class TestExternalSystemAPI:
    """测试外部系统API端点"""
    
    def test_create_external_system_unauthorized(self, client: TestClient, db: Session):
        """测试未授权用户创建外部系统"""
        system_data = {
            "name": "api_test_system",
            "display_name": "API测试系统",
            "base_url": "https://api.test.com",
            "auth_url": "/auth/login",
            "username": "api_user",
            "password": "api_password",
            "auth_type": "username_password"
        }
        
        response = client.post("/api/v1/external-systems/", json=system_data)
        assert response.status_code == 401
    
    def test_create_external_system_authorized(self, client: TestClient, db: Session):
        """测试授权用户创建外部系统"""
        # 创建超级用户
        superuser = create_superuser(db, email="admin@test.com", password="AdminPassword123")
        
        # 获取认证令牌
        api_helper = APITestHelper(client, db)
        headers = api_helper.get_auth_headers(superuser)
        
        system_data = {
            "name": "api_test_system",
            "display_name": "API测试系统",
            "base_url": "https://api.test.com",
            "auth_url": "/auth/login",
            "username": "api_user",
            "password": "api_password",
            "auth_type": "username_password"
        }
        
        response = client.post("/api/v1/external-systems/", json=system_data, headers=headers)
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == "api_test_system"
        assert data["display_name"] == "API测试系统"
    
    def test_list_external_systems(self, client: TestClient, db: Session):
        """测试获取外部系统列表"""
        # 创建超级用户
        superuser = create_superuser(db, email="admin@test.com", password="AdminPassword123")
        
        # 获取认证令牌
        api_helper = APITestHelper(client, db)
        headers = api_helper.get_auth_headers(superuser)
        
        # 创建测试系统
        system_data = {
            "name": "list_test_system",
            "display_name": "列表测试系统",
            "base_url": "https://api.test.com",
            "auth_url": "/auth/login",
            "username": "api_user",
            "password": "api_password",
            "auth_type": "username_password"
        }
        
        client.post("/api/v1/external-systems/", json=system_data, headers=headers)
        
        # 获取系统列表
        response = client.get("/api/v1/external-systems/", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_authenticate_external_system(self, client: TestClient, db: Session):
        """测试对外部系统进行认证"""
        # 创建超级用户
        superuser = create_superuser(db, email="admin@test.com", password="AdminPassword123")
        
        # 获取认证令牌
        api_helper = APITestHelper(client, db)
        headers = api_helper.get_auth_headers(superuser)
        
        # 创建测试系统
        system_data = {
            "name": "auth_test_system",
            "display_name": "认证测试系统",
            "base_url": "https://api.test.com",
            "auth_url": "/auth/login",
            "username": "api_user",
            "password": "api_password",
            "auth_type": "username_password"
        }
        
        create_response = client.post("/api/v1/external-systems/", json=system_data, headers=headers)
        assert create_response.status_code == 201
        
        # 模拟认证API调用
        with patch('app.core.service_base.ExternalAPIService.post') as mock_post:
            mock_post.return_value = {
                "status_code": 200,
                "data": {
                    "success": True,
                    "token": "mock_auth_token_12345",
                    "expires_in": 3600
                },
                "response_time": 150,
                "headers": {}
            }
            
            # 执行认证
            auth_response = client.post("/api/v1/external-systems/auth_test_system/authenticate", headers=headers)
            assert auth_response.status_code == 200
            
            auth_data = auth_response.json()
            assert auth_data["success"] is True
            assert auth_data["system_name"] == "auth_test_system"


class TestExternalSystemIntegration:
    """测试外部系统集成"""
    
    @pytest.mark.asyncio
    async def test_call_external_api_success(self, db):
        """测试成功调用外部API"""
        # 创建系统
        system_in = ExternalSystemCreate(
            name="integration_test_system",
            display_name="集成测试系统",
            base_url="https://api.test.com",
            auth_url="/auth/login",
            username="test_user",
            password="test_password"
        )
        system = await external_system_service.create_system(db, system_in=system_in)
        
        # 创建会话
        from app.models.external_system import ExternalSystemSession
        session = ExternalSystemSession(
            system_id=system.id,
            session_token="test_session_token",
            is_valid=True,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        db.add(session)
        db.commit()
        
        # 模拟API调用
        with patch('app.core.service_base.ExternalAPIService.get') as mock_get:
            mock_get.return_value = {
                "status_code": 200,
                "data": {"message": "success", "data": [1, 2, 3]},
                "response_time": 120,
                "headers": {}
            }
            
            # 调用外部API
            response = await external_system_service.call_external_api(
                db,
                system_name="integration_test_system",
                method="GET",
                endpoint="/api/data"
            )
            
            assert response["status_code"] == 200
            assert "data" in response
    
    @pytest.mark.asyncio
    async def test_call_external_api_reauth(self, db):
        """测试调用外部API时自动重新认证"""
        # 创建系统
        system_in = ExternalSystemCreate(
            name="reauth_test_system",
            display_name="重新认证测试系统",
            base_url="https://api.test.com",
            auth_url="/auth/login",
            username="test_user",
            password="test_password"
        )
        system = await external_system_service.create_system(db, system_in=system_in)
        
        # 模拟第一次调用失败（会话无效），然后重新认证成功
        with patch('app.core.service_base.ExternalAPIService.get') as mock_get, \
             patch('app.core.service_base.ExternalAPIService.post') as mock_post:
            
            # 第一次调用失败（模拟会话无效）
            mock_get.side_effect = Exception("会话无效")
            
            # 模拟认证成功
            mock_post.return_value = {
                "status_code": 200,
                "data": {
                    "success": True,
                    "token": "new_auth_token_12345",
                    "expires_in": 3600
                },
                "response_time": 150,
                "headers": {}
            }
            
            # 第二次调用成功
            mock_get.side_effect = None
            mock_get.return_value = {
                "status_code": 200,
                "data": {"message": "success"},
                "response_time": 120,
                "headers": {}
            }
            
            # 调用外部API
            response = await external_system_service.call_external_api(
                db,
                system_name="reauth_test_system",
                method="GET",
                endpoint="/api/data"
            )
            
            assert response["status_code"] == 200