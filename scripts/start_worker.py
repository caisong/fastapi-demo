#!/usr/bin/env python3
"""
Start ARQ worker
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from arq.worker import run_worker
from app.worker import WorkerSettings

if __name__ == "__main__":
    print("Starting ARQ worker...")
    # Use the direct run_worker call without asyncio.run
    run_worker(WorkerSettings)