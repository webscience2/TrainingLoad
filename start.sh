#!/bin/bash

# TrainingLoad Application Startup Script
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGS_DIR="$PROJECT_ROOT/logs"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

echo "🚀 Starting TrainingLoad Application..."
echo "Project root: $PROJECT_ROOT"

# Create logs directory if it doesn't exist
mkdir -p "$LOGS_DIR"

# Kill any existing processes on our ports
echo "📋 Cleaning up existing processes..."
lsof -ti:8000 2>/dev/null | xargs kill -9 2>/dev/null || echo "No processes on port 8000"
lsof -ti:5173 2>/dev/null | xargs kill -9 2>/dev/null || echo "No processes on port 5173"

# Function to start backend
start_backend() {
    echo "🔧 Starting backend server..."
    cd "$BACKEND_DIR"
    
    # Start backend with uv and log to file
    nohup uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000 \
        > "$LOGS_DIR/backend.log" 2>&1 &
    
    BACKEND_PID=$!
    echo $BACKEND_PID > "$LOGS_DIR/backend.pid"
    echo "Backend started with PID: $BACKEND_PID"
    echo "Backend logs: $LOGS_DIR/backend.log"
}

# Function to start frontend
start_frontend() {
    echo "🎨 Starting frontend server..."
    cd "$FRONTEND_DIR"
    
    # Start frontend and log to file
    nohup npx vite > "$LOGS_DIR/frontend.log" 2>&1 &
    
    FRONTEND_PID=$!
    echo $FRONTEND_PID > "$LOGS_DIR/frontend.pid"
    echo "Frontend started with PID: $FRONTEND_PID"
    echo "Frontend logs: $LOGS_DIR/frontend.log"
}

# Start both services
start_backend
sleep 3  # Give backend time to start
start_frontend

echo ""
echo "✅ TrainingLoad Application Started Successfully!"
echo ""
echo "🌐 Services:"
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:5173"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "📋 Process Management:"
echo "  Backend PID:  $(cat $LOGS_DIR/backend.pid 2>/dev/null || echo 'Not found')"
echo "  Frontend PID: $(cat $LOGS_DIR/frontend.pid 2>/dev/null || echo 'Not found')"
echo ""
echo "📊 Logs:"
echo "  Backend:  tail -f $LOGS_DIR/backend.log"
echo "  Frontend: tail -f $LOGS_DIR/frontend.log"
echo ""
echo "🛑 To stop: ./stop.sh"
echo ""
