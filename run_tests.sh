#!/bin/bash

# Exit on error
set -e

echo "Starting Docker Compose services..."
docker compose up -d --build

echo "Waiting for services to be healthy..."

# Wait for backend to be ready
until curl -s http://localhost:8030/health >/dev/null; do
    echo "Waiting for backend to be ready..."
    sleep 5
done

# Wait for frontend to be ready
until curl -s http://localhost:3030 >/dev/null; do
    echo "Waiting for frontend to be ready..."
    sleep 5
done

# Wait for customer portal to be ready
until curl -s http://localhost:3040 >/dev/null; do
    echo "Waiting for customer portal to be ready..."
    sleep 5
done

echo "All services are up and running!"

# Install test dependencies
echo "Installing test dependencies..."
pip install -r requirements-automation.txt

# Run the tests
echo "Running automated tests..."
python automate_customer_portal.py

if [ $? -eq 0 ]; then
    echo "All tests passed successfully!"
    exit 0
else
    echo "Tests failed!"
    exit 1
fi
