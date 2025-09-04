#!/usr/bin/env python3
"""
Redis server management script
"""
import subprocess
import sys
import time
import os
import signal


def check_redis_running():
    """Check if Redis server is running"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        return True
    except:
        return False


def start_redis_server():
    """Start Redis server"""
    print("🔴 Starting Redis server...")
    
    try:
        # Try to start redis-server
        process = subprocess.Popen(
            ["redis-server", "--port", "6379", "--daemonize", "yes"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait a moment for Redis to start
        time.sleep(2)
        
        if check_redis_running():
            print("✅ Redis server started successfully on port 6379")
            return True
        else:
            print("❌ Failed to start Redis server")
            return False
            
    except FileNotFoundError:
        print("❌ redis-server not found. Please install Redis:")
        print("   Ubuntu/Debian: sudo apt-get install redis-server")
        print("   macOS: brew install redis")
        print("   Or use Docker: docker run -d -p 6379:6379 redis:alpine")
        return False
    except Exception as e:
        print(f"❌ Error starting Redis: {e}")
        return False


def stop_redis_server():
    """Stop Redis server"""
    print("🛑 Stopping Redis server...")
    
    try:
        # Try to stop via redis-cli
        subprocess.run(["redis-cli", "shutdown"], check=True, capture_output=True)
        print("✅ Redis server stopped successfully")
        return True
    except:
        try:
            # Try to kill redis-server process
            subprocess.run(["pkill", "-f", "redis-server"], check=True)
            print("✅ Redis server stopped successfully")
            return True
        except:
            print("❌ Failed to stop Redis server")
            return False


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python scripts/redis_manager.py [start|stop|status|restart]")
        return 1
    
    command = sys.argv[1].lower()
    
    if command == "status":
        if check_redis_running():
            print("✅ Redis server is running")
        else:
            print("❌ Redis server is not running")
    
    elif command == "start":
        if check_redis_running():
            print("✅ Redis server is already running")
        else:
            start_redis_server()
    
    elif command == "stop":
        if check_redis_running():
            stop_redis_server()
        else:
            print("❌ Redis server is not running")
    
    elif command == "restart":
        if check_redis_running():
            stop_redis_server()
            time.sleep(1)
        start_redis_server()
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Available commands: start, stop, status, restart")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())