# 🎯 Next Steps: Testing Your Twilio Integration

## ✅ What We've Set Up

1. **Agent Configuration**
   - ✅ Donna agent configured with invoice verification prompt
   - ✅ Dynamic variables defined for personalization
   - ✅ Agent synced to ElevenLabs (ID: `agent_2601k6rm4bjae2z9amfm5w1y6aps`)

2. **Test Scripts**
   - ✅ `test_outbound_call.py` - Comprehensive outbound call testing
   - ✅ `test_direct_call.py` - Alternative API testing
   - ✅ `import_twilio_number.py` - Twilio number import helper

3. **Documentation**
   - ✅ `TWILIO_INTEGRATION_GUIDE.md` - Detailed setup guide
   - ✅ This file - Next steps and testing plan

## 🚀 What You Need to Do Now

### Step 1: Import Twilio Number (5 minutes)

**Option A: Via ElevenLabs Dashboard (Recommended)**

1. Go to https://elevenlabs.io/app/conversational-ai
2. Click the **"Phone Numbers"** tab in the left sidebar
3. Click **"Import Phone Number"** or **"Add Phone Number"**
4. Select **"Twilio"** as the provider
5. Fill in the form:
   ```
   Label: Donna Billing Verifier
   Phone Number: YOUR_TWILIO_PHONE_NUMBER
   Twilio Account SID: YOUR_TWILIO_ACCOUNT_SID
   Twilio Auth Token: YOUR_TWILIO_AUTH_TOKEN
   ```
6. **Assign Agent**: Select "Donna" from dropdown (for inbound calls)
7. Click **"Save"** or **"Import"**
8. ✅ You should see the number appear in your list

**Option B: Via API (If dashboard doesn't work)**

```bash
curl -X POST "https://api.elevenlabs.io/v1/convai/phone-numbers" \
  -H "xi-api-key: YOUR_ELEVENLABS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "twilio",
    "phone_number": "YOUR_TWILIO_PHONE_NUMBER",
    "twilio_account_sid": "YOUR_TWILIO_ACCOUNT_SID",
    "twilio_auth_token": "YOUR_TWILIO_AUTH_TOKEN",
    "label": "Donna Billing Verifier",
    "agent_id": "agent_2601k6rm4bjae2z9amfm5w1y6aps"
  }'
```

---

### Step 2: Test Outbound Calls (Dashboard Method) (5 minutes)

**Note:** This system is **outbound-only**. Donna calls vendors to verify invoices; she does NOT receive inbound calls.

---

**Using the ElevenLabs Dashboard:**

1. Go to https://elevenlabs.io/app/conversational-ai
2. Click **"Phone Numbers"** tab
3. Find your imported number: **+18887064372**
4. Click the **three dots (•••)** on the right side of the row
5. Select **"Make outbound call"** or similar option
6. Configure the test call:
   - **Select Agent**: "Donna"
   - **To Phone Number**: `+13473580012` (your number)
   - **Dynamic Variables** (optional): Leave default or add test data
7. Click **"Send Test Call"** or **"Initiate Call"**
8. **Answer your phone!**

**What to Verify:**
- ✅ Your phone rings within 5-10 seconds
- ✅ Caller ID shows +18887064372
- ✅ Donna introduces herself when you answer
- ✅ Dynamic variables are substituted correctly (listen for "Pixamp Inc", "Amazon Web Services", etc.)
- ✅ Donna follows the conversation flow
- ✅ Call quality is good

---

### Step 4: Test Outbound Calls (API Method) (5 minutes)

**Using the Test Script:**

```bash
cd /Users/voyager/Documents/GitHub/donna/api

# Set environment variables
export ELEVENLABS_API_KEY="sk_9af95a2fca8ea120a514561389ef270c6e3c2235b3da347a"
export ELEVEN_LABS_AGENT_ID="agent_2601k6rm4bjae2z9amfm5w1y6aps"

# Run the test
python3 test_outbound_call.py +13473580012
```

**Expected Output:**

```
======================================================================
🎯 ElevenLabs Outbound Call Test
======================================================================

🔍 Looking up phone number ID...
   Found 1 imported phone number(s)
   - +18887064372 (ID: pn_xxxxx)
✅ Found matching phone number ID: pn_xxxxx

📞 Initiating outbound call...
   From: +18887064372 (via ElevenLabs)
   To: +13473580012
   Agent: agent_2601k6rm4bjae2z9amfm5w1y6aps

📋 Dynamic Variables (first 5):
   case_id: TEST-001
   customer_org: Pixamp Inc
   user__company_name: Pixamp Inc
   vendor__legal_name: Amazon Web Services
   email__vendor_name: AWS
   ... and 23 more variables

✅ Call initiated successfully!
   Call ID: call_xxxxx
   Conversation ID: conv_xxxxx
   Status: initiated

📱 Your phone (+13473580012) should ring shortly!
```

**What to Verify:**
- ✅ Script finds the imported phone number
- ✅ API call succeeds (200 response)
- ✅ Conversation ID is returned
- ✅ Your phone rings
- ✅ Donna introduces herself correctly
- ✅ Dynamic variables are working

---

### Step 4: Test Dynamic Variables (10 minutes)

**During an outbound call, listen carefully for these substitutions:**

| Variable | Expected Value | What Donna Should Say |
|----------|---------------|----------------------|
| `{{customer_org}}` | "Pixamp Inc" | "I am calling from **Pixamp Inc**" |
| `{{vendor__legal_name}}` | "Amazon Web Services" | "regarding billing for **Amazon Web Services**" |
| `{{email__invoice_number}}` | "INV-2024-12345" | "invoice **INV-2024-12345**" |
| `{{email__amount}}` | "$1,250.00" | "for **$1,250.00**" |
| `{{email__due_date}}` | "2024-10-15" | "due **2024-10-15**" |
| `{{case_id}}` | "TEST-001" | "case **TEST-001**" |

**Test Checklist:**
- [ ] Donna says "Pixamp Inc" (not {{customer_org}})
- [ ] Donna says "Amazon Web Services" (not {{vendor__legal_name}})
- [ ] Donna mentions the invoice number correctly
- [ ] Donna mentions the amount correctly
- [ ] All other variables are substituted (not showing as {{variable}})

**If variables are NOT substituting:**
1. Check that you passed them in the API call (see test_outbound_call.py)
2. Verify variable names match exactly (case-sensitive!)
3. Check agent configuration has the variables defined
4. Review conversation transcript in dashboard to see raw data

---

### Step 5: Test Call Flow Scenarios (15 minutes)

**Test these scenarios to verify Donna's behavior:**

#### Scenario 1: Normal Verification Flow
1. Call Donna (or have her call you)
2. Confirm you're the right person for billing
3. Ask her for invoice details
4. Verify the invoice exists
5. Provide a ticket number
6. End call naturally

**Expected:** Donna should follow the full verification flow and collect all information.

---

#### Scenario 2: Wrong Number
1. Start a call
2. When Donna asks if you're the right person, say: **"No, wrong number"**

**Expected:** Donna should apologize and end the call quickly.

---

#### Scenario 3: Request More Details
1. Start a call
2. Ask: **"What invoice number are you asking about?"**
3. Ask: **"What's the amount?"**
4. Ask: **"What's your company name again?"**

**Expected:** Donna should provide the requested details from dynamic variables.

---

#### Scenario 4: Suspicious Invoice
1. Start a call
2. When asked about the invoice, say: **"We never sent that invoice"**
3. Say: **"That looks like fraud"**

**Expected:** Donna should:
- Not argue
- Ask for the fraud/security contact
- Mark the invoice as suspected fraud
- End call professionally

---

#### Scenario 5: Need to Transfer
1. Start a call
2. Say: **"I need to transfer you to billing"**

**Expected:** Donna should:
- Acknowledge the transfer
- Re-state her purpose when the new person picks up
- Continue the verification flow

---

#### Scenario 6: Interruption Handling
1. Start a call
2. While Donna is speaking, start talking (interrupt her)

**Expected:** Donna should:
- Stop speaking
- Listen to you
- Respond appropriately to what you said

---

### Step 6: Review Call History (5 minutes)

**After each test call:**

1. Go to https://elevenlabs.io/app/conversational-ai
2. Click **"Calls History"** or **"Conversations"**
3. Find your recent test call
4. Click to view details

**Review:**
- ✅ Full transcript of the conversation
- ✅ Dynamic variables that were passed
- ✅ Agent's responses and tool usage
- ✅ Call duration and quality metrics
- ✅ Any errors or issues

**Look for:**
- Are dynamic variables showing correctly in transcript?
- Did Donna follow the prompt instructions?
- Were there any errors or unexpected behaviors?
- How was the conversation quality?

---

## 📊 Success Criteria

Your Twilio integration is **fully working** when:

- [x] Twilio number is imported into ElevenLabs
- [ ] Outbound calls (dashboard) work successfully ← **PRIMARY TEST**
- [ ] Outbound calls (API) work successfully ← **PRODUCTION USE**
- [ ] Dynamic variables are substituted correctly
- [ ] Donna follows the conversation flow from the prompt
- [ ] Donna handles edge cases appropriately (wrong number, suspicious invoice, etc.)
- [ ] Call quality is good (clear audio, no lag)
- [ ] Calls appear in history with full transcripts

**Note:** Inbound calls are NOT needed - this is an outbound-only verification system.

---

## 🐛 Troubleshooting

### Problem: "Phone number not found" error

**Solution:**
1. Verify you completed Step 1 (import number)
2. Check the number appears in ElevenLabs dashboard
3. Wait a few minutes for the import to complete
4. Try running `python3 test_outbound_call.py` again

---

### Problem: Call doesn't connect

**Possible causes:**
- Twilio account is out of credit
- Phone number is not properly configured
- Your test number is blocked or incorrect

**Solution:**
1. Check Twilio console for errors: https://console.twilio.com/
2. Verify your test number is correct: +13473580012
3. Ensure Twilio number has voice capabilities
4. Check Twilio account balance

---

### Problem: Dynamic variables not substituting

**Solution:**
1. Verify variables are passed in the API call (see test_outbound_call.py)
2. Check variable names match exactly (case-sensitive!)
3. Review agent config: `agent/agent_configs/dev/donna-billing-verifier.json`
4. Look at line 45-81 for dynamic_variable_placeholders
5. Ensure all variables in the prompt have corresponding placeholders

---

### Problem: Donna doesn't follow the prompt

**Possible causes:**
- Prompt not synced to deployed agent
- Temperature too high (causing randomness)
- LLM model changed

**Solution:**
1. Re-sync agent: `cd agent && agents sync --env prod`
2. Check temperature setting (should be 0.3)
3. Review recent agent config changes
4. Test in dashboard first to isolate issues

---

## 📁 Files Reference

| File | Purpose |
|------|---------|
| `agent/agent_configs/dev/donna-billing-verifier.json` | Dev agent configuration |
| `agent/agent_configs/prod/donna-billing-verifier.json` | Prod agent configuration |
| `agent/TWILIO_INTEGRATION_GUIDE.md` | Detailed setup guide |
| `agent/NEXT_STEPS.md` | This file - testing checklist |
| `api/test_outbound_call.py` | Comprehensive test script (use this!) |
| `api/test_direct_call.py` | Alternative API test |
| `api/import_twilio_number.py` | Number import helper |

---

## 🎉 When You're Done

Once all tests pass, you're ready to integrate with your fraud detection pipeline!

**Next phase:**
1. Update `api/app/routers/fraud.py` to call `test_outbound_call.py` logic
2. Pass real invoice data as dynamic variables
3. Store call results in Supabase
4. Set up alerts for suspicious invoices
5. Deploy to production

---

## 💡 Questions?

- **ElevenLabs Docs**: https://elevenlabs.io/docs/agents-platform/phone-numbers/twilio-integration/native-integration
- **Twilio Console**: https://console.twilio.com/
- **ElevenLabs Dashboard**: https://elevenlabs.io/app/conversational-ai
- **Agent Config**: `/Users/voyager/Documents/GitHub/donna/agent/`

Good luck! 🚀
