# Email Trigger - Setup Guide

## 🎯 What This Does

**`email_trigger.py`** is a dedicated service that watches your Supabase database for emails with `label='unsure'` and **automatically triggers verification calls** using your `outbound_call_service.py`.

**The Answer to Your Question:**
> "If the database is updated right now, will it trigger the agent to call?"

**YES!** ✅ This file makes it happen automatically!

---

## 🚀 Quick Start

### Option 1: Run Once (Test Mode)

Process all pending unsure emails right now:

```bash
cd /Users/voyager/Documents/GitHub/donna
python api/email_trigger.py --mode once
```

**What happens:**
1. ✅ Checks database for `label='unsure'` emails
2. ✅ Maps each email to 32 dynamic variables
3. ✅ Calls `outbound_call_service.initiate_call()`
4. ✅ Agent makes call with full context
5. ✅ Updates database with `call_initiated_at`
6. ✅ Exits

**Perfect for testing!**

### Option 2: Run as Service (Production)

Continuously monitor database every 30 seconds:

```bash
python api/email_trigger.py --mode service --interval 30
```

**What happens:**
- ✅ Runs forever in background
- ✅ Checks database every 30 seconds
- ✅ Processes any new unsure emails
- ✅ Automatically triggers calls
- ✅ Rate-limited (5s between calls)

**Perfect for production!**

### Option 3: Webhook Server

Run as HTTP webhook (called by Supabase):

```bash
python api/email_trigger.py --mode webhook --port 8001
```

Then trigger via HTTP:
```bash
# Process all pending
curl -X POST http://localhost:8001/

# Process specific email
curl -X POST http://localhost:8001/ \
  -H "Content-Type: application/json" \
  -d '{"email_id": "12345"}'
```

---

## 📋 How It Works

```
┌─────────────────────────────────────────────────────────────┐
│  EMAIL ADDED TO DATABASE                                    │
│  ─────────────────────────────────────────────────────────  │
│  INSERT INTO emails (label, vendor_name, ...)               │
│  VALUES ('unsure', 'Acme Corp', ...)                        │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│  EMAIL_TRIGGER.PY DETECTS IT                                │
│  ─────────────────────────────────────────────────────────  │
│  SELECT * FROM emails                                       │
│  WHERE label = 'unsure'                                     │
│  AND call_initiated_at IS NULL                              │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│  MAPS EMAIL → DYNAMIC VARIABLES                             │
│  ─────────────────────────────────────────────────────────  │
│  map_email_to_dynamic_variables(email_data)                 │
│                                                             │
│  Returns 32 variables:                                      │
│    {                                                        │
│      "case_id": "CASE-12345",                               │
│      "customer_org": "Pixamp, Inc",                         │
│      "email__vendor_name": "Acme Corp",                     │
│      "email__invoice_number": "INV-001",                    │
│      "official_canonical_phone": "+18005551234",            │
│      ... all 32 variables ...                               │
│    }                                                        │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│  CALLS OUTBOUND_CALL_SERVICE.PY                             │
│  ─────────────────────────────────────────────────────────  │
│  from services.outbound_call_service import initiate_call   │
│                                                             │
│  call_result = initiate_call(                               │
│      destination_number="+18005551234",                     │
│      agent_variables=dynamic_vars  ← All 32 variables!      │
│  )                                                          │
│                                                             │
│  This is YOUR existing outbound call service!               │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│  ELEVENLABS AGENT CALLS VENDOR                              │
│  ─────────────────────────────────────────────────────────  │
│  • Agent receives all 32 variables resolved                 │
│  • Makes call with full invoice context                     │
│  • Verifies invoice authenticity                            │
│  • Updates verified__* variables during call                │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│  DATABASE UPDATED                                           │
│  ─────────────────────────────────────────────────────────  │
│  UPDATE emails SET                                          │
│    call_initiated_at = NOW(),                               │
│    conversation_id = 'conv_xxx'                             │
│  WHERE id = '12345'                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧪 Test It Right Now

### Step 1: Check for pending emails

```bash
python api/email_trigger.py --mode once
```

**Expected Output:**
```
🚀 Email Trigger - Run Once Mode
================================================================================

🔍 Checking for pending unsure emails...
================================================================================
   📬 Found 2 pending email(s)

--- Processing 1/2 ---
📧 Processing Email: 12345
   Vendor: Acme Corp
   Invoice: INV-001
   Amount: $500.00
   📋 Mapping email data to dynamic variables...
   ✅ Mapped 32 variables
   📞 Determining call destination...
   📞 Selected phone from Official: +18005551234
   🚀 Initiating call to +18005551234...
   📦 Passing 32 dynamic variables to agent

🚀 Initiating outbound call
   Time: 2025-10-05 15:30:00
   From: +18887064372
   To: +18005551234

✅ Call initiated successfully!
   🆔 Conversation ID: conv_abc123
   🔗 Dashboard: https://elevenlabs.io/app/conversational-ai/conversations/conv_abc123
   ✅ Marked email 12345 as call initiated

================================================================================
📊 PROCESSING COMPLETE
   Total Processed: 2
   ✅ Successful: 2
   ❌ Failed: 0
================================================================================
```

---

## ⚙️ Configuration

### Environment Variables

Create/update `.env`:

```bash
# Customer defaults for dynamic variables
CUSTOMER_ORG="Pixamp, Inc"
USER_FULL_NAME="Sarah Johnson"
USER_PHONE="+14155551234"

# ElevenLabs (already configured)
ELEVENLABS_API_KEY=sk_...
ELEVEN_LABS_AGENT_ID=agent_...

# Supabase (already configured)
SUPABASE_URL=https://...
SUPABASE_KEY=...
```

### Service Configuration

In `email_trigger.py`:

```python
# Database polling interval (seconds)
DEFAULT_POLL_INTERVAL = 30

# Maximum emails to process per cycle
MAX_EMAILS_PER_CYCLE = 10

# Minimum time between calls (seconds) to avoid rate limiting
CALL_RATE_LIMIT_DELAY = 5
```

---

## 🚀 Production Deployment

### Option 1: Systemd Service (Linux)

Create `/etc/systemd/system/email-trigger.service`:

```ini
[Unit]
Description=Email Trigger Service
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/donna
ExecStart=/usr/bin/python3 /path/to/donna/api/email_trigger.py --mode service --interval 30
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable email-trigger
sudo systemctl start email-trigger
sudo systemctl status email-trigger
```

View logs:
```bash
sudo journalctl -u email-trigger -f
```

### Option 2: Supervisor (Linux/Mac)

Install supervisor:
```bash
pip install supervisor
```

Create config `/etc/supervisor/conf.d/email-trigger.conf`:

```ini
[program:email-trigger]
command=python /path/to/donna/api/email_trigger.py --mode service --interval 30
directory=/path/to/donna
autostart=true
autorestart=true
stderr_logfile=/var/log/email-trigger.err.log
stdout_logfile=/var/log/email-trigger.out.log
```

Start:
```bash
supervisorctl reread
supervisorctl update
supervisorctl start email-trigger
```

### Option 3: Docker Container

Create `Dockerfile.trigger`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY api/requirements.txt .
RUN pip install -r requirements.txt

COPY api/ ./api/
COPY app/ ./app/

CMD ["python", "api/email_trigger.py", "--mode", "service", "--interval", "30"]
```

Build and run:
```bash
docker build -f Dockerfile.trigger -t donna-email-trigger .
docker run -d --name email-trigger donna-email-trigger
```

### Option 4: Cron Job (Simple)

Add to crontab (runs every 5 minutes):

```bash
crontab -e
```

Add line:
```
*/5 * * * * cd /path/to/donna && python api/email_trigger.py --mode once >> /var/log/email-trigger.log 2>&1
```

---

## 📊 Monitoring

### Check Service Status

```bash
# If running as systemd service
sudo systemctl status email-trigger

# If running as supervisor
supervisorctl status email-trigger

# If running manually
ps aux | grep email_trigger
```

### View Logs

Logs show everything that's happening:

```bash
# If using systemd
sudo journalctl -u email-trigger -f

# If using supervisor
tail -f /var/log/email-trigger.out.log

# If running manually (stdout)
# Logs appear in terminal
```

### Check Database

```sql
-- See processed emails
SELECT 
    id,
    vendor_name,
    label,
    call_initiated_at,
    conversation_id,
    created_at
FROM emails
WHERE label = 'unsure'
ORDER BY created_at DESC;

-- See pending emails
SELECT COUNT(*) as pending_count
FROM emails
WHERE label = 'unsure'
AND call_initiated_at IS NULL;
```

---

## 🔧 CLI Options

```bash
# Run once (process all pending and exit)
python api/email_trigger.py --mode once

# Run as service (continuous monitoring)
python api/email_trigger.py --mode service

# Custom poll interval (60 seconds)
python api/email_trigger.py --mode service --interval 60

# Webhook server
python api/email_trigger.py --mode webhook --port 8001

# Help
python api/email_trigger.py --help
```

---

## 🐛 Troubleshooting

### "No pending unsure emails found"

**Problem:** No emails with `label='unsure'` in database

**Solution:**
```sql
-- Check what labels exist
SELECT label, COUNT(*) FROM emails GROUP BY label;

-- Manually set an email to unsure for testing
UPDATE emails SET label = 'unsure', call_initiated_at = NULL WHERE id = 'test_id';
```

### "No valid phone number found"

**Problem:** Email record doesn't have phone field populated

**Solution:**
```sql
-- Update email with phone number
UPDATE emails SET 
    official_phone = '+18005551234'
WHERE id = 'email_id';
```

### "Import error: No module named..."

**Problem:** Dependencies not installed

**Solution:**
```bash
cd /Users/voyager/Documents/GitHub/donna
pip install -r api/requirements.txt
```

### Service not starting

**Problem:** Configuration error

**Solution:**
```bash
# Test manually first
python api/email_trigger.py --mode once

# Check logs
journalctl -u email-trigger -n 50
```

---

## 📈 Performance

### Rate Limiting

- **5 second delay** between calls (avoid ElevenLabs rate limits)
- **Max 10 emails** per cycle (configurable)
- **30 second** poll interval (configurable)

### Capacity

- **2 calls/minute** with default settings
- **120 calls/hour** sustained
- **2,880 calls/day** maximum

Adjust `CALL_RATE_LIMIT_DELAY` and `DEFAULT_POLL_INTERVAL` for your needs.

---

## ✅ Verification Checklist

Before production:

- [ ] Test run once mode successfully
- [ ] Verify calls are made via outbound_call_service.py
- [ ] Check ElevenLabs dashboard shows calls
- [ ] Confirm database updates with call_initiated_at
- [ ] Test service mode (let it run 5+ minutes)
- [ ] Set up monitoring/alerting
- [ ] Configure as systemd service or cron job
- [ ] Test error handling (invalid phone, etc.)

---

## 🎉 Summary

**You asked:** "Can we create a file that triggers the agent to call when database is updated?"

**Answer:** **YES!** ✅

**`email_trigger.py` does exactly that:**

1. ✅ Watches database for `label='unsure'` emails
2. ✅ Maps email data to 32 dynamic variables
3. ✅ Calls **YOUR `outbound_call_service.py`** ✨
4. ✅ Agent makes call with full context
5. ✅ Updates database automatically

**It's ready to use right now!**

```bash
# Try it:
python api/email_trigger.py --mode once
```
