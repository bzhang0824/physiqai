# Flaky System Fixes - Implementation Plan

## Problems Identified

### 1. API Process Unreliability (CRITICAL)
**Problem:** The mobile_avatar_api.py process crashes/stops randomly. No auto-restart.
**Impact:** Uploads fail completely, users see infinite loading screen.
**Root Causes:**
- Flask dev server not production-ready
- No process supervision
- No health monitoring
- Memory leaks or uncaught exceptions kill the process

### 2. Silent Failures (CRITICAL)
**Problem:** When API is down, fetch() fails silently or with confusing errors.
**Impact:** Users don't know why upload failed, bad UX.
**Root Causes:**
- No retry logic
- Poor error handling
- No offline detection

### 3. No Monitoring/Observability (HIGH)
**Problem:** We don't know when API crashes until user complains.
**Impact:** Downtime goes unnoticed.
**Root Causes:**
- No health checks
- No alerting
- No logs aggregation

### 4. CORS/Network Issues (MEDIUM)
**Problem:** Mobile browsers block requests to port 5001.
**Impact:** Uploads fail on some networks.
**Root Causes:**
- Separate port for API
- Corporate/mobile firewalls block non-standard ports

---

## Proposed Solutions

### Phase 1: Process Reliability (Do First)

#### 1.1 Process Supervisor
**What:** Use systemd or PM2 to keep API running
**Implementation:**
- Create systemd service file for mobile_avatar_api
- Auto-restart on crash (Restart=always)
- Log rotation
- Start on boot

#### 1.2 Health Check Loop
**What:** Background script that pings API every 30 seconds
**Implementation:**
- Simple bash script: curl health endpoint
- If fails 3 times in a row, restart service
- Log status to file

#### 1.3 API Hardening
**What:** Make Flask more production-ready
**Implementation:**
- Add proper exception handling
- Add request timeouts
- Add memory limits
- Use threaded mode or WSGI server

### Phase 2: Frontend Resilience (Do Second)

#### 2.1 Retry Logic with Exponential Backoff
**What:** Frontend retries failed uploads automatically
**Implementation:**
- 3 retry attempts
- Delay: 1s, 3s, 5s
- Show "Retrying..." message
- Only then show error

#### 2.2 API Status Indicator
**What:** Visual indicator if API is up/down
**Implementation:**
- Ping health endpoint on page load
- Show green/red dot in header
- Disable upload button if API down

#### 2.3 Better Error Messages
**What:** Tell user exactly what's wrong
**Implementation:**
- "Server is starting up, please wait..."
- "Network error, checking connection..."
- "Upload failed after 3 attempts. Please try again."

### Phase 3: Single Port Architecture (Do Third)

#### 3.1 API Proxy Through Main Server
**What:** Route API calls through port 8080 (same as web)
**Implementation Options:**
- Option A: nginx reverse proxy
- Option B: Flask app on 8080 with URL routing
- Option C: Express.js wrapper

**Recommended:** Option B - Simple Flask app that serves static files AND handles API

---

## Implementation Order

1. **Process Supervisor** (systemd service) - 30 min
2. **Health Check Loop** (cron script) - 20 min
3. **Frontend Retry Logic** - 30 min
4. **API Status Indicator** - 20 min
5. **Better Error Messages** - 15 min
6. **Single Port Migration** - 1 hour (optional but recommended)

---

## Success Criteria

- [ ] API stays up for 24+ hours without manual restart
- [ ] Upload succeeds on first try >90% of the time
- [ ] If API is down, user sees clear message within 5 seconds
- [ ] API auto-restarts within 30 seconds of crash
- [ ] Works on all networks (corporate, mobile, home)

---

## Testing Plan

1. Kill API process manually → Should auto-restart
2. Upload while API down → Should show status indicator + retry
3. Upload on mobile network → Should work (or show specific error)
4. Leave running overnight → Check logs in morning