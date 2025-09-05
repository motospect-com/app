#!/bin/bash
# MOTOSPECT Microservices Startup Script
# Quick startup without complex Service Manager dependencies

set -e

echo "🚀 Starting MOTOSPECT Microservices Ecosystem"
echo "================================================"

# Function to check if port is available
check_port() {
    if ! nc -z localhost $1 2>/dev/null; then
        return 0  # Port is available
    else
        return 1  # Port is in use
    fi
}

# Load environment variables from .env
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Function to start service
start_service() {
    local service_name=$1
    local port=$2
    local service_dir=$3
    
    echo "🔄 Starting $service_name on port $port..."
    
    if ! check_port $port; then
        echo "⚠️  Port $port already in use, skipping $service_name"
        return
    fi
    
    cd services/$service_dir
    export PORT=$port
    export PYTHONPATH="$(pwd)/../../backend:$PYTHONPATH"
    
    # Install requirements if not present
    if [ -f "requirements.txt" ] && [ ! -f ".deps_installed" ]; then
        echo "📦 Installing dependencies for $service_name..."
        pip3 install -r requirements.txt > /dev/null 2>&1
        touch .deps_installed
    fi
    
    # Start service in background
    nohup python3 main.py > "../../logs/${service_name}.log" 2>&1 &
    echo $! > "../../logs/${service_name}.pid"
    
    # Wait a moment for startup
    sleep 2
    
    # Check if service started successfully
    if check_port $port; then
        echo "❌ Failed to start $service_name"
    else
        echo "✅ $service_name started successfully"
    fi
    
    cd - > /dev/null
}

# Create logs directory
mkdir -p logs

# Stop any existing services
echo "🛑 Stopping existing services..."
pkill -f "python3 main.py" 2>/dev/null || true
sleep 1

# Start services in dependency order
echo ""
echo "🚀 Starting microservices..."

# 1. VIN Decoder Service (no dependencies)
start_service "VIN Decoder Service" "${VIN_DECODER_SERVICE_PORT:-8001}" "vin-decoder-service"

# 2. Fault Detector Service (no dependencies)  
start_service "Fault Detector Service" "${FAULT_DETECTOR_SERVICE_PORT:-8002}" "fault-detector-service"

# 3. MQTT Bridge Service (no dependencies)
start_service "MQTT Bridge Service" "${MQTT_BRIDGE_SERVICE_PORT:-8004}" "mqtt-bridge-service"

# 4. Diagnostic Service (depends on VIN + Fault services)
start_service "Diagnostic Service" "${DIAGNOSTIC_SERVICE_PORT:-8003}" "diagnostic-service"

# 5. API Gateway (depends on all services)
start_service "API Gateway" "${API_GATEWAY_PORT:-8000}" "api-gateway"

echo ""
echo "⏳ Waiting for services to fully initialize..."
sleep 3

echo ""
echo "📊 Service Status Check:"
echo "========================"

services=("vin-decoder-service:${VIN_DECODER_SERVICE_PORT:-8001}" "fault-detector-service:${FAULT_DETECTOR_SERVICE_PORT:-8002}" "diagnostic-service:${DIAGNOSTIC_SERVICE_PORT:-8003}" "mqtt-bridge-service:${MQTT_BRIDGE_SERVICE_PORT:-8004}" "api-gateway:${API_GATEWAY_PORT:-8000}")

for service_port in "${services[@]}"; do
    IFS=':' read -r service port <<< "$service_port"
    
    if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
        echo "✅ $service (port $port) - Healthy"
    else
        echo "❌ $service (port $port) - Not responding"
    fi
done

echo ""
echo "🌐 Service URLs:"
echo "================"
echo "🔧 API Gateway:          http://localhost:${API_GATEWAY_PORT:-8000}"
echo "📖 API Documentation:    http://localhost:${API_GATEWAY_PORT:-8000}/docs"
echo "🏷️  VIN Decoder:          http://localhost:${VIN_DECODER_SERVICE_PORT:-8001}"
echo "🔍 Fault Detector:       http://localhost:${FAULT_DETECTOR_SERVICE_PORT:-8002}"
echo "📋 Diagnostic Service:   http://localhost:${DIAGNOSTIC_SERVICE_PORT:-8003}"
echo "📡 MQTT Bridge:          http://localhost:${MQTT_BRIDGE_SERVICE_PORT:-8004}"

echo ""
echo "🎯 Quick Test Commands:"
echo "======================="
echo "curl http://localhost:${API_GATEWAY_PORT:-8000}/health                    # API Gateway health"
echo "curl http://localhost:${API_GATEWAY_PORT:-8000}/api/vin/decode/1HGBH41JXMN109186  # VIN decode"
echo "curl http://localhost:${VIN_DECODER_SERVICE_PORT:-8001}/api/vin/info             # VIN service info"
echo "curl http://localhost:${FAULT_DETECTOR_SERVICE_PORT:-8002}/api/fault/info           # Fault service info"

echo ""
echo "📄 View logs:"
echo "============="
echo "tail -f logs/vin-decoder-service.log"
echo "tail -f logs/fault-detector-service.log"
echo "tail -f logs/diagnostic-service.log"
echo "tail -f logs/mqtt-bridge-service.log"
echo "tail -f logs/api-gateway.log"

echo ""
echo "🛑 To stop all services:"
echo "========================"
echo "./stop_microservices.sh"

echo ""
echo "🎉 MOTOSPECT Microservices started successfully!"
echo "💡 All services are independent and can be scaled individually"
