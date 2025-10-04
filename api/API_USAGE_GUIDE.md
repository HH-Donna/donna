# Biller Extraction API - Usage Guide

## 🚀 Extract Biller Profiles from Gmail

### Endpoint

```
POST /emails/billers/extract
```

### Description

Extracts unique biller/company profiles from user's Gmail invoice emails over the past 3 months. Returns immediately (200 OK) and processes in the background.

### Request

**Headers:**
```
Content-Type: application/json
Authorization: Bearer <API_TOKEN>
```

**Body:**
```json
{
  "user_uuid": "a33138b1-09c3-43ec-a1f2-af3bebed78b7"
}
```

### Complete cURL Example

```bash
curl -X POST "http://localhost:8000/emails/billers/extract" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test" \
  -d '{
    "user_uuid": "a33138b1-09c3-43ec-a1f2-af3bebed78b7"
  }'
```

### Response (Immediate)

```json
{
  "message": "Biller extraction started in background",
  "user_uuid": "a33138b1-09c3-43ec-a1f2-af3bebed78b7",
  "status": "processing",
  "note": "Check your database in a few moments for extracted billers"
}
```

**Status Code:** `200 OK`

**Response Time:** < 500ms (instant)

## 🔄 Background Processing

After the instant response, the system:

1. ✅ Fetches invoice emails from Gmail (past 3 months)
2. ✅ Validates with AI (excludes bank statements, newsletters)
3. ✅ Filters out user's sent emails
4. ✅ Downloads and parses PDF attachments
5. ✅ Extracts biller information with Gemini AI (batched)
6. ✅ Detects invoice versions (drafts vs final)
7. ✅ Fetches profile pictures from Google Contacts
8. ✅ Calculates billing frequency
9. ✅ Deduplicates by company name
10. ✅ Saves all billers to `companies` table in Supabase

**Processing Time:** 30-60 seconds (depends on email count)

## 📊 Data Saved to Database

Each biller is saved to the `companies` table with:

```sql
companies (
  id                      UUID (PK)
  user_id                 UUID (FK to auth.users)
  name                    TEXT (Company name)
  domain                  TEXT (e.g., "netflix.com")
  contact_emails          TEXT[] (All email addresses)
  billing_address         TEXT (Physical address)
  profile_picture_url     TEXT (Logo URL)
  payment_method          TEXT (How they accept payment)
  biller_billing_details  TEXT (Their bank account info)
  user_billing_details    TEXT (User's payment method)
  frequency               TEXT (Monthly, Weekly, etc.)
  total_invoices          INTEGER (Count of invoices)
  source_email_ids        TEXT[] (Gmail message IDs)
  created_at              TIMESTAMPTZ
  updated_at              TIMESTAMPTZ
)
```

## 📋 Example Extracted Data

```json
{
  "name": "G.Network Communications Limited",
  "domain": "g.network",
  "contact_emails": [
    "do-not-reply@g.network",
    "noreply@gocardless.com"
  ],
  "billing_address": "69 Wilson St, London, England, EC2A 2BB",
  "profile_picture_url": "",
  "payment_method": "Direct Debit, Credit Card, Internet Banking",
  "biller_billing_details": "Barclays Bank, Sort Code: 20-78-98, Account No: 03902919",
  "user_billing_details": "Direct Debit from bank account ******84 (HSBC UK BANK PLC)",
  "frequency": "Monthly",
  "total_invoices": 3,
  "source_email_ids": ["msg_id_1", "msg_id_2", "msg_id_3"]
}
```

## 🔐 Authentication Requirements

### User Must Have:

1. ✅ Valid Supabase account
2. ✅ Authenticated via Google OAuth with scopes:
   - `https://mail.google.com/` (Gmail access)
   - `https://www.googleapis.com/auth/gmail.labels`
   - `https://www.googleapis.com/auth/contacts.readonly` (Profile pictures)
3. ✅ OAuth tokens stored in `user_oauth_tokens` table

### API Token:

The `Authorization: Bearer <token>` header must match the `API_TOKEN` environment variable.

## 📝 Integration Example (Frontend)

### JavaScript/TypeScript

```typescript
async function extractBillers(userId: string) {
  try {
    const response = await fetch('http://localhost:8000/emails/billers/extract', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${process.env.API_TOKEN}`
      },
      body: JSON.stringify({
        user_uuid: userId
      })
    });
    
    const data = await response.json();
    
    if (response.ok) {
      console.log('✅ Extraction started:', data.message);
      // Show loading state to user
      // Poll database or wait for webhook to check completion
    } else {
      console.error('❌ Error:', data.detail);
    }
  } catch (error) {
    console.error('❌ Request failed:', error);
  }
}

// Usage
extractBillers('a33138b1-09c3-43ec-a1f2-af3bebed78b7');
```

### Python

```python
import requests

def extract_billers(user_uuid: str):
    response = requests.post(
        'http://localhost:8000/emails/billers/extract',
        headers={
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test'
        },
        json={'user_uuid': user_uuid}
    )
    
    if response.ok:
        data = response.json()
        print(f"✅ {data['message']}")
        return data
    else:
        print(f"❌ Error: {response.json()}")
        return None

# Usage
extract_billers('a33138b1-09c3-43ec-a1f2-af3bebed78b7')
```

## 🔍 Checking Results

### Query Database After Processing

```sql
-- Get all billers for a user
SELECT 
  name,
  domain,
  contact_emails,
  billing_address,
  payment_method,
  frequency,
  total_invoices,
  updated_at
FROM public.companies
WHERE user_id = 'a33138b1-09c3-43ec-a1f2-af3bebed78b7'
ORDER BY total_invoices DESC;
```

### Expected Results

After 30-60 seconds, you should see ~6-8 companies in the database with:
- ✅ Company names
- ✅ Multiple contact emails (if applicable)
- ✅ Physical addresses
- ✅ Payment methods
- ✅ Bank details (separated: biller vs user)
- ✅ Billing frequency
- ✅ Invoice counts

## ⚠️ Error Handling

### Possible Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid API token | Check Authorization header |
| `404 Not Found` | No OAuth tokens for user | User needs to login via Google OAuth |
| `403 Forbidden` | Missing Gmail permissions | User needs to re-authenticate with Gmail scopes |
| `500 Internal Error` | Processing error | Check server logs for details |

### Error Response Format

```json
{
  "detail": "Error message here"
}
```

## 🎯 Best Practices

### 1. **Show Loading State**
```typescript
// Immediate response
setStatus('processing');

// Poll or wait
setTimeout(() => {
  fetchCompaniesFromDatabase();
  setStatus('complete');
}, 45000); // Wait 45 seconds
```

### 2. **Handle Re-runs**
- Safe to call multiple times
- Updates existing companies
- Adds new billers
- Preserves existing data

### 3. **Monitor Logs**
Check server console for:
- `🔄 Starting background biller extraction`
- `✅ Background processing complete`
- `💾 Saved X/Y billers to database`

## 📈 Performance

- **Response Time:** < 500ms (instant)
- **Background Processing:** 30-60 seconds
- **Emails Analyzed:** ~25-100 per user
- **Billers Extracted:** ~6-10 unique companies
- **API Calls:** 2-3 Gemini requests (batched)
- **Database Writes:** 6-10 upserts

## 🔗 Related Endpoints

### Test Attachments
```bash
POST /emails/attachments/test
```
Returns details about attachments found in emails (for debugging).

### Fetch Emails
```bash
POST /emails/fetch
```
Returns raw invoice emails without extraction (for debugging).

### Test Mock Data
```bash
POST /emails/test
```
Returns mock invoice data (no Gmail required).

## 📞 Support

For issues or questions:
1. Check server logs for detailed error messages
2. Verify OAuth tokens are valid and have correct scopes
3. Ensure database schema is up to date
4. Test with `/emails/attachments/test` endpoint first
