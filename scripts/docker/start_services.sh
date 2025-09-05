#!/bin/bash

echo "Starting MOTOSPECT Services..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q fastapi uvicorn aiohttp paho-mqtt python-dotenv python-multipart starlette websockets pandas numpy

# Start backend
echo "Starting backend on port 8030..."
cd backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8030 --reload &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 5

# Check if backend is running
if curl -s http://localhost:8030/health > /dev/null 2>&1; then
    echo "✓ Backend started successfully (PID: $BACKEND_PID)"
else
    echo "✗ Backend failed to start"
    exit 1
fi

# Start frontend
echo "Starting frontend on port 3030..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi
PORT=3030 npm start &
FRONTEND_PID=$!
cd ..

echo ""
echo "=================================="
echo "Services Started Successfully!"
echo "=================================="
echo "Backend API: http://localhost:8030"
echo "API Docs: http://localhost:8030/docs"
echo "Frontend: http://localhost:3030"
echo ""
echo "PIDs:"
echo "  Backend: $BACKEND_PID"
echo "  Frontend: $FRONTEND_PID"
echo ""
echo "To stop: kill $BACKEND_PID $FRONTEND_PID"
echo "=================================="
echo ""
echo "Press Ctrl+C to stop all services"

# Keep script running
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
