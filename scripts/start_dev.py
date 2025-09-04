#!/usr/bin/env python3
"""
Start all development processes using Honcho
"""
import subprocess
import sys
import os


def main():
    """Start all processes with Honcho"""
    print("🚀 Starting FastAPI Development Environment with Honcho")
    print("=" * 60)
    
    # Check if honcho is installed
    try:
        subprocess.run(["honcho", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Honcho is not installed. Installing...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "honcho"], check=True)
            print("✅ Honcho installed successfully")
        except subprocess.CalledProcessError:
            print("❌ Failed to install honcho. Please install manually: pip install honcho")
            return 1
    
    # Check if Redis is running (optional check)
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis server is running")
        redis_running = True
    except:
        print("⚠️  Redis server not running - tasks will execute synchronously")
        redis_running = False
    
    # Start processes with Honcho
    print("\n🔧 Starting development processes...")
    print("   - FastAPI server (web)")
    print("   - ARQ worker (worker)")
    
    if redis_running:
        print("   - Connected to Redis for async tasks")
    else:
        print("   - Running in sync mode (no Redis)")
    
    print("\n📝 Logs from all processes:")
    print("-" * 40)
    
    try:
        # Run honcho start
        subprocess.run(["honcho", "start"], cwd=os.getcwd())
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down all processes...")
        return 0
    except Exception as e:
        print(f"\n❌ Error running honcho: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())