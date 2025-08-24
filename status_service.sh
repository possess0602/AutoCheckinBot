#!/bin/bash

# Configuration variables
PID_FILE="attendance_service.pid"  # Windows compatible path
LOG_FILE="logs/attendance_service.log"

echo "📊 Attendance Service Status Check"
echo "=================================="

# Check PID file
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    echo "PID file: $PID_FILE (PID: $PID)"
    
    # Check if process is running (Windows compatible)
    if tasklist /FI "PID eq $PID" 2>/dev/null | grep -q "$PID"; then
        echo "Status: ✅ Running"
        
        # Show process information (Windows compatible)
        echo ""
        echo "Process information:"
        tasklist /FI "PID eq $PID" /FO table
        
    else
        echo "Status: ❌ Stopped (PID file exists but process not found)"
        echo "Suggestion: rm -f $PID_FILE"
    fi
else
    echo "PID file: Not found"
    
    # Look for possible orphaned processes (Windows compatible)
    PIDS=$(tasklist /FI "IMAGENAME eq python.exe" /FO csv | grep "attendance_service.py" | cut -d',' -f2 | tr -d '"' 2>/dev/null)
    if [ ! -z "$PIDS" ]; then
        echo "Status: ⚠️  Orphaned processes found"
        echo "Orphaned process PIDs: $PIDS"
        echo "Suggestion: ./stop_service.sh"
    else
        echo "Status: ❌ Not running"
    fi
fi

echo ""
echo "Schedule information:"
echo "- Punch-in: Monday to Friday 09:10-09:20 (random)"
echo "- Punch-out: Monday to Friday 18:10-18:30 (guaranteed 9 hours)"

# Check log file
echo ""
if [ -f "$LOG_FILE" ]; then
    echo "Log file: $LOG_FILE"
    echo "File size: $(du -h "$LOG_FILE" | cut -f1)"
    echo "Last modified: $(stat -c %y "$LOG_FILE" 2>/dev/null || stat -f %Sm "$LOG_FILE" 2>/dev/null)"
    
    echo ""
    echo "Recent 5 log entries:"
    echo "===================="
    tail -n 5 "$LOG_FILE" 2>/dev/null || echo "Cannot read log file"
else
    echo "Log file: Not found"
fi

echo ""
echo "Management commands:"
echo "- Start service: ./start_service.sh"
echo "- Stop service: ./stop_service.sh"
echo "- View full logs: tail -f $LOG_FILE"
echo "- Reload config: kill -HUP <PID>" 