# Makefile for FastAPI project testing and development

.PHONY: help test test-unit test-integration test-performance test-coverage test-verbose test-fast install-dev lint format type-check clean setup-test-db

# Default target
help:
	@echo "Available commands:"
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