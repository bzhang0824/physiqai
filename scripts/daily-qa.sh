#!/bin/bash
# PhysiqAI Daily QA Automation Script
# Runs every day at 6 AM UTC via cron
# Reports to: mission-control.json and Slack/Telegram

APP_DIR="/home/clawd/.openclaw/workspace/projects/physiqai"
LOG_DIR="$APP_DIR/logs"
QA_LOG="$LOG_DIR/daily-qa-$(date +%Y%m%d).log"
REPORT_FILE="$APP_DIR/qa-reports/latest.json"

mkdir -p $LOG_DIR $(dirname $REPORT_FILE)

echo "=== PhysiqAI Daily QA Report $(date) ===" > $QA_LOG

# Function to log and output
log() {
    echo "$1" | tee -a $QA_LOG
}

# 1. CODE QUALITY CHECKS
log "\n🔍 1. CODE QUALITY CHECKS"

# Check for console.logs
CONSOLE_LOGS=$(grep -r "console.log" $APP_DIR/app --include="*.js" 2>/dev/null | wc -l)
log "   Console.log statements: $CONSOLE_LOGS"

# Check for TODO/FIXME
TODOS=$(grep -ri "TODO\|FIXME" $APP_DIR/app --include="*.js" --include="*.html" 2>/dev/null | wc -l)
log "   TODO/FIXME items: $TODOS"

# Check for error handling
TRY_CATCH=$(grep -r "try {" $APP_DIR/app --include="*.js" 2>/dev/null | wc -l)
log "   Try/catch blocks: $TRY_CATCH"

# 2. FILE INVENTORY
log "\n📁 2. FILE INVENTORY"
HTML_COUNT=$(find $APP_DIR/app -name "*.html" 2>/dev/null | wc -l)
JS_COUNT=$(find $APP_DIR/app -name "*.js" 2>/dev/null | wc -l)
CSS_COUNT=$(find $APP_DIR/app -name "*.css" 2>/dev/null | wc -l)
log "   HTML files: $HTML_COUNT"
log "   JS files: $JS_COUNT"
log "   CSS files: $CSS_COUNT"

# 3. DATA HEALTH CHECK
log "\n💾 3. DATA HEALTH CHECK"
if [ -f "$APP_DIR/data/collected/database.json" ]; then
    POSTS=$(cat $APP_DIR/data/collected/database.json 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d['posts']))" 2>/dev/null || echo "0")
    log "   Total posts: $POSTS"
else
    log "   ⚠️  Database file missing!"
fi

# 4. CHECK FOR CRITICAL FILES
log "\n⚠️  4. CRITICAL FILES CHECK"
CRITICAL_FILES=(
    "app/index.html"
    "app/avatar.html"
    "app/dashboard.html"
    "app/integration.js"
)

MISSING_FILES=0
for file in "${CRITICAL_FILES[@]}"; do
    if [ ! -f "$APP_DIR/$file" ]; then
        log "   ❌ Missing: $file"
        MISSING_FILES=$((MISSING_FILES + 1))
    fi
done

if [ $MISSING_FILES -eq 0 ]; then
    log "   ✅ All critical files present"
fi

# 5. GENERATE QA SCORE
log "\n📊 5. QA SCORE CALCULATION"

# Scoring algorithm
SCORE=100

# Deduct for console.logs
if [ $CONSOLE_LOGS -gt 10 ]; then
    SCORE=$((SCORE - 10))
elif [ $CONSOLE_LOGS -gt 5 ]; then
    SCORE=$((SCORE - 5))
fi

# Deduct for TODOs
if [ $TODOS -gt 5 ]; then
    SCORE=$((SCORE - 5))
fi

# Deduct for missing error handling
if [ $TRY_CATCH -lt 5 ]; then
    SCORE=$((SCORE - 10))
fi

# Deduct for missing files
SCORE=$((SCORE - MISSING_FILES * 10))

log "   Daily QA Score: $SCORE/100"

# 6. GENERATE JSON REPORT
cat > $REPORT_FILE << EOF
{
    "date": "$(date -Iseconds)",
    "score": $SCORE,
    "checks": {
        "console_logs": $CONSOLE_LOGS,
        "todos": $TODOS,
        "try_catch": $TRY_CATCH,
        "missing_files": $MISSING_FILES,
        "html_files": $HTML_COUNT,
        "js_files": $JS_COUNT,
        "css_files": $CSS_COUNT
    },
    "status": $(if [ $SCORE -ge 80 ]; then echo '"PASS"'; elif [ $SCORE -ge 60 ]; then echo '"WARNING"'; else echo '"FAIL"'; fi),
    "recommendations": [
        $(if [ $CONSOLE_LOGS -gt 0 ]; then echo '"Remove console.log statements before production",'; fi)
        $(if [ $TODOS -gt 0 ]; then echo '"Address TODO/FIXME items",'; fi)
        $(if [ $MISSING_FILES -gt 0 ]; then echo '"Fix missing critical files",'; fi)
        "Review full log at: $QA_LOG"
    ]
}
EOF

log "\n📄 Report saved: $REPORT_FILE"

# 7. ALERTS FOR CRITICAL ISSUES
if [ $SCORE -lt 60 ]; then
    log "\n🚨 CRITICAL: QA Score below 60! Immediate attention required."
    # Could send Telegram alert here
fi

# 8. SUMMARY
log "\n✅ QA Complete"
log "   Full log: $QA_LOG"
log "   Dashboard: http://76.13.121.143:8080/qa-dashboard.html"

echo "$(date): Daily QA complete - Score: $SCORE" >> $LOG_DIR/qa-history.log
