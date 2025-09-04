"""
ARQ task queue configuration and setup
"""
import asyncio
from typing import Any, Dict
from arq import create_pool
from arq.connections import RedisSettings
from redis.asyncio import Redis

from app.core.config import settings


# Redis settings for ARQ
redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)


async def get_redis_pool():
    """Get Redis connection pool for ARQ"""
    return await create_pool(redis_settings)


async def get_redis_client():
    """Get Redis client for direct Redis operations"""
    return Redis.from_url(settings.REDIS_URL)


class TaskQueue:
    """ARQ task queue wrapper"""
    
    def __init__(self):
        self.pool = None
        self.redis = None
    
    async def startup(self):
        """Initialize Redis connections"""
        try:
            self.pool = await get_redis_pool()
            self.redis = await get_redis_client()
            print("✅ Task queue initialized successfully")
        except Exception as e:
            print(f"⚠️ Task queue initialization failed: {e}")
            print("📝 Tasks will be executed synchronously")
            self.pool = None
            self.redis = None
    
    async def shutdown(self):
        """Close Redis connections"""
        if self.pool:
            await self.pool.aclose()
        if self.redis:
            await self.redis.aclose()
    
    async def enqueue_task(self, function_name: str, *args, **kwargs) -> str:
        """Enqueue a task for processing"""
        if not self.pool:
            # Execute task synchronously if Redis is not available
            print(f"💪 Executing task synchronously: {function_name}")
            try:
                # Import and execute task function directly
                from app.tasks import TASK_FUNCTIONS
                task_func = None
                for func in TASK_FUNCTIONS:
                    if func.__name__ == function_name:
                        task_func = func
                        break
                
                if task_func:
                    # Execute with dummy context
                    result = await task_func({}, *args, **kwargs)
                    print(f"✅ Task completed: {result}")
                    return "sync_execution"
                else:
                    print(f"❌ Task function not found: {function_name}")
                    return "error_not_found"
            except Exception as e:
                print(f"❌ Task execution failed: {e}")
                return "error_execution"
        
        job = await self.pool.enqueue_job(function_name, *args, **kwargs)
        return job.job_id
    
    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get status of a job"""
        if job_id == "sync_execution":
            return {
                "job_id": job_id,
                "status": "completed",
                "result": "Executed synchronously",
                "message": "Task was executed synchronously due to Redis unavailability"
            }
        
        if job_id.startswith("error_"):
            return {
                "job_id": job_id,
                "status": "failed",
                "result": "Task execution failed",
                "message": "Task failed during synchronous execution"
            }
        
        if not self.redis:
            return {
                "job_id": job_id,
                "status": "unavailable",
                "message": "Task queue not available"
            }
        
        job_info = await self.redis.hgetall(f"arq:job:{job_id}")
        if job_info:
            return {
                "job_id": job_id,
                "status": job_info.get(b"status", b"").decode(),
                "result": job_info.get(b"result", b"").decode(),
                "enqueue_time": job_info.get(b"enqueue_time", b"").decode(),
                "start_time": job_info.get(b"start_time", b"").decode(),
                "finish_time": job_info.get(b"finish_time", b"").decode(),
            }
        return {"job_id": job_id, "status": "not_found"}


# Global task queue instance
task_queue = TaskQueue()