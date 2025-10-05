# Google Search + ElevenLabs Agent Integration Guide

## Overview

This integration enhances the company verification process by:
1. Using **Google Custom Search API** to find company information online when not found in the database
2. Automatically calling companies via **ElevenLabs Conversational AI** when a phone number is discovered
3. **Injecting user information** from the `profiles` table into the agent's system prompt for personalized calls

## Architecture

### Flow Diagram

```
Email Received
    ↓
Company Verification Against Database
    ↓
[Not Found] → Google Search API
    ↓
Extract: Phone, Address, Email, Website
    ↓
[Phone Found + Confidence ≥ 0.5] → Fetch User Info from profiles table
    ↓
ElevenLabs Agent Call with Dynamic Variables
    ↓
Call Initiated (Async)
```

## Key Components

### 1. ElevenLabs Agent Service (`app/services/eleven_agent.py`)

**Purpose**: Handles phone verification calls using ElevenLabs Conversational AI with user context injection.

**Key Features**:
- Fetches user information from `profiles` table
- Injects dynamic variables into agent prompt:
  - `vendor__legal_name`: Company being verified
  - `vendor_email`: Company email
  - `customer_name`: User's full name
  - `customer_email`: User's email
  - `customer_phone`: User's phone
  - `customer_company`: User's company
- Formats phone numbers to E.164 format
- Returns call status and conversation tracking info

**Usage Example**:
```python
from app.services.eleven_agent import eleven_agent

result = await eleven_agent.verify_company_by_call(
    company_name="Shopify",
    phone_number="(888) 746-7439",
    email="billing@shopify.com",
    user_uuid="user-uuid-here"  # Used to fetch user context
)

if result['success']:
    print(f"Call initiated: {result['conversation_id']}")
```

### 2. Modified Company Verification (`ml/domain_checker.py`)

**Changes Made**:

#### `verify_company_online()` → Now `async`
- Searches Google for company information
- Extracts phone number, address, email, website
- **NEW**: Automatically calls ElevenLabs agent when:
  - Phone number is found
  - Extraction confidence ≥ 0.5
  - User UUID is provided

#### `verify_company_against_database()` → Now `async`
- Checks database for company match
- Falls back to `verify_company_online()` if not found

#### `check_billing_email_legitimacy()` → Now `async`
- Main orchestrator function for fraud detection
- Now supports async company verification

### 3. Google Search Service (`app/services/google_search_service.py`)

**Already Exists** - No changes needed. This service:
- Searches for company info using Google Custom Search API
- Extracts billing address, phone number, email, website
- Returns confidence scores based on extraction quality

## User Information Injection

### Profiles Table Structure

The integration fetches user information from the `profiles` table:

```sql
profiles (
    id UUID PRIMARY KEY,           -- User UUID
    full_name TEXT,                -- User's full name
    phone TEXT,                    -- User's phone number
    company_name TEXT,             -- User's company
    updated_at TIMESTAMP
)
```

### Dynamic Variables Passed to Agent

When calling a company, the agent receives these dynamic variables:

```json
{
    "vendor__legal_name": "Shopify",
    "vendor_email": "billing@shopify.com",
    "customer_name": "John Doe",
    "customer_email": "john.doe@company.com",
    "customer_phone": "+1234567890",
    "customer_company": "Acme Corp"
}
```

These variables can be used in the ElevenLabs agent's system prompt to personalize the conversation.

## Environment Variables Required

Add these to your `.env` file:

```bash
# ElevenLabs Configuration
ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_AGENT_ID=agent_2601k6rm4bjae2z9amfm5w1y6aps
ELEVENLABS_PHONE_NUMBER_ID=phnum_4801k6sa89eqfpnsfjsxbr40phen

# Google Custom Search (already configured)
GOOGLE_CUSTOM_SEARCH_API_KEY=your_google_api_key
GOOGLE_CUSTOM_SEARCH_ENGINE_ID=your_search_engine_id

# Supabase (already configured)
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_service_key
```

## Testing

### Test Script: `test_integration.py`

Run the integration test:

```bash
# Basic test with default company (Shopify)
python api/test_integration.py

# Test with custom company
python api/test_integration.py "Google Cloud"
```

**What the test does**:
1. Creates a mock email from the company
2. Searches Google for company info
3. If phone found, initiates ElevenLabs call
4. Shows extracted attributes and call status

### Expected Output

```
🧪 TESTING GOOGLE SEARCH + ELEVENLABS INTEGRATION
======================================================================

📋 Test Configuration:
   User UUID: a33138b1-09c3-43ec-a1f2-af3bebed78b7
   Company: Shopify
   Email: billing@shopify.com

🔍 STEP 1: Google Search for Company Info
======================================================================

📞 Phone number found for Shopify: (888) 746-7439
   Confidence: 0.75 - Initiating ElevenLabs agent call...
   ✅ Call initiated successfully
   Conversation ID: conv_abc123

📊 Verification Results:
   Is Verified: False
   Verification Status: call
   Confidence: 0.85
   Phone: (888) 746-7439
   Address: 150 Elgin St, Ottawa, ON K2P 1L4, Canada

📞 STEP 2: ElevenLabs Agent Call
======================================================================

✅ Call Initiated Successfully!
   Phone Number: +18887467439
   Company: Shopify
   Conversation ID: conv_abc123
   Call SID: CA123abc...
   Status: initiated

💡 The agent will call the company with user context injected!
   User info (name, email, company) was dynamically added to the prompt
```

## API Endpoints

### Verify Company Online

**Endpoint**: `POST /fraud/verify-online`

**Request**:
```json
{
    "gmail_message": { ... },
    "user_uuid": "user-uuid-here",
    "company_name": "Shopify"
}
```

**Response**:
```json
{
    "email_id": "msg_123",
    "company_name": "Shopify",
    "is_verified": false,
    "verification_status": "call",
    "confidence": 0.85,
    "online_phone": "+18887467439",
    "call_initiated": true,
    "call_result": {
        "success": true,
        "conversation_id": "conv_abc123",
        "call_sid": "CA123abc",
        "phone_number": "+18887467439",
        "company_name": "Shopify"
    }
}
```

## How to Configure ElevenLabs Agent Prompt

In your ElevenLabs agent dashboard, you can reference the dynamic variables:

```
You are Donna, a helpful assistant verifying billing information.

You are calling {{vendor__legal_name}} on behalf of {{customer_name}} 
from {{customer_company}}.

The customer ({{customer_email}}) received an invoice from 
{{vendor_email}}. Please verify that this is a legitimate company 
and confirm their billing contact information.

Ask to speak with the billing department and confirm:
1. The company name is correct
2. The email address is used for billing
3. Any other verification details
```

## Call Triggering Logic

A call is initiated when **ALL** of these conditions are met:

1. ✅ Company not found in database
2. ✅ Google Search finds a phone number
3. ✅ Extraction confidence ≥ 0.5 (50%)
4. ✅ User UUID is provided
5. ✅ ElevenLabs API key is configured

## Verification Status Types

| Status | Meaning | Action |
|--------|---------|--------|
| `legit` | Phone and address both match | No call needed |
| `call` | Phone found and verified | Call initiated |
| `pending` | Insufficient data | Human review needed |

## Error Handling

The integration handles various failure scenarios:

- **No phone found**: Skips call, marks as `pending`
- **Low confidence**: Skips call if confidence < 0.5
- **API errors**: Logs error, continues processing
- **User not found**: Proceeds without user context injection
- **Call fails**: Logs error, marks `call_initiated: false`

## Monitoring Call Results

To check call status later:

```python
from app.services.eleven_agent import eleven_agent

status = await eleven_agent.get_call_status("conv_abc123")
print(status['data'])  # Call transcript, duration, etc.
```

## Future Enhancements

Potential improvements:
- [ ] Store call transcripts in database
- [ ] Add webhook to receive call completion status
- [ ] Implement call result parsing (legitimate vs fraud)
- [ ] Add retry logic for failed calls
- [ ] Support international phone number formats
- [ ] Add call scheduling (avoid calling outside business hours)

## Troubleshooting

### Call not initiated

**Check**:
1. Phone number was found: `result.get('online_phone')`
2. Confidence is sufficient: `result.get('confidence') >= 0.5`
3. ElevenLabs API key is set: `echo $ELEVENLABS_API_KEY`
4. User UUID is valid

### User info not injected

**Check**:
1. User exists in `profiles` table
2. `user_uuid` is passed to `verify_company_by_call()`
3. Profiles table has `full_name`, `phone`, `company_name` fields

### Phone number format issues

The service automatically formats phone numbers to E.164 format:
- `(888) 746-7439` → `+18887467439`
- `888-746-7439` → `+18887467439`
- `8887467439` → `+18887467439`

## Support

For issues or questions:
1. Check logs: `tail -f api/logs/app.log`
2. Test with: `python api/test_integration.py`
3. Review error messages in function responses
