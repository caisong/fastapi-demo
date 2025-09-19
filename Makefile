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
	@echo "Service Management:"
	@echo "  dev                  - Start FastAPI development server directly"
	@echo "  start                - Start all services (production)"
	@echo "  start-dev            - Start all services with Redis (development)"
	@echo "  start-monitoring     - Start all services with monitoring"
	@echo "  stop                 - Stop all services"
	@echo "  status               - Show service status"
	@echo "  logs                 - Show service logs"
	@echo "  logs-web             - Show web service logs"
	@echo "  logs-worker          - Show worker service logs"
	@echo "  logs-prometheus      - Show Prometheus service logs"
	@echo "  logs-pushgateway     - Show Pushgateway service logs"
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
	pip install -r requirements.txt
	pip install -e .

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
	@echo "Starting FastAPI development server..."
	PYTHONPATH=/data/code/webdev3:$$PYTHONPATH fastapi dev main.py --host 0.0.0.0 --port 8000

# Start all services (production)
start:
	@echo "Starting all services..."
	honcho start

# Start all services with Redis (development)
start-dev:
	@echo "Starting all services with Redis (development mode)..."
	honcho start -f Procfile.dev

# Start all services with monitoring
start-monitoring:
	@echo "Starting all services with monitoring..."
	honcho start -f Procfile.monitoring

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
	honcho start web

start-worker:
	@echo "Starting worker service only..."
	honcho start worker

start-prometheus:
	@echo "Starting Prometheus service only..."
	honcho start prometheus

start-pushgateway:
	@echo "Starting Pushgateway service only..."
	honcho start pushgateway

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
	@pip install honcho

# Setup development environment
setup-dev: install-honcho install-dev
	@echo "Development environment setup complete!"
	@echo "Run 'make start-dev' to start all services with Redis"

# Quick start for development
dev: setup-dev start-dev
	@echo "Development environment started!"
	@echo "Web service: http://localhost:8000"
	@echo "API docs: http://localhost:8000/docs"
	@echo "Prometheus metrics: http://localhost:9090/metrics"
	@echo "Pushgateway: http://localhost:9091/health"