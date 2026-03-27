#!/bin/bash
#
# PhysiqAI API Health Check Script
# Pings the API health endpoint and restarts service if failing
#

# Configuration
API_URL="http://localhost:5001/api/health"
MAX_FAILURES=3
CHECK_INTERVAL=30
LOG_FILE="/home/clawd/.openclaw/workspace/projects/physiqai/logs/health_check.log"
STATE_FILE="/tmp/physiqai_health_failures"
SERVICE_NAME="physiqai-api"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Initialize failure counter if not exists
if [[ ! -f "$STATE_FILE" ]]; then
    echo "0" > "$STATE_FILE"
fi

FAILURE_COUNT=$(cat "$STATE_FILE")

# Perform health check
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$API_URL" 2>/dev/null)

if [[ "$HTTP_CODE" == "200" ]]; then
    # API is healthy
    if [[ "$FAILURE_COUNT" -gt 0 ]]; then
        log "INFO: API recovered after $FAILURE_COUNT failure(s)"
        echo "0" > "$STATE_FILE"
    fi
    log "INFO: Health check PASSED (HTTP $HTTP_CODE)"
    exit 0
else
    # API is not responding properly
    FAILURE_COUNT=$((FAILURE_COUNT + 1))
    echo "$FAILURE_COUNT" > "$STATE_FILE"
    
    log "WARNING: Health check FAILED (HTTP ${HTTP_CODE:-'no response'}) - Failure $FAILURE_COUNT/$MAX_FAILURES"
    
    if [[ "$FAILURE_COUNT" -ge "$MAX_FAILURES" ]]; then
        log "CRITICAL: API failed $MAX_FAILURES consecutive checks. Restarting service..."
        
        # Attempt service restart
        if systemctl restart "$SERVICE_NAME" 2>/dev/null; then
            log "INFO: Service restart initiated successfully"
            # Reset failure count after restart
            echo "0" > "$STATE_FILE"
            
            # Wait a moment and verify
            sleep 5
            VERIFY_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$API_URL" 2>/dev/null)
            if [[ "$VERIFY_CODE" == "200" ]]; then
                log "INFO: Service restart verified - API responding (HTTP 200)"
            else
                log "ERROR: Service restart failed verification (HTTP ${VERIFY_CODE:-'no response'})"
            fi
        else
            log "ERROR: Failed to restart service. Is the service installed?"
        fi
    fi
    
    exit 1
fi
