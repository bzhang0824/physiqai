# PhysiqAI API Reliability - Testing Guide

## What Was Installed

### 1. Systemd Service (`physiqai-api`)
- **Path:** `/etc/systemd/system/physiqai-api.service`
- **Source:** `/home/clawd/.openclaw/workspace/projects/physiqai/backend/api/physiqai-api.service`
- **Features:**
  - Auto-restarts on crash (5 second delay)
  - Starts on boot
  - Logs to `/home/clawd/.openclaw/workspace/projects/physiqai/logs/`

### 2. Health Check Script
- **Path:** `/home/clawd/.openclaw/workspace/projects/physiqai/scripts/api_health_check.sh`
- **Cron:** Runs every minute (checks API every 30s internally)
- **Logs:** `/home/clawd/.openclaw/workspace/projects/physiqai/logs/health_check.log`
- **Action:** Restarts service after 3 consecutive failures

### 3. Installation Script
- **Path:** `/home/clawd/.openclaw/workspace/projects/physiqai/scripts/install_service.sh`
- **Usage:** `sudo bash scripts/install_service.sh`

---

## Quick Verification

```bash
# Check service status
sudo systemctl status physiqai-api

# Test health endpoint
curl http://localhost:5001/api/health

# View service logs
sudo journalctl -u physiqai-api -f

# View health check logs
tail -f /home/clawd/.openclaw/workspace/projects/physiqai/logs/health_check.log
```

---

## Test Procedures

### Test 1: Verify Service Auto-Start on Boot
```bash
# Simulate reboot
sudo systemctl restart physiqai-api
sleep 3
sudo systemctl status physiqai-api
```
**Expected:** Service shows `Active: active (running)`

### Test 2: Verify Auto-Restart on Crash
```bash
# Get current PID
MAIN_PID=$(sudo systemctl show physiqai-api --property=MainPID --value)
echo "Current PID: $MAIN_PID"

# Kill the process
sudo kill -9 $MAIN_PID

# Wait for restart
sleep 6

# Verify new PID
sudo systemctl status physiqai-api
```
**Expected:** New PID, service still running

### Test 3: Verify Health Check Monitoring
```bash
# Stop the service
sudo systemctl stop physiqai-api

# Wait 3 minutes (3 health check failures)
sleep 180

# Check if service was restarted
sudo systemctl status physiqai-api
```
**Expected:** Service automatically restarted by health check script

### Test 4: Verify Health Endpoint
```bash
curl -s http://localhost:5001/api/health | python3 -m json.tool
```
**Expected:** JSON response with `"status": "healthy"`

---

## Useful Commands

| Command | Description |
|---------|-------------|
| `sudo systemctl status physiqai-api` | Check service status |
| `sudo systemctl restart physiqai-api` | Restart service |
| `sudo systemctl stop physiqai-api` | Stop service |
| `sudo journalctl -u physiqai-api -f` | View live logs |
| `sudo systemctl enable physiqai-api` | Enable auto-start on boot |
| `sudo systemctl disable physiqai-api` | Disable auto-start |

---

## Troubleshooting

### Service Won't Start
```bash
# Check for errors
sudo journalctl -u physiqai-api -n 50

# Check log files
cat /home/clawd/.openclaw/workspace/projects/physiqai/logs/api_service_error.log
```

### Port 5001 Already in Use
```bash
# Find process using port 5001
sudo lsof -i :5001

# Kill it
sudo kill -9 <PID>

# Restart service
sudo systemctl restart physiqai-api
```

### Reinstall Service
```bash
# Uninstall
sudo bash /home/clawd/.openclaw/workspace/projects/physiqai/scripts/install_service.sh --uninstall

# Reinstall
sudo bash /home/clawd/.openclaw/workspace/projects/physiqai/scripts/install_service.sh
```

---

## Log Files

| Log File | Purpose |
|----------|---------|
| `/home/clawd/.openclaw/workspace/projects/physiqai/logs/api_service.log` | Service stdout |
| `/home/clawd/.openclaw/workspace/projects/physiqai/logs/api_service_error.log` | Service stderr |
| `/home/clawd/.openclaw/workspace/projects/physiqai/logs/health_check.log` | Health monitor |
| `/tmp/mobile_avatar_api.log` | Application logs (rotating) |

---

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Cron (1 min)  │────▶│  Health Check    │────▶│  systemd        │
│                 │     │  Script (30s)    │     │  physiqai-api   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │                           │
                               ▼                           ▼
                        ┌──────────────┐           ┌──────────────┐
                        │  3 failures  │──────────▶│  Auto-restart│
                        │  = restart   │           │  service     │
                        └──────────────┘           └──────────────┘
```
