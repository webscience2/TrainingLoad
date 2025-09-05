#!/bin/bash

# TrainingLoad Log Viewer Script
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGS_DIR="$PROJECT_ROOT/logs"

show_help() {
    echo "TrainingLoad Log Viewer"
    echo ""
    echo "Usage: ./logs.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -b, --backend     Show backend logs"
    echo "  -f, --frontend    Show frontend logs"
    echo "  -a, --all         Show both logs side by side"
    echo "  -s, --status      Show service status"
    echo "  -h, --help        Show this help"
    echo ""
    echo "Examples:"
    echo "  ./logs.sh -b         # Follow backend logs"
    echo "  ./logs.sh -f         # Follow frontend logs"
    echo "  ./logs.sh -a         # Show both logs"
    echo "  ./logs.sh -s         # Check service status"
    echo ""
}

show_status() {
    echo "🔍 TrainingLoad Service Status"
    echo ""
    
    # Check backend
    if [ -f "$LOGS_DIR/backend.pid" ]; then
        backend_pid=$(cat "$LOGS_DIR/backend.pid")
        if kill -0 "$backend_pid" 2>/dev/null; then
            echo "✅ Backend:  Running (PID: $backend_pid) - http://localhost:8000"
        else
            echo "❌ Backend:  Not running (stale PID file)"
        fi
    else
        echo "❌ Backend:  Not running (no PID file)"
    fi
    
    # Check frontend
    if [ -f "$LOGS_DIR/frontend.pid" ]; then
        frontend_pid=$(cat "$LOGS_DIR/frontend.pid")
        if kill -0 "$frontend_pid" 2>/dev/null; then
            echo "✅ Frontend: Running (PID: $frontend_pid) - http://localhost:5173"
        else
            echo "❌ Frontend: Not running (stale PID file)"
        fi
    else
        echo "❌ Frontend: Not running (no PID file)"
    fi
    
    echo ""
    echo "🌐 Port Usage:"
    lsof -i:8000 2>/dev/null || echo "Port 8000: Available"
    lsof -i:5173 2>/dev/null || echo "Port 5173: Available"
    echo ""
}

# Parse command line arguments
case "${1:-}" in
    -b|--backend)
        echo "📋 Following backend logs (Ctrl+C to exit)..."
        tail -f "$LOGS_DIR/backend.log" 2>/dev/null || echo "No backend logs found"
        ;;
    -f|--frontend)
        echo "🎨 Following frontend logs (Ctrl+C to exit)..."
        tail -f "$LOGS_DIR/frontend.log" 2>/dev/null || echo "No frontend logs found"
        ;;
    -a|--all)
        echo "📋 Following all logs (Ctrl+C to exit)..."
        echo "Backend logs will be prefixed with [BACKEND]"
        echo "Frontend logs will be prefixed with [FRONTEND]"
        echo ""
        (tail -f "$LOGS_DIR/backend.log" 2>/dev/null | sed 's/^/[BACKEND] /' &
         tail -f "$LOGS_DIR/frontend.log" 2>/dev/null | sed 's/^/[FRONTEND] /' &
         wait)
        ;;
    -s|--status)
        show_status
        ;;
    -h|--help|"")
        show_help
        ;;
    *)
        echo "Unknown option: $1"
        echo "Use ./logs.sh --help for usage information"
        exit 1
        ;;
esac
