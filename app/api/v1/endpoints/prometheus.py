"""
Prometheus API endpoints for querying metrics
"""
from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse

from app.services.prometheus import prometheus_service
from app.schemas.prometheus import (
    PrometheusQueryRequest,
    PrometheusRangeQueryRequest,
    PrometheusQueryResponse,
    PrometheusRangeQueryResponse,
    PrometheusHealthResponse,
    PrometheusMetricsListResponse,
    PrometheusTargetsResponse,
    ApplicationMetricsResponse,
    SystemMetricsResponse
)
from app.api.deps import get_current_active_user
from app.models.user import User

router = APIRouter()


@router.get("/health", response_model=PrometheusHealthResponse)
async def prometheus_health():
    """Check Prometheus server health"""
    result = await prometheus_service.health_check()
    return JSONResponse(content=result)


@router.post("/query", response_model=PrometheusQueryResponse)
async def prometheus_query(
    request: PrometheusQueryRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Execute an instant query against Prometheus"""
    result = await prometheus_service.query_instant(request.query)
    return JSONResponse(content=result)


@router.get("/query", response_model=PrometheusQueryResponse)
async def prometheus_query_get(
    query: str = Query(..., description="PromQL query string"),
    current_user: User = Depends(get_current_active_user)
):
    """Execute an instant query against Prometheus (GET method)"""
    result = await prometheus_service.query_instant(query)
    return JSONResponse(content=result)


@router.post("/query_range", response_model=PrometheusRangeQueryResponse)
async def prometheus_query_range(
    request: PrometheusRangeQueryRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Execute a range query against Prometheus"""
    result = await prometheus_service.query_range(
        query=request.query,
        start_time=request.start,
        end_time=request.end,
        step=request.step
    )
    return JSONResponse(content=result)


@router.get("/query_range", response_model=PrometheusRangeQueryResponse)
async def prometheus_query_range_get(
    query: str = Query(..., description="PromQL query string"),
    start: datetime = Query(..., description="Start timestamp"),
    end: datetime = Query(..., description="End timestamp"),
    step: str = Query("15s", description="Query resolution step width"),
    current_user: User = Depends(get_current_active_user)
):
    """Execute a range query against Prometheus (GET method)"""
    result = await prometheus_service.query_range(
        query=query,
        start_time=start,
        end_time=end,
        step=step
    )
    return JSONResponse(content=result)


@router.get("/metrics", response_model=PrometheusMetricsListResponse)
async def get_prometheus_metrics(
    current_user: User = Depends(get_current_active_user)
):
    """Get list of available metrics from Prometheus"""
    result = await prometheus_service.get_metrics_list()
    return JSONResponse(content=result)


@router.get("/targets", response_model=PrometheusTargetsResponse)
async def get_prometheus_targets(
    current_user: User = Depends(get_current_active_user)
):
    """Get Prometheus targets information"""
    result = await prometheus_service.get_targets()
    return JSONResponse(content=result)


@router.get("/application_metrics", response_model=ApplicationMetricsResponse)
async def get_application_metrics(
    current_user: User = Depends(get_current_active_user)
):
    """Get common application metrics"""
    result = await prometheus_service.get_application_metrics()
    return JSONResponse(content=result)


@router.get("/system_metrics", response_model=SystemMetricsResponse)
async def get_system_metrics(
    current_user: User = Depends(get_current_active_user)
):
    """Get system-level metrics"""
    result = await prometheus_service.get_system_metrics()
    return JSONResponse(content=result)


# Convenience endpoints for common queries
@router.get("/quick/cpu_usage")
async def get_cpu_usage(
    current_user: User = Depends(get_current_active_user)
):
    """Get current CPU usage"""
    result = await prometheus_service.query_instant("rate(process_cpu_seconds_total[5m])")
    return JSONResponse(content=result)


@router.get("/quick/memory_usage")
async def get_memory_usage(
    current_user: User = Depends(get_current_active_user)
):
    """Get current memory usage"""
    result = await prometheus_service.query_instant("process_resident_memory_bytes")
    return JSONResponse(content=result)


@router.get("/quick/http_requests_rate")
async def get_http_requests_rate(
    current_user: User = Depends(get_current_active_user)
):
    """Get HTTP requests rate (last 5 minutes)"""
    result = await prometheus_service.query_instant("sum(rate(http_requests_total[5m]))")
    return JSONResponse(content=result)


@router.get("/quick/uptime")
async def get_application_uptime(
    current_user: User = Depends(get_current_active_user)
):
    """Get application uptime"""
    result = await prometheus_service.query_instant("time() - process_start_time_seconds")
    return JSONResponse(content=result)