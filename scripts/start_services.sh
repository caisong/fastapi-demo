#!/bin/bash
# Service management script for FastAPI project
# Usage: ./scripts/start_services.sh [command] [options]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
PROCFILE="Procfile"
SERVICES=""
VERBOSE=false

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check if honcho is installed
check_honcho() {
    if ! command -v honcho &> /dev/null; then
        print_status $RED "Error: honcho is not installed"
        print_status $YELLOW "Installing honcho..."
        
        # Check if we're in a virtual environment
        if [ -n "$VIRTUAL_ENV" ]; then
            pip install honcho
        else
            # Try to activate virtual environment if it exists
            if [ -f "/data/fastapi/bin/activate" ]; then
                print_status $YELLOW "Activating virtual environment..."
                source /data/fastapi/bin/activate
                pip install honcho
            else
                print_status $RED "No virtual environment found. Please activate your virtual environment first."
                print_status $YELLOW "Example: source /data/fastapi/bin/activate"
                exit 1
            fi
        fi
    fi
}

# Function to check if services are running
check_services() {
    if pgrep -f "honcho" > /dev/null; then
        print_status $GREEN "Services are running"
        return 0
    else
        print_status $YELLOW "No services are running"
        return 1
    fi
}

# Function to start services
start_services() {
    local procfile=$1
    local services=$2
    
    print_status $BLUE "Starting services using $procfile..."
    
    if [ -n "$services" ]; then
        print_status $YELLOW "Starting specific services: $services"
        honcho start -f $procfile $services
    else
        print_status $YELLOW "Starting all services"
        honcho start -f $procfile
    fi
}

# Function to stop services
stop_services() {
    print_status $BLUE "Stopping all services..."
    
    if check_services; then
        pkill -f "honcho"
        print_status $GREEN "Services stopped successfully"
    else
        print_status $YELLOW "No services to stop"
    fi
}

# Function to show service status
show_status() {
    print_status $BLUE "Service Status:"
    echo "==============="
    
    if check_services; then
        echo ""
        print_status $GREEN "Honcho processes running:"
        ps aux | grep honcho | grep -v grep
        
        echo ""
        print_status $GREEN "Individual services:"
        pgrep -f "python scripts/dev.py" > /dev/null && echo "  ✓ Web service (FastAPI)" || echo "  ✗ Web service (FastAPI)"
        pgrep -f "python scripts/start_worker.py" > /dev/null && echo "  ✓ Worker service (ARQ)" || echo "  ✗ Worker service (ARQ)"
        pgrep -f "python scripts/start_prometheus.py" > /dev/null && echo "  ✓ Prometheus service" || echo "  ✗ Prometheus service"
        pgrep -f "python scripts/start_pushgateway.py" > /dev/null && echo "  ✓ Pushgateway service" || echo "  ✗ Pushgateway service"
        pgrep -f "redis-server" > /dev/null && echo "  ✓ Redis service" || echo "  ✗ Redis service"
    fi
}

# Function to show logs
show_logs() {
    local service=$1
    
    if check_services; then
        if [ -n "$service" ]; then
            print_status $BLUE "Showing logs for $service service (press Ctrl+C to exit):"
            honcho logs $service
        else
            print_status $BLUE "Showing all service logs (press Ctrl+C to exit):"
            honcho logs
        fi
    else
        print_status $YELLOW "No services running. Start services first with './scripts/start_services.sh start'"
    fi
}

# Function to check service health
check_health() {
    print_status $BLUE "Checking service health..."
    echo "========================="
    
    # Check web service
    echo -n "Web service (FastAPI): "
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null | grep -q "200"; then
        print_status $GREEN "✓ Healthy"
    else
        print_status $RED "✗ Unhealthy"
    fi
    
    # Check Prometheus metrics
    echo -n "Prometheus metrics: "
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:9090/metrics 2>/dev/null | grep -q "200"; then
        print_status $GREEN "✓ Healthy"
    else
        print_status $RED "✗ Unhealthy"
    fi
    
    # Check Pushgateway
    echo -n "Pushgateway: "
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:9091/health 2>/dev/null | grep -q "200"; then
        print_status $GREEN "✓ Healthy"
    else
        print_status $RED "✗ Unhealthy"
    fi
    
    # Check Redis
    echo -n "Redis: "
    if redis-cli ping 2>/dev/null | grep -q "PONG"; then
        print_status $GREEN "✓ Healthy"
    else
        print_status $RED "✗ Unhealthy"
    fi
}

# Function to show help
show_help() {
    echo "Service Management Script"
    echo "========================"
    echo ""
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  start [services]     - Start services (default: all)"
    echo "  start-dev [services] - Start services with Redis (development)"
    echo "  start-monitoring     - Start services with monitoring"
    echo "  stop                 - Stop all services"
    echo "  status               - Show service status"
    echo "  logs [service]       - Show service logs"
    echo "  health               - Check service health"
    echo "  restart [services]   - Restart services"
    echo "  help                 - Show this help message"
    echo ""
    echo "Available services:"
    echo "  web, worker, prometheus, pushgateway, redis"
    echo ""
    echo "Examples:"
    echo "  $0 start                    # Start all services"
    echo "  $0 start-dev                # Start with Redis (development)"
    echo "  $0 start web worker         # Start only web and worker"
    echo "  $0 logs web                 # Show web service logs"
    echo "  $0 status                   # Show service status"
    echo "  $0 health                   # Check service health"
}

# Function to restart services
restart_services() {
    local services=$1
    
    print_status $BLUE "Restarting services..."
    stop_services
    sleep 2
    start_services $PROCFILE "$services"
}

# Main script logic
main() {
    # Check if honcho is installed
    check_honcho
    
    # Parse command line arguments
    case "${1:-help}" in
        "start")
            PROCFILE="Procfile"
            SERVICES="${@:2}"
            start_services $PROCFILE "$SERVICES"
            ;;
        "start-dev")
            PROCFILE="Procfile.dev"
            SERVICES="${@:2}"
            start_services $PROCFILE "$SERVICES"
            ;;
        "start-monitoring")
            PROCFILE="Procfile.monitoring"
            SERVICES="${@:2}"
            start_services $PROCFILE "$SERVICES"
            ;;
        "stop")
            stop_services
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs "${2:-}"
            ;;
        "health")
            check_health
            ;;
        "restart")
            SERVICES="${@:2}"
            restart_services "$SERVICES"
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_status $RED "Unknown command: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"