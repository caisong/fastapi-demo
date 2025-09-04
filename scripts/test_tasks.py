#!/usr/bin/env python3
"""
Test task queue functionality
"""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.task_queue import task_queue
from app.tasks.helpers import (
    send_welcome_email_task,
    process_item_task,
    generate_report_task
)


async def test_tasks():
    """Test various tasks"""
    print("🚀 Testing ARQ Task Queue")
    print("=" * 50)
    
    # Initialize task queue
    await task_queue.startup()
    
    try:
        # Test 1: Welcome email task
        print("\n📧 Testing welcome email task...")
        job1 = await send_welcome_email_task.delay("test@example.com", "Test User")
        print(f"   Job ID: {job1}")
        
        # Test 2: Process item task
        print("\n📦 Testing process item task...")
        job2 = await process_item_task.delay(123)
        print(f"   Job ID: {job2}")
        
        # Test 3: Generate report task
        print("\n📊 Testing generate report task...")
        job3 = await generate_report_task.delay(1, "user_activity")
        print(f"   Job ID: {job3}")
        
        # Wait a bit and check job statuses
        print("\n⏳ Waiting 2 seconds before checking status...")
        await asyncio.sleep(2)
        
        print("\n📋 Job Statuses:")
        for i, job_id in enumerate([job1, job2, job3], 1):
            status = await task_queue.get_job_status(job_id)
            print(f"   Job {i}: {status['status']}")
        
        print("\n✅ Task queue test completed!")
        print("\nNote: Make sure the ARQ worker is running to process these tasks.")
        print("Run: python scripts/start_worker.py")
        
    finally:
        await task_queue.shutdown()


if __name__ == "__main__":
    asyncio.run(test_tasks())