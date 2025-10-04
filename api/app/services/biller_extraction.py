import os
import json
import re
from typing import Dict, List
from datetime import datetime
from bs4 import BeautifulSoup
from google import genai
from app.models import BillerProfile


class BillerExtractor:
    """Service for extracting biller profile information from invoice emails."""
    
    def __init__(self, user_email: str = None):
        """
        Initialize the biller extractor.
        
        Args:
            user_email: The authenticated user's email address (to filter out sent emails)
        """
        self.user_email = user_email.lower() if user_email else None
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        if self.gemini_key:
            try:
                # Initialize Gemini client with the new API
                self.client = genai.Client(
                    api_key=self.gemini_key,
                    http_options={'api_version': 'v1alpha'}
                )
                self.model_name = 'gemini-2.0-flash-exp'  # Latest fast model
                print(f"✅ Initialized Gemini client with {self.model_name}")
            except Exception as e:
                self.client = None
                print(f"⚠️  Failed to initialize Gemini: {e}. Using regex fallback.")
        else:
            self.client = None
            print("⚠️  GEMINI_API_KEY not set. Using regex extraction.")
    
    def extract_biller_profiles(self, emails: List[Dict]) -> List[BillerProfile]:
        """
        Extract unique biller profiles from a list of invoice emails.
        Uses batch processing with AI to minimize API calls.
        
        Args:
            emails: List of email dictionaries with content and metadata
            
        Returns:
            List of unique BillerProfile objects
        """
        if not emails:
            return []
        
        # Filter out emails sent by the user (only analyze received emails)
        received_emails = self._filter_received_emails(emails)
        print(f"📧 Filtered {len(emails)} emails → {len(received_emails)} received emails (excluded user's sent emails)")
        
        if not received_emails:
            return []
        
        # Use AI batch processing if available, otherwise process individually
        if self.client:
            all_billers = self._batch_extract_with_ai(received_emails)
        else:
            # Fallback to individual regex extraction
            all_billers = []
            for email in received_emails:
                try:
                    biller_info = self._extract_from_single_email(email)
                    if biller_info:
                        all_billers.append(biller_info)
                except Exception as e:
                    print(f"Error extracting from email {email.get('id')}: {e}")
                    continue
        
        # Deduplicate billers and calculate frequency
        unique_billers = self._deduplicate_billers(all_billers)
        
        return unique_billers
    
    def _filter_received_emails(self, emails: List[Dict]) -> List[Dict]:
        """Filter to only include emails received by the user (exclude sent emails)."""
        received = []
        
        for email in emails:
            from_address = email.get('from', '').lower()
            
            # Extract email from "Name <email@domain.com>" format
            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', from_address)
            sender_email = email_match.group().lower() if email_match else from_address
            
            # Skip if this email is from the user
            if self.user_email and self.user_email in sender_email:
                print(f"⏭️  Skipping email from user: {email.get('subject', '')[:50]}")
                continue
            
            received.append(email)
        
        return received
    
    def _batch_extract_with_ai(self, emails: List[Dict]) -> List[Dict]:
        """
        Extract biller info from multiple emails in batches using AI.
        Includes validation step to filter out non-invoice emails (bank statements, newsletters).
        """
        BATCH_SIZE = 10  # Process 10 emails per API call
        
        # Step 1: Validate which emails are actual invoices/bills (not statements or newsletters)
        validated_emails = self._validate_invoice_emails(emails)
        print(f"📋 Validated {len(emails)} emails → {len(validated_emails)} are actual invoices/bills")
        
        if not validated_emails:
            return []
        
        all_billers = []
        
        # Step 2: Process validated emails in batches
        for i in range(0, len(validated_emails), BATCH_SIZE):
            batch = validated_emails[i:i + BATCH_SIZE]
            try:
                batch_billers = self._extract_batch_with_ai(batch)
                all_billers.extend(batch_billers)
                print(f"✅ Processed batch {i//BATCH_SIZE + 1}: {len(batch)} emails → {len(batch_billers)} billers extracted")
            except Exception as e:
                print(f"⚠️  Batch {i//BATCH_SIZE + 1} AI extraction failed: {e}. Using regex fallback.")
                # Fallback to regex for this batch
                for email in batch:
                    try:
                        biller_info = self._regex_extract_biller_info(
                            self._prepare_email_content(email), 
                            email
                        )
                        if biller_info:
                            all_billers.append(biller_info)
                    except:
                        continue
        
        return all_billers
    
    def _validate_invoice_emails(self, emails: List[Dict]) -> List[Dict]:
        """
        Use LLM to validate which emails are actual invoices/bills.
        Filters out bank statements, newsletters, receipts without billing info.
        """
        if not self.client or len(emails) == 0:
            return emails  # Skip validation if no AI client
        
        # Prepare emails for validation (lighter content - just subject and snippet)
        validation_data = []
        for idx, email in enumerate(emails):
            validation_data.append({
                'id': idx,
                'from': email.get('from', ''),
                'subject': email.get('subject', ''),
                'snippet': email.get('snippet', '')[:200]
            })
        
        prompt = f"""You are validating which emails are ACTUAL INVOICES or BILLS (not statements, newsletters, or receipts).

Emails to validate:
{json.dumps(validation_data, indent=2)}

INCLUDE emails that are:
✅ Invoices (bills requesting payment)
✅ Receipts for services/subscriptions with billing info
✅ Payment confirmations with billing details
✅ Subscription renewals with charges

EXCLUDE emails that are:
❌ Bank account statements (these are user's statements, not invoices TO the user)
❌ Newsletters or marketing emails
❌ Simple receipts without billing (e.g., "Thanks for your payment")
❌ User's own sent emails

Return ONLY a JSON array of email IDs that should be INCLUDED:

[0, 2, 5, 7, ...]

Return only the array, no explanation."""

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            response_text = response.text
            
            # Parse JSON response
            json_match = re.search(r'\[.*?\]', response_text, re.DOTALL)
            if json_match:
                valid_indices = json.loads(json_match.group())
                validated_emails = [emails[idx] for idx in valid_indices if isinstance(idx, int) and idx < len(emails)]
                excluded_count = len(emails) - len(validated_emails)
                if excluded_count > 0:
                    print(f"🔍 LLM excluded {excluded_count} non-invoice emails (statements/newsletters)")
                return validated_emails
            else:
                print("⚠️  Could not parse validation response, including all emails")
                return emails
                
        except Exception as e:
            print(f"⚠️  Email validation failed: {e}. Including all emails")
            return emails
    
    def _extract_from_single_email(self, email: Dict) -> Dict:
        """Extract biller information from a single email."""
        
        # Prepare email content for analysis
        email_content = self._prepare_email_content(email)
        
        # Use AI to extract structured biller information
        if self.client:
            biller_info = self._ai_extract_biller_info(email_content, email)
        else:
            # Fallback to regex-based extraction
            biller_info = self._regex_extract_biller_info(email_content, email)
        
        return biller_info
    
    def _prepare_email_content(self, email: Dict) -> str:
        """Prepare email content for analysis."""
        parts = []
        
        # Add from address
        parts.append(f"From: {email.get('from', '')}")
        
        # Add subject
        parts.append(f"Subject: {email.get('subject', '')}")
        
        # Add date
        parts.append(f"Date: {email.get('date', '')}")
        
        # Add body content
        if 'body_preview' in email:
            parts.append(f"\nBody:\n{email['body_preview']}")
        elif 'snippet' in email:
            parts.append(f"\nSnippet:\n{email['snippet']}")
        
        # Add full body if available
        if 'full_body' in email:
            parts.append(f"\nFull Content:\n{email['full_body']}")
        
        # Add attachment info
        if 'attachments' in email and email['attachments']:
            parts.append(f"\nAttachments: {len(email['attachments'])} file(s)")
            for att in email['attachments']:
                if 'extracted_text' in att:
                    parts.append(f"\nAttachment '{att['filename']}':\n{att['extracted_text']}")
        
        return "\n".join(parts)
    
    def _extract_batch_with_ai(self, emails: List[Dict]) -> List[Dict]:
        """
        Extract biller information from a batch of emails using a single AI request.
        Uses XML structured output for reliable parsing.
        """
        # Prepare batch content
        emails_xml = []
        for idx, email in enumerate(emails):
            email_content = self._prepare_email_content(email)
            # Truncate each email to ~2000 chars to fit more in context
            email_summary = email_content[:2000]
            
            emails_xml.append(f"""<email id="{idx}" message_id="{email.get('id', '')}">
<from>{email.get('from', '')}</from>
<subject>{email.get('subject', '')}</subject>
<date>{email.get('date', '')}</date>
<content>{email_summary}</content>
</email>""")
        
        batch_xml = "\n".join(emails_xml)
        
        prompt = f"""You are an expert at extracting structured billing information from invoice emails.

Analyze these {len(emails)} invoice emails and extract UNIQUE biller profiles. 

CRITICAL ANALYSIS RULES:
1. If multiple emails are from the same company/biller, extract their info ONCE and combine all their email IDs
2. DETECT invoice versions: If you see "Draft", "Revised", "Adjustment", "Updated" in subject - these are NOT separate invoices
3. For versioned invoices (e.g., "Invoice #123 Draft", "Invoice #123 Final"), count as ONE invoice and use the FINAL version's email ID
4. Detect billing FREQUENCY by analyzing dates between invoices from same biller (weekly, monthly, quarterly, one-time, irregular)

<emails>
{batch_xml}
</emails>

For each UNIQUE biller (company/person sending invoices), extract:

<extraction_guide>
<field name="full_name">Company official name, or "FirstName LastName from CompanyName" for individuals</field>
<field name="email_address">Sender's email address (from From: field)</field>
<field name="domain">Domain name only (e.g., "netflix.com", "uber.com")</field>
<field name="profile_picture_url">Logo image URL from email (empty if none)</field>
<field name="full_address">Complete physical address: street, city, postal code, country</field>
<field name="payment_method">How they accept payment: Credit Card, Direct Debit, Bank Transfer, PayPal, etc.</field>
<field name="billing_info">Bank account details, IBAN, sort code, payment reference numbers, billing instructions</field>
<field name="frequency">Billing pattern: "Monthly", "Weekly", "Quarterly", "Annual", "One-time", "Irregular"</field>
<field name="source_email_ids">Comma-separated email IDs (use FINAL version only for revised invoices)</field>
<field name="latest_date">Most recent invoice date</field>
</extraction_guide>

IMPORTANT:
- Look in email body/footer for addresses, bank details, payment info
- Extract logo URLs from <img src="..."> tags
- For "noreply@company.com", extract company name from domain
- Use empty string "" if info not found
- Deduplicate by email_address

Return ONLY valid JSON array (no markdown, no explanation):

[
  {{
    "full_name": "Company Name Inc.",
    "email_address": "billing@company.com",
    "domain": "company.com",
    "profile_picture_url": "https://logo.url",
    "full_address": "123 Main St, City, ZIP, Country",
    "payment_method": "Credit Card",
    "billing_info": "Account: 1234567890",
    "frequency": "Monthly",
    "source_email_ids": [0, 5, 7],
    "latest_date": "2025-10-01"
  }}
]"""

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            response_text = response.text
            
            # Parse JSON response
            billers = self._parse_json_billers(response_text, emails)
            return billers
            
        except Exception as e:
            print(f"AI batch extraction error: {e}")
            raise
    
    def _parse_json_billers(self, json_text: str, emails: List[Dict]) -> List[Dict]:
        """Parse JSON response into biller dictionaries."""
        try:
            # Extract JSON from response (might have markdown code blocks)
            json_match = re.search(r'\[.*\]', json_text, re.DOTALL)
            if json_match:
                json_text = json_match.group()
            
            billers_data = json.loads(json_text)
            billers = []
            
            for biller_item in billers_data:
                # Convert email indices to actual email IDs
                source_indices = biller_item.get('source_email_ids', [])
                source_email_ids = []
                
                if isinstance(source_indices, list):
                    for idx in source_indices:
                        if isinstance(idx, int) and idx < len(emails):
                            source_email_ids.append(emails[idx].get('id', ''))
                
                # Extract domain if not provided
                domain = biller_item.get('domain', '')
                if not domain and biller_item.get('email_address'):
                    domain_match = re.search(r'@([\w\.-]+\.\w+)', biller_item['email_address'])
                    domain = domain_match.group(1) if domain_match else ''
                
                biller = {
                    'full_name': biller_item.get('full_name', ''),
                    'email_address': biller_item.get('email_address', ''),
                    'domain': domain,
                    'profile_picture_url': biller_item.get('profile_picture_url', ''),
                    'full_address': biller_item.get('full_address', ''),
                    'payment_method': biller_item.get('payment_method', ''),
                    'billing_info': biller_item.get('billing_info', ''),
                    'frequency': biller_item.get('frequency', ''),
                    'source_email_id': source_email_ids[0] if source_email_ids else '',
                    'email_date': biller_item.get('latest_date', ''),
                    'all_source_emails': source_email_ids
                }
                billers.append(biller)
            
            return billers
            
        except Exception as e:
            print(f"Error parsing JSON response: {e}")
            print(f"Response text: {json_text[:500]}")
            return []
    
    def _ai_extract_biller_info(self, email_content: str, email: Dict) -> Dict:
        """Use Gemini AI to extract biller information."""
        
        prompt = f"""Analyze this invoice email and extract the biller/company information in JSON format.

Email Content:
{email_content[:4000]}  

Extract the following information about the BILLER (the company/person sending the invoice):
1. full_name: Company name or "Full Name from Company" if individual
2. email_address: Biller's email address
3. profile_picture_url: Any logo URL found (empty string if none)
4. full_address: Complete billing/company address
5. payment_method: How they accept payment (credit card, bank transfer, etc.)
6. billing_info: Bank details, account numbers, payment instructions

Return ONLY valid JSON with these exact keys. If information is not found, use empty string "".
Example:
{{
    "full_name": "Netflix Inc.",
    "email_address": "billing@netflix.com",
    "profile_picture_url": "",
    "full_address": "100 Winchester Circle, Los Gatos, CA 95032, USA",
    "payment_method": "Credit Card",
    "billing_info": "Charged to card ending in 1234"
}}"""

        try:
            # Use the new Gemini API
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            response_text = response.text
            
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                biller_data = json.loads(json_match.group())
            else:
                biller_data = json.loads(response_text)
            
            # Add metadata
            biller_data['source_email_id'] = email.get('id', '')
            biller_data['email_date'] = email.get('date', '')
            
            return biller_data
            
        except Exception as e:
            print(f"AI extraction error: {e}")
            return self._regex_extract_biller_info(email_content, email)
    
    def _regex_extract_biller_info(self, email_content: str, email: Dict) -> Dict:
        """Fallback regex-based extraction."""
        
        # Extract from email address
        from_address = email.get('from', '')
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', from_address)
        biller_email = email_match.group() if email_match else ''
        
        # Extract company name from "From" field
        name_match = re.match(r'([^<]+)<', from_address)
        if name_match:
            full_name = name_match.group(1).strip()
        else:
            # Try to extract from email domain
            if biller_email:
                domain = biller_email.split('@')[1].split('.')[0]
                full_name = domain.capitalize()
            else:
                full_name = "Unknown Biller"
        
        # Try to extract address using common patterns
        address_patterns = [
            r'\d+\s+[\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Circle|Cir)[\w\s,]+(?:\d{5})?',
            r'(?:P\.?O\.?\s+Box\s+\d+)[^,\n]*',
        ]
        
        full_address = ""
        for pattern in address_patterns:
            match = re.search(pattern, email_content, re.IGNORECASE)
            if match:
                full_address = match.group().strip()
                break
        
        # Extract domain
        domain = ''
        if biller_email:
            domain_match = re.search(r'@([\w\.-]+\.\w+)', biller_email)
            domain = domain_match.group(1) if domain_match else ''
        
        return {
            'full_name': full_name,
            'email_address': biller_email,
            'domain': domain,
            'profile_picture_url': '',
            'full_address': full_address,
            'payment_method': '',
            'billing_info': '',
            'frequency': '',
            'source_email_id': email.get('id', ''),
            'email_date': email.get('date', '')
        }
    
    def _deduplicate_billers(self, all_billers: List[Dict]) -> List[BillerProfile]:
        """Deduplicate billers by email address and merge information."""
        
        biller_map: Dict[str, Dict] = {}
        
        for biller in all_billers:
            email_key = biller.get('email_address', '').lower()
            if not email_key:
                continue
            
            # Handle both single source_email_id and all_source_emails list
            source_emails = biller.get('all_source_emails', [])
            if not source_emails and biller.get('source_email_id'):
                source_emails = [biller.get('source_email_id')]
            
            # Filter out empty strings
            source_emails = [e for e in source_emails if e]
            
            if email_key not in biller_map:
                # Extract domain from email if not provided
                domain = biller.get('domain', '')
                if not domain:
                    domain_match = re.search(r'@([\w\.-]+\.\w+)', email_key)
                    domain = domain_match.group(1) if domain_match else ''
                
                # New biller
                biller_map[email_key] = {
                    'full_name': biller.get('full_name', ''),
                    'email_address': biller.get('email_address', ''),
                    'domain': domain,
                    'profile_picture_url': biller.get('profile_picture_url', ''),
                    'full_address': biller.get('full_address', ''),
                    'payment_method': biller.get('payment_method', ''),
                    'billing_info': biller.get('billing_info', ''),
                    'frequency': biller.get('frequency', ''),
                    'source_emails': source_emails,
                    'email_dates': [biller.get('email_date', '')] if biller.get('email_date') else []
                }
            else:
                # Merge with existing biller
                existing = biller_map[email_key]
                
                # Update fields if they were empty and now have data
                if not existing['full_address'] and biller.get('full_address'):
                    existing['full_address'] = biller['full_address']
                if not existing['payment_method'] and biller.get('payment_method'):
                    existing['payment_method'] = biller['payment_method']
                if not existing['billing_info'] and biller.get('billing_info'):
                    existing['billing_info'] = biller['billing_info']
                if not existing['profile_picture_url'] and biller.get('profile_picture_url'):
                    existing['profile_picture_url'] = biller['profile_picture_url']
                if not existing['frequency'] and biller.get('frequency'):
                    existing['frequency'] = biller['frequency']
                
                # Add to source emails (avoid duplicates)
                for email_id in source_emails:
                    if email_id and email_id not in existing['source_emails']:
                        existing['source_emails'].append(email_id)
                
                if biller.get('email_date') and biller['email_date'] not in existing['email_dates']:
                    existing['email_dates'].append(biller['email_date'])
        
        # Convert to BillerProfile objects
        profiles = []
        for email_addr, data in biller_map.items():
            # Sort dates to find first and last seen
            dates = sorted([d for d in data['email_dates'] if d])
            
            profile = BillerProfile(
                full_name=data['full_name'],
                email_address=data['email_address'],
                domain=data['domain'],
                profile_picture_url=data['profile_picture_url'],
                full_address=data['full_address'],
                payment_method=data['payment_method'],
                billing_info=data['billing_info'],
                frequency=data['frequency'],
                source_emails=data['source_emails'],
                first_seen=dates[0] if dates else '',
                last_seen=dates[-1] if dates else '',
                total_invoices=len(data['source_emails'])
            )
            profiles.append(profile)
        
        # Sort by most recent invoice
        profiles.sort(key=lambda p: p.last_seen, reverse=True)
        
        return profiles
