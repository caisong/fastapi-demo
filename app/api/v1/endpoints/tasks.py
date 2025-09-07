"""
Task management endpoints
"""
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.api import deps
from app.db.database import get_db
from app.models.user import User
from app.core.task_queue import task_queue
from app.core.task_monitor import task_monitor
from app.tasks.helpers import (
    generate_report_task,
    send_batch_notifications_task,
    cleanup_old_data_task
)

router = APIRouter()


class ReportRequest(BaseModel):
    report_type: str
    

class NotificationRequest(BaseModel):
    message: str
    user_emails: List[str]


@router.post("/reports/generate")
async def generate_report(
    report_type: str,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Generate a report for the current user
    """
    if report_type not in ["user_activity", "items_summary", "monthly_report"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid report type"
        )
    
    job_id = await generate_report_task.delay(current_user.id, report_type)
    
    return {
        "message": f"Report generation started for {report_type}",
        "job_id": job_id,
        "status": "queued"
    }


@router.post("/notifications/batch")
async def send_batch_notifications(
    request: NotificationRequest,
    current_user: User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Send batch notifications (admin only)
    """
    if len(request.user_emails) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Email list cannot be empty"
        )
    
    if len(request.user_emails) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot send to more than 100 users at once"
        )
    
    job_id = await send_batch_notifications_task.delay(request.user_emails, request.message)
    
    return {
        "message": f"Batch notification started for {len(request.user_emails)} users",
        "job_id": job_id,
        "recipient_count": len(request.user_emails),
        "status": "queued"
    }


@router.post("/cleanup")
async def trigger_cleanup(
    current_user: User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Manually trigger data cleanup (admin only)
    """
    job_id = await cleanup_old_data_task.delay()
    
    return {
        "message": "Data cleanup task started",
        "job_id": job_id,
        "status": "queued"
    }


@router.get("/jobs/{job_id}/status")
async def get_job_status(
    job_id: str,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get status of a background job
    """
    status_info = await task_queue.get_job_status(job_id)
    
    if status_info["status"] == "not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    return status_info


@router.get("/queue/info")
async def get_queue_info(
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get task queue information
    """
    return await task_monitor.get_queue_info()


@router.get("/jobs/recent")
async def get_recent_jobs(
    limit: int = 10,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get recent jobs
    """
    if limit > 50:
        limit = 50
    
    return await task_monitor.get_recent_jobs(limit)