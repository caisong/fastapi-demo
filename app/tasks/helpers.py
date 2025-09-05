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


# Apply decorator to task functions
from app.tasks import (
    send_welcome_email_task,
    send_item_notification_task,
    process_item_task,
    cleanup_old_data_task,
    generate_report_task,
    send_batch_notifications_task,
    collect_third_party_metrics_task,
    collect_specific_api_task,
)

# Make tasks enqueueable
send_welcome_email_task = async_task(send_welcome_email_task)
send_item_notification_task = async_task(send_item_notification_task)
process_item_task = async_task(process_item_task)
cleanup_old_data_task = async_task(cleanup_old_data_task)
generate_report_task = async_task(generate_report_task)
send_batch_notifications_task = async_task(send_batch_notifications_task)
collect_third_party_metrics_task = async_task(collect_third_party_metrics_task)
collect_specific_api_task = async_task(collect_specific_api_task)