# QA Automation Setup

## Daily Automated QA Engineer

### What It Does
Runs every day at 6 AM UTC automatically:
- ✅ Checks code quality (console.logs, TODOs, error handling)
- ✅ Validates all critical files exist
- ✅ Monitors database health
- ✅ Calculates QA score (0-100)
- ✅ Generates JSON report
- ✅ Alerts on critical issues

### Setup Instructions

#### 1. Add Cron Job
```bash
# Edit crontab
crontab -e

# Add this line for daily 6 AM runs:
0 6 * * * /home/clawd/.openclaw/workspace/projects/physiqai/scripts/daily-qa.sh

# Or for testing every hour:
0 * * * * /home/clawd/.openclaw/workspace/projects/physiqai/scripts/daily-qa.sh
```

#### 2. Make Executable
```bash
chmod +x /home/clawd/.openclaw/workspace/projects/physiqai/scripts/daily-qa.sh
```

#### 3. Test Run
```bash
./projects/physiqai/scripts/daily-qa.sh
```

### QA Score Algorithm

| Issue | Deduction |
|-------|-----------|
| >10 console.logs | -10 points |
| 5-10 console.logs | -5 points |
| >5 TODOs | -5 points |
| <5 try/catch blocks | -10 points |
| Missing critical file | -10 points each |

**Grade Scale:**
- 80-100: 🟢 PASS
- 60-79: 🟡 WARNING  
- <60: 🔴 FAIL (alerts sent)

### Output Locations

- **Daily logs:** `logs/daily-qa-YYYYMMDD.log`
- **Latest report:** `qa-reports/latest.json`
- **History:** `logs/qa-history.log`
- **Dashboard:** `qa-dashboard.html`

### View Results

```bash
# Latest score
cat projects/physiqai/qa-reports/latest.json | jq '.score'

# Full report
cat projects/physiqai/qa-reports/latest.json | jq

# History
tail projects/physiqai/logs/qa-history.log
```

### Extending The QA

Add more checks by editing `daily-qa.sh`:
- Security audit (check for exposed API keys)
- Performance tests (bundle size, load times)
- Accessibility checks (a11y)
- Mobile responsiveness tests

### Manual Trigger

Run anytime:
```bash
openclaw run daily-qa
```

---

## Continuous QA Agent (Advanced)

For real-time QA on every commit:

### GitHub Actions Integration

Create `.github/workflows/qa.yml`:
```yaml
name: Daily QA
on:
  schedule:
    - cron: '0 6 * * *'  # Daily at 6 AM
  workflow_dispatch:  # Manual trigger

jobs:
  qa:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run QA Script
        run: ./scripts/daily-qa.sh
      - name: Upload Report
        uses: actions/upload-artifact@v2
        with:
          name: qa-report
          path: qa-reports/latest.json
```

---

## Benefits

1. **Catch issues early** - Daily monitoring vs. weekly/monthly
2. **Prevent regression** - Automated catches new problems
3. **Track trends** - See quality improve over time
4. **No manual work** - Runs automatically, reports to dashboard
5. **Enforce standards** - Keeps codebase clean

## Cost

**$0** - Uses existing compute, runs as cron job.
