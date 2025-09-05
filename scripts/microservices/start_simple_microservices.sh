#!/bin/bash

# MOTOSPECT Simple Microservices Startup Script
# This script starts all microservices with their simple implementations

set -e

echo "🚀 Starting MOTOSPECT Simple Microservices..."
echo "=============================================="

# Function to check if port is available
check_port() {
    local port=$1
    if netstat -tuln | grep -q ":$port "; then
        echo "⚠️  Port $port is already in use"
        return 1
    fi
    return 0
}

# Function to wait for service to start
wait_for_service() {
    local port=$1
    local service_name=$2
    local max_attempts=10
    local attempt=1
    
    echo "⏳ Waiting for $service_name to start on port $port..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:$port/health > /dev/null 2>&1; then
            echo "✅ $service_name is healthy on port $port"
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done
    
    echo "❌ $service_name failed to start on port $port"
    return 1
}

# Kill existing microservices processes
echo "🧹 Cleaning up existing processes..."
pkill -f "simple_main.py" || true
sleep 2

# Service configurations
declare -A SERVICES=(
    [8001]="VIN Decoder Service:services/vin-decoder-service"
    [8002]="Fault Detector Service:services/fault-detector-service" 
    [8003]="Diagnostic Service:services/diagnostic-service"
    [8004]="MQTT Bridge Service:services/mqtt-bridge-service"
    [8000]="API Gateway:services/api-gateway"
)

# Start services in order (gateway last)
START_ORDER=(8001 8002 8003 8004 8000)

for port in "${START_ORDER[@]}"; do
    IFS=':' read -ra SERVICE_INFO <<< "${SERVICES[$port]}"
    SERVICE_NAME="${SERVICE_INFO[0]}"
    SERVICE_PATH="${SERVICE_INFO[1]}"
    
    echo ""
    echo "🔧 Starting $SERVICE_NAME on port $port..."
    
    if ! check_port $port; then
        echo "Skipping $SERVICE_NAME - port $port already in use"
        continue
    fi
    
    # Start the service
    cd "$SERVICE_PATH"
    PORT=$port nohup python3 simple_main.py > "../../logs/${SERVICE_NAME// /_}_$port.log" 2>&1 &
    SERVICE_PID=$!
    cd - > /dev/null
    
    echo "Started $SERVICE_NAME (PID: $SERVICE_PID)"
    
    # Wait for service to be healthy
    if wait_for_service $port "$SERVICE_NAME"; then
        echo "✅ $SERVICE_NAME successfully started"
    else
        echo "❌ $SERVICE_NAME failed to start properly"
    fi
done

echo ""
echo "🎉 Microservices startup complete!"
echo "=================================="
echo ""
echo "📊 Service Status:"
echo "API Gateway:        http://localhost:8000"
echo "VIN Decoder:        http://localhost:8001" 
echo "Fault Detector:     http://localhost:8002"
echo "Diagnostic Service: http://localhost:8003"
echo "MQTT Bridge:        http://localhost:8004"
echo ""
echo "🔍 Check all services: curl http://localhost:8000/services/status"
echo "📋 View logs: tail -f logs/*.log"
echo ""

# Final health check through API Gateway
echo "🏥 Performing final health check through API Gateway..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ All services are accessible through API Gateway"
    
    # Show service status summary
    echo ""
    echo "📈 Services Status Summary:"
    curl -s http://localhost:8000/services/status | python3 -m json.tool
else
    echo "❌ API Gateway health check failed"
    exit 1
fi
