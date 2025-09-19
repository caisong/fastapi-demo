"""
外部系统认证中间件
"""
import logging
from typing import Optional, Callable
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.services.external_system import external_system_service
from app.db.database import get_db

logger = logging.getLogger(__name__)


class ExternalSystemAuthMiddleware(BaseHTTPMiddleware):
    """
    外部系统认证中间件
    自动处理外部系统的认证和会话管理
    """
    
    def __init__(self, app, exclude_paths: Optional[list] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/redoc", 
            "/openapi.json",
            "/health",
            "/metrics",
            "/api/v1/auth/register",
            "/api/v1/auth/login",
            "/api/v1/auth/login-json",
            "/api/v1/auth/refresh",
        ]
    
    async def dispatch(self, request: Request, call_next: Callable):
        # 跳过不需要认证的路径
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # 检查是否需要外部系统认证
        # 这里可以根据请求路径或头部信息来判断
        external_system_name = request.headers.get("X-External-System")
        
        if external_system_name:
            try:
                # 获取数据库会话
                async for db in get_db():
                    # 检查外部系统状态
                    system_status = await external_system_service.get_system_status(
                        db, system_name=external_system_name
                    )
                    
                    if not system_status:
                        return JSONResponse(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            content={"detail": f"外部系统 '{external_system_name}' 不存在"}
                        )
                    
                    # 如果会话无效，尝试重新认证
                    if not system_status.is_session_valid:
                        auth_result = await external_system_service.authenticate_system(
                            db, system_name=external_system_name
                        )
                        
                        if not auth_result.success:
                            return JSONResponse(
                                status_code=status.HTTP_401_UNAUTHORIZED,
                                content={"detail": f"外部系统认证失败: {auth_result.message}"}
                            )
                    
                    # 将外部系统信息添加到请求状态中
                    request.state.external_system_name = external_system_name
                    request.state.external_system_status = system_status
                    break
                    
            except Exception as e:
                logger.error(f"外部系统认证中间件错误: {str(e)}")
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={"detail": "外部系统认证处理错误"}
                )
        
        # 继续处理请求
        response = await call_next(request)
        return response


class ExternalSystemRateLimitMiddleware(BaseHTTPMiddleware):
    """
    外部系统调用频率限制中间件
    防止对外部系统的过度调用
    """
    
    def __init__(self, app, calls_per_minute: int = 60):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.call_counts = {}  # system_name -> [timestamp]
    
    async def dispatch(self, request: Request, call_next: Callable):
        # 检查是否是外部系统API调用
        external_system_name = getattr(request.state, "external_system_name", None)
        
        if external_system_name:
            import time
            current_time = time.time()
            
            # 清理过期的调用记录
            if external_system_name in self.call_counts:
                self.call_counts[external_system_name] = [
                    timestamp for timestamp in self.call_counts[external_system_name]
                    if current_time - timestamp < 60  # 保留1分钟内的记录
                ]
            else:
                self.call_counts[external_system_name] = []
            
            # 检查调用频率
            if len(self.call_counts[external_system_name]) >= self.calls_per_minute:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "对外部系统的调用频率超出限制"}
                )
            
            # 记录本次调用
            self.call_counts[external_system_name].append(current_time)
        
        # 继续处理请求
        response = await call_next(request)
        return response


# 便捷函数用于在路由中检查外部系统认证状态
async def check_external_system_auth(request: Request, system_name: str) -> bool:
    """
    检查特定外部系统的认证状态
    
    Args:
        request: FastAPI请求对象
        system_name: 外部系统名称
        
    Returns:
        bool: 认证是否有效
    """
    external_system_name = getattr(request.state, "external_system_name", None)
    external_system_status = getattr(request.state, "external_system_status", None)
    
    if external_system_name == system_name and external_system_status:
        return external_system_status.is_session_valid
    
    return False


# 便捷函数用于获取外部系统会话令牌
async def get_external_system_token(request: Request, system_name: str) -> Optional[str]:
    """
    获取外部系统的会话令牌
    
    Args:
        request: FastAPI请求对象
        system_name: 外部系统名称
        
    Returns:
        Optional[str]: 会话令牌，如果不可用则返回None
    """
    # 这里需要从数据库或缓存中获取实际的会话令牌
    # 简化实现，实际应用中需要更复杂的逻辑
    return None