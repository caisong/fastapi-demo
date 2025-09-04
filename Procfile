# Procfile for Honcho process management
# Usage: honcho start

# Main FastAPI application server
web: python scripts/dev.py

# ARQ worker for async task processing
worker: python scripts/start_worker.py

# Prometheus metrics server
prometheus: python scripts/start_prometheus.py

# Redis server (if not using external Redis)
# redis: redis-server --port 6379

# Optional: Redis monitoring
# redis-cli: redis-cli monitor