"""
Pydantic schemas for Prometheus API endpoints
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class PrometheusQueryRequest(BaseModel):
    """Schema for Prometheus instant query request"""
    query: str = Field(..., description="PromQL query string")
    time: Optional[datetime] = Field(None, description="Evaluation timestamp")


class PrometheusRangeQueryRequest(BaseModel):
    """Schema for Prometheus range query request"""
    query: str = Field(..., description="PromQL query string")
    start: datetime = Field(..., description="Start timestamp")
    end: datetime = Field(..., description="End timestamp")
    step: str = Field("15s", description="Query resolution step width")


class PrometheusResponse(BaseModel):
    """Base schema for Prometheus responses"""
    status: str = Field(..., description="Query status")
    timestamp: Optional[str] = Field(None, description="Response timestamp")


class PrometheusQueryResponse(PrometheusResponse):
    """Schema for Prometheus query response"""
    query: Optional[str] = Field(None, description="Original query")
    result: Optional[List[Dict[str, Any]]] = Field(None, description="Query result")
    error: Optional[str] = Field(None, description="Error message if any")


class PrometheusRangeQueryResponse(PrometheusResponse):
    """Schema for Prometheus range query response"""
    query: Optional[str] = Field(None, description="Original query")
    start_time: Optional[str] = Field(None, description="Query start time")
    end_time: Optional[str] = Field(None, description="Query end time")
    step: Optional[str] = Field(None, description="Query step")
    result: Optional[List[Dict[str, Any]]] = Field(None, description="Query result")
    error: Optional[str] = Field(None, description="Error message if any")


class PrometheusHealthResponse(PrometheusResponse):
    """Schema for Prometheus health check response"""
    prometheus_url: Optional[str] = Field(None, description="Prometheus server URL")
    error: Optional[str] = Field(None, description="Error message if any")


class PrometheusMetricsListResponse(PrometheusResponse):
    """Schema for Prometheus metrics list response"""
    metrics: Optional[List[str]] = Field(None, description="List of available metrics")
    count: Optional[int] = Field(None, description="Number of metrics")
    error: Optional[str] = Field(None, description="Error message if any")


class PrometheusTargetsResponse(PrometheusResponse):
    """Schema for Prometheus targets response"""
    targets: Optional[Dict[str, Any]] = Field(None, description="Targets information")
    error: Optional[str] = Field(None, description="Error message if any")


class ApplicationMetricsResponse(PrometheusResponse):
    """Schema for application metrics response"""
    application_metrics: Optional[Dict[str, Any]] = Field(None, description="Application metrics data")


class SystemMetricsResponse(PrometheusResponse):
    """Schema for system metrics response"""
    system_metrics: Optional[Dict[str, Any]] = Field(None, description="System metrics data")