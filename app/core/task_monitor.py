"""
Task monitoring and management utilities
"""
from typing import List, Dict, Any
from redis.asyncio import Redis
from app.core.config import settings


class TaskMonitor:
    """Monitor and manage ARQ tasks"""
    
    def __init__(self):
        self.redis = None
    
    async def get_redis(self):
        """Get Redis connection"""
        if not self.redis:
            self.redis = Redis.from_url(settings.REDIS_URL)
        return self.redis
    
    async def get_queue_info(self) -> Dict[str, Any]:
        """Get general queue information"""
        try:
            redis = await self.get_redis()
            
            # Get queue length
            queue_length = await redis.llen("arq:queue")
            
            # Get worker information (this is simplified)
            worker_keys = await redis.keys("arq:worker:*")
            active_workers = len(worker_keys)
            
            return {
                "queue_length": queue_length,
                "active_workers": active_workers,
                "redis_connected": True,
                "mode": "async"
            }
        except Exception as e:
            return {
                "queue_length": 0,
                "active_workers": 0,
                "redis_connected": False,
                "mode": "sync_fallback",
                "error": str(e)
            }
    
    async def get_recent_jobs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent job information"""
        try:
            redis = await self.get_redis()
            
            # Get job keys (this is a simplified implementation)
            job_keys = await redis.keys("arq:job:*")
            
            jobs = []
            for key in job_keys[:limit]:
                job_data = await redis.hgetall(key)
                if job_data:
                    job_id = key.decode().split(":")[-1]
                    jobs.append({
                        "job_id": job_id,
                        "status": job_data.get(b"status", b"").decode(),
                        "function": job_data.get(b"function", b"").decode(),
                        "enqueue_time": job_data.get(b"enqueue_time", b"").decode(),
                    })
            
            return sorted(jobs, key=lambda x: x.get("enqueue_time", ""), reverse=True)
        except Exception:
            return [{
                "job_id": "sync_mode",
                "status": "info",
                "function": "Task queue in sync mode",
                "enqueue_time": "N/A",
                "message": "Redis not available, tasks execute synchronously"
            }]
    
    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()


# Global monitor instance
task_monitor = TaskMonitor()