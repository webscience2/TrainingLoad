#!/bin/bash

# TrainingLoad Application Shutdown Script
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGS_DIR="$PROJECT_ROOT/logs"

echo "🛑 Stopping TrainingLoad Application..."

# Function to stop a service by PID file
stop_service() {
    local service_name=$1
    local pid_file="$LOGS_DIR/${service_name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "Stopping $service_name (PID: $pid)..."
            kill "$pid"
            sleep 2
            
            # Force kill if still running
            if kill -0 "$pid" 2>/dev/null; then
                echo "Force killing $service_name..."
                kill -9 "$pid" 2>/dev/null || true
            fi
        else
            echo "$service_name process (PID: $pid) not running"
        fi
        rm -f "$pid_file"
    else
        echo "No PID file found for $service_name"
    fi
}

# Stop services
stop_service "backend"
stop_service "frontend"

# Kill any remaining processes on our ports (backup cleanup)
echo "🧹 Final cleanup of ports 8000 and 5173..."
lsof -ti:8000 2>/dev/null | xargs kill -9 2>/dev/null || echo "Port 8000 clear"
lsof -ti:5173 2>/dev/null | xargs kill -9 2>/dev/null || echo "Port 5173 clear"

echo ""
echo "✅ TrainingLoad Application Stopped"
echo ""
echo "📊 Logs preserved in: $LOGS_DIR/"
echo "   - backend.log"
echo "   - frontend.log"
echo ""
