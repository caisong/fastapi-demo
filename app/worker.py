"""
ARQ worker configuration and startup
"""
import logging
from arq import create_pool, cron
from arq.connections import RedisSettings
from arq.worker import Worker

from app.core.config import settings
from app.tasks import TASK_FUNCTIONS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def startup(ctx):
    """Worker startup function"""
    logger.info("ARQ Worker starting up...")
    ctx['startup_time'] = "Worker started successfully"


async def shutdown(ctx):
    """Worker shutdown function"""
    logger.info("ARQ Worker shutting down...")


class WorkerSettings:
    """ARQ Worker settings"""
    
    # Redis connection
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    
    # Task functions
    functions = TASK_FUNCTIONS
    
    # Worker configuration
    on_startup = startup
    on_shutdown = shutdown
    
    # Performance settings
    max_jobs = 10
    job_timeout = 300  # 5 minutes
    keep_result = 3600  # 1 hour
    
    # Cron jobs (periodic tasks) - commented out for now
    # You can add them later using the correct ARQ syntax
    # cron_jobs = []


if __name__ == '__main__':
    """Run ARQ worker"""
    import asyncio
    from arq.worker import run_worker
    
    async def main():
        await run_worker(WorkerSettings)
    
    asyncio.run(main())