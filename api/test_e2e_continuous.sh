#!/bin/bash
# Continuous E2E Call Test - Every Minute
# =======================================
# This script launches a test call every minute.
# Press Ctrl+C to stop.

echo "🔄 Starting continuous call testing (every 60 seconds)"
echo "Press Ctrl+C to stop"
echo "=========================================="

# Counter for tracking calls
call_count=0

while true; do
    call_count=$((call_count + 1))
    
    echo ""
    echo "📞 Call #${call_count} - $(date '+%Y-%m-%d %H:%M:%S')"
    echo "----------------------------------------"
    
    # Run the test
    python api/test_e2e_launch.py
    
    exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo "✅ Call #${call_count} completed"
    else
        echo "❌ Call #${call_count} failed (exit code: $exit_code)"
    fi
    
    echo ""
    echo "⏳ Waiting 60 seconds until next call..."
    echo "   Next call will be at: $(date -v+60S '+%Y-%m-%d %H:%M:%S')"
    
    sleep 60
done
