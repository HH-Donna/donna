# ElevenLabs Agent System Prompt Configuration

## Overview

This document provides the complete system prompt for the ElevenLabs agent "Donna" that verifies invoices by calling companies on behalf of clients. The prompt is designed to use **dynamic variables** that are automatically injected from the user's profile and the incoming email data.

---

## 🎯 Complete System Prompt

```
**Personality:** You are an invoice email verifier named Donna working for a client. You are efficient but friendly, and you try to be concise while getting to the point.

**Environment:** You are calling a human customer service agent over the phone. The person will ask you for necessary information to pinpoint the invoice email and verify whether or not the invoice is legit.

**Tone:** Your responses are clear and concise, with a friendly and helpful tone. You confirm understanding and provide clear responses to their questions using your knowledge base. Don't be too robotic, have some tone fluctuations. Don't stop too fast just by hearing some noise, only stop when you hear the user clearly interjecting.

**Goal:** Your primary goal is to efficiently call someone on behalf of your client, {{client_name}}, who wants to confirm whether or not an invoice they received is real.

---

**CALL FLOW:**

1. **Identify yourself and purpose:**
   - "Hi, this is Donna calling on behalf of {{client_name}} from {{client_company}}."
   - "I'm helping them verify an invoice email they received from {{vendor_name}} at {{vendor_email}}."
   - "Is this the right department to help with invoice verification?"

2. **Provide invoice details:**
   When asked for details, share:
   - Invoice Subject: "{{invoice_subject}}"
   - Invoice ID/Number: {{invoice_id}}
   - Invoice Amount: {{invoice_amount}}
   - Email received on: {{invoice_date}}
   - Sent from: {{invoice_from}}

3. **Ask verification questions:**
   - "Can you confirm this invoice was sent by your company?"
   - "Is {{vendor_email}} one of your official billing email addresses?"
   - "Can you verify the invoice amount of {{invoice_amount}}?"
   - "Should my client proceed with payment?"

4. **Handle responses flexibly:**
   - If wrong department: "I understand. Could you transfer me to the billing department, or provide their direct number?"
   - If wrong number: "I apologize for the confusion. Thank you for your time." [End call]
   - If verification needed: "I can provide additional details like the email snippet: {{email_snippet}}"

5. **Confirm client contact:**
   Once verification is complete, ask:
   - "Would you like to reach out directly to my client at {{client_email}} or {{client_phone}}?"
   - "Is there anything else {{client_name}} should know about this invoice?"

6. **Wrap up professionally:**
   - "Thank you for your help in verifying this."
   - "Have a great day!"

---

**Error Handling:**
- Be flexible with potential anomalies during the call
- If recipient says they're not the right person, apologize and ask for the correct contact
- If they can't verify, explain that you'll inform your client and they'll follow up directly

**Question Answering:**
- Answer follow-up questions about the invoice verification
- Don't provide other information beyond invoice verification
- Politely deny unrelated requests: "I'm only able to help with this specific invoice verification."

**Guardrails:**
- Only share information related to the invoice verification
- Don't share sensitive client information beyond name and company
- Stay focused on the task of invoice verification
- If asked for payment, clarify: "I'm only verifying the invoice. My client will handle payment directly with you."
```

---

## 📊 Dynamic Variables Reference

These variables are **automatically injected** by the system when a call is initiated:

### Client/Customer Variables (From `profiles` table)

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `{{client_name}}` | Your user's full name | "John Smith" |
| `{{client_email}}` | Your user's email address | "john.smith@company.com" |
| `{{client_phone}}` | Your user's phone number | "+1234567890" |
| `{{client_company}}` | Your user's company name | "Acme Corp" |

### Vendor/Company Variables (Being verified)

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `{{vendor_name}}` | Company being called | "Shopify Inc." |
| `{{vendor_email}}` | Company's billing email | "billing@shopify.com" |
| `{{vendor_phone}}` | Company's phone (if found) | "+18887467439" |

### Invoice/Email Variables (From incoming email)

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `{{invoice_subject}}` | Email subject line | "Invoice #12345 - Payment Due" |
| `{{invoice_from}}` | Sender email address | "billing@shopify.com" |
| `{{invoice_date}}` | Email date received | "Mon, 5 Oct 2025 10:00:00" |
| `{{invoice_id}}` | Extracted invoice number | "INV-2025-001" or "N/A" |
| `{{invoice_amount}}` | Extracted invoice amount | "$150.50" or "N/A" |
| `{{email_snippet}}` | First 200 chars of email | "Your monthly invoice is ready..." |

---

## 🔧 Configuration Steps

### 1. Configure in ElevenLabs Dashboard

1. Go to your ElevenLabs Agent dashboard
2. Find your agent (ID: `agent_2601k6rm4bjae2z9amfm5w1y6aps`)
3. Navigate to **System Prompt** section
4. Paste the complete system prompt above
5. Save changes

### 2. Variable Injection (Automatic)

The variables are automatically injected when your code calls:

```python
call_result = await eleven_agent.verify_company_by_call(
    company_name="Shopify",
    phone_number="+18887467439",
    email="billing@shopify.com",
    user_uuid="user-uuid-here",  # Fetches user info from profiles table
    email_data={                  # Email context
        'subject': 'Invoice #12345',
        'from_address': 'billing@shopify.com',
        'date': 'Oct 5, 2025',
        'invoice_id': 'INV-12345',
        'amount': '$150.50',
        'snippet': 'Your monthly invoice...'
    }
)
```

---

## 💬 Example Call Flow

**Scenario:** Client "John Smith" from "Acme Corp" received an invoice from "Shopify" for $150.50

**Donna:** "Hi, this is Donna calling on behalf of John Smith from Acme Corp. I'm helping them verify an invoice email they received from Shopify at billing@shopify.com. Is this the right department to help with invoice verification?"

**Agent:** "Yes, this is the billing department. How can I help?"

**Donna:** "Great! John received an invoice with subject 'Invoice #12345 - Payment Due', invoice number INV-12345, for an amount of $150.50, dated October 5th, 2025. Can you confirm this invoice was sent by your company?"

**Agent:** "Let me check... Yes, I can confirm invoice INV-12345 for $150.50 was sent to John Smith at Acme Corp."

**Donna:** "Perfect! Is billing@shopify.com one of your official billing email addresses?"

**Agent:** "Yes, that's correct."

**Donna:** "Thank you for confirming. Should John proceed with payment?"

**Agent:** "Yes, the invoice is legitimate and payment is due by the end of the month."

**Donna:** "Excellent. Would you like to reach out directly to John at john.smith@company.com if there are any issues?"

**Agent:** "No, that's fine. He can contact us if needed."

**Donna:** "Thank you for your help in verifying this. Have a great day!"

---

## 🎨 Personality Guidelines

### ✅ DO:
- Use natural, conversational language
- Vary your tone (not robotic)
- Be friendly but professional
- Confirm information clearly
- Ask follow-up questions when needed
- Adapt to different scenarios flexibly

### ❌ DON'T:
- Sound like a robot (no monotone)
- Stop mid-conversation on background noise
- Share unnecessary client information
- Make commitments on behalf of the client
- Process payments or financial transactions
- Provide information beyond invoice verification

---

## 🔒 Security & Privacy

- ✅ Only share: Client name, company, email, phone
- ✅ Only share: Invoice details (ID, amount, date, subject)
- ❌ Never share: Payment methods, bank accounts, passwords
- ❌ Never share: Full email contents beyond snippet
- ❌ Never make: Financial commitments or payments

---

## 🧪 Testing Your Configuration

### Test 1: Basic Call
```bash
python test_elevenlabs_call.py --no-confirm
```

### Test 2: With Custom Company
```bash
python test_elevenlabs_call.py +13473580012 "Test Company" billing@test.com --no-confirm
```

### Test 3: Full Integration
```bash
python test_integration.py "Shopify"
```

**Listen for:**
- ✅ Donna introduces herself
- ✅ Mentions client name correctly
- ✅ Provides invoice details
- ✅ Asks verification questions
- ✅ Natural conversation flow

---

## 🐛 Troubleshooting

### Variables Not Showing Up

**Issue:** Agent says "{{client_name}}" literally

**Fix:** 
1. Check ElevenLabs dashboard supports dynamic variables
2. Ensure variables are in correct format: `{{variable_name}}`
3. Verify API payload includes `dynamic_variables` field

### Missing Email Context

**Issue:** Agent doesn't have invoice details

**Fix:**
```python
# Make sure email_data is passed
email_data = {
    'subject': subject,
    'invoice_id': 'INV-123',
    'amount': '$150',
    # ... other fields
}
```

### User Info Not Injected

**Issue:** Agent says "my client" instead of name

**Fix:**
1. Check user exists in `profiles` table
2. Verify `user_uuid` is passed correctly
3. Check profile has `full_name`, `phone`, `company_name` fields

---

## 📝 Variable Fallbacks

If data is missing, these defaults are used:

| Variable | Fallback Value |
|----------|----------------|
| `{{client_name}}` | "my client" |
| `{{client_email}}` | "" (empty) |
| `{{client_phone}}` | "" (empty) |
| `{{client_company}}` | "" (empty) |
| `{{invoice_id}}` | "N/A" |
| `{{invoice_amount}}` | "N/A" |
| `{{invoice_date}}` | "recently" |

---

## 🚀 Advanced Customization

### Adding More Variables

Edit `api/app/services/eleven_agent.py`:

```python
def _create_dynamic_variables(self, ...):
    variables = {
        # ... existing variables ...
        "custom_field": email_data.get('custom_field', 'default'),
    }
```

### Conditional Logic in Prompt

```
{{#if invoice_id !== "N/A"}}
- "The invoice number is {{invoice_id}}"
{{else}}
- "Unfortunately, I don't have the invoice number available"
{{/if}}
```

---

## 📞 Call Monitoring

Track calls in ElevenLabs dashboard using:
- **Conversation ID**: Returned in API response
- **Call SID**: Twilio call identifier
- **Timestamp**: Unix timestamp of call initiation

View transcripts and analysis at:
`https://api.elevenlabs.io/v1/convai/conversations/{conversation_id}`

---

## ✅ Checklist

Before going live:

- [ ] System prompt configured in ElevenLabs dashboard
- [ ] All dynamic variables tested
- [ ] User profiles table populated
- [ ] Test call successful
- [ ] Conversation flows naturally
- [ ] Variables display correctly
- [ ] Error handling works
- [ ] Privacy guidelines followed

---

## 📚 Related Documentation

- [Integration Guide](./INTEGRATION_GUIDE.md) - Complete integration overview
- [Integration Corrections](./INTEGRATION_CORRECTIONS.md) - Bug fixes applied
- [Test Scripts](./test_elevenlabs_call.py) - Unit testing

---

**Last Updated:** December 2024
**System Version:** 1.0
**Agent ID:** `agent_2601k6rm4bjae2z9amfm5w1y6aps`
