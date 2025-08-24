#!/bin/bash

# Configuration variables
PID_FILE="attendance_service.pid"  # Windows compatible path

echo "🛑 Stopping attendance service..."

# Check if PID file exists
if [ ! -f "$PID_FILE" ]; then
    echo "❗ PID file not found, service may not be running"
    
    # Try to find and terminate related processes (Windows compatible)
    PIDS=$(tasklist /FI "IMAGENAME eq python.exe" /FO csv | grep "attendance_service.py" | cut -d',' -f2 | tr -d '"' 2>/dev/null)
    if [ ! -z "$PIDS" ]; then
        echo "Found related processes, terminating..."
        echo "$PIDS" | xargs taskkill /PID /F
        sleep 2
        echo "✅ Cleanup completed"
    else
        echo "❌ No related processes found"
    fi
    exit 0
fi

# Read PID
PID=$(cat "$PID_FILE")

# Check if process exists (Windows compatible)
if ! tasklist /FI "PID eq $PID" 2>/dev/null | grep -q "$PID"; then
    echo "❗ Process $PID does not exist, cleaning up PID file"
    rm -f "$PID_FILE"
    exit 0
fi

# Gracefully stop service (Windows compatible)
echo "Sending TERM signal to process $PID..."
taskkill /PID $PID /T

# Wait for process to end
for i in {1..10}; do
    if ! tasklist /FI "PID eq $PID" 2>/dev/null | grep -q "$PID"; then
        echo "✅ Service stopped gracefully"
        rm -f "$PID_FILE"
        exit 0
    fi
    echo "Waiting for service to stop... ($i/10)"
    sleep 1
done

# Force terminate
echo "⚠️  Process not responding, force killing..."
taskkill /PID $PID /F
sleep 1

if ! tasklist /FI "PID eq $PID" 2>/dev/null | grep -q "$PID"; then
    echo "✅ Service force stopped"
    rm -f "$PID_FILE"
else
    echo "❌ Unable to stop service"
    exit 1
fi 