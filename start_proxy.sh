#!/bin/bash
# Devstral Proxy Startup Script

set -e

# Default values
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
HOST="0.0.0.0"
PORT="9000"
RELOAD=false
DEBUG=false
LOG_LEVEL="info"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --host)
            HOST="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --reload)
            RELOAD=true
            shift
            ;;
        --debug)
            DEBUG=true
            LOG_LEVEL="debug"
            shift
            ;;
        --log-level)
            LOG_LEVEL="$2"
            shift 2
            ;;
        --help)
            echo "Devstral Proxy Startup Script"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --host HOST         Proxy server host (default: 0.0.0.0)"
            echo "  --port PORT         Proxy server port (default: 9000)"
            echo "  --reload            Enable auto-reload for development"
            echo "  --debug             Enable debug mode"
            echo "  --log-level LEVEL   Set log level (debug, info, warning, error)"
            echo "  --help              Show this help message"
            echo ""
            echo "Environment Variables:"
            echo "  VLLM_BASE           VLLM server URL"
            echo "  PROXY_HOST          Proxy server host"
            echo "  PROXY_PORT          Proxy server port"
            echo "  DEBUG               Enable debug mode"
            echo "  LOG_LEVEL           Set log level"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Change to project directory
cd "$PROJECT_ROOT"

# Check if virtual environment exists
if [[ -d "venv" ]]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
elif [[ -f "pyproject.toml" ]] && command -v poetry &> /dev/null; then
    echo "Using Poetry environment..."
    poetry shell
else
    echo "Warning: No virtual environment found"
fi

# Check if required packages are installed
python -c "import fastapi, uvicorn, httpx, pydantic" 2>/dev/null || {
    echo "Installing dependencies..."
    if command -v poetry &> /dev/null; then
        poetry install
    else
        pip install -e .
    fi
}

# Check if .env file exists
if [[ ! -f ".env" ]]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env file with your configuration"
fi

# Set environment variables for the script
export PROXY_HOST="$HOST"
export PROXY_PORT="$PORT"
export DEBUG="$DEBUG"
export LOG_LEVEL="$LOG_LEVEL"

# Build the command
CMD="python devstral_proxy/main.py"

# Add reload flag if requested
if [[ "$RELOAD" == "true" ]]; then
    CMD="$CMD --reload"
fi

# Display startup information
echo "==========================================="
echo "Devstral Proxy Starting Up"
echo "==========================================="
echo "Host: $HOST"
echo "Port: $PORT"
echo "Debug: $DEBUG"
echo "Log Level: $LOG_LEVEL"
echo "Reload: $RELOAD"
echo "==========================================="

# Start the proxy
exec $CMD