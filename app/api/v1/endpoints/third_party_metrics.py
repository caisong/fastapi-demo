"""
第三方指标管理端点
"""
from typing import Any, List, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.db.database import get_db
from app.models.user import User
from app.tasks.third_party_collector import collector
from app.core.task_queue import task_queue

router = APIRouter()


@router.post("/collect")
async def trigger_collection(
    current_user: User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    手动触发第三方数据收集
    """
    try:
        # 异步执行收集任务
        job_id = await task_queue.enqueue_task(
            "collect_third_party_metrics_task"
        )
        
        return {
            "message": "Third party data collection started",
            "job_id": job_id,
            "status": "queued"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start collection: {str(e)}"
        )


@router.post("/collect/{api_name}")
async def trigger_specific_collection(
    api_name: str,
    current_user: User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    手动触发特定API的数据收集
    """
    try:
        # 异步执行特定API收集任务
        job_id = await task_queue.enqueue_task(
            "collect_specific_api_task",
            api_name
        )
        
        return {
            "message": f"Data collection started for API: {api_name}",
            "job_id": job_id,
            "status": "queued"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start collection for {api_name}: {str(e)}"
        )


@router.get("/config")
async def get_apis_config(
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取API配置列表
    """
    try:
        configs = []
        for config in collector.apis_config:
            configs.append({
                "name": config["name"],
                "url": config["url"],
                "interval": config["interval"],
                "enabled": config.get("enabled", False),
                "params": config.get("params", {})
            })
        
        return {
            "apis": configs,
            "total": len(configs)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get API configs: {str(e)}"
        )


@router.put("/config/{api_name}/enable")
async def enable_api(
    api_name: str,
    current_user: User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    启用API收集
    """
    try:
        for config in collector.apis_config:
            if config["name"] == api_name:
                config["enabled"] = True
                return {
                    "message": f"API {api_name} enabled successfully",
                    "api_name": api_name,
                    "enabled": True
                }
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API {api_name} not found"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enable API {api_name}: {str(e)}"
        )


@router.put("/config/{api_name}/disable")
async def disable_api(
    api_name: str,
    current_user: User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    禁用API收集
    """
    try:
        for config in collector.apis_config:
            if config["name"] == api_name:
                config["enabled"] = False
                return {
                    "message": f"API {api_name} disabled successfully",
                    "api_name": api_name,
                    "enabled": False
                }
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API {api_name} not found"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disable API {api_name}: {str(e)}"
        )


@router.get("/status")
async def get_collection_status(
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取收集状态
    """
    try:
        enabled_apis = [config for config in collector.apis_config if config.get("enabled", False)]
        disabled_apis = [config for config in collector.apis_config if not config.get("enabled", False)]
        
        return {
            "total_apis": len(collector.apis_config),
            "enabled_apis": len(enabled_apis),
            "disabled_apis": len(disabled_apis),
            "enabled_api_names": [api["name"] for api in enabled_apis],
            "disabled_api_names": [api["name"] for api in disabled_apis]
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get collection status: {str(e)}"
        )