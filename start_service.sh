#!/bin/bash

# Configuration variables
SERVICE_NAME="attendance_service"
PYTHON_SCRIPT="attendance_service.py"
PID_FILE="attendance_service.pid"  # Windows compatible path
LOG_FILE="logs/attendance_service.log"

# Create logs directory
mkdir -p logs

echo "🚀 Starting attendance service..."

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "❌ Python not found, please ensure Python is installed"
    exit 1
fi

# Check if already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    # Windows compatible process check
    if tasklist /FI "PID eq $PID" 2>/dev/null | grep -q "$PID"; then
        echo "❗ Service already running (PID: $PID)"
        echo "To restart, please run: ./stop_service.sh first"
        exit 1
    else
        echo "Cleaning up old PID file..."
        rm -f "$PID_FILE"
    fi
fi

# Start service in background
nohup python "$PYTHON_SCRIPT" > "$LOG_FILE" 2>&1 &
SERVICE_PID=$!

# Wait a moment to confirm service startup
sleep 2

# Check if service started successfully (Windows compatible)
if tasklist /FI "PID eq $SERVICE_PID" 2>/dev/null | grep -q "$SERVICE_PID"; then
    echo "✅ Service started in background"
    echo "📊 PID: $SERVICE_PID"
    echo "📁 Log file: $LOG_FILE"
    echo ""
    echo "Management commands:"
    echo "  Check status: ./status_service.sh"
    echo "  View logs: tail -f $LOG_FILE"
    echo "  Stop service: ./stop_service.sh"
    echo "  Reload config: kill -HUP $SERVICE_PID"
else
    echo "❌ Service startup failed, please check logs: $LOG_FILE"
    exit 1
fi 