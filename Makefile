# Makefile for FastAPI project testing and development

.PHONY: help test test-unit test-integration test-performance test-coverage test-verbose test-fast install-dev lint format type-check clean setup-test-db start start-dev start-monitoring stop status logs

# Default target
help:
	@echo "Available commands:"
	@echo ""
	@echo "Development & Testing:"
	@echo "  test                 - Run all tests"
	@echo "  test-unit            - Run only unit tests"
	@echo "  test-integration     - Run only integration tests"
	@echo "  test-performance     - Run performance and benchmark tests"
	@echo "  test-coverage        - Run tests with coverage report"
	@echo "  test-verbose         - Run tests with verbose output"
	@echo "  test-fast            - Run tests in parallel (fast)"
	@echo "  test-auth            - Run authentication tests only"
	@echo "  test-api             - Run API endpoint tests only"
	@echo "  test-watch           - Run tests in watch mode"
	@echo "  install-dev          - Install development dependencies"
	@echo "  lint                 - Run linting (flake8)"
	@echo "  format               - Format code (black, isort)"
	@echo "  type-check           - Run type checking (mypy)"
	@echo "  clean                - Clean test artifacts"
	@echo "  setup-test-db        - Setup test database"
	@echo ""
	@echo "Database Management (Alembic):"
	@echo "  db-init              - 🗃️  Initialize database with migrations and default data"
	@echo "  db-migrate           - 📝 Create new database migration"
	@echo "  db-upgrade           - ⬆️  Apply pending migrations"
	@echo "  db-downgrade         - ⬇️  Rollback database migration"
	@echo "  db-history           - 📋 Show migration history"
	@echo "  db-current           - 📍 Show current database revision"
	@echo "  db-reset             - ⚠️  Reset database (DANGEROUS)"
	@echo ""
	@echo "Service Management:"
	@echo "  dev                  - 🚀 Start FastAPI development server (recommended for API development)"
	@echo "  dev-quick            - ⚡ Quick FastAPI server start (minimal output)"
	@echo "  start                - Start all services (production)"
	@echo "  start-dev            - 🚀 Start all services with Redis (recommended for full stack development)"
	@echo "  start-monitoring     - Start all services with monitoring"
	@echo "  setup-dev            - 🔧 Setup complete development environment"
	@echo "  stop                 - Stop all services"
	@echo "  status               - Show service status"
	@echo "  logs                 - Show service logs"
	@echo "  logs-web             - Show web service logs"
	@echo "  logs-worker          - Show worker service logs"
	@echo "  logs-prometheus      - Show Prometheus service logs"
	@echo "  logs-pushgateway     - Show Pushgateway service logs"
	@echo "  health-check         - Check service health status"
	@echo ""
	@echo "Individual Services:"
	@echo "  start-web            - Start only web service"
	@echo "  start-worker         - Start only worker service"
	@echo "  start-prometheus     - Start only Prometheus service"
	@echo "  start-pushgateway    - Start only Pushgateway service"

# Test commands
test:
	pytest

test-unit:
	pytest -m "unit or not integration and not performance"

test-integration:
	pytest -m "integration"

test-performance:
	pytest -m "performance or benchmark" --benchmark-only

test-coverage:
	pytest --cov=app --cov-report=html --cov-report=term-missing

test-verbose:
	pytest -v -s

test-fast:
	pytest -n auto

test-auth:
	pytest -m "auth" -v

test-api:
	pytest -m "api" -v

test-watch:
	pytest-watch

test-specific:
	@read -p "Enter test file or pattern: " test_pattern; \
	pytest $$test_pattern -v

# Development setup
install-dev:
	. venv/bin/activate && pip install -r requirements.txt

# Code quality
lint:
	flake8 app tests
	
format:
	black app tests
	isort app tests

type-check:
	mypy app

check-all: lint type-check test

# Database setup
setup-test-db:
	python -c "from app.db.database import Base, engine; Base.metadata.create_all(bind=engine)"

# Database migration commands (Alembic)
db-init:
	@echo "🗃️  Initializing database with Alembic..."
	@echo "1. Applying database migrations..."
	. venv/bin/activate && alembic upgrade head
	@echo "2. Initializing default data..."
	. venv/bin/activate && PYTHONPATH=. python scripts/init_default_data.py
	@echo "✅ Database initialization complete!"

db-migrate:
	@echo "📝 Creating new database migration..."
	@read -p "Enter migration message: " msg; \
	. venv/bin/activate && alembic revision --autogenerate -m "$$msg"

db-upgrade:
	@echo "⬆️  Applying database migrations..."
	. venv/bin/activate && alembic upgrade head

db-downgrade:
	@echo "⬇️  Rolling back database migration..."
	@read -p "Enter target revision (or 'base' for complete rollback): " rev; \
	. venv/bin/activate && alembic downgrade "$$rev"

db-history:
	@echo "📋 Database migration history:"
	. venv/bin/activate && alembic history --verbose

db-current:
	@echo "📍 Current database revision:"
	. venv/bin/activate && alembic current

db-reset:
	@echo "⚠️  WARNING: This will reset the entire database!"
	@read -p "Are you sure? Type 'yes' to continue: " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		. venv/bin/activate && alembic downgrade base && alembic upgrade head; \
		echo "✅ Database reset complete"; \
	else \
		echo "❌ Database reset cancelled"; \
	fi

# Cleanup
clean:
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf coverage.xml
	rm -f test.db
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Docker test environment
test-docker:
	docker-compose -f docker-compose.yml up -d postgres redis
	sleep 5
	pytest
	docker-compose -f docker-compose.yml down

# Run specific test classes
test-auth-class:
	pytest tests/test_auth.py::TestUserLogin -v

test-user-class:
	pytest tests/test_users.py::TestUserListEndpoint -v

test-item-class:
	pytest tests/test_items.py::TestItemCreationEndpoint -v

# Generate test reports
test-report:
	pytest --html=reports/test_report.html --self-contained-html

test-junit:
	pytest --junitxml=reports/junit.xml

# Performance testing
benchmark:
	pytest --benchmark-only --benchmark-sort=mean --benchmark-html=reports/benchmark.html

# Security testing
test-security:
	pytest tests/test_auth.py::TestAuthenticationSecurity -v
	pytest tests/test_integration.py::TestSecurityIntegration -v

# Run tests with different markers
test-slow:
	pytest -m "slow" -v

test-not-slow:
	pytest -m "not slow"

# Debugging helpers
test-debug:
	pytest --pdb

test-last-failed:
	pytest --lf

test-failed-first:
	pytest --ff

# Continuous integration helpers
ci-test:
	pytest --cov=app --cov-report=xml --junitxml=reports/junit.xml

# Create test reports directory
setup-reports:
	mkdir -p reports

# Full test suite with reports
test-full: setup-reports
	pytest --cov=app --cov-report=html:reports/coverage --cov-report=xml:reports/coverage.xml --html=reports/test_report.html --self-contained-html --junitxml=reports/junit.xml

# Service Management Commands
# ==========================

# Start development server directly with FastAPI CLI
dev:
	@echo "🚀 Starting FastAPI development server..."
	@echo "======================================="
	@echo "🌐 Server: http://localhost:8000"
	@echo "📝 API docs: http://localhost:8000/docs"
	@echo "🔍 Interactive API: http://localhost:8000/redoc"
	@echo "🔴 Admin interface: http://localhost:8000/admin"
	@echo "======================================="
	. venv/bin/activate && fastapi dev main.py --host 0.0.0.0 --port 8000

# Quick development server (simplified)
dev-quick:
	@echo "⚡ Quick FastAPI server start..."
	. venv/bin/activate && fastapi dev main.py

# Start all services (production)
start:
	@echo "Starting all services..."
	. venv/bin/activate && honcho start

# Start all services with Redis (development)
start-dev:
	@echo "🚀 Starting FastAPI Development Environment with Honcho"
	@echo "=========================================================="
	@echo "Checking dependencies..."
	@if ! . venv/bin/activate && command -v honcho >/dev/null 2>&1; then \
		echo "❌ Honcho is not installed. Installing..."; \
		. venv/bin/activate && pip install honcho && echo "✅ Honcho installed successfully" || (echo "❌ Failed to install honcho. Please install manually: pip install honcho" && exit 1); \
	fi
	@echo "Checking Redis connection..."
	@if redis-cli ping >/dev/null 2>&1; then \
		echo "✅ Redis server is running"; \
		echo "\n🔧 Starting development processes..."; \
		echo "   - FastAPI server (web)"; \
		echo "   - ARQ worker (worker)"; \
		echo "   - Connected to Redis for async tasks"; \
		echo "\n📝 Logs from all processes:"; \
		echo "----------------------------------------"; \
		. venv/bin/activate && honcho start -f Procfile.dev; \
	else \
		echo "⚠️  Redis server not running - tasks will execute synchronously"; \
		echo "\n🔧 Starting development processes..."; \
		echo "   - FastAPI server (web)"; \
		echo "   - ARQ worker (worker)"; \
		echo "   - Running in sync mode (no Redis)"; \
		echo "\n📝 Logs from all processes:"; \
		echo "----------------------------------------"; \
		. venv/bin/activate && honcho start; \
	fi

# Start all services with monitoring
start-monitoring:
	@echo "Starting all services with monitoring..."
	. venv/bin/activate && honcho start -f Procfile.monitoring

# Stop all services
stop:
	@echo "Stopping all services..."
	@if pgrep -f "honcho" > /dev/null; then \
		pkill -f "honcho"; \
		echo "Services stopped."; \
	else \
		echo "No services running."; \
	fi

# Show service status
status:
	@echo "Service Status:"
	@echo "==============="
	@if pgrep -f "honcho" > /dev/null; then \
		echo "Honcho processes running:"; \
		ps aux | grep honcho | grep -v grep; \
		echo ""; \
		echo "Individual services:"; \
		pgrep -f "python scripts/dev.py" > /dev/null && echo "  ✓ Web service (FastAPI)" || echo "  ✗ Web service (FastAPI)"; \
		pgrep -f "python scripts/start_worker.py" > /dev/null && echo "  ✓ Worker service (ARQ)" || echo "  ✗ Worker service (ARQ)"; \
		pgrep -f "python scripts/start_prometheus.py" > /dev/null && echo "  ✓ Prometheus service" || echo "  ✗ Prometheus service"; \
		pgrep -f "python scripts/start_pushgateway.py" > /dev/null && echo "  ✓ Pushgateway service" || echo "  ✗ Pushgateway service"; \
		pgrep -f "redis-server" > /dev/null && echo "  ✓ Redis service" || echo "  ✗ Redis service"; \
	else \
		echo "No services running."; \
	fi

# Show all service logs
logs:
	@echo "Service logs (press Ctrl+C to exit):"
	@if pgrep -f "honcho" > /dev/null; then \
		honcho logs; \
	else \
		echo "No services running. Start services first with 'make start' or 'make start-dev'"; \
	fi

# Show specific service logs
logs-web:
	@echo "Web service logs (press Ctrl+C to exit):"
	@if pgrep -f "honcho" > /dev/null; then \
		honcho logs web; \
	else \
		echo "No services running. Start services first with 'make start' or 'make start-dev'"; \
	fi

logs-worker:
	@echo "Worker service logs (press Ctrl+C to exit):"
	@if pgrep -f "honcho" > /dev/null; then \
		honcho logs worker; \
	else \
		echo "No services running. Start services first with 'make start' or 'make start-dev'"; \
	fi

logs-prometheus:
	@echo "Prometheus service logs (press Ctrl+C to exit):"
	@if pgrep -f "honcho" > /dev/null; then \
		honcho logs prometheus; \
	else \
		echo "No services running. Start services first with 'make start' or 'make start-dev'"; \
	fi

logs-pushgateway:
	@echo "Pushgateway service logs (press Ctrl+C to exit):"
	@if pgrep -f "honcho" > /dev/null; then \
		honcho logs pushgateway; \
	else \
		echo "No services running. Start services first with 'make start' or 'make start-dev'"; \
	fi

# Individual service commands
start-web:
	@echo "Starting web service only..."
	. venv/bin/activate && honcho start web

start-worker:
	@echo "Starting worker service only..."
	. venv/bin/activate && honcho start worker

start-prometheus:
	@echo "Starting Prometheus service only..."
	. venv/bin/activate && honcho start prometheus

start-pushgateway:
	@echo "Starting Pushgateway service only..."
	. venv/bin/activate && honcho start pushgateway

# Service health checks
health-check:
	@echo "Checking service health..."
	@echo "========================="
	@echo -n "Web service (FastAPI): "
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null | grep -q "200" && echo "✓ Healthy" || echo "✗ Unhealthy"
	@echo -n "Prometheus metrics: "
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:9090/metrics 2>/dev/null | grep -q "200" && echo "✓ Healthy" || echo "✗ Unhealthy"
	@echo -n "Pushgateway: "
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:9091/health 2>/dev/null | grep -q "200" && echo "✓ Healthy" || echo "✗ Unhealthy"
	@echo -n "Redis: "
	@redis-cli ping 2>/dev/null | grep -q "PONG" && echo "✓ Healthy" || echo "✗ Unhealthy"

# Install honcho if not present
install-honcho:
	@echo "Installing honcho..."
	@if ! command -v honcho >/dev/null 2>&1; then \
		. venv/bin/activate && pip install honcho && echo "✅ Honcho installed successfully"; \
	else \
		echo "✅ Honcho is already installed"; \
	fi

# Setup development environment
setup-dev: install-honcho install-dev
	@echo "🔧 Development environment setup complete!"
	@echo "📋 Available commands:"
	@echo "   make start-dev    - Start all services with Redis"
	@echo "   make dev          - Start FastAPI server only"
	@echo "   make test         - Run all tests"
	@echo "   make health-check - Check service health"

# Quick start for development
quick-start: setup-dev start-dev

# Show service information after starting
show-services:
	@echo "🎆 Development environment started!"
	@echo "=========================================="
	@echo "🌐 Web service: http://localhost:8000"
	@echo "📝 API docs: http://localhost:8000/docs"
	@echo "🔍 Interactive API: http://localhost:8000/redoc"
	@echo "📊 Prometheus metrics: http://localhost:9090/metrics"
	@echo "📁 Pushgateway: http://localhost:9091/health"
	@echo "🔴 Admin interface: http://localhost:8000/admin"
	@echo "\nUse Ctrl+C to stop all services"