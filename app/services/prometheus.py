"""
Prometheus Query Service
Provides functionality to query metrics from Prometheus server
"""
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
import asyncio
import aiohttp
from prometheus_api_client import PrometheusConnect

from app.core.config import settings

logger = logging.getLogger(__name__)


class PrometheusService:
    """Service for querying Prometheus metrics"""
    
    def __init__(self):
        self.prometheus_url = settings.PROMETHEUS_SERVER_URL
        self.timeout = settings.PROMETHEUS_QUERY_TIMEOUT
        self._client: Optional[PrometheusConnect] = None
    
    @property
    def client(self) -> PrometheusConnect:
        """Get Prometheus client instance"""
        if self._client is None:
            self._client = PrometheusConnect(
                url=self.prometheus_url,
                disable_ssl=True
            )
        return self._client
    
    async def health_check(self) -> Dict[str, Any]:iax
        """Check if Prometheus server is healthy"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(f"{self.prometheus_url}/-/healthy") as response:
                    if response.status == 200:
                        return {"status": "healthy", "prometheus_url": self.prometheus_url}
                    else:
                        return {"status": "unhealthy", "error": f"HTTP {response.status}"}
        except Exception as e:
            logger.error(f"Prometheus health check failed: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def query_instant(self, query: str) -> Dict[str, Any]:
        """Execute an instant query against Prometheus"""
        try:
            # Run in thread pool since prometheus-api-client is synchronous
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                lambda: self.client.custom_query(query=query)
            )
            return {
                "status": "success",
                "query": query,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Prometheus instant query failed: {str(e)}")
            return {
                "status": "error",
                "query": query,
                "error": str(e)
            }
    
    async def query_range(
        self, 
        query: str, 
        start_time: datetime, 
        end_time: datetime, 
        step: str = "15s"
    ) -> Dict[str, Any]:
        """Execute a range query against Prometheus"""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                lambda: self.client.custom_query_range(
                    query=query,
                    start_time=start_time,
                    end_time=end_time,
                    step=step
                )
            )
            return {
                "status": "success",
                "query": query,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "step": step,
                "result": result
            }
        except Exception as e:
            logger.error(f"Prometheus range query failed: {str(e)}")
            return {
                "status": "error",
                "query": query,
                "error": str(e)
            }
    
    async def get_metrics_list(self) -> Dict[str, Any]:
        """Get list of available metrics"""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                lambda: self.client.all_metrics()
            )
            return {
                "status": "success",
                "metrics": result,
                "count": len(result) if result else 0
            }
        except Exception as e:
            logger.error(f"Failed to get metrics list: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def get_targets(self) -> Dict[str, Any]:
        """Get Prometheus targets information"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"{self.prometheus_url}/api/v1/targets") as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "status": "success",
                            "targets": data.get("data", {})
                        }
                    else:
                        return {"status": "error", "error": f"HTTP {response.status}"}
        except Exception as e:
            logger.error(f"Failed to get targets: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def get_application_metrics(self) -> Dict[str, Any]:
        """Get common application metrics"""
        queries = {
            "http_requests_total": "sum(rate(http_requests_total[5m])) by (method, endpoint)",
            "http_request_duration": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "memory_usage": "process_resident_memory_bytes",
            "cpu_usage": "rate(process_cpu_seconds_total[5m])",
            "active_connections": "http_requests_currently_active",
        }
        
        results = {}
        for metric_name, query in queries.items():
            result = await self.query_instant(query)
            results[metric_name] = result
        
        return {
            "status": "success",
            "application_metrics": results,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get system-level metrics"""
        queries = {
            "python_gc_collections": "python_gc_objects_collected_total",
            "python_info": "python_info",
            "process_start_time": "process_start_time_seconds",
            "uptime": "time() - process_start_time_seconds"
        }
        
        results = {}
        for metric_name, query in queries.items():
            result = await self.query_instant(query)
            results[metric_name] = result
        
        return {
            "status": "success",
            "system_metrics": results,
            "timestamp": datetime.utcnow().isoformat()
        }


# Create service instance
prometheus_service = PrometheusService()