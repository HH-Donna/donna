import os
import json
import re
from typing import Dict
from google import genai


def extract_invoice_data(email_body: str, attachment_text: str, sender: str) -> Dict:
    """
    Extract structured invoice data from email and attachments using Gemini AI.
    
    Args:
        email_body: Email body text
        attachment_text: Extracted text from PDF attachments
        sender: Sender email address
        
    Returns:
        dict with extracted invoice data
    """
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        print("⚠️  GEMINI_API_KEY not set, using fallback extraction")
        return fallback_extract_invoice_data(email_body, attachment_text, sender)
    
    try:
        client = genai.Client(
            api_key=gemini_key,
            http_options={'api_version': 'v1alpha'}
        )
        
        # Combine email and attachment text
        full_content = f"""EMAIL BODY:
{email_body[:3000]}

ATTACHMENT CONTENT:
{attachment_text[:5000]}

SENDER: {sender}"""
        
        prompt = f"""Extract invoice/billing information from this email and its attachments.

{full_content}

Extract the following fields (use empty string "" if not found, except amount which should be 0.0):

1. billing_address: Sender/biller's complete billing address (street, city, postal code, country)
2. payment_method: How they accept payment (e.g., "Credit Card", "Direct Debit", "Bank Transfer")
3. biller_billing_details: Biller's bank account, IBAN, sort code for paying them
4. contact_email: Biller's contact email (may be different from sender)
5. user_account_number: User's account/client/customer number with this biller
6. biller_phone_number: Biller's contact phone number
7. invoice_number: Invoice or reference number
8. amount: Total amount due as a number (e.g., 150.50 for £150.50 or $150.50)

IMPORTANT:
- Look carefully in both email body and attachment content
- billing_address is the BILLER's address (who sent the invoice)
- biller_billing_details are for paying the biller (their bank info)
- user_account_number is the user's ID with this company

Return ONLY valid JSON (no markdown, no explanation):

{{
  "billing_address": "123 Main St, City, ZIP, Country",
  "payment_method": "Credit Card",
  "biller_billing_details": "Bank: HSBC, Account: 12345678",
  "contact_email": "billing@company.com",
  "user_account_number": "Account: A-12345",
  "biller_phone_number": "+1-800-123-4567",
  "invoice_number": "INV-2025-001",
  "amount": 150.50
}}"""
        
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=prompt
        )
        
        response_text = response.text
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            extracted_data = json.loads(json_match.group())
        else:
            extracted_data = json.loads(response_text)
        
        # Cleanup client
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(client.aclose())
        except:
            pass
        
        return extracted_data
        
    except Exception as e:
        print(f"⚠️  Gemini extraction failed: {e}, using fallback")
        return fallback_extract_invoice_data(email_body, attachment_text, sender)


def fallback_extract_invoice_data(email_body: str, attachment_text: str, sender: str) -> Dict:
    """
    Fallback regex-based extraction when Gemini is not available.
    """
    combined_text = f"{email_body} {attachment_text}"
    
    # Extract email from sender
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', sender)
    contact_email = email_match.group() if email_match else ''
    
    # Try to extract phone number
    phone_patterns = [
        r'\+?[\d\s\-\(\)]{10,}',
        r'\d{3}[-\.\s]?\d{3}[-\.\s]?\d{4}',
        r'\+\d{1,3}\s?\d{3,}'
    ]
    phone_number = ''
    for pattern in phone_patterns:
        match = re.search(pattern, combined_text)
        if match:
            phone_number = match.group().strip()
            break
    
    # Try to extract invoice number
    invoice_patterns = [
        r'invoice\s*#?\s*:?\s*([A-Z0-9\-]+)',
        r'reference\s*#?\s*:?\s*([A-Z0-9\-]+)',
        r'bill\s*#?\s*:?\s*([A-Z0-9\-]+)'
    ]
    invoice_number = ''
    for pattern in invoice_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            invoice_number = match.group(1)
            break
    
    # Try to extract account number
    account_patterns = [
        r'account\s*#?\s*:?\s*([A-Z0-9\-]+)',
        r'customer\s*#?\s*:?\s*([A-Z0-9\-]+)',
        r'client\s*#?\s*:?\s*([A-Z0-9\-]+)'
    ]
    account_number = ''
    for pattern in account_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            account_number = f"Account: {match.group(1)}"
            break
    
    # Try to extract amount
    amount_patterns = [
        r'[\$£€]\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
        r'total[:\s]+[\$£€]?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
        r'amount[:\s]+[\$£€]?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)'
    ]
    amount = 0.0
    for pattern in amount_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(',', '')
            try:
                amount = float(amount_str)
                break
            except:
                pass
    
    return {
        'billing_address': '',
        'payment_method': '',
        'biller_billing_details': '',
        'contact_email': contact_email,
        'user_account_number': account_number,
        'biller_phone_number': phone_number,
        'invoice_number': invoice_number,
        'amount': amount
    }
