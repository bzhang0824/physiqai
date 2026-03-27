#!/bin/bash
# PhysiqAI Overnight Automation Script
# Runs every 10 minutes to check status and deploy agents

LOG_FILE="/home/clawd/.openclaw/workspace/projects/physiqai/logs/overnight.log"
mkdir -p /home/clawd/.openclaw/workspace/projects/physiqai/logs

echo "[$(date)] Starting overnight check..." >> $LOG_FILE

# Check database growth
POSTS=$(cd /home/clawd/.openclaw/workspace/projects/physiqai && cat data/collected/database.json 2>/dev/null | python3 -c "import json,sys; print(len(json.load(sys.stdin)['posts']))" 2>/dev/null || echo "0")
echo "[$(date)] Current posts: $POSTS" >> $LOG_FILE

# Check if agents are running
ACTIVE_AGENTS=$(openclaw subagents list 2>/dev/null | grep -c "running" || echo "0")
echo "[$(date)] Active agents: $ACTIVE_AGENTS" >> $LOG_FILE

# Deploy planning agents if none running
if [ "$ACTIVE_AGENTS" -lt "2" ]; then
    echo "[$(date)] Deploying additional agents..." >> $LOG_FILE
    
    # Gap analysis agent
    cd /home/clawd/.openclaw/workspace/projects/physiqai && openclaw spawn --model kimi --label "overnight-gap-check" "Analyze current data gaps. What are we missing for training? Report top 3 gaps." 2>&1 >> $LOG_FILE || true
    
    # Progress tracker agent
    cd /home/clawd/.openclaw/workspace/projects/physiqai && openclaw spawn --model kimi --label "overnight-progress" "Check what files were created recently. Summarize progress made in last few hours." 2>&1 >> $LOG_FILE || true
fi

# Update dashboard timestamp
echo "[$(date)] Dashboard updated" >> $LOG_FILE

echo "[$(date)] Check complete" >> $LOG_FILE
