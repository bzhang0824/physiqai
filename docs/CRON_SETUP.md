# Setup Cron Jobs

## Installation

```bash
# Make scripts executable
chmod +x scripts/update-docs.sh
chmod +x scripts/continuous_qa.py

# Edit crontab
crontab -e
```

## Add These Lines

```bash
# Documentation updates - 6 AM and 6 PM UTC
0 6,18 * * * /home/clawd/.openclaw/workspace/projects/physiqai/scripts/update-docs.sh >> /home/clawd/.openclaw/workspace/projects/physiqai/logs/cron.log 2>&1

# Continuous QA monitor (runs continuously in background)
@reboot /home/clawd/.openclaw/workspace/projects/physiqai/scripts/continuous_qa.py /home/clawd/.openclaw/workspace/projects/physiqai >> /home/clawd/.openclaw/workspace/projects/physiqai/logs/qa-monitor.log 2>&1 &

# Daily full QA report - 7 AM UTC
0 7 * * * cd /home/clawd/.openclaw/workspace/projects/physiqai && python3 scripts/qa_validator.py --report >> logs/daily-qa.log 2>&1

# Weekly dependency check - Sundays at midnight
0 0 * * 0 cd /home/clawd/.openclaw/workspace/projects/physiqai && pip list --outdated >> logs/dependency-check.log 2>&1
```

## Manual Run

```bash
# Update docs now
./scripts/update-docs.sh

# Start continuous QA
python3 scripts/continuous_qa.py

# Run full QA check
python3 scripts/qa_validator.py
```

## Monitoring

Check logs:
```bash
tail -f logs/cron.log
tail -f logs/qa-monitor.log
tail -f logs/daily-qa.log
```
