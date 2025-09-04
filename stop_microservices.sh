#!/bin/bash
# MOTOSPECT Microservices Stop Script

echo "🛑 Stopping MOTOSPECT Microservices..."

# Kill all Python main.py processes (our microservices)
if pgrep -f "python3 main.py" > /dev/null; then
    echo "🔄 Terminating microservice processes..."
    pkill -f "python3 main.py"
    sleep 2
    
    # Force kill if still running
    if pgrep -f "python3 main.py" > /dev/null; then
        echo "🔨 Force killing remaining processes..."
        pkill -9 -f "python3 main.py"
    fi
else
    echo "ℹ️  No microservice processes found"
fi

# Clean up PID files
if [ -d "logs" ]; then
    echo "🧹 Cleaning up PID files..."
    rm -f logs/*.pid
fi

echo "✅ All MOTOSPECT microservices stopped"

# Show port status
echo ""
echo "📊 Port Status Check:"
echo "===================="
ports=(8000 8001 8002 8003 8004)
for port in "${ports[@]}"; do
    if nc -z localhost $port 2>/dev/null; then
        echo "⚠️  Port $port still in use"
    else
        echo "✅ Port $port available"
    fi
done
