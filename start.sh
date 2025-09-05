#!/bin/bash
# Quick start script for FastAPI project
# This script automatically activates the virtual environment and starts services

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}FastAPI Project Quick Start${NC}"
echo "=============================="

# Check if virtual environment exists
if [ ! -f "/data/fastapi/bin/activate" ]; then
    echo -e "${YELLOW}Virtual environment not found at /data/fastapi/bin/activate${NC}"
    echo "Please create a virtual environment first:"
    echo "  python3 -m venv /data/fastapi"
    echo "  source /data/fastapi/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source /data/fastapi/bin/activate

# Check if honcho is installed
if ! command -v honcho &> /dev/null; then
    echo -e "${YELLOW}Installing honcho...${NC}"
    pip install honcho
fi

# Parse command line arguments
case "${1:-start-dev}" in
    "start")
        echo -e "${GREEN}Starting all services (production mode)...${NC}"
        make start
        ;;
    "start-dev")
        echo -e "${GREEN}Starting all services (development mode)...${NC}"
        make start-dev
        ;;
    "start-monitoring")
        echo -e "${GREEN}Starting all services (monitoring mode)...${NC}"
        make start-monitoring
        ;;
    "stop")
        echo -e "${YELLOW}Stopping all services...${NC}"
        make stop
        ;;
    "status")
        echo -e "${BLUE}Service status:${NC}"
        make status
        ;;
    "logs")
        echo -e "${BLUE}Service logs:${NC}"
        make logs
        ;;
    "health")
        echo -e "${BLUE}Health check:${NC}"
        make health-check
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  start              - Start all services (production)"
        echo "  start-dev          - Start all services with Redis (development) [default]"
        echo "  start-monitoring   - Start all services with monitoring"
        echo "  stop               - Stop all services"
        echo "  status             - Show service status"
        echo "  logs               - Show service logs"
        echo "  health             - Check service health"
        echo "  help               - Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0                 # Start development environment"
        echo "  $0 start           # Start production environment"
        echo "  $0 stop            # Stop all services"
        echo "  $0 status          # Show service status"
        ;;
    *)
        echo -e "${YELLOW}Unknown command: $1${NC}"
        echo "Use '$0 help' to see available commands"
        exit 1
        ;;
esac