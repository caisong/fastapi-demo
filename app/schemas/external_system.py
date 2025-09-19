"""
外部系统认证配置的Pydantic模型
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ExternalSystemBase(BaseModel):
    """外部系统基础模型"""
    name: str = Field(..., max_length=100, description="系统名称")
    display_name: Optional[str] = Field(None, max_length=200, description="显示名称")
    base_url: str = Field(..., max_length=500, description="系统基础URL")
    auth_url: Optional[str] = Field(None, max_length=500, description="认证URL")
    username: str = Field(..., max_length=100, description="登录用户名")
    auth_type: str = Field(default="username_password", description="认证类型")
    session_timeout: int = Field(default=3600, description="会话超时时间(秒)")
    max_retry_count: int = Field(default=3, description="最大重试次数")
    is_active: bool = Field(default=True, description="是否启用")
    extra_config: Optional[Dict[str, Any]] = Field(None, description="扩展配置信息")


class ExternalSystemCreate(ExternalSystemBase):
    """创建外部系统配置"""
    password: str = Field(..., description="登录密码")


class ExternalSystemUpdate(BaseModel):
    """更新外部系统配置"""
    display_name: Optional[str] = Field(None, max_length=200)
    base_url: Optional[str] = Field(None, max_length=500)
    auth_url: Optional[str] = Field(None, max_length=500)
    username: Optional[str] = Field(None, max_length=100)
    password: Optional[str] = Field(None, description="登录密码")
    auth_type: Optional[str] = Field(None)
    session_timeout: Optional[int] = Field(None)
    max_retry_count: Optional[int] = Field(None)
    is_active: Optional[bool] = Field(None)
    extra_config: Optional[Dict[str, Any]] = Field(None)


class ExternalSystemInDBBase(ExternalSystemBase):
    """数据库返回的外部系统基础模型"""
    id: int
    last_login_time: Optional[datetime] = None
    last_error: Optional[str] = None
    auth_status: str = "inactive"
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExternalSystem(ExternalSystemInDBBase):
    """外部系统模型"""
    pass


class ExternalSystemWithPassword(ExternalSystemInDBBase):
    """包含密码的外部系统模型(仅内部使用)"""
    password_hash: str


# 会话相关模型
class ExternalSystemSessionBase(BaseModel):
    """外部系统会话基础模型"""
    system_id: int
    session_token: Optional[str] = None
    session_data: Optional[Dict[str, Any]] = None
    is_valid: bool = True
    expires_at: Optional[datetime] = None


class ExternalSystemSessionCreate(ExternalSystemSessionBase):
    """创建外部系统会话"""
    pass


class ExternalSystemSessionUpdate(BaseModel):
    """更新外部系统会话"""
    session_token: Optional[str] = None
    session_data: Optional[Dict[str, Any]] = None
    is_valid: Optional[bool] = None
    expires_at: Optional[datetime] = None


class ExternalSystemSessionInDB(ExternalSystemSessionBase):
    """数据库返回的外部系统会话模型"""
    id: int
    request_count: int
    last_used_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExternalSystemSession(ExternalSystemSessionInDB):
    """外部系统会话模型"""
    pass


# 日志相关模型
class ExternalSystemLogBase(BaseModel):
    """外部系统日志基础模型"""
    system_id: int
    operation: str
    endpoint: str
    request_method: str
    request_data: Optional[Dict[str, Any]] = None
    response_status: Optional[int] = None
    response_time: Optional[int] = None
    response_data: Optional[Dict[str, Any]] = None
    is_success: bool
    error_message: Optional[str] = None


class ExternalSystemLogCreate(ExternalSystemLogBase):
    """创建外部系统日志"""
    pass


class ExternalSystemLogInDB(ExternalSystemLogBase):
    """数据库返回的外部系统日志模型"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ExternalSystemLog(ExternalSystemLogInDB):
    """外部系统日志模型"""
    pass


# 认证响应模型
class ExternalSystemAuthResponse(BaseModel):
    """外部系统认证响应"""
    system_id: int
    system_name: str
    success: bool
    message: str
    session_token: Optional[str] = None
    expires_at: Optional[datetime] = None


class ExternalSystemAuthStatus(BaseModel):
    """外部系统认证状态"""
    system_id: int
    system_name: str
    status: str  # inactive/active/error
    last_login_time: Optional[datetime] = None
    last_error: Optional[str] = None
    is_session_valid: bool
    session_expires_at: Optional[datetime] = None


class ExternalSystemAuthBatchResponse(BaseModel):
    """批量认证响应"""
    total_systems: int
    success_count: int
    failed_count: int
    results: List[ExternalSystemAuthResponse]