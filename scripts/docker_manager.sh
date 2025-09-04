#!/bin/bash
# Docker Compose Management Script for FastAPI Application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default environment
ENVIRONMENT=${ENVIRONMENT:-development}

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE} $1${NC}"
    echo -e "${BLUE}================================================${NC}"
}

# Check if Docker and Docker Compose are installed
check_requirements() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
}

# Copy appropriate environment file
setup_environment() {
    local env="$1"
    case "$env" in
        development|dev)
            print_status "Setting up development environment..."
            cp .env.development .env
            ;;
        production|prod)
            print_status "Setting up production environment..."
            cp .env.production .env
            print_warning "Make sure to update passwords and secrets in .env file!"
            ;;
        docker)
            print_status "Setting up Docker environment..."
            cp .env.docker .env
            ;;
        *)
            print_error "Unknown environment: $env"
            print_status "Available environments: development, production, docker"
            exit 1
            ;;
    esac
}

# Start services
start_services() {
    local env="${1:-development}"
    local profiles="${2:-}"
    
    print_header "Starting FastAPI Application Stack (Environment: $env)"
    
    setup_environment "$env"
    
    # Build compose command
    local compose_cmd="docker-compose up -d"
    
    # Add profiles if specified
    if [ -n "$profiles" ]; then
        compose_cmd="docker-compose --profile $profiles up -d"
    fi
    
    print_status "Starting services with Docker Compose..."
    eval "$compose_cmd"
    
    print_status "Waiting for services to be ready..."
    sleep 15
    
    print_status "Checking service health..."
    docker-compose ps
    
    echo ""
    print_header "Services are running!"
    show_endpoints
}

# Show service endpoints
show_endpoints() {
    # Read current environment variables
    source .env 2>/dev/null || true
    
    echo -e "${GREEN}FastAPI Application:${NC} http://localhost:${APP_EXTERNAL_PORT:-8010}"
    echo -e "${GREEN}FastAPI Docs:${NC} http://localhost:${APP_EXTERNAL_PORT:-8010}/docs"
    echo -e "${GREEN}FastAPI Admin:${NC} http://localhost:${APP_EXTERNAL_PORT:-8010}/admin"
    echo -e "${GREEN}Prometheus:${NC} http://localhost:${PROMETHEUS_EXTERNAL_PORT:-9091}"
    echo -e "${GREEN}Metrics Proxy:${NC} http://localhost:${METRICS_EXTERNAL_PORT:-9090}/metrics"
    echo -e "${GREEN}Grafana:${NC} http://localhost:${GRAFANA_EXTERNAL_PORT:-3000} (admin/${GRAFANA_PASSWORD:-admin123})"
    echo -e "${GREEN}PostgreSQL:${NC} localhost:${POSTGRES_EXTERNAL_PORT:-15432}"
    echo -e "${GREEN}Redis:${NC} localhost:${REDIS_EXTERNAL_PORT:-6379}"
}

# Stop all services
stop_services() {
    print_header "Stopping FastAPI Application Stack"
    docker-compose down
    print_status "All services stopped."
}

# Restart all services
restart_services() {
    local env="${1:-development}"
    local profiles="${2:-}"
    print_header "Restarting FastAPI Application Stack"
    stop_services
    start_services "$env" "$profiles"
}

# Show logs
show_logs() {
    if [ -z "$1" ]; then
        print_status "Showing logs for all services..."
        docker-compose logs -f
    else
        print_status "Showing logs for service: $1"
        docker-compose logs -f "$1"
    fi
}

# Show service status
show_status() {
    print_header "Service Status"
    docker-compose ps
    
    echo ""
    print_header "Container Health Status"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    echo ""
    print_header "Service Endpoints"
    show_endpoints
}

# Clean up everything
cleanup() {
    print_header "Cleaning up Docker resources"
    print_warning "This will remove all containers, volumes, and images related to the project."
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down -v --rmi all
        print_status "Cleanup completed."
    else
        print_status "Cleanup cancelled."
    fi
}

# Initialize database
init_database() {
    print_header "Initializing Database"
    print_status "Running database migrations..."
    docker-compose exec fastapi_app python scripts/init_db.py
    print_status "Database initialization completed."
}

# Build images
build_images() {
    print_header "Building Docker Images"
    docker-compose build --no-cache
    print_status "Images built successfully."
}

# Show help
show_help() {
    echo "FastAPI Docker Management Script"
    echo ""
    echo "Usage: $0 [COMMAND] [ENVIRONMENT] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  start [env] [profiles]  Start all services (default: development)"
    echo "  stop                    Stop all services"
    echo "  restart [env] [profiles] Restart all services"
    echo "  logs [service]          Show logs for all or specific service"
    echo "  status                  Show service status and endpoints"
    echo "  init-db                 Initialize database"
    echo "  build                   Build Docker images"
    echo "  cleanup                 Remove all containers, volumes, and images"
    echo "  help                    Show this help message"
    echo ""
    echo "Environments:"
    echo "  development (default)   Local development with external access"
    echo "  production             Production configuration"
    echo "  docker                 Docker-optimized configuration"
    echo ""
    echo "Profiles (optional):"
    echo "  metrics                Include metrics proxy"
    echo "  monitoring             Include Grafana for monitoring"
    echo ""
    echo "Examples:"
    echo "  $0 start                        # Start with development environment"
    echo "  $0 start production             # Start with production environment"
    echo "  $0 start development metrics    # Start with metrics proxy"
    echo "  $0 start docker monitoring      # Start with Docker env and Grafana"
    echo ""
    echo "Available services: fastapi_app, postgres, redis, prometheus, arq_worker, metrics_proxy, grafana"
}

# Main script logic
main() {
    check_requirements
    
    case "${1:-help}" in
        start)
            start_services "${2:-development}" "$3"
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services "${2:-development}" "$3"
            ;;
        logs)
            show_logs "$2"
            ;;
        status)
            show_status
            ;;
        init-db)
            init_database
            ;;
        build)
            build_images
            ;;
        cleanup)
            cleanup
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"