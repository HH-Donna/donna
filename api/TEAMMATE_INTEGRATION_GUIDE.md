# Biller Extraction API - Integration Guide

## 🎯 Quick Start

### API Endpoint

```
POST http://localhost:8000/emails/billers/extract
```

### Request

```bash
curl -X POST "http://localhost:8000/emails/billers/extract" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test" \
  -d '{"user_uuid": "USER_UUID_HERE"}'
```

### Response (Instant - < 500ms)

```json
{
  "message": "Biller extraction started in background",
  "user_uuid": "a33138b1-09c3-43ec-a1f2-af3bebed78b7",
  "status": "processing",
  "note": "Check your database in a few moments for extracted billers"
}
```

## 📋 What It Does

### Automatically Extracts:

1. **Company Information**
   - Full company name
   - All contact email addresses (array)
   - Domain name
   - Company logo/profile picture

2. **Address & Contact**
   - Complete physical/billing address
   - Multiple contact emails if company uses different addresses

3. **Payment Information**
   - Payment methods accepted (Credit Card, Direct Debit, etc.)
   - Biller's bank account details (for paying them)
   - User's payment method used (Card ending XXXX)
   - User's account/customer number with the biller

4. **Billing Patterns**
   - Frequency (Monthly, Weekly, Quarterly, Irregular, One-time)
   - Total invoice count
   - Gmail message IDs for reference

## 💾 Database Schema

### Table: `companies`

```sql
CREATE TABLE companies (
  id                      UUID PRIMARY KEY,
  user_id                 UUID REFERENCES auth.users(id),
  name                    TEXT NOT NULL,
  domain                  TEXT,
  contact_emails          TEXT[],  -- Multiple emails
  billing_address         TEXT,
  profile_picture_url     TEXT,
  payment_method          TEXT,
  biller_billing_details  TEXT,    -- Their bank info
  user_billing_details    TEXT,    -- User's payment method
  user_account_number     TEXT,    -- User's account number
  frequency               TEXT,
  total_invoices          INTEGER,
  source_email_ids        TEXT[],
  created_at              TIMESTAMPTZ,
  updated_at              TIMESTAMPTZ
);
```

### Required Migrations

Run these SQL files in Supabase (in order):

1. `companies_table_migration.sql` - Initial setup
2. `update_billing_fields.sql` - Split billing fields
3. `add_contact_emails_array.sql` - Add email array
4. `drop_contact_email.sql` - Remove single email field
5. `add_user_account_number.sql` - Add account number field

## 🔄 Integration Flow

```
User Request
    ↓
API Returns 200 OK Instantly
    ↓
Background Processing Starts
    ↓
├─ Fetch Gmail Emails (90 days)
├─ Validate with AI (exclude statements/newsletters)
├─ Filter user's sent emails
├─ Download PDF attachments
├─ Extract text from PDFs
├─ AI extraction (Gemini, batched)
├─ Fetch profile pictures (Google Contacts)
├─ Deduplicate by company name
└─ Save to database
    ↓
Complete (30-60 seconds)
```

## 📊 Example Results

### G.Network (Merged from 2 email addresses)

```json
{
  "name": "G.Network Communications Limited",
  "domain": "g.network",
  "contact_emails": [
    "do-not-reply@g.network",
    "noreply@gocardless.com"
  ],
  "billing_address": "69 Wilson St, London, England, EC2A 2BB",
  "payment_method": "Direct Debit, Credit Card, Internet Banking",
  "biller_billing_details": "Barclays Bank, Sort Code: 20-78-98, Account No: 03902919",
  "user_billing_details": "Direct Debit from bank account ******84 (HSBC UK BANK PLC)",
  "user_account_number": "Account No: A-07857F19",
  "frequency": "Monthly",
  "total_invoices": 3
}
```

### Octopus Energy

```json
{
  "name": "Octopus Energy",
  "domain": "octopus.energy",
  "contact_emails": ["hello@octopus.energy"],
  "billing_address": "Octopus Energy Limited, UK House, 5th Floor, 164-182 Oxford Street, London, W1D 1NN",
  "payment_method": "Debit Card, Direct Debit",
  "user_account_number": "Account No: A-07857F19",
  "frequency": "Monthly",
  "total_invoices": 8
}
```

## 💻 Frontend Implementation

### React/Next.js Example

```typescript
'use client';

import { useState } from 'react';

export function ExtractBillersButton({ userId }: { userId: string }) {
  const [status, setStatus] = useState<'idle' | 'processing' | 'complete'>('idle');

  const handleExtract = async () => {
    setStatus('processing');
    
    try {
      const response = await fetch('/api/extract-billers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_uuid: userId })
      });
      
      const data = await response.json();
      
      if (response.ok) {
        console.log('✅ Extraction started');
        
        // Wait for processing (or use websocket/polling)
        setTimeout(() => {
          setStatus('complete');
          // Refresh companies list from database
          fetchCompanies();
        }, 45000); // 45 seconds
      }
    } catch (error) {
      console.error('Error:', error);
      setStatus('idle');
    }
  };

  return (
    <button onClick={handleExtract} disabled={status === 'processing'}>
      {status === 'idle' && 'Extract Billers'}
      {status === 'processing' && 'Processing... (check back in 1 min)'}
      {status === 'complete' && 'Complete! ✓'}
    </button>
  );
}
```

### API Route (Next.js)

```typescript
// app/api/extract-billers/route.ts
export async function POST(request: Request) {
  const { user_uuid } = await request.json();
  
  const response = await fetch('http://localhost:8000/emails/billers/extract', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${process.env.API_TOKEN}`
    },
    body: JSON.stringify({ user_uuid })
  });
  
  return Response.json(await response.json());
}
```

## 🔍 Querying Results

### Get All Billers for User

```typescript
const { data: companies } = await supabase
  .from('companies')
  .select('*')
  .eq('user_id', userId)
  .order('total_invoices', { ascending: false });
```

### Get Monthly Billers

```typescript
const { data: monthlyBillers } = await supabase
  .from('companies')
  .select('*')
  .eq('user_id', userId)
  .eq('frequency', 'Monthly')
  .order('total_invoices', { ascending: false });
```

### Display in UI

```typescript
{companies?.map(company => (
  <div key={company.id} className="company-card">
    <img src={company.profile_picture_url || '/default-logo.png'} />
    <h3>{company.name}</h3>
    <p>{company.domain}</p>
    <p>📍 {company.billing_address}</p>
    <p>💳 {company.payment_method}</p>
    <p>🏦 Account: {company.user_account_number}</p>
    <p>📅 {company.frequency} - {company.total_invoices} invoices</p>
    <div>
      {company.contact_emails.map(email => (
        <span key={email}>{email}</span>
      ))}
    </div>
  </div>
))}
```

## ⚠️ Important Notes

### User Must Be Authenticated

User must have logged in via Google OAuth with these scopes:
- `https://mail.google.com/` (Gmail)
- `https://www.googleapis.com/auth/gmail.labels`
- `https://www.googleapis.com/auth/contacts.readonly` (Profile pictures)

### First-Time Setup

Users need to:
1. Login through your webapp's Google OAuth
2. Grant Gmail and Contacts permissions
3. OAuth tokens automatically stored in `user_oauth_tokens` table

### Processing Time

- Instant API response (< 500ms)
- Background processing: 30-60 seconds
- Depends on number of emails (typically 25-100)

### Re-running

- Safe to call multiple times
- Updates existing companies
- Adds new billers discovered
- Preserves and merges data

## 🎯 Expected Output

For a typical user with 3 months of invoices:

- **Emails Analyzed**: 25-100
- **Emails Validated**: 15-30 (after filtering)
- **Billers Extracted**: 6-10 unique companies
- **Data Completeness**: 70-90% (depends on invoice quality)
- **Processing Time**: 30-60 seconds

## 🐛 Debugging

### Check Server Logs

```bash
# Look for these log messages:
🔄 Starting background biller extraction
📧 Filtered X emails → Y received emails
📋 Validated X emails → Y are actual invoices
✅ Processed batch 1: 10 emails
🖼️  Found X/Y profile pictures
💾 Saved X/Y billers to database
✅ Background processing complete
```

### Test Endpoints

```bash
# Test attachments
POST /emails/attachments/test

# Test raw emails
POST /emails/fetch

# Test mock data
POST /emails/test
```

## 📞 Support

If extraction fails:
1. Check OAuth tokens are valid
2. Verify database schema is up to date
3. Ensure Gemini API key is set
4. Check server logs for detailed errors

## 🎉 Success Criteria

After calling the endpoint, within 1 minute you should see:
- ✅ Companies in database
- ✅ Complete addresses (from PDFs)
- ✅ Bank details (separated: biller vs user)
- ✅ User account numbers
- ✅ Multiple contact emails per company
- ✅ Billing frequency patterns
- ✅ Profile pictures (when available)
