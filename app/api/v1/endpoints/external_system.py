"""
外部系统认证管理API端点
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.schemas.external_system import (
    ExternalSystem, ExternalSystemCreate, ExternalSystemUpdate,
    ExternalSystemAuthResponse, ExternalSystemAuthStatus,
    ExternalSystemAuthBatchResponse
)
from app.services.external_system import external_system_service
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=ExternalSystem, status_code=status.HTTP_201_CREATED)
async def create_external_system(
    system_in: ExternalSystemCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser)
) -> ExternalSystem:
    """
    创建外部系统配置 (仅超级用户)
    """
    # 检查系统名称是否已存在
    existing_system = await external_system_service.get_system_by_name(db, name=system_in.name)
    if existing_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"系统 '{system_in.name}' 已存在"
        )
    
    return await external_system_service.create_system(db, system_in=system_in)


@router.get("/", response_model=List[ExternalSystem])
async def list_external_systems(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser)
) -> List[ExternalSystem]:
    """
    获取外部系统列表 (仅超级用户)
    """
    return await external_system_service.get_systems(db, skip=skip, limit=limit)


@router.get("/{system_id}", response_model=ExternalSystem)
async def get_external_system(
    system_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser)
) -> ExternalSystem:
    """
    获取外部系统详情 (仅超级用户)
    """
    system = await external_system_service.get_system(db, system_id=system_id)
    if not system:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="系统不存在"
        )
    return system


@router.put("/{system_id}", response_model=ExternalSystem)
async def update_external_system(
    system_id: int,
    system_in: ExternalSystemUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser)
) -> ExternalSystem:
    """
    更新外部系统配置 (仅超级用户)
    """
    system = await external_system_service.get_system(db, system_id=system_id)
    if not system:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="系统不存在"
        )
    
    return await external_system_service.update_system(db, db_obj=system, system_in=system_in)


@router.delete("/{system_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_external_system(
    system_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser)
) -> None:
    """
    删除外部系统配置 (仅超级用户)
    """
    system = await external_system_service.get_system(db, system_id=system_id)
    if not system:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="系统不存在"
        )
    
    await external_system_service.delete_system(db, system_id=system_id)


@router.post("/{system_name}/authenticate", response_model=ExternalSystemAuthResponse)
async def authenticate_external_system(
    system_name: str,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser)
) -> ExternalSystemAuthResponse:
    """
    对外部系统进行认证 (仅超级用户)
    """
    result = await external_system_service.authenticate_system(db, system_name=system_name)
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message
        )
    return result


@router.post("/authenticate-all", response_model=ExternalSystemAuthBatchResponse)
async def authenticate_all_external_systems(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser)
) -> ExternalSystemAuthBatchResponse:
    """
    批量认证所有启用的外部系统 (仅超级用户)
    """
    return await external_system_service.authenticate_all_systems(db)


@router.get("/{system_name}/status", response_model=ExternalSystemAuthStatus)
async def get_external_system_status(
    system_name: str,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> ExternalSystemAuthStatus:
    """
    获取外部系统认证状态
    """
    status = await external_system_service.get_system_status(db, system_name=system_name)
    if not status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"系统 '{system_name}' 不存在"
        )
    return status


@router.get("/status", response_model=List[ExternalSystemAuthStatus])
async def get_all_external_systems_status(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> List[ExternalSystemAuthStatus]:
    """
    获取所有外部系统认证状态
    """
    return await external_system_service.get_all_systems_status(db)