#!/bin/bash

# MOTOSPECT Quick Start Script
echo "==================================="
echo "MOTOSPECT System Startup"
echo "==================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

# Load environment variables
source .env

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install --user -q fastapi uvicorn[standard] aiohttp paho-mqtt python-dotenv python-multipart websockets starlette numpy pandas

# Check Docker
if command -v docker &> /dev/null; then
    echo "Docker found, using Docker Compose..."
    
    # Stop any existing containers
    docker-compose down 2>/dev/null
    
    # Build and start services
    echo "Building Docker images..."
    docker-compose build
    
    echo "Starting services..."
    docker-compose up -d
    
    # Wait for services
    echo "Waiting for services to start..."
    sleep 10
    
    # Check status
    echo ""
    echo "Service Status:"
    docker-compose ps
    
    echo ""
    echo "Testing backend health..."
    curl -s http://localhost:8030/health | python3 -m json.tool 2>/dev/null || echo "Backend not ready yet"
    
else
    echo "Docker not found, running locally..."
    
    # Start backend
    echo "Starting backend on port 8030..."
    cd backend
    python3 -m uvicorn main:app --host 0.0.0.0 --port 8030 --reload &
    BACKEND_PID=$!
    cd ..
    
    # Start frontend
    echo "Starting frontend on port 3030..."
    cd frontend
    npm install 2>/dev/null
    PORT=3030 npm start &
    FRONTEND_PID=$!
    cd ..
    
    echo "Services started:"
    echo "  Backend PID: $BACKEND_PID"
    echo "  Frontend PID: $FRONTEND_PID"
    echo ""
    echo "To stop services, run: kill $BACKEND_PID $FRONTEND_PID"
fi

echo ""
echo "==================================="
echo "MOTOSPECT is starting up!"
echo "==================================="
echo "Backend API: http://localhost:8030"
echo "Frontend: http://localhost:3030"
echo "Customer Portal: http://localhost:3040"
echo "API Documentation: http://localhost:8030/docs"
echo ""
echo "Use 'make status' to check service status"
echo "Use 'make test-complete' to run system tests"
