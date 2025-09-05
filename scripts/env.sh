#!/bin/bash
# Common environment setup for all scripts

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load .env file if exists
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
fi

# Set default values if not in .env
export BACKEND_PORT=${BACKEND_PORT:-8030}
export FRONTEND_PORT=${FRONTEND_PORT:-3030}
export CUSTOMER_PORTAL_PORT=${CUSTOMER_PORTAL_PORT:-3040}
export REPORT_SERVICE_PORT=${REPORT_SERVICE_PORT:-3050}
export MQTT_PORT=${MQTT_PORT:-1884}

# Microservices ports
export API_GATEWAY_PORT=${API_GATEWAY_PORT:-8000}
export VIN_DECODER_PORT=${VIN_DECODER_PORT:-8001}
export FAULT_DETECTOR_PORT=${FAULT_DETECTOR_PORT:-8002}
export DIAGNOSTIC_PORT=${DIAGNOSTIC_PORT:-8003}
export MQTT_BRIDGE_PORT=${MQTT_BRIDGE_PORT:-8004}

# Python path
export PYTHONPATH="$PROJECT_ROOT/backend:$PROJECT_ROOT/lib/python:$PYTHONPATH"

# Colors for output
export RED='\033[0;31m'
export GREEN='\033[0;32m'
export YELLOW='\033[1;33m'
export BLUE='\033[0;34m'
export NC='\033[0m' # No Color

# Common functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

wait_for_service() {
    local url=$1
    local max_attempts=${2:-30}
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 1
    done
    return 1
}
