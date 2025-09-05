#!/bin/bash

# MOTOSPECT Simple Microservices Stop Script
# This script stops all running microservices

echo "🛑 Stopping MOTOSPECT Simple Microservices..."
echo "============================================="

# Kill all simple_main.py processes
echo "🧹 Terminating microservice processes..."
pkill -f "simple_main.py" && echo "✅ Microservices stopped" || echo "ℹ️  No microservices were running"

# Check for any remaining processes
echo ""
echo "🔍 Checking for remaining processes..."
REMAINING=$(ps aux | grep "simple_main.py" | grep -v grep || true)

if [ -z "$REMAINING" ]; then
    echo "✅ All microservices have been stopped successfully"
else
    echo "⚠️  Some processes may still be running:"
    echo "$REMAINING"
fi

echo ""
echo "🎯 Microservices shutdown complete!"
