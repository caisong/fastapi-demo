# Process Management with Honcho

This guide explains how to manage multiple processes for the FastAPI application using Honcho.

## Overview

The application consists of multiple processes:
- **Web Server**: FastAPI application server
- **Worker**: ARQ async task worker
- **Redis**: Redis server for task queue and caching

## Quick Start

### Option 1: All-in-One Script (Recommended)
```bash
python scripts/start_dev.py
```
This script will:
- Check and install honcho if needed
- Check Redis availability
- Start all processes using Honcho

### Option 2: Manual Honcho Commands

Start all processes (without Redis):
```bash
honcho start
```

Start all processes including Redis:
```bash
honcho start -f Procfile.dev
```

Start specific processes:
```bash
# Start only web server
honcho start web

# Start web server and worker
honcho start web worker

# Start with Redis server
honcho start -f Procfile.dev web worker redis
```

## Redis Management

### Check Redis Status
```bash
python scripts/redis_manager.py status
```

### Start Redis Server
```bash
python scripts/redis_manager.py start
```

### Stop Redis Server
```bash
python scripts/redis_manager.py stop
```

### Restart Redis Server
```bash
python scripts/redis_manager.py restart
```

## Process Configuration

### Procfile (Default)
```
web: python scripts/dev.py
worker: python scripts/start_worker.py
```

### Procfile.dev (With Redis)
```
web: python scripts/dev.py
worker: python scripts/start_worker.py
redis: redis-server --port 6379 --loglevel warning
```

## Environment Variables

Required Redis configuration in `.env`:
```env
# Redis settings
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
REDIS_URL=redis://localhost:6379/0

# ARQ Task Queue
ARQ_MAX_JOBS=10
ARQ_JOB_TIMEOUT=300
ARQ_KEEP_RESULT=3600
```

## Development Workflow

### 1. Full Development Environment
```bash
# Start everything (web, worker, redis)
python scripts/start_dev.py
```

### 2. Web Only (No Background Tasks)
```bash
# Start only the web server
honcho start web
```

### 3. Web + Worker (External Redis)
```bash
# If you have Redis running elsewhere
honcho start web worker
```

## Monitoring

### View Process Status
```bash
# Honcho shows all process outputs
honcho start
```

### Monitor Redis
```bash
# In a separate terminal
redis-cli monitor
```

### View Task Queue
```bash
# Check queue status via API
curl http://localhost:8010/api/v1/tasks/queue/info

# Check recent jobs
curl http://localhost:8010/api/v1/tasks/jobs/recent
```

## Troubleshooting

### Redis Connection Issues
1. Check if Redis is running:
   ```bash
   python scripts/redis_manager.py status
   ```

2. Start Redis if not running:
   ```bash
   python scripts/redis_manager.py start
   ```

3. If Redis unavailable, tasks run synchronously

### Port Conflicts
- Web server: PORT=8010 (configurable via .env)
- Redis: 6379 (configurable via REDIS_PORT)

### Process Management
- Use `Ctrl+C` to stop all processes
- Honcho handles graceful shutdown
- Individual processes can be restarted

## Production Deployment

For production, consider:
- Using external Redis service
- Process managers like systemd or supervisor
- Container orchestration (Docker Compose/Kubernetes)
- Separate worker instances for scaling

## Available Commands

```bash
# Development
python scripts/start_dev.py          # Start all development processes
python scripts/dev.py               # Start web server only
python scripts/start_worker.py      # Start worker only

# Redis Management
python scripts/redis_manager.py status    # Check Redis status
python scripts/redis_manager.py start     # Start Redis
python scripts/redis_manager.py stop      # Stop Redis
python scripts/redis_manager.py restart   # Restart Redis

# Honcho Process Management
honcho start                         # Start web + worker
honcho start -f Procfile.dev        # Start web + worker + redis
honcho start web                     # Start web server only
honcho start worker                  # Start worker only
```