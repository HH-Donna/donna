# Comprehensive Troubleshooting: Calls Stopped Working

## 🔍 Analysis of Last 2 Call Logs

### ✅ Working Call (Reference: CA50b6311ad90d5f58437dd8e433eac214)
```
Date: 05:53:38 EDT 2025-10-05
Duration: 14 seconds
Status: Completed ✅
TwiML: <Stream url="wss://api.us.elevenlabs.io/v1/convai/conversation">
       <Parameter name="conversation_id" value="conv_7901k6swn1wqee4a8ecby0yyvzt6" />
```
**Key Success Factors:**
- Correct WebSocket endpoint
- Valid conversation_id from ElevenLabs
- Proper authentication
- Clean connection

### ❌ Failed Calls (Previous attempts: CA5a004ba4, CA0b3c01ec)
```
Error 31921: Stream - WebSocket - Close Error (Authentication)
Error 31920: Stream - WebSocket - Handshake Error (Wrong endpoint)
Duration: 3-8 seconds (hung up immediately)
```

**Root Cause Pattern:**
All successful calls use ElevenLabs-generated `conversation_id`. Failed calls tried to connect directly without proper conversation setup.

---

## 🎯 PRIMARY ISSUE: Trial Account Restrictions

### **Most Likely Cause: Phone Number Not Verified**

**Evidence:**
- First call worked (possibly during grace period)
- Subsequent calls failing silently
- Twilio has credits ✅
- No error messages appearing in dashboard

**Explanation:**
Twilio **TRIAL accounts** can ONLY call **verified phone numbers**. This is a hard restriction that cannot be bypassed without:
1. Verifying the target number
2. OR upgrading to paid account

**Reference Documentation:**
- [Twilio Trial Account Limitations](https://www.twilio.com/docs/usage/tutorials/how-to-use-your-free-trial-account)
- [Verified Caller IDs](https://support.twilio.com/hc/en-us/articles/223180048-Adding-a-Verified-Phone-Number-or-Caller-ID-with-Twilio)

---

## ✅ SOLUTION 1: Verify Your Phone Number (5 minutes)

### Step-by-Step Verification:

```bash
1. Go to Twilio Console
   URL: https://console.twilio.com/us1/develop/phone-numbers/manage/verified

2. Click "Add a new Caller ID" or "+ Add Caller ID"

3. Enter your phone number
   Format: +13473580012 (must include + and country code)

4. Choose verification method
   • Call verification (recommended)
   • SMS verification

5. Complete verification
   • Answer the call or read the SMS
   • Enter the verification code
   • Wait for confirmation

6. Verify it appears in list
   • Refresh the page
   • Confirm +13473580012 is listed
   • Status should be "Verified"

7. Retry outbound call from ElevenLabs dashboard
```

**This should immediately fix the issue!**

---

## ✅ SOLUTION 2: Upgrade Twilio Account (Permanent Fix)

### Benefits of Upgrading:
- ✅ Call ANY phone number (no restrictions)
- ✅ Remove "Trial" limitations
- ✅ Higher call quality/reliability
- ✅ Access to advanced features
- ✅ Production-ready

### How to Upgrade:

```bash
1. Go to Twilio Billing
   URL: https://console.twilio.com/billing

2. Add funds to account
   • Minimum: $20 recommended
   • Account auto-upgrades from trial status

3. Confirm upgrade
   • Check for "Trial" badge removal
   • Account type should show "Pay-As-You-Go" or "Paid"

4. Retry calls
   • Can now call any number
   • No verification needed
```

**Cost:** ~$0.014 per minute outbound call

---

## 🔍 SOLUTION 3: Check ElevenLabs Quota

### Secondary Possible Cause: Usage Limits

**Evidence Check:**
```bash
1. Go to ElevenLabs Usage Dashboard
   URL: https://elevenlabs.io/app/usage

2. Check "Conversational AI" usage
   • Character limit: _____ / _____
   • Minute limit: _____ / _____
   • Conversation limit: _____ / _____

3. Check account tier
   • Free trial
   • Starter
   • Creator
   • Pro

4. Look for warnings
   • "Approaching limit"
   • "Quota exceeded"
   • "Upgrade required"
```

**If Quota Exhausted:**
- Conversations won't be created
- Dashboard may not show clear error
- Calls fail silently

**Fix:**
- Wait for monthly reset (check date)
- OR upgrade to paid ElevenLabs plan
- OR contact support for temporary increase

---

## 🔧 SOLUTION 4: Diagnostic Test Procedure

### Run These Tests to Isolate Issue:

#### Test 1: Check Account Status
```bash
Run this script:
```

```python
# save as: diagnose_accounts.py
from twilio.rest import Client
import os

# Credentials
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

print("=" * 70)
print("TWILIO ACCOUNT DIAGNOSTIC")
print("=" * 70)

# Get account info
account = client.api.accounts(TWILIO_ACCOUNT_SID).fetch()
print(f"\nAccount Status: {account.status}")
print(f"Account Type: {account.type}")

# Get balance
balance = client.api.accounts(TWILIO_ACCOUNT_SID).balance.fetch()
print(f"Balance: {balance.balance} {balance.currency}")

# Check if trial
if account.type == "Trial":
    print("\n⚠️  TRIAL ACCOUNT DETECTED!")
    print("   You can ONLY call verified numbers.")
    print("   Action required: Verify +13473580012")
    print("   URL: https://console.twilio.com/us1/develop/phone-numbers/manage/verified")

# List verified numbers
print("\nVerified Caller IDs:")
verified = client.outgoing_caller_ids.list()
if verified:
    for v in verified:
        print(f"  ✓ {v.phone_number}")
else:
    print("  ❌ No verified numbers!")
    print("  This is why calls are failing!")

# Check target number
TARGET = "+13473580012"
is_verified = any(v.phone_number == TARGET for v in verified)
print(f"\nTarget {TARGET} verified: {is_verified}")

if not is_verified:
    print("\n🔧 FIX:")
    print("  1. Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/verified")
    print("  2. Add caller ID: +13473580012")
    print("  3. Complete verification")
    print("  4. Retry call")

print("=" * 70)
```

```bash
Run:
cd /Users/voyager/Documents/GitHub/donna/api
python3 diagnose_accounts.py
```

#### Test 2: Check Twilio Number Config
```python
# Already have this - check_twilio_config.py
# Run: python3 check_twilio_config.py
```

#### Test 3: Test Inbound (Validates Integration)
```bash
ACTION: Call +18887064372 from your phone

Expected: Donna answers

If works: Integration is fine, issue is with outbound setup
If fails: Integration broken, need to re-import number
```

---

## 📋 Edge Cases & Advanced Issues

### Edge Case 1: Rate Limiting
**Symptom:** First call works, next few fail
**Cause:** Too many rapid attempts
**Fix:** Wait 60 seconds between attempts

### Edge Case 2: Conversation Not Cleaned Up
**Symptom:** First call works, second fails
**Cause:** Previous conversation still active
**Fix:** Wait 2 minutes, or check Conversations dashboard and ensure previous call ended

### Edge Case 3: API Key Permissions
**Symptom:** Dashboard works, but shows no options
**Cause:** ElevenLabs API key lacks permissions
**Fix:** Regenerate API key in ElevenLabs settings

### Edge Case 4: Geographic Restrictions
**Symptom:** Some numbers work, others don't
**Cause:** Twilio/carrier blocks certain regions
**Fix:** Check Twilio's geographic permissions

### Edge Case 5: Webhook Timeout
**Symptom:** Call connects then drops
**Cause:** ElevenLabs webhook taking too long
**Fix:** Check ElevenLabs service status

---

## 🎯 RECOMMENDED ACTION PLAN

### Priority 1: Verify Phone Number (DO THIS FIRST!)
```bash
Time: 5 minutes
Impact: HIGH - Will likely fix issue immediately
Action: https://console.twilio.com/us1/develop/phone-numbers/manage/verified
```

### Priority 2: Check ElevenLabs Quota
```bash
Time: 2 minutes
Impact: MEDIUM - Could be blocking calls
Action: https://elevenlabs.io/app/usage
```

### Priority 3: Run Diagnostic Script
```bash
Time: 1 minute
Impact: HIGH - Identifies exact issue
Action: python3 diagnose_accounts.py
```

### Priority 4: Test Inbound Call
```bash
Time: 1 minute
Impact: HIGH - Validates integration
Action: Call +18887064372 from phone
```

### Priority 5: Contact Support (If Still Failing)
```bash
ElevenLabs: support@elevenlabs.io
Include: Agent ID, Phone Number, Working call SID, Error screenshots

Twilio: https://support.twilio.com/
Include: Account SID, Call SIDs, Error codes
```

---

## ✅ SUCCESS CRITERIA

After fixes, verify:
- [ ] Phone number verified in Twilio
- [ ] Outbound call connects
- [ ] Phone rings within 10 seconds
- [ ] Donna speaks clearly
- [ ] Dynamic variables work
- [ ] Call lasts >10 seconds
- [ ] Can have conversation
- [ ] Call ends cleanly

---

## 📊 Decision Matrix

| Symptom | Cause | Fix |
|---------|-------|-----|
| Phone never rings | Trial account | Verify number |
| Call connects then drops | WebSocket auth | Check integration |
| Dashboard shows error | Quota exceeded | Upgrade plan |
| No error but no ring | Silent failure | Check logs |
| First works, rest fail | Rate limit | Wait between calls |

---

**Last Updated:** 2025-10-05  
**Priority:** Critical  
**Next Action:** Verify +13473580012 in Twilio Console