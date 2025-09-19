"""
外部系统认证配置模型
"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON
from sqlalchemy.sql import func

from app.db.database import Base


class ExternalSystem(Base):
    """外部系统配置表"""
    __tablename__ = "external_systems"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, comment="系统名称")
    display_name = Column(String(200), comment="显示名称")
    base_url = Column(String(500), comment="系统基础URL")
    auth_url = Column(String(500), comment="认证URL")
    username = Column(String(100), comment="登录用户名")
    password_hash = Column(String(500), comment="加密后的密码")
    
    # 认证相关字段
    auth_type = Column(String(50), default="username_password", comment="认证类型")
    session_timeout = Column(Integer, default=3600, comment="会话超时时间(秒)")
    max_retry_count = Column(Integer, default=3, comment="最大重试次数")
    
    # 状态字段
    is_active = Column(Boolean, default=True, comment="是否启用")
    last_login_time = Column(DateTime, comment="最后登录时间")
    last_error = Column(Text, comment="最后错误信息")
    auth_status = Column(String(20), default="inactive", comment="认证状态: inactive/active/error")
    
    # 扩展配置
    extra_config = Column(JSON, comment="扩展配置信息")
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<ExternalSystem(name='{self.name}', status='{self.auth_status}')>"


class ExternalSystemSession(Base):
    """外部系统会话管理表"""
    __tablename__ = "external_system_sessions"

    id = Column(Integer, primary_key=True, index=True)
    system_id = Column(Integer, index=True, comment="外部系统ID")
    session_token = Column(String(1000), comment="会话令牌")
    session_data = Column(JSON, comment="会话数据")
    
    # 会话状态
    is_valid = Column(Boolean, default=True, comment="会话是否有效")
    expires_at = Column(DateTime, comment="过期时间")
    
    # 统计信息
    request_count = Column(Integer, default=0, comment="请求次数")
    last_used_at = Column(DateTime, server_default=func.now(), comment="最后使用时间")
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<ExternalSystemSession(system_id={self.system_id}, valid={self.is_valid})>"


class ExternalSystemLog(Base):
    """外部系统调用日志表"""
    __tablename__ = "external_system_logs"

    id = Column(Integer, primary_key=True, index=True)
    system_id = Column(Integer, index=True, comment="外部系统ID")
    operation = Column(String(100), comment="操作类型")
    endpoint = Column(String(500), comment="调用端点")
    
    # 请求信息
    request_method = Column(String(10), comment="请求方法")
    request_data = Column(JSON, comment="请求数据")
    
    # 响应信息
    response_status = Column(Integer, comment="响应状态码")
    response_time = Column(Integer, comment="响应时间(毫秒)")
    response_data = Column(JSON, comment="响应数据(截断)")
    
    # 结果状态
    is_success = Column(Boolean, comment="是否成功")
    error_message = Column(Text, comment="错误信息")
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")

    def __repr__(self):
        return f"<ExternalSystemLog(system_id={self.system_id}, operation='{self.operation}', success={self.is_success})>"