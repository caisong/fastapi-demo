"""
Task helper functions and decorators
"""
import functools
from typing import Any, Callable, Dict

from app.core.task_queue import task_queue


def async_task(func: Callable) -> Callable:
    """
    Decorator to make a function enqueueable as an async task
    """
    @functools.wraps(func)
    async def delay(*args, **kwargs) -> str:
        """Enqueue the task for background processing"""
        return await task_queue.enqueue_task(func.__name__, *args, **kwargs)
    
    # Add delay method to the function
    func.delay = delay
    return func


# Mock task functions for testing when task system is not available
class MockTask:
    """Mock task for testing"""
    
    def __init__(self, name):
        self.name = name
    
    async def delay(self, *args, **kwargs):
        """Mock delay method"""
        return f"mock-job-{self.name}"


# Create mock tasks
send_welcome_email_task = MockTask("send_welcome_email")
send_item_notification_task = MockTask("send_item_notification")
process_item_task = MockTask("process_item")
cleanup_old_data_task = MockTask("cleanup_old_data")
generate_report_task = MockTask("generate_report")
send_batch_notifications_task = MockTask("send_batch_notifications")
collect_third_party_metrics_task = MockTask("collect_third_party_metrics")
collect_specific_api_task = MockTask("collect_specific_api")