# Dynamic Variables Quick Start Guide

## 🎯 TL;DR

When an email arrives with `label='unsure'` in Supabase, this system:
1. Fetches the email data
2. Maps 32 fields to dynamic variables
3. Enriches with Google/database lookups
4. Calls the vendor using ElevenLabs agent with full context
5. Updates the email with verification results

## 🚀 Quick Test

```bash
# Test without making a call (dry run)
python api/test_dynamic_variables.py --dry-run

# Make an actual test call
python api/test_dynamic_variables.py

# Process specific email
python api/test_dynamic_variables.py --email-id 12345
```

## 📦 Key Files

| File | Purpose |
|------|---------|
| `test_dynamic_variables.py` | Test script for the pipeline |
| `services/email_to_call_service.py` | Production service module |
| `services/outbound_call_service.py` | Low-level call initiation |
| `DYNAMIC_VARIABLES_WORKFLOW.md` | Complete documentation |

## 🔑 Key Concepts

### 1. Dynamic Variables are Placeholders
In your agent config, variables look like this:
```
"Hi, this is Donna calling about case {{case_id}} for {{customer_org}}..."
```

### 2. Runtime Values Replace Placeholders
When you start a call, you pass real values:
```python
dynamic_vars = {
    "case_id": "CASE-12345",
    "customer_org": "Pixamp, Inc",
    ...
}

initiate_call(
    destination_number="+18005551234",
    agent_variables=dynamic_vars  # ← Magic happens here
)
```

### 3. Agent Receives Resolved Context
The agent sees:
```
"Hi, this is Donna calling about case CASE-12345 for Pixamp, Inc..."
```

## 📊 Data Flow

```
Supabase Email (label='unsure')
  ↓
map_email_to_dynamic_variables()
  ↓
enrich_with_google_search()
  ↓
enrich_with_database_lookup()
  ↓
initiate_call(agent_variables=...)
  ↓
ElevenLabs resolves {{variables}}
  ↓
Agent makes call with full context
```

## 🗺️ Variable Mapping Example

```python
# Supabase email table columns → Dynamic variables
{
    "vendor_name": "Acme Corp"     → "email__vendor_name": "Acme Corp"
    "invoice_number": "INV-001"    → "email__invoice_number": "INV-001"
    "amount": "500.00"             → "email__amount": "500.00"
    "official_phone": "+18005551234" → "official_canonical_phone": "+18005551234"
    "id": 12345                    → "case_id": "CASE-12345"
}
```

## 🔧 Production Usage

### Option 1: Manual Trigger
```python
from services.email_to_call_service import trigger_verification_call

# Process latest unsure email
result = trigger_verification_call()

# Process specific email
result = trigger_verification_call(email_id="12345")
```

### Option 2: Batch Processing
```python
from services.email_to_call_service import process_batch_unsure_emails

# Process up to 10 unsure emails
results = process_batch_unsure_emails(max_emails=10)
```

### Option 3: Webhook Integration
```python
# In your email processing router
@router.post("/emails/process")
async def process_email(email_data: dict):
    if email_data['label'] == 'unsure':
        from services.email_to_call_service import trigger_verification_call
        result = trigger_verification_call(email_data=email_data)
        return result
```

## 📝 Required Supabase Schema

Your `emails` table should have these columns:

```sql
-- Required for basic operation
id                   (uuid/text)
label                (text) -- should contain 'unsure'
vendor_name          (text)
invoice_number       (text)
amount               (text/numeric)
due_date             (text/date)

-- Optional enrichment columns
official_phone       (text)
official_domain      (text)
db_phone            (text)
local_phone         (text)
online_phone        (text)

-- Optional tracking columns
call_initiated_at    (timestamp)
conversation_id      (text)
call_metadata        (jsonb)
verified_at          (timestamp)
verification_data    (jsonb)
is_fraud            (boolean)
```

## 🎭 All 32 Variables (Condensed)

**Customer (6):** `customer_org`, `user__company_name`, `user__full_name`, `user__phone`, `user__account_id`, `user__acct_last4`

**Case (2):** `case_id`, `case__id`

**Email Details (7):** `email__vendor_name`, `email__invoice_number`, `email__amount`, `email__due_date`, `email__billing_address`, `email__contact_email`, `email__contact_phone`

**Official Info (6):** `official_canonical_phone`, `official_canonical_domain`, `official_canonical_billing_address`, `db__official_phone`, `local__phone`, `online__phone`

**Verified (8):** `verified__rep_name`, `verified__issued_by_vendor`, `verified__invoice_exists`, `verified__amount`, `verified__due_date`, `verified__official_contact_email`, `verified__ticket_id`, `verified__security_contact`

**Fraud (1):** `fraud__is_suspected`

**System (2):** `policy_recording_notice`, `rep__secure_email`

## 🐛 Troubleshooting

**"No email found"**
- Check that emails exist with `label='unsure'`
- Verify Supabase connection works

**"No valid phone number found"**
- Ensure at least one phone field is populated
- Check phone format (should be E.164: `+18005551234`)

**"Variables showing as x or N/A"**
- Default placeholders kick in when runtime values aren't provided
- Check your mapping function extracts correct columns

**"Call initiated but agent doesn't have context"**
- Verify `agent_variables` is passed to `initiate_call()`
- Check ElevenLabs dashboard for actual variable values sent

## 📚 Learn More

- Full Documentation: `DYNAMIC_VARIABLES_WORKFLOW.md`
- ElevenLabs Docs: https://elevenlabs.io/docs/agents-platform/customization/personalization/dynamic-variables
- Agent Config: `agent/agent_configs/dev/donna-billing-verifier.json`

## ✅ Verification Checklist

Before using in production:

- [ ] Tested with `--dry-run` flag
- [ ] Verified variable mapping with real email data
- [ ] Tested actual call with test phone number
- [ ] Confirmed agent receives context correctly
- [ ] Set up error handling and logging
- [ ] Configured webhook or scheduled job
- [ ] Tested post-call database updates
