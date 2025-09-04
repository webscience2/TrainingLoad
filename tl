#!/bin/bash

# TrainingLoad Quick Management Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

show_help() {
    echo "TrainingLoad Management Script"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start       Start the TrainingLoad application"
    echo "  stop        Stop the TrainingLoad application"
    echo "  restart     Restart the TrainingLoad application"
    echo "  status      Show status of running processes"
    echo "  logs        Show recent backend logs"
    echo "  logs-live   Follow backend logs in real-time"
    echo "  help        Show this help message"
    echo ""
    echo "URLs:"
    echo "  Backend:    http://localhost:8000"
    echo "  Frontend:   http://localhost:5173"
    echo "  API Docs:   http://localhost:8000/docs"
    echo "  Dashboard:  http://localhost:8000/dashboard/1"
    echo "  Intervals:  file://$SCRIPT_DIR/intervals_icu_integration.html"
    echo ""
}

start_app() {
    echo "🚀 Starting TrainingLoad..."
    "$SCRIPT_DIR/start.sh"
}

stop_app() {
    echo "🛑 Stopping TrainingLoad..."
    "$SCRIPT_DIR/stop.sh"
}

restart_app() {
    echo "🔄 Restarting TrainingLoad..."
    stop_app
    sleep 2
    start_app
}

show_status() {
    echo "📊 TrainingLoad Status"
    echo "===================="
    
    # Check backend
    if [ -f "$SCRIPT_DIR/logs/backend.pid" ]; then
        BACKEND_PID=$(cat "$SCRIPT_DIR/logs/backend.pid")
        if ps -p $BACKEND_PID > /dev/null 2>&1; then
            echo "✅ Backend: Running (PID: $BACKEND_PID)"
        else
            echo "❌ Backend: Not running (stale PID file)"
        fi
    else
        echo "❌ Backend: Not running"
    fi
    
    # Check frontend
    if [ -f "$SCRIPT_DIR/logs/frontend.pid" ]; then
        FRONTEND_PID=$(cat "$SCRIPT_DIR/logs/frontend.pid")
        if ps -p $FRONTEND_PID > /dev/null 2>&1; then
            echo "✅ Frontend: Running (PID: $FRONTEND_PID)"
        else
            echo "❌ Frontend: Not running (stale PID file)"
        fi
    else
        echo "❌ Frontend: Not running"
    fi
    
    echo ""
    echo "🌐 URLs:"
    echo "   Backend:  http://localhost:8000"
    echo "   Frontend: http://localhost:5173"
    echo "   API Docs: http://localhost:8000/docs"
    echo ""
    
    # Test backend connectivity
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend responding"
    else
        echo "❌ Backend not responding"
    fi
}

show_logs() {
    echo "📋 Recent Backend Logs:"
    echo "======================"
    if [ -f "$SCRIPT_DIR/logs/backend.log" ]; then
        tail -20 "$SCRIPT_DIR/logs/backend.log"
    else
        echo "No backend logs found"
    fi
}

follow_logs() {
    echo "📋 Following Backend Logs (Ctrl+C to exit):"
    echo "============================================"
    if [ -f "$SCRIPT_DIR/logs/backend.log" ]; then
        tail -f "$SCRIPT_DIR/logs/backend.log"
    else
        echo "No backend logs found"
    fi
}

# Main command handling
case "${1:-help}" in
    start)
        start_app
        ;;
    stop)
        stop_app
        ;;
    restart)
        restart_app
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    logs-live)
        follow_logs
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
