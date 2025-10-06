# Twilio Integration Setup Guide

## Overview

This guide will help you set up the native Twilio integration with ElevenLabs so that your Donna agent can make outbound verification calls.

## Prerequisites

- ✅ ElevenLabs Account with API access
- ✅ Twilio Account with an active phone number
- ✅ Agent configured and deployed in ElevenLabs

## Credentials

```
ELEVENLABS_API_KEY: YOUR_ELEVENLABS_API_KEY
ELEVEN_LABS_AGENT_ID: YOUR_AGENT_ID

TWILIO_ACCOUNT_SID: YOUR_TWILIO_ACCOUNT_SID
TWILIO_AUTH_TOKEN: YOUR_TWILIO_AUTH_TOKEN
TWILIO_PHONE_NUMBER: YOUR_TWILIO_PHONE_NUMBER

TEST_NUMBER: YOUR_TEST_PHONE_NUMBER
```

## Step 1: Import Twilio Number into ElevenLabs (Dashboard Method)

Since the API endpoint may not be publicly available, use the dashboard method:

### Via ElevenLabs Dashboard:

1. **Navigate to Phone Numbers**
   - Go to https://elevenlabs.io/app/conversational-ai
   - Click on "Phone Numbers" tab

2. **Import Twilio Number**
   - Click "Import Phone Number" or "Add Phone Number"
   - Select "Twilio" as the provider
   - Fill in the details:
     - **Label**: "Donna Billing Verifier - Outbound Only"
     - **Phone Number**: `YOUR_TWILIO_PHONE_NUMBER`
     - **Twilio Account SID**: `YOUR_TWILIO_ACCOUNT_SID`
     - **Twilio Auth Token**: `YOUR_TWILIO_AUTH_TOKEN`

3. **Agent Assignment (Optional)**
   - For **outbound-only** use case: Leave agent unassigned or select "Donna"
   - Note: Agent assignment is only needed for inbound call handling
   - Donna will make outbound verification calls, not receive calls

4. **Save Configuration**
   - ElevenLabs will automatically configure your Twilio number
   - Verify the number appears in your phone numbers list

### Via API (Alternative - if available):

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
    "agent_id": "YOUR_AGENT_ID"
  }'
```

## Step 2: Test Outbound Calls

**Note:** This system is outbound-only. Donna calls vendors to verify invoices; she does not receive inbound calls.

### Method A: Via Dashboard (Quick Test)

1. **Navigate to Phone Numbers** in ElevenLabs dashboard
2. **Find your imported number** (`+18887064372`)
3. **Click the three dots (•••)** on the right side
4. **Select "Make outbound call"** or similar option
5. **Configure the call**:
   - **Agent**: Select "Donna"
   - **To Number**: `+13473580012` (your test number)
   - **Dynamic Variables**: Leave default or customize
6. **Click "Send Test Call"** or "Initiate Call"
7. **Answer your phone** - Donna will call you to verify an invoice!

### Method B: Via API (Production Use)

Use the provided `test_outbound_call.py` script:

```bash
cd /Users/voyager/Documents/GitHub/donna/api
export ELEVENLABS_API_KEY="YOUR_ELEVENLABS_API_KEY"
export ELEVEN_LABS_AGENT_ID="YOUR_AGENT_ID"

# Test call to your number
python3 test_outbound_call.py YOUR_TEST_PHONE_NUMBER
```

The script will:
1. Look up your imported phone number ID
2. Initiate an outbound call to your test number
3. Pass dynamic variables for the invoice verification scenario
4. Display call status and conversation ID

## Step 3: Verify Dynamic Variables

During the outbound call, verify that dynamic variables are correctly substituted:

### Variables to Listen For:

- `{{customer_org}}` → "Pixamp Inc"
- `{{vendor__legal_name}}` → "Amazon Web Services"
- `{{email__invoice_number}}` → "INV-2024-12345"
- `{{email__amount}}` → "$1,250.00"
- `{{case_id}}` → "TEST-001"

### What Donna Should Say:

> "Hi, this is Donna and I am calling from **Pixamp Inc**. I wanted to double check about an email I got regarding billing for **Amazon Web Services**—are you the right person to confirm this billing details?"

If you hear "Pixamp Inc" and "Amazon Web Services" correctly, dynamic variables are working!

## Step 4: Test Call Flow

Engage with Donna and test the full verification flow:

1. **Introduction**: Donna introduces herself and states purpose
2. **Verification Request**: Ask for invoice details
3. **Information Exchange**: Donna provides invoice number, amount, due date
4. **Anomaly Handling**: 
   - Say "wrong number" → Donna should apologize and end call
   - Ask for more details → Donna should provide relevant info
5. **Call Completion**: Once verified, Donna should ask about follow-up actions

## Troubleshooting

### Issue: 404 Error when importing number

**Solution**: Use the ElevenLabs dashboard instead of API. The API endpoint may require special permissions or different authentication.

### Issue: Call doesn't connect

**Possible causes**:
1. Twilio number not properly imported
2. Agent not assigned to phone number
3. Twilio credentials incorrect
4. Phone number format wrong (must include country code: +1...)

**Solution**: 
- Verify number is listed in ElevenLabs dashboard
- Check Twilio console for any errors
- Ensure phone numbers use E.164 format (+15555555555)

### Issue: Dynamic variables not substituting

**Possible causes**:
1. Variables not passed in API call
2. Variable names don't match agent configuration
3. Typo in variable names (e.g., `customer_org` vs `user__company_name`)

**Solution**:
- Review `test_outbound_call.py` - ensure all variables match agent config
- Check agent configuration in dashboard for exact variable names
- Test with minimal variables first, then add more

### Issue: Agent doesn't follow prompt

**Possible causes**:
1. Prompt not synced to deployed agent
2. LLM temperature too high (causes randomness)
3. Prompt logic unclear or contradictory

**Solution**:
- Re-sync agent config: `cd agent && agents sync --env prod`
- Review temperature setting (should be 0.3 for consistent behavior)
- Simplify prompt if needed

## Integration with Fraud Detection Pipeline

Once Twilio integration is working, integrate with your fraud detection system:

```python
# In your fraud detection pipeline
from app.services.elevenlabs_service import initiate_verification_call

# After detecting suspicious invoice
if fraud_score > threshold:
    result = await initiate_verification_call(
        phone_number=vendor_contact_phone,
        invoice_data={
            "case_id": f"FRAUD-{invoice_id}",
            "customer_org": "Pixamp Inc",
            "vendor__legal_name": extracted_vendor_name,
            "email__invoice_number": invoice_number,
            "email__amount": invoice_amount,
            # ... more variables
        }
    )
```

## Next Steps

1. ✅ Import Twilio number (Dashboard or API)
2. ✅ Test inbound call
3. ✅ Test outbound call via dashboard
4. ✅ Test outbound call via API
5. ✅ Verify dynamic variables
6. ✅ Test call flow scenarios
7. ⬜ Integrate with fraud detection system
8. ⬜ Set up call logging and analytics
9. ⬜ Configure production environment
10. ⬜ Deploy to production

## Resources

- [ElevenLabs Twilio Integration Docs](https://elevenlabs.io/docs/agents-platform/phone-numbers/twilio-integration/native-integration)
- [Twilio Console](https://console.twilio.com/)
- [ElevenLabs Dashboard](https://elevenlabs.io/app/conversational-ai)
- [Agent Configuration](./agent_configs/prod/donna-billing-verifier.json)
