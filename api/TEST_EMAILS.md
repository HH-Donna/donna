# Test Emails for Fraud Detection System

Based on your companies in the database, here are test emails to send to yourself (allen.brd.75@gmail.com):

## 🟢 Test 1: SAFE Email (Should pass all checks)

**From:** payments-noreply@google.com  
**Subject:** Google Cloud Platform Invoice - October 2025  
**Body:**

```
Google Cloud EMEA Limited
Velasco, Clanwilliam Place
Dublin 2, Ireland

Invoice Date: October 4, 2025
Invoice Number: INV-2025-10-04-001
Account Number: 1987-2824-6290

INVOICE SUMMARY
Services Used: Cloud Storage, Compute Engine
Total Amount Due: £45.50

Payment will be automatically charged to your payment method on file.

Payments profile ID: 1987-2824-6290

Questions? Contact: payments-noreply@google.com

Google Cloud EMEA Limited
VAT Number: 368 0079 83
```

**Expected Result:** ✅ Label = `safe`, company matched, no changes detected

---

## 🟡 Test 2: UNSURE Email (Changed phone number)

**From:** do-not-reply@g.network  
**Subject:** Your G.Network Bill - October 2025  
**Body:**

```
G.Network Communications Limited
69 Wilson St
London, England
EC2A 2BB

Invoice Number: BD1062641
Date: 4 October 2025
Account Number: A-07857F19

Monthly Broadband Service: £35.00
Total Amount Due: £35.00

Payment Methods:
- Direct Debit
- Credit or Debit Card
- Internet Banking
- Phone Banking

Pay by Bank Transfer:
Bank: Barclays Bank
Sort Code: 20-78-98
Account Number: 03902919

For queries, call us: +44 20 1234 5678  ← CHANGED PHONE NUMBER

Quote your invoice number when making payment.
```

**Expected Result:** ⚠️ Label = `unsure`, phone number change detected in `unsure_about` array

---

## 🔴 Test 3: FRAUDULENT Email (Changed bank details - CRITICAL)

**From:** billing@g.network  
**Subject:** URGENT: Update Your Payment Details - G.Network  
**Body:**

```
G.Network Communications Limited
69 Wilson St
London, England
EC2A 2BB

IMPORTANT NOTICE
Invoice Number: BD1062642
Date: 4 October 2025
Account Number: A-07857F19

Due to a banking system upgrade, please update your payment details.

Monthly Broadband Service: £35.00
Total Amount Due: £35.00

NEW PAYMENT DETAILS:  ← CRITICAL CHANGE
Bank: HSBC UK
Sort Code: 12-34-56  ← DIFFERENT BANK
Account Number: 98765432  ← DIFFERENT ACCOUNT
Account Name: G Network Ltd

Please make payment to the NEW account details above.

For queries: billing@g.network
Phone: +44 20 3909 4555
```

**Expected Result:** 🚨 Label = `unsure` (HIGH RISK), bank details change in `unsure_about`, requires advanced research

---

## 🟢 Test 4: SAFE Email (Shopify - verified company)

**From:** billing@shopify.com  
**Subject:** Shopify Invoice #413943929  
**Body:**

```
Shopify Inc.
151 O'Connor Street
Ground floor
Ottawa ON, K2P 2L8
Canada

Invoice Date: October 4, 2025
Invoice Number: 413943929

Monthly Subscription: $29.00
Transaction Fees: $2.50
Total Amount Due: $31.50

Payment Method: Mastercard ending in 0204

Your subscription will renew automatically.

Questions? Contact billing@shopify.com

Shopify Inc.
```

**Expected Result:** ✅ Label = `safe`, company matched, no changes

---

## 🟡 Test 5: UNSURE Email (New company - not in database)

**From:** billing@newcompany.com  
**Subject:** Invoice from New Company Ltd  
**Body:**

```
New Company Ltd
456 Unknown Street
London, UK

Invoice Number: NC-2025-001
Date: October 4, 2025

Services Rendered: Consulting
Total Amount Due: £500.00

Please pay by bank transfer:
Bank: NatWest
Sort Code: 11-22-33
Account: 44556677

Contact: billing@newcompany.com
Phone: +44 20 9999 8888
```

**Expected Result:** ⚠️ Label = `unsure`, company not found in database, triggers online verification

---

## 🔴 Test 6: FRAUDULENT Email (Suspicious domain)

**From:** billing@g-netw0rk.tk  ← Suspicious TLD and typosquatting  
**Subject:** G.Network Invoice - URGENT PAYMENT REQUIRED  
**Body:**

```
G.Network Communications
69 Wilson Street
London EC2A 2BB

Invoice: URGENT-001
Amount Due: £350.00  ← Suspiciously high

IMMEDIATE PAYMENT REQUIRED
Pay within 24 hours to avoid service disconnection.

Bank Details:
Bank: Random Bank
Sort Code: 99-88-77
Account: 11223344

Contact: urgent@g-netw0rk.tk
```

**Expected Result:** 🚨 Label = `fraudulent`, suspicious domain detected, moved to spam

---

## 📋 How to Test:

1. **Send these emails** to allen.brd.75@gmail.com from different accounts
2. **Wait 5-10 seconds** for Pub/Sub notification
3. **Check your database**: `SELECT * FROM emails ORDER BY received_at DESC LIMIT 10;`
4. **Check Gmail**: Look for colored Donna labels
5. **Check logs**: Server console will show processing steps

## 🎯 Expected Results Summary:

| Test | Label | Gmail Label | Moved to Spam | unsure_about |
|------|-------|-------------|---------------|--------------|
| 1 - Google | `safe` | 🟢 Donna/Safe | No | `[]` |
| 2 - G.Network (phone) | `unsure` | 🟡 Donna/Unsure | No | `["biller_phone_number"]` |
| 3 - G.Network (bank) | `unsure` | 🟡 Donna/Unsure | No | `["biller_billing_details"]` |
| 4 - Shopify | `safe` | 🟢 Donna/Safe | No | `[]` |
| 5 - New Company | `unsure` | 🟡 Donna/Unsure | No | `[]` |
| 6 - Fake domain | `fraudulent` | 🔴 Donna/Fraudulent | Yes | N/A |
