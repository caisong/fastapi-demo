"""
外部系统认证服务
"""
import asyncio
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.external_system import ExternalSystem, ExternalSystemSession, ExternalSystemLog
from app.schemas.external_system import (
    ExternalSystemCreate, ExternalSystemUpdate,
    ExternalSystemSessionCreate, ExternalSystemSessionUpdate,
    ExternalSystemAuthResponse, ExternalSystemAuthStatus,
    ExternalSystemLogCreate, ExternalSystemAuthBatchResponse
)
from app.core.security import get_password_hash, verify_password
from app.core.service_base import ExternalAPIService
from app.db.crud import CRUDBase


logger = logging.getLogger(__name__)


class CRUDExternalSystem(CRUDBase[ExternalSystem, ExternalSystemCreate, ExternalSystemUpdate]):
    """外部系统配置CRUD操作"""
    
    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[ExternalSystem]:
        """根据名称获取外部系统配置"""
        result = await db.execute(select(ExternalSystem).filter(ExternalSystem.name == name))
        return result.scalar_one_or_none()
    
    async def get_active_systems(self, db: AsyncSession) -> List[ExternalSystem]:
        """获取所有启用的外部系统"""
        result = await db.execute(
            select(ExternalSystem).filter(ExternalSystem.is_active == True)
        )
        return result.scalars().all()
    
    async def update_auth_status(
        self, 
        db: AsyncSession, 
        *, 
        db_obj: ExternalSystem, 
        status: str,
        last_error: Optional[str] = None
    ) -> ExternalSystem:
        """更新认证状态"""
        # 刷新对象以确保它在当前会话中
        await db.refresh(db_obj)
        
        update_data = {
            "auth_status": status,
            "updated_at": datetime.utcnow()
        }
        
        if status == "active":
            update_data["last_login_time"] = datetime.utcnow()
        
        if last_error is not None:
            update_data["last_error"] = last_error
            
        try:
            await db.execute(
                update(ExternalSystem)
                .where(ExternalSystem.id == db_obj.id)
                .values(**update_data)
            )
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except Exception as e:
            await db.rollback()
            raise


class CRUDExternalSystemSession(CRUDBase[ExternalSystemSession, ExternalSystemSessionCreate, ExternalSystemSessionUpdate]):
    """外部系统会话CRUD操作"""
    
    async def get_active_session(self, db: AsyncSession, *, system_id: int) -> Optional[ExternalSystemSession]:
        """获取有效的会话"""
        now = datetime.utcnow()
        result = await db.execute(
            select(ExternalSystemSession)
            .filter(
                ExternalSystemSession.system_id == system_id,
                ExternalSystemSession.is_valid == True,
                ExternalSystemSession.expires_at > now
            )
        )
        return result.scalar_one_or_none()
    
    async def invalidate_session(self, db: AsyncSession, *, session_id: int) -> None:
        """使会话失效"""
        await db.execute(
            update(ExternalSystemSession)
            .where(ExternalSystemSession.id == session_id)
            .values(is_valid=False, updated_at=datetime.utcnow())
        )
        await db.commit()
    
    async def invalidate_all_sessions(self, db: AsyncSession, *, system_id: int) -> None:
        """使所有会话失效"""
        await db.execute(
            update(ExternalSystemSession)
            .where(ExternalSystemSession.system_id == system_id)
            .values(is_valid=False, updated_at=datetime.utcnow())
        )
        await db.commit()


class CRUDExternalSystemLog(CRUDBase[ExternalSystemLog, ExternalSystemLogCreate, ExternalSystemLogCreate]):
    """外部系统日志CRUD操作"""
    
    async def create_log(self, db: AsyncSession, *, log_in: ExternalSystemLogCreate) -> ExternalSystemLog:
        """创建日志记录"""
        # 截断响应数据以避免存储过大的数据
        if log_in.response_data and len(str(log_in.response_data)) > 1000:
            log_in.response_data = {"truncated": True, "size": len(str(log_in.response_data))}
        
        db_obj = ExternalSystemLog(**log_in.dict())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


# 实例化CRUD操作
external_system_crud = CRUDExternalSystem(ExternalSystem)
external_session_crud = CRUDExternalSystemSession(ExternalSystemSession)
external_log_crud = CRUDExternalSystemLog(ExternalSystemLog)


class ExternalSystemService:
    """外部系统认证服务"""
    
    def __init__(self):
        self.systems: Dict[str, ExternalSystem] = {}
        self.sessions: Dict[str, ExternalSystemSession] = {}
        self.api_clients: Dict[str, ExternalAPIService] = {}
    
    async def create_system(self, db: AsyncSession, *, system_in: ExternalSystemCreate) -> ExternalSystem:
        """创建外部系统配置"""
        # 加密密码
        password_hash = get_password_hash(system_in.password)
        
        # 创建系统配置对象
        system_data = system_in.dict(exclude={'password'})
        system_data['password_hash'] = password_hash
        
        db_obj = ExternalSystem(**system_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        
        # 缓存系统配置
        self.systems[db_obj.name] = db_obj
        
        return db_obj
    
    async def update_system(
        self, 
        db: AsyncSession, 
        *, 
        db_obj: ExternalSystem, 
        system_in: ExternalSystemUpdate
    ) -> ExternalSystem:
        """更新外部系统配置"""
        update_data = system_in.dict(exclude_unset=True)
        
        # 如果提供了新密码，则加密
        if 'password' in update_data and update_data['password']:
            update_data['password_hash'] = get_password_hash(update_data['password'])
            del update_data['password']
        
        # 更新对象
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        
        # 更新缓存
        self.systems[db_obj.name] = db_obj
        
        return db_obj
    
    async def get_system(self, db: AsyncSession, *, system_id: int) -> Optional[ExternalSystem]:
        """根据ID获取外部系统"""
        return await external_system_crud.get(db, id=system_id)
    
    async def get_system_by_name(self, db: AsyncSession, *, name: str) -> Optional[ExternalSystem]:
        """根据名称获取外部系统"""
        return await external_system_crud.get_by_name(db, name=name)
    
    async def get_systems(self, db: AsyncSession, *, skip: int = 0, limit: int = 100) -> List[ExternalSystem]:
        """获取外部系统列表"""
        return await external_system_crud.get_multi(db, skip=skip, limit=limit)
    
    async def delete_system(self, db: AsyncSession, *, system_id: int) -> bool:
        """删除外部系统"""
        return await external_system_crud.remove(db, id=system_id)
    
    async def authenticate_system(self, db: AsyncSession, *, system_name: str) -> ExternalSystemAuthResponse:
        """对外部系统进行认证"""
        # 获取系统配置
        system = await external_system_crud.get_by_name(db, name=system_name)
        if not system:
            return ExternalSystemAuthResponse(
                system_id=0,
                system_name=system_name,
                success=False,
                message=f"系统 '{system_name}' 不存在"
            )
        
        if not system.is_active:
            return ExternalSystemAuthResponse(
                system_id=system.id,
                system_name=system.name,
                success=False,
                message=f"系统 '{system_name}' 已禁用"
            )
        
        try:
            # 创建API客户端
            api_client = ExternalAPIService(base_url=system.base_url)
            
            # 执行登录请求
            login_data = {
                "username": system.username,
                "password": system.password_hash  # 注意：这里需要解密密码，实际应用中需要安全处理
            }
            
            # 发送登录请求
            response = await api_client.post(system.auth_url or "/login", data=login_data)
            
            # 处理登录响应
            if response.get("success", False) or response.get("status_code", 0) in [200, 201]:
                # 登录成功，创建会话
                session_token = response.get("token") or response.get("access_token") or str(hashlib.md5(str(datetime.utcnow()).encode()).hexdigest())
                
                # 计算过期时间
                expires_at = datetime.utcnow() + timedelta(seconds=system.session_timeout)
                
                # 创建会话记录
                session_in = ExternalSystemSessionCreate(
                    system_id=system.id,
                    session_token=session_token,
                    session_data=response.get("data", {}),  # 只存储响应数据部分，避免存储复杂对象
                    expires_at=expires_at
                )
                
                session = None
                try:
                    session = await external_session_crud.create(db, obj_in=session_in)
                except Exception as session_error:
                    logger.error(f"创建会话失败: {str(session_error)}")
                    # 即使会话创建失败，也继续更新系统状态
                
                # 更新系统认证状态
                await external_system_crud.update_auth_status(db, db_obj=system, status="active")
                
                # 记录日志
                log_in = ExternalSystemLogCreate(
                    system_id=system.id,
                    operation="authenticate",
                    endpoint=system.auth_url or "/login",
                    request_method="POST",
                    request_data={"username": system.username},  # 不记录密码
                    response_status=200,
                    response_time=0,  # 实际应用中应计算响应时间
                    response_data=response.get("data", {}),
                    is_success=True,
                    error_message=None
                )
                await external_log_crud.create_log(db, log_in=log_in)
                
                return ExternalSystemAuthResponse(
                    system_id=system.id,
                    system_name=system.name,
                    success=True,
                    message="认证成功",
                    session_token=session_token,
                    expires_at=expires_at
                )
            else:
                # 登录失败
                error_msg = response.get("message", "认证失败")
                
                # 更新系统认证状态
                await external_system_crud.update_auth_status(db, db_obj=system, status="error", last_error=error_msg)
                
                # 记录日志
                log_in = ExternalSystemLogCreate(
                    system_id=system.id,
                    operation="authenticate",
                    endpoint=system.auth_url or "/login",
                    request_method="POST",
                    request_data=login_data,
                    response_status=401,
                    response_time=0,
                    response_data=response,
                    is_success=False,
                    error_message=error_msg
                )
                await external_log_crud.create_log(db, log_in=log_in)
                
                return ExternalSystemAuthResponse(
                    system_id=system.id,
                    system_name=system.name,
                    success=False,
                    message=error_msg
                )
                
        except Exception as e:
            error_msg = f"认证过程中发生错误: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            # 更新系统认证状态
            await external_system_crud.update_auth_status(db, db_obj=system, status="error", last_error=error_msg)
            
            # 记录日志
            log_in = ExternalSystemLogCreate(
                system_id=system.id,
                operation="authenticate",
                endpoint=system.auth_url or "/login",
                request_method="POST",
                request_data={"username": system.username},  # 不记录密码
                response_status=500,
                response_time=0,
                response_data={},
                is_success=False,
                error_message=error_msg
            )
            await external_log_crud.create_log(db, log_in=log_in)
            
            return ExternalSystemAuthResponse(
                system_id=system.id,
                system_name=system.name,
                success=False,
                message=error_msg
            )
    
    async def authenticate_all_systems(self, db: AsyncSession) -> ExternalSystemAuthBatchResponse:
        """批量认证所有启用的外部系统"""
        systems = await external_system_crud.get_active_systems(db)
        results = []
        success_count = 0
        
        for system in systems:
            result = await self.authenticate_system(db, system_name=system.name)
            results.append(result)
            if result.success:
                success_count += 1
        
        return ExternalSystemAuthBatchResponse(
            total_systems=len(systems),
            success_count=success_count,
            failed_count=len(systems) - success_count,
            results=results
        )
    
    async def get_system_status(self, db: AsyncSession, *, system_name: str) -> Optional[ExternalSystemAuthStatus]:
        """获取外部系统认证状态"""
        system = await external_system_crud.get_by_name(db, name=system_name)
        if not system:
            return None
        
        # 获取当前会话
        session = await external_session_crud.get_active_session(db, system_id=system.id)
        
        return ExternalSystemAuthStatus(
            system_id=system.id,
            system_name=system.name,
            status=system.auth_status,
            last_login_time=system.last_login_time,
            last_error=system.last_error,
            is_session_valid=session is not None,
            session_expires_at=session.expires_at if session else None
        )
    
    async def get_all_systems_status(self, db: AsyncSession) -> List[ExternalSystemAuthStatus]:
        """获取所有外部系统认证状态"""
        systems = await external_system_crud.get_active_systems(db)
        statuses = []
        
        for system in systems:
            status = await self.get_system_status(db, system_name=system.name)
            if status:
                statuses.append(status)
        
        return statuses
    
    async def call_external_api(
        self,
        db: AsyncSession,
        *,
        system_name: str,
        method: str = "GET",
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """调用外部系统API"""
        # 获取系统配置
        system = await external_system_crud.get_by_name(db, name=system_name)
        if not system:
            raise ValueError(f"系统 '{system_name}' 不存在")
        
        if not system.is_active:
            raise ValueError(f"系统 '{system_name}' 已禁用")
        
        # 获取有效会话
        session = await external_session_crud.get_active_session(db, system_id=system.id)
        if not session:
            # 尝试重新认证
            auth_result = await self.authenticate_system(db, system_name=system_name)
            if not auth_result.success:
                raise ValueError(f"系统 '{system_name}' 认证失败: {auth_result.message}")
            
            # 重新获取会话
            session = await external_session_crud.get_active_session(db, system_id=system.id)
            if not session:
                raise ValueError(f"系统 '{system_name}' 无法创建有效会话")
        
        try:
            # 创建API客户端
            api_client = ExternalAPIService(base_url=system.base_url)
            
            # 添加认证头
            auth_headers = headers or {}
            if session.session_token:
                auth_headers["Authorization"] = f"Bearer {session.session_token}"
            
            # 调用API
            start_time = datetime.utcnow()
            
            if method.upper() == "GET":
                response = await api_client.get(endpoint, params=params, headers=auth_headers)
            elif method.upper() == "POST":
                response = await api_client.post(endpoint, data=data, headers=auth_headers)
            elif method.upper() == "PUT":
                response = await api_client.put(endpoint, data=data, headers=auth_headers)
            elif method.upper() == "DELETE":
                response = await api_client.delete(endpoint, headers=auth_headers)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
            
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000  # 毫秒
            
            # 更新会话使用信息
            session.request_count += 1
            session.last_used_at = datetime.utcnow()
            await db.commit()
            
            # 记录日志
            log_in = ExternalSystemLogCreate(
                system_id=system.id,
                operation="api_call",
                endpoint=endpoint,
                request_method=method,
                request_data=data,
                response_status=response["status_code"],
                response_time=int(response_time),
                response_data=response["data"],
                is_success=True,
                error_message=None
            )
            await external_log_crud.create_log(db, log_in=log_in)
            
            return response
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"调用外部系统API失败: {error_msg}", exc_info=True)
            
            # 记录日志
            log_in = ExternalSystemLogCreate(
                system_id=system.id,
                operation="api_call",
                endpoint=endpoint,
                request_method=method,
                request_data=data,
                response_status=500,
                response_time=0,
                response_data={},
                is_success=False,
                error_message=error_msg
            )
            await external_log_crud.create_log(db, log_in=log_in)
            
            raise


# 创建服务实例
external_system_service = ExternalSystemService()