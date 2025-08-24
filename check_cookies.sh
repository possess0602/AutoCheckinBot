#!/bin/bash

# Cookie health check script
echo "🍪 Cookie Health Check"
echo "====================="

# Check if alert file exists
ALERT_FILE="logs/cookie_alert.txt"
if [ -f "$ALERT_FILE" ]; then
    echo "⚠️  COOKIE ALERT DETECTED!"
    echo "Content:"
    cat "$ALERT_FILE"
    echo ""
    echo "🔧 Quick fix:"
    echo "  1. Run: python manual_punch.py update"
    echo "  2. Restart service: ./stop_service.sh && ./start_service.sh"
    echo ""
    exit 1
fi

# Test cookies by running a test punch
echo "Testing current cookies..."
python -c "
from manual_punch import punch_attendance
import sys

try:
    result = punch_attendance(attendance_type=1)
    if result.get('success', False):
        print('✅ Cookies are working fine!')
        sys.exit(0)
    else:
        error = result.get('error', 'Unknown error')
        if 'Cookie expired' in error or 'refresh failed' in error:
            print('❌ Cookies are expired!')
            print('💡 Run: python manual_punch.py update')
            sys.exit(2)
        else:
            print(f'⚠️  Test failed but may not be cookie issue: {error}')
            sys.exit(1)
except Exception as e:
    print(f'❌ Test failed with exception: {e}')
    sys.exit(1)
"

EXIT_CODE=$?
case $EXIT_CODE in
    0)
        echo "✅ All systems operational!"
        ;;
    1)
        echo "⚠️  Test failed - check system status"
        ;;
    2)
        echo "🍪 Cookie update required!"
        echo "Run: python manual_punch.py update"
        ;;
esac

exit $EXIT_CODE 