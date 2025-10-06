# Dynamic Variables Workflow Documentation

## 📚 Overview

This document explains how to populate ElevenLabs agent dynamic variables from Supabase email data to enable context-aware phone verification calls.

**Reference**: [ElevenLabs Dynamic Variables Documentation](https://elevenlabs.io/docs/agents-platform/customization/personalization/dynamic-variables)

---

## 🔄 Complete Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│  1. EMAIL ARRIVES → Supabase `emails` table                    │
│     Column: label = 'unsure'                                    │
└────────────────────┬────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│  2. TRIGGER DETECTION                                           │
│     - Supabase webhook/trigger                                  │
│     - Scheduled job polling                                     │
│     - Manual API call                                           │
└────────────────────┬────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│  3. FETCH LATEST EMAIL                                          │
│     SELECT * FROM emails                                        │
│     WHERE label = 'unsure'                                      │
│     ORDER BY created_at DESC                                    │
│     LIMIT 1                                                     │
└────────────────────┬────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│  4. MAP EMAIL FIELDS → DYNAMIC VARIABLES                        │
│                                                                 │
│     Supabase Column          →  Dynamic Variable               │
│     ─────────────────────────────────────────────────────────  │
│     vendor_name              →  email__vendor_name             │
│     invoice_number           →  email__invoice_number          │
│     amount                   →  email__amount                  │
│     due_date                 →  email__due_date                │
│     billing_address          →  email__billing_address         │
│     contact_email            →  email__contact_email           │
│     contact_phone            →  email__contact_phone           │
│                                                                 │
└────────────────────┬────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│  5. ENRICH WITH EXTERNAL DATA                                   │
│     - Google Search for official vendor contact                │
│     - Database lookup for legitimate billers                   │
│     - Previous verification history                            │
│                                                                 │
│     → official_canonical_phone                                 │
│     → official_canonical_domain                                │
│     → db__official_phone                                       │
└────────────────────┬────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│  6. BUILD DYNAMIC VARIABLES DICT                                │
│     {                                                           │
│       "case_id": "CASE-12345",                                  │
│       "customer_org": "Pixamp, Inc",                            │
│       "email__vendor_name": "Acme Corp",                        │
│       "email__invoice_number": "INV-001",                       │
│       "email__amount": "$500.00",                               │
│       "official_canonical_phone": "+18005551234",               │
│       ...                                                       │
│     }                                                           │
└────────────────────┬────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│  7. INITIATE CALL with outbound_call_service                    │
│                                                                 │
│     initiate_call(                                              │
│       destination_number="+18005551234",                        │
│       agent_variables=dynamic_vars                              │
│     )                                                           │
│                                                                 │
│     → ElevenLabs API POST /v1/convai/twilio/outbound-call       │
│       {                                                         │
│         "agent_id": "agent_xxx",                                │
│         "to_number": "+18005551234",                            │
│         "conversation_initiation_client_data": {                │
│           "dynamic_variables": { ... }                          │
│         }                                                       │
│       }                                                         │
└────────────────────┬────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│  8. AGENT RECEIVES RESOLVED VARIABLES                           │
│                                                                 │
│     System Prompt (before resolution):                          │
│     "You are calling about case {{case_id}} for                 │
│      {{customer_org}}. The invoice is {{email__invoice_number}} │
│      from {{email__vendor_name}}..."                            │
│                                                                 │
│     System Prompt (after resolution):                           │
│     "You are calling about case CASE-12345 for                  │
│      Pixamp, Inc. The invoice is INV-001                        │
│      from Acme Corp..."                                         │
│                                                                 │
└────────────────────┬────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│  9. AGENT MAKES CALL                                            │
│     - First message personalized with variables                │
│     - Tool calls can use dynamic variables as parameters       │
│     - Agent has full context of the email and case             │
└────────────────────┬────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│  10. TOOL RESPONSES UPDATE VARIABLES                            │
│                                                                 │
│      During call, tools can update variables:                  │
│      - verified__rep_name = "John Smith"                        │
│      - verified__issued_by_vendor = true                        │
│      - verified__ticket_id = "TICKET-789"                       │
│      - fraud__is_suspected = false                              │
│                                                                 │
└────────────────────┬────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│  11. POST-CALL PROCESSING                                       │
│      - Update Supabase email record with verification results  │
│      - Store conversation transcript                           │
│      - Update email label based on fraud__is_suspected         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 Dynamic Variables Schema

### Complete Variable List (32 variables)

#### 🏢 Customer/User Information (6 variables)
| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `customer_org` | string | Customer organization name | "Pixamp, Inc" |
| `user__company_name` | string | User's company name | "Pixamp, Inc" |
| `user__full_name` | string | Full name of caller | "Sarah Johnson" |
| `user__phone` | string | Callback phone number | "+14155551234" |
| `user__account_id` | string | Full account ID (sensitive) | "ACC-123456789" |
| `user__acct_last4` | string | Last 4 of account | "4421" |

#### 📁 Case Information (2 variables)
| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `case_id` | string | Case identifier | "CASE-12345" |
| `case__id` | string | Alternative case ID | "CASE-12345" |

#### 📨 Email/Invoice Details (7 variables)
| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `email__vendor_name` | string | Vendor name from email | "Acme Corp" |
| `email__invoice_number` | string | Invoice number | "INV-001" |
| `email__amount` | string | Invoice amount | "$500.00" |
| `email__due_date` | string | Due date | "2025-11-15" |
| `email__billing_address` | string | Billing address | "123 Main St" |
| `email__contact_email` | string | Contact email | "billing@example.com" |
| `email__contact_phone` | string | Contact phone | "+18005551234" |

#### ✅ Official/Canonical Info (6 variables)
| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `official_canonical_phone` | string | Official phone (trusted) | "+18005551234" |
| `official_canonical_domain` | string | Official domain | "acme.com" |
| `official_canonical_billing_address` | string | Official address | "456 Corp Ave" |
| `db__official_phone` | string | Phone from database | "+18005551234" |
| `local__phone` | string | Local/preferred phone | "+18005551234" |
| `online__phone` | string | Phone found online | "+18005551234" |

#### 🔍 Verified Information (8 variables)
*These are populated during/after the call via tool responses*

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `verified__rep_name` | string | Rep name spoken to | "John Smith" |
| `verified__issued_by_vendor` | boolean | Vendor issued invoice? | "true" |
| `verified__invoice_exists` | boolean | Invoice exists? | "true" |
| `verified__amount` | string | Confirmed amount | "$500.00" |
| `verified__due_date` | string | Confirmed due date | "2025-11-15" |
| `verified__official_contact_email` | string | Official email confirmed | "billing@acme.com" |
| `verified__ticket_id` | string | Reference ticket | "TICKET-789" |
| `verified__security_contact` | string | Security contact | "security@acme.com" |

#### 🚨 Fraud Detection (1 variable)
| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `fraud__is_suspected` | boolean | Fraud suspected? | "false" |

#### 🔒 System/Compliance (2 variables)
| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `policy_recording_notice` | string | Recording notice | "This call may be recorded..." |
| `rep__secure_email` | string | Secure email (captured during call) | "secure@acme.com" |

---

## 🔧 Implementation Guide

### Step 1: Define Variables in Agent Config

In your agent configuration (`agent_configs/dev/donna-billing-verifier.json`), variables are already defined in:
- System prompt (line 85)
- First message (line 44)
- Tool parameters

Example from first message:
```json
"first_message": "Hi, this is Donna calling from {{customer_org}} about case {{case_id}}..."
```

### Step 2: Set Default Placeholders (Optional)

In the agent config, you can set default values:
```json
"dynamic_variables": {
  "dynamic_variable_placeholders": {
    "customer_org": "Pixamp, Inc",
    "email__vendor_name": "Unknown Vendor",
    ...
  }
}
```

### Step 3: Map Supabase Columns to Variables

```python
def map_email_to_dynamic_variables(email_data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        # Email fields
        "email__vendor_name": email_data.get("vendor_name"),
        "email__invoice_number": email_data.get("invoice_number"),
        "email__amount": email_data.get("amount"),
        
        # Official fields (from enrichment)
        "official_canonical_phone": email_data.get("official_phone"),
        
        # Customer info
        "customer_org": "Pixamp, Inc",
        "case_id": f"CASE-{email_data.get('id')}",
        
        # ... all 32 variables
    }
```

### Step 4: Pass Variables at Runtime

```python
from services.outbound_call_service import initiate_call

# Fetch email with label='unsure'
email = supabase.table("emails").select("*").eq("label", "unsure").single().execute()

# Map to dynamic variables
dynamic_vars = map_email_to_dynamic_variables(email.data)

# Initiate call with variables
result = initiate_call(
    destination_number="+18005551234",
    agent_variables=dynamic_vars  # ← This is the key!
)
```

**Behind the scenes**, `outbound_call_service.py` does:
```python
payload = {
    "agent_id": agent_id,
    "to_number": destination_number,
    "conversation_initiation_client_data": {
        "dynamic_variables": agent_variables  # ← Passed to ElevenLabs
    }
}
```

### Step 5: Tool Responses Update Variables

Configure tool assignments in the agent config to extract values from tool responses:

```json
{
  "type": "webhook",
  "name": "verify_invoice",
  "assignments": [
    {
      "variable_name": "verified__invoice_exists",
      "json_path": "response.invoice_exists"
    },
    {
      "variable_name": "fraud__is_suspected",
      "json_path": "response.is_fraud"
    }
  ]
}
```

---

## 🧪 Testing

### Quick Test (Dry Run)
```bash
python api/test_dynamic_variables.py --dry-run
```
- Fetches latest unsure email
- Maps to dynamic variables
- Prints variable values
- Does NOT make a call

### Full Pipeline Test
```bash
python api/test_dynamic_variables.py
```
- Fetches latest unsure email
- Maps and enriches variables
- Makes actual outbound call
- Monitors call status

### Test Specific Email
```bash
python api/test_dynamic_variables.py --email-id 12345
```

### Override Destination
```bash
python api/test_dynamic_variables.py --destination +14155551234
```

---

## 🔐 Security Best Practices

### 1. Use Secret Variables for Sensitive Data
Prefix with `secret__` to keep out of LLM prompts:
```python
dynamic_vars = {
    "secret__internal_api_key": "sk_xxx",  # Only used in headers/tools
    "customer_org": "Pixamp, Inc"          # Can be in prompts
}
```

### 2. Least-Privilege Disclosure
Only populate sensitive fields if needed:
```python
# Only set account ID if verification requires it
if requires_account_verification:
    dynamic_vars["user__account_id"] = full_account_id
else:
    dynamic_vars["user__acct_last4"] = last_four_digits
```

### 3. Validate All External Data
```python
def validate_phone_number(phone: str) -> bool:
    # Ensure E.164 format
    return bool(re.match(r'^\+[1-9]\d{1,14}$', phone))

if not validate_phone_number(official_phone):
    raise ValueError("Invalid phone number")
```

---

## 📊 Monitoring & Debugging

### View Conversation with Variables
```python
from services.outbound_call_service import get_conversation_details

details = get_conversation_details(conversation_id)
print(details['dynamic_variables'])  # See what was passed
```

### Check Variable Resolution
In the ElevenLabs dashboard:
1. Go to Conversational AI → Conversations
2. Click on the conversation
3. View "Dynamic Variables" section to see resolved values

### Common Issues

**Variables not resolving?**
- Check spelling: `{{customer_org}}` not `{{customer_organization}}`
- Ensure double curly braces: `{{var}}` not `{var}`
- Verify variable is in the dynamic_variables dict

**Values showing as "x" or default?**
- Ensure runtime values are passed in `agent_variables` parameter
- Check that Supabase query returned data
- Verify mapping function is extracting correct columns

---

## 🚀 Production Deployment

### Option 1: Supabase Trigger (Recommended)
Create a Supabase Edge Function that triggers on email insert:

```sql
CREATE TRIGGER on_unsure_email_inserted
AFTER INSERT ON emails
FOR EACH ROW
WHEN (NEW.label = 'unsure')
EXECUTE FUNCTION trigger_verification_call();
```

### Option 2: Webhook from Email Processing
```python
@router.post("/emails/process")
async def process_email(email_data: dict):
    # ... classify email ...
    
    if classification == "unsure":
        # Trigger call immediately
        from services.email_to_call_service import trigger_verification_call
        result = trigger_verification_call(email_data)
```

### Option 3: Scheduled Job
```python
# Run every 5 minutes
@scheduler.scheduled_job('interval', minutes=5)
def check_for_unsure_emails():
    emails = fetch_unsure_emails()
    for email in emails:
        trigger_verification_call(email)
```

---

## 📚 Additional Resources

- [ElevenLabs Dynamic Variables Docs](https://elevenlabs.io/docs/agents-platform/customization/personalization/dynamic-variables)
- [ElevenLabs Agents API Reference](https://elevenlabs.io/docs/api-reference/agents)
- [Supabase Python Client](https://github.com/supabase-community/supabase-py)
- [Donna Agent Config](../agent/agent_configs/dev/donna-billing-verifier.json)

---

## ✅ Checklist

Before deploying to production:

- [ ] All 32 dynamic variables have sensible defaults
- [ ] Email-to-variable mapping handles NULL values gracefully
- [ ] External enrichment (Google Search) is implemented
- [ ] Phone number validation is in place
- [ ] Destination phone priority order is configured
- [ ] Tool assignments are configured for verified__* variables
- [ ] Post-call webhook updates Supabase with results
- [ ] Monitoring and logging are set up
- [ ] Error handling for failed calls is implemented
- [ ] Rate limiting is configured (if needed)
