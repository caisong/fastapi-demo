# Procfile for Honcho process management
# Usage: honcho start

# Main FastAPI application server
web: PYTHONPATH=/data/code/webdev3:$PYTHONPATH fastapi dev main.py --host 0.0.0.0 --port 8000

# ARQ worker for async task processing
worker: python scripts/start_worker.py

# Prometheus metrics proxy server
prometheus: python scripts/start_prometheus.py

# Prometheus Pushgateway server
pushgateway: python scripts/start_pushgateway.py

# Redis server (if not using external Redis)
# redis: redis-server --port 6379

# Optional: Redis monitoring
# redis-cli: redis-cli monitor