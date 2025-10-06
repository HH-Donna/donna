# Root Cause Analysis: 404 Errors in Outbound Calling

## Summary

**Problem**: All attempts to initiate outbound calls via ElevenLabs API returned 404 errors.

**Root Cause**: We were using incorrect/outdated API endpoints that don't exist or aren't publicly accessible.

**Solution**: Use the correct Twilio-specific outbound call endpoint with proper parameter structure.

---

## Diagnostic Process

### Step 1: Verified API Authentication ✅
- API Key validation: **PASS** (200 OK)
- User info retrieval: **PASS** (Creator tier, 14,104/110,000 characters used)
- Agent access: **PASS** (Found Donna: agent_2601k6rm4bjae2z9amfm5w1y6aps)
- Phone numbers access: **PASS** (Found +18887064372: phnum_4801k6sa89eqfpnsfjsxbr40phen)

**Conclusion**: Authentication is working, agent exists, phone number is imported.

### Step 2: Tested Conversation Endpoints ❌
```
POST /v1/convai/conversation → 404 Not Found
POST /v1/convai/conversations → 405 Method Not Allowed
POST /v1/convai/conversation/phone → 404 Not Found
```

**Conclusion**: These endpoints either don't exist, are deprecated, or require special permissions.

### Step 3: Analyzed OpenAPI Specification ✅
Downloaded and parsed the ElevenLabs OpenAPI spec to find all available endpoints.

**Discovery**: Found a Twilio-specific endpoint that we weren't using:
```
POST /v1/convai/twilio/outbound-call
```

### Step 4: Tested Correct Endpoint ✅
Using the correct endpoint with proper parameters:
- **Status**: 200 OK
- **Result**: Call successfully initiated
- **Conversation ID**: conv_8001k6sysqn2fqzbdj1aedbpsx6z
- **Twilio Call SID**: CA3a30ebe993987c58f989333d3d0e5b0a

---

## The Fix

### ❌ OLD (Incorrect) Implementation:

```python
# This returns 404
url = f"https://api.elevenlabs.io/v1/convai/phone-number/{phone_number_id}/call"
payload = {
    "agent_id": ELEVEN_LABS_AGENT_ID,
    "to_phone_number": destination_number,
    "dynamic_variables": variables
}
```

### ✅ NEW (Correct) Implementation:

```python
# This works!
url = "https://api.elevenlabs.io/v1/convai/twilio/outbound-call"
payload = {
    "agent_id": ELEVEN_LABS_AGENT_ID,
    "agent_phone_number_id": PHONE_NUMBER_ID,  # Must use the ID, not the number
    "to_number": destination_number,
    "conversation_initiation_client_data": {
        "dynamic_variables": variables  # Nested inside this object
    }
}
```

### Key Differences:

| Parameter | Old | New | Notes |
|-----------|-----|-----|-------|
| **Endpoint** | `/v1/convai/phone-number/{id}/call` | `/v1/convai/twilio/outbound-call` | Twilio-specific endpoint |
| **Phone ID** | In URL path | In request body as `agent_phone_number_id` | More explicit |
| **Destination** | `to_phone_number` | `to_number` | Different param name |
| **Variables** | `dynamic_variables` (root level) | `conversation_initiation_client_data.dynamic_variables` | Nested structure |

---

## API Schema (from OpenAPI spec)

### Required Parameters:
```json
{
  "agent_id": "string",
  "agent_phone_number_id": "string",
  "to_number": "string"
}
```

### Optional Parameters:
```json
{
  "conversation_initiation_client_data": {
    "dynamic_variables": {
      "key": "string | number | boolean"
    },
    "user_id": "string",
    "custom_llm_extra_body": {},
    "conversation_config_override": {},
    "source_info": {}
  }
}
```

---

## Working Test Script

Use `test_working_outbound_call.py` for end-to-end testing:

```bash
cd /Users/voyager/Documents/GitHub/donna/api
python3 test_working_outbound_call.py +13473580012
```

**Expected Output:**
```
✅ CALL INITIATED SUCCESSFULLY!
   Conversation ID: conv_xxxxx
   Twilio Call SID: CAxxxxx
```

---

## Lessons Learned

1. **Documentation Can Be Outdated**: The endpoint we were using may have been from older documentation or examples.

2. **OpenAPI Spec is Authoritative**: When in doubt, fetch and analyze the actual OpenAPI specification.

3. **Provider-Specific Endpoints**: ElevenLabs has separate endpoints for different providers (Twilio vs SIP trunk):
   - `/v1/convai/twilio/outbound-call` (for Twilio)
   - `/v1/convai/sip-trunk/outbound-call` (for SIP)

4. **Phone Number ID vs Phone Number**: The API requires the internal phone number ID (`phnum_xxx`), not the actual phone number string (`+1888...`).

5. **Test Methodically**: Our diagnostic script tested:
   - Authentication
   - Resource access (agents, phone numbers)
   - Multiple endpoint variations
   - OpenAPI spec analysis
   
   This systematic approach identified the exact issue.

---

## Next Steps

1. ✅ Update all outbound call scripts to use correct endpoint
2. ✅ Update `api/app/routers/twilio.py` webhook
3. ✅ Document the correct usage
4. ⬜ Add error handling for common issues
5. ⬜ Create integration tests
6. ⬜ Update fraud detection pipeline to use correct endpoint

---

## Files Updated

- `test_working_outbound_call.py` - New working test script
- `diagnose_elevenlabs_api.py` - Comprehensive diagnostics tool
- `404_ERROR_ROOT_CAUSE.md` - This document

---

## References

- ElevenLabs API: https://api.elevenlabs.io
- OpenAPI Spec: https://api.elevenlabs.io/openapi.json
- Dashboard: https://elevenlabs.io/app/conversational-ai
- Conversation History: https://elevenlabs.io/app/conversational-ai/conversations/{conversation_id}
