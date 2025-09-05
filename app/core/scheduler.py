"""
定时任务调度器
使用ARQ的cron功能实现定时任务
"""
import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

from app.core.task_queue import task_queue
from app.tasks.third_party_collector import collect_third_party_metrics_task

logger = logging.getLogger(__name__)


class Scheduler:
    """定时任务调度器"""
    
    def __init__(self):
        self.running = False
        self.tasks = []
    
    async def start(self):
        """启动调度器"""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        self.running = True
        logger.info("Starting scheduler...")
        
        # 启动定时任务
        await self._start_cron_tasks()
    
    async def stop(self):
        """停止调度器"""
        if not self.running:
            logger.warning("Scheduler is not running")
            return
        
        self.running = False
        logger.info("Stopping scheduler...")
        
        # 取消所有任务
        for task in self.tasks:
            task.cancel()
        
        # 等待任务完成
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        self.tasks.clear()
        logger.info("Scheduler stopped")
    
    async def _start_cron_tasks(self):
        """启动定时任务"""
        # 第三方数据收集任务 - 每5分钟执行一次
        task1 = asyncio.create_task(
            self._run_periodic_task(
                collect_third_party_metrics_task,
                interval=300,  # 5分钟
                task_name="third_party_metrics_collection"
            )
        )
        self.tasks.append(task1)
        
        # 可以添加更多定时任务
        # task2 = asyncio.create_task(
        #     self._run_periodic_task(
        #         another_task,
        #         interval=600,  # 10分钟
        #         task_name="another_periodic_task"
        #     )
        # )
        # self.tasks.append(task2)
    
    async def _run_periodic_task(self, task_func, interval: int, task_name: str):
        """
        运行周期性任务
        
        Args:
            task_func: 任务函数
            interval: 间隔时间（秒）
            task_name: 任务名称
        """
        logger.info(f"Starting periodic task: {task_name} (interval: {interval}s)")
        
        while self.running:
            try:
                # 执行任务
                logger.info(f"Executing periodic task: {task_name}")
                await task_queue.enqueue_task(task_func.__name__)
                
                # 等待间隔时间
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                logger.info(f"Periodic task {task_name} cancelled")
                break
            except Exception as e:
                logger.error(f"Error in periodic task {task_name}: {str(e)}")
                # 即使出错也继续运行，但等待一段时间
                await asyncio.sleep(60)  # 等待1分钟后重试
    
    async def add_one_time_task(self, task_func, delay: int = 0):
        """
        添加一次性任务
        
        Args:
            task_func: 任务函数
            delay: 延迟时间（秒）
        """
        async def delayed_task():
            if delay > 0:
                await asyncio.sleep(delay)
            await task_queue.enqueue_task(task_func.__name__)
        
        task = asyncio.create_task(delayed_task())
        self.tasks.append(task)
        return task
    
    def get_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        return {
            "running": self.running,
            "active_tasks": len(self.tasks),
            "task_names": [task.get_name() for task in self.tasks if hasattr(task, 'get_name')],
            "timestamp": datetime.now().isoformat()
        }


# 创建全局调度器实例
scheduler = Scheduler()