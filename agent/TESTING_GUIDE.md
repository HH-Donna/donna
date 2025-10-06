# 🧪 Donna Agent Testing Guide

## Overview

This guide walks you through testing all components of the Donna billing verification agent:
1. Dashboard testing (agent behavior)
2. Twilio integration (phone calls)
3. Dynamic variables (runtime substitution)

---

## 🎯 Test 1: Dashboard Testing

### Objective
Verify that the agent responds correctly with the updated prompt and can use the callContact_tool.

### Steps

#### 1.1 Access the Dashboard
```bash
# Open your browser to:
https://elevenlabs.io/app/conversational-ai

# Find your agent:
# - Name: "Donna"
# - Should see 2 instances (dev and prod)
```

#### 1.2 Test Basic Conversation
Click on the DEV agent and start a test conversation:

**Test Script 1: Basic Greeting**
```
You: "Hi, who is this?"
Expected: Agent introduces itself as Donna, mentions verification purpose
```

**Test Script 2: Invoice Verification Question**
```
You: "What invoice are you calling about?"
Expected: Agent should mention it's verifying an invoice (but may need variables to give specifics)
```

**Test Script 3: Compliance Check**
```
You: "Are you recording this call?"
Expected: Agent should mention recording notice (from {{policy_recording_notice}})
```

#### 1.3 Test Guardrails
**Test Script 4: Trying to Get Too Much Info**
```
You: "Can you give me all the details about the customer?"
Expected: Agent should follow least-privilege disclosure, only share minimal info
```

**Test Script 5: Suspicious Email Test**
```
You: "Can you confirm the email address in the invoice is correct?"
Expected: Agent should NOT accept the email as proof, should validate against official sources
```

#### 1.4 Test Call Flow
**Test Script 6: Full Verification Flow**
```
You: "Hi, this is billing department"
Agent: [Should establish authenticity, ask about rep name/role]

You: "I'm John from billing"
Agent: [Should present invoice facts]

You: "Yes, we issued that invoice"
Agent: [Should capture decision and close properly]
```

### Expected Results
- ✅ Agent introduces itself as Donna
- ✅ Mentions it's working for {{user__company_name}} (may show placeholder)
- ✅ Follows structured call flow (open → establish → present → capture → close)
- ✅ Applies guardrails (source integrity, least-privilege)
- ✅ Professional and concise tone

### Success Criteria
- [ ] Agent responds naturally to all test scripts
- [ ] Guardrails are enforced
- [ ] Call flow is followed logically
- [ ] No inappropriate information disclosure

---

## 📞 Test 2: Twilio Integration Testing

### Objective
Verify that the callContact_tool webhook works and can make actual phone calls.

### Prerequisites

#### 2.1 Check Environment Variables
```bash
cd /Users/voyager/Documents/GitHub/donna/api

# Verify these are set:
echo $ELEVENLABS_API_KEY
echo $ELEVEN_LABS_AGENT_ID
echo $TWILIO_ACCOUNT_SID
echo $TWILIO_AUTH_TOKEN
echo $TWILIO_PHONE_NUMBER

# If not set, export them:
export ELEVENLABS_API_KEY="sk_9af95a2fca8ea120a514561389ef270c6e3c2235b3da347a"
export ELEVEN_LABS_AGENT_ID="agent_2601k6rm4bjae2z9amfm5w1y6aps"
export TWILIO_ACCOUNT_SID="your-twilio-sid"
export TWILIO_AUTH_TOKEN="your-twilio-token"
export TWILIO_PHONE_NUMBER="+1234567890"
```

#### 2.2 Verify ngrok is Running
```bash
# Your webhook URL is:
# https://gemmiparous-parlously-coreen.ngrok-free.dev/twilio/webhook

# Check if ngrok is running:
curl https://gemmiparous-parlously-coreen.ngrok-free.dev/health

# If not running, start ngrok:
# ngrok http 8000
```

#### 2.3 Check Webhook Endpoint
```bash
# The callContact_tool is configured to POST to:
# https://gemmiparous-parlously-coreen.ngrok-free.dev/twilio/webhook

# With parameters:
# - phone_number: string
# - company_name: string
# - invoice_id: string (optional)
# - customer_org: string (optional)
# - vendor_legal_name: string (optional)
```

### Steps

#### 2.4 Create Test Webhook (if not exists)

Create `/Users/voyager/Documents/GitHub/donna/api/app/routers/twilio.py`:

```python
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import os
from elevenlabs import ElevenLabs

router = APIRouter()

class CallRequest(BaseModel):
    phone_number: str
    company_name: str
    invoice_id: str = ""
    customer_org: str = ""
    vendor_legal_name: str = ""

@router.post("/twilio/webhook")
async def initiate_call(request: CallRequest):
    """
    Webhook endpoint for ElevenLabs callContact_tool
    Initiates a phone call using Twilio integration
    """
    try:
        client = ElevenLabs(api_key=os.environ.get("ELEVENLABS_API_KEY"))
        agent_id = os.environ.get("ELEVEN_LABS_AGENT_ID")
        
        # Initiate signed out conversation with Twilio
        response = client.conversational_ai.conversations.create(
            agent_id=agent_id,
            phone_number=request.phone_number,
            # Pass dynamic variables
            variables={
                "company_name": request.company_name,
                "customer_org": request.customer_org or "Pixamp, Inc",
                "vendor__legal_name": request.vendor_legal_name,
                "email__invoice_number": request.invoice_id,
                "case_id": f"TEST-{request.invoice_id}"
            }
        )
        
        return {
            "success": True,
            "conversation_id": response.conversation_id,
            "status": "call_initiated",
            "message": f"Call initiated to {request.phone_number}"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

Register the router in `main.py`:
```python
from app.routers import twilio

app.include_router(twilio.router, tags=["twilio"])
```

#### 2.5 Test with curl
```bash
# Test the webhook endpoint:
curl -X POST https://gemmiparous-parlously-coreen.ngrok-free.dev/twilio/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1234567890",
    "company_name": "Test Company",
    "invoice_id": "INV-12345",
    "customer_org": "Pixamp, Inc",
    "vendor_legal_name": "Test Vendor LLC"
  }'

# Expected response:
# {
#   "success": true,
#   "conversation_id": "conv_...",
#   "status": "call_initiated",
#   "message": "Call initiated to +1234567890"
# }
```

#### 2.6 Test Real Call
```bash
# Use YOUR phone number for testing
# Replace with your actual number:
curl -X POST https://gemmiparous-parlously-coreen.ngrok-free.dev/twilio/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+15555555555",
    "company_name": "Google Cloud",
    "invoice_id": "INV-TEST-001",
    "customer_org": "Pixamp, Inc",
    "vendor_legal_name": "Google LLC"
  }'

# You should receive a call within 10-15 seconds
```

#### 2.7 Monitor the Call
```bash
# Check ElevenLabs dashboard for conversation:
# https://elevenlabs.io/app/conversational-ai/conversations

# Look for:
# - Conversation ID from the response
# - Call status (completed, in_progress, failed)
# - Transcript
# - Data collection fields
```

### Expected Results
- ✅ Webhook returns 200 OK with conversation_id
- ✅ Phone rings within 10-15 seconds
- ✅ Agent introduces itself as Donna
- ✅ Agent mentions working for "Pixamp, Inc"
- ✅ Agent mentions verifying invoice "INV-TEST-001"
- ✅ Agent mentions "Google Cloud" or "Google LLC"
- ✅ Call follows the structured flow

### Success Criteria
- [ ] Webhook endpoint responds successfully
- [ ] Call is initiated via Twilio
- [ ] Phone rings and agent speaks
- [ ] Dynamic variables are substituted correctly
- [ ] Call completes without errors
- [ ] Conversation appears in dashboard

---

## 🔤 Test 3: Dynamic Variables Testing

### Objective
Verify that all 33 dynamic variables are properly substituted at runtime.

### Variable Categories

#### 3.1 Case Information
```json
{
  "case_id": "CASE-001",
  "user__company_name": "Pixamp, Inc",
  "customer_org": "Pixamp, Inc",
  "user__full_name": "John Doe",
  "user__phone": "+1-555-0100"
}
```

#### 3.2 Email/Invoice Details
```json
{
  "email__vendor_name": "Amazon Web Services",
  "email__invoice_number": "INV-987654",
  "email__amount": "$1,234.56",
  "email__due_date": "2025-10-15",
  "email__billing_address": "410 Terry Ave N, Seattle, WA 98109",
  "email__contact_email": "billing@suspicious-domain.com",
  "email__contact_phone": "+1-888-555-0199"
}
```

#### 3.3 Canonical Vendor Data
```json
{
  "official_canonical_domain": "aws.amazon.com",
  "official_canonical_phone": "+1-206-266-1000",
  "official_canonical_billing_address": "410 Terry Ave N, Seattle, WA 98109",
  "local__phone": "+1-206-266-1000",
  "db__official_phone": "+1-206-266-1000",
  "online__phone": "+1-206-266-1001"
}
```

#### 3.4 Verification Results
```json
{
  "verified__invoice_exists": "true",
  "verified__issued_by_vendor": "true",
  "verified__amount": "$1,234.56",
  "verified__due_date": "2025-10-15",
  "verified__official_contact_email": "billing@aws.amazon.com",
  "verified__ticket_id": "TICKET-12345",
  "verified__rep_name": "Sarah Johnson",
  "verified__security_contact": "security@aws.amazon.com",
  "fraud__is_suspected": "false",
  "rep__secure_email": "billing@aws.amazon.com"
}
```

#### 3.5 Policy/Compliance
```json
{
  "policy_recording_notice": "This call may be recorded for quality assurance purposes",
  "user__account_id": "ACCT-123456789",
  "user__acct_last4": "4421"
}
```

### Testing Method

#### 3.6 Create Test Script
Create `/Users/voyager/Documents/GitHub/donna/api/test_dynamic_variables.py`:

```python
import os
import requests
from elevenlabs import ElevenLabs

# Test data with all variables
test_variables = {
    # Case info
    "case_id": "TEST-CASE-001",
    "user__company_name": "Pixamp Inc",
    "customer_org": "Pixamp Inc",
    "user__full_name": "John Doe",
    "user__phone": "+1-555-0100",
    
    # Email/Invoice
    "email__vendor_name": "Amazon Web Services",
    "email__invoice_number": "INV-987654",
    "email__amount": "$1,234.56",
    "email__due_date": "2025-10-15",
    "email__billing_address": "410 Terry Ave N, Seattle, WA 98109",
    "email__contact_email": "billing@suspicious-domain.com",
    "email__contact_phone": "+1-888-555-0199",
    
    # Canonical data
    "official_canonical_domain": "aws.amazon.com",
    "official_canonical_phone": "+1-206-266-1000",
    "official_canonical_billing_address": "410 Terry Ave N, Seattle, WA 98109",
    "local__phone": "+1-206-266-1000",
    "db__official_phone": "+1-206-266-1000",
    "online__phone": "+1-206-266-1001",
    
    # Verification results (initially empty, filled during call)
    "verified__invoice_exists": "",
    "verified__issued_by_vendor": "",
    "verified__amount": "",
    "verified__due_date": "",
    "verified__official_contact_email": "",
    "verified__ticket_id": "",
    "verified__rep_name": "",
    "verified__security_contact": "",
    "fraud__is_suspected": "",
    "rep__secure_email": "",
    
    # Policy
    "policy_recording_notice": "This call may be recorded for quality assurance",
    "user__account_id": "ACCT-123456789",
    "user__acct_last4": "4421",
    
    # Tool reference
    "call_contact_tool": "callContact_tool"
}

def test_variables_via_api():
    """Test dynamic variables through the webhook"""
    
    webhook_url = "https://gemmiparous-parlously-coreen.ngrok-free.dev/twilio/webhook"
    
    payload = {
        "phone_number": "+15555555555",  # Replace with your test number
        "company_name": test_variables["email__vendor_name"],
        "invoice_id": test_variables["email__invoice_number"],
        "customer_org": test_variables["customer_org"],
        "vendor_legal_name": test_variables["email__vendor_name"]
    }
    
    response = requests.post(webhook_url, json=payload)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Call initiated!")
        print(f"Conversation ID: {data.get('conversation_id')}")
        print(f"\nCheck the call transcript to verify variables:")
        print(f"- Should mention 'Pixamp Inc' (customer_org)")
        print(f"- Should mention 'TEST-CASE-001' (case_id)")
        print(f"- Should mention 'INV-987654' (invoice number)")
        print(f"- Should mention 'Amazon Web Services' (vendor)")
        print(f"- Should mention '$1,234.56' (amount)")
        
        return data.get('conversation_id')
    else:
        print(f"❌ Error: {response.text}")
        return None

def test_variables_via_sdk():
    """Test dynamic variables directly via ElevenLabs SDK"""
    
    client = ElevenLabs(api_key=os.environ.get("ELEVENLABS_API_KEY"))
    agent_id = os.environ.get("ELEVEN_LABS_AGENT_ID")
    
    try:
        # Create conversation with all variables
        response = client.conversational_ai.conversations.create(
            agent_id=agent_id,
            # For testing without actual phone call, use test mode
            # phone_number="+15555555555",  # Uncomment for real call
            variables=test_variables
        )
        
        print(f"✅ Conversation created!")
        print(f"Conversation ID: {response.conversation_id}")
        print(f"\nVariables passed:")
        for key, value in test_variables.items():
            if value:  # Only show non-empty
                print(f"  {key}: {value}")
        
        return response.conversation_id
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    print("=== Testing Dynamic Variables ===\n")
    
    print("Option 1: Test via webhook (makes real call)")
    print("Option 2: Test via SDK (creates conversation)\n")
    
    choice = input("Choose option (1 or 2): ")
    
    if choice == "1":
        conv_id = test_variables_via_api()
    else:
        conv_id = test_variables_via_sdk()
    
    if conv_id:
        print(f"\n📊 View conversation at:")
        print(f"https://elevenlabs.io/app/conversational-ai/conversations/{conv_id}")
