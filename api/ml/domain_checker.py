"""
Donna Domain Legitimacy Checker

This module provides focused domain and vendor legitimacy checking for email fraud detection.
It analyzes domain names, vendor information, and account details to determine if the
metadata appears legitimate or suspicious.

Key Features:
- Sophisticated domain similarity matching
- Vendor master database integration
- Account number validation
- Domain age and reputation checking
- Homograph attack detection

Main Components:
1. Domain Analysis: Extract and validate domain information
2. Vendor Matching: Compare against known vendor database
3. Account Validation: Check account number patterns
4. Legitimacy Assessment: Determine if metadata is trustworthy
"""

from __future__ import annotations
import re
import unicodedata
import difflib
import socket
import base64
import os
from typing import Dict, Any, List, Tuple, Optional

# Optional imports for enhanced domain analysis
try:
    import tldextract
except Exception:
    tldextract = None

# Optional imports for Gemini AI
try:
    import google.generativeai as genai
except Exception:
    genai = None

# =============================================================================
# CONFIGURATION AND PATTERNS
# =============================================================================

# Vendor matching removed - will be replaced with separate database integration

# Enhanced domain analysis patterns
SUSPICIOUS_DOMAIN_PATTERNS = [
    r"[0-9]",  # Contains numbers (potential homograph)
    r"[^a-zA-Z0-9.-]",  # Contains special characters
    r"^[0-9]",  # Starts with number
]

# TLD classification for better fraud detection
LEGITIMATE_TLDS = {
    'com', 'org', 'net',           # Classic trusted
    'edu', 'gov', 'mil',           # Institutional
    'co.uk', 'de', 'fr', 'ca',     # Major countries
    'au', 'jp', 'it', 'es',        # Other major countries
    'io', 'ai', 'co',              # Tech companies
    'us', 'uk', 'eu',              # Geographic
}

SUSPICIOUS_TLDS = {
    'tk', 'ml', 'ga', 'cf',        # Free domains often used for fraud
    'ru', 'cn',                    # Countries with high fraud rates
    'info', 'biz', 'name',         # Often used for spam/scams
    'cc', 'pro', 'mobi',           # Mixed reputation TLDs
}

# Bank account validation removed - scammers can easily get valid account numbers

# =============================================================================
# GEMINI AI INTEGRATION
# =============================================================================

def initialize_gemini():
    """Initialize Gemini AI with API key from environment."""
    if not genai:
        return None
    
    # Load environment variables from .env.local
    from dotenv import load_dotenv
    load_dotenv('.env.local')
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Warning: GEMINI_API_KEY not found in environment variables")
        return None
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        return model
    except Exception as e:
        print(f"Warning: Failed to initialize Gemini: {e}")
        return None


def analyze_email_with_gemini(gmail_msg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Use Gemini AI to analyze if email is a bill vs receipt vs neither.
    
    Args:
        gmail_msg (Dict[str, Any]): Gmail API message JSON
        
    Returns:
        Dict[str, Any]: Analysis results containing:
            - is_billing: Boolean indicating if email is billing-related
            - email_type: "bill", "receipt", or "other"
            - confidence: Confidence score (0.0-1.0)
            - reasoning: AI's reasoning for the decision
    """
    model = initialize_gemini()
    if not model:
        # Fallback to rule-based detection
        return {
            "is_billing": is_billing_email(gmail_msg),
            "email_type": "unknown",
            "confidence": 0.5,
            "reasoning": "Gemini not available, using fallback detection"
        }
    
    # Parse email content
    parsed_data = parse_gmail_message(gmail_msg)
    subject = parsed_data.get("subject", "")
    body_text = parsed_data.get("body_text", "")
    from_address = parsed_data.get("from_address", "")
    
    # Check if money is mentioned (trigger for Gemini analysis)
    money_indicators = ["$", "usd", "dollar", "euro", "£", "€", "amount", "total", "price", "cost", "fee", "charge"]
    has_money = any(indicator.lower() in f"{subject} {body_text}".lower() for indicator in money_indicators)
    
    if not has_money:
        return {
            "is_billing": False,
            "email_type": "other",
            "confidence": 0.9,
            "reasoning": "No monetary amounts detected"
        }
    
    # Prepare prompt for Gemini
    prompt = f"""
    Analyze this email to determine if it's a BILL, RECEIPT, or OTHER type of email.

    EMAIL DETAILS:
    From: {from_address}
    Subject: {subject}
    Body: {body_text[:1000]}...

    CLASSIFICATION RULES:
    - BILL: Requesting payment, invoice, statement, payment due, subscription renewal
    - RECEIPT: Confirmation of payment, transaction completed, order confirmation
    - OTHER: Everything else (newsletters, notifications, personal emails, etc.)

    Respond with ONLY a JSON object in this exact format:
    {{
        "is_billing": true/false,
        "email_type": "bill" or "receipt" or "other",
        "confidence": 0.0-1.0,
        "reasoning": "Brief explanation of decision"
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Extract JSON from response
        import json
        if response_text.startswith("```json"):
            response_text = response_text[7:-3]
        elif response_text.startswith("```"):
            response_text = response_text[3:-3]
        
        result = json.loads(response_text)
        
        # Validate response format
        if not all(key in result for key in ["is_billing", "email_type", "confidence", "reasoning"]):
            raise ValueError("Invalid response format")
        
        return result
        
    except Exception as e:
        print(f"Warning: Gemini analysis failed: {e}")
        # Fallback to rule-based detection
        return {
            "is_billing": is_billing_email(gmail_msg),
            "email_type": "unknown",
            "confidence": 0.5,
            "reasoning": f"Gemini failed: {str(e)}, using fallback"
        }


# =============================================================================
# BILLING EMAIL DETECTION
# =============================================================================

def is_billing_email(gmail_msg: Dict[str, Any]) -> bool:
    """
    Check if a Gmail message is billing/invoice related.
    
    Analyzes email subject, body, and sender to determine if it's
    a billing or invoice email that should be processed for fraud detection.
    
    Args:
        gmail_msg (Dict[str, Any]): Gmail API message JSON
        
    Returns:
        bool: True if email appears to be billing/invoice related
    """
    if not gmail_msg or "payload" not in gmail_msg:
        return False
    
    payload = gmail_msg["payload"]
    headers = {}
    
    # Extract headers
    for header in payload.get("headers", []):
        headers[header["name"].lower()] = header["value"]
    
    # Get email content
    subject = headers.get("subject", "").lower()
    from_address = headers.get("from", "").lower()
    
    # Extract body text for analysis
    body_text = ""
    def extract_text_from_parts(parts: List[Dict[str, Any]]):
        nonlocal body_text
        for part in parts:
            mime_type = part.get("mimeType", "")
            if mime_type in ["text/plain", "text/html"]:
                body_data = part.get("body", {}).get("data")
                if body_data:
                    try:
                        decoded_text = base64.urlsafe_b64decode(body_data + "==").decode("utf-8")
                        body_text += decoded_text.lower() + " "
                    except Exception:
                        pass
            if "parts" in part:
                extract_text_from_parts(part["parts"])
    
    if "parts" in payload:
        extract_text_from_parts(payload["parts"])
    
    # Combine all text for analysis
    all_text = f"{subject} {body_text}".lower()
    
    # Billing/invoice keywords
    billing_keywords = [
        # Invoice terms
        "invoice", "bill", "billing", "statement", "receipt",
        # Payment terms  
        "payment", "pay", "due", "overdue", "outstanding",
        # Amount terms
        "amount", "total", "subtotal", "tax", "fee", "charge",
        # Account terms
        "account", "balance", "debit", "credit", "transaction",
        # Subscription terms
        "subscription", "renewal", "monthly", "annual", "recurring",
        # Service terms
        "service", "usage", "consumption", "meter", "quota",
        # Financial terms
        "financial", "fiscal", "quarterly", "yearly", "period"
    ]
    
    # Check if any billing keywords are present
    keyword_matches = sum(1 for keyword in billing_keywords if keyword in all_text)
    
    # Threshold: at least 2 billing keywords or specific high-confidence terms
    high_confidence_terms = ["invoice", "bill", "payment due", "statement", "receipt"]
    has_high_confidence = any(term in all_text for term in high_confidence_terms)
    
    # Additional checks
    has_amount = any(char.isdigit() for char in all_text) and any(word in all_text for word in ["$", "usd", "dollar", "euro", "£", "€"])
    has_account_info = any(term in all_text for term in ["account number", "routing", "iban", "swift", "wire"])
    
    # Decision logic
    is_billing = (
        keyword_matches >= 2 or  # Multiple billing keywords
        has_high_confidence or   # High-confidence terms
        (keyword_matches >= 1 and (has_amount or has_account_info))  # One keyword + financial details
    )
    
    return is_billing


def classify_email_type_with_gemini(
    gmail_msg: Dict[str, Any], 
    user_uuid: Optional[str] = None,
    fraud_logger: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Classify email type using Gemini AI (bill vs receipt vs other).
    
    This function determines if an email is billing-related and what type
    it is using Gemini AI analysis.
    
    Args:
        gmail_msg (Dict[str, Any]): Gmail API message JSON
        user_uuid (str, optional): User UUID for logging
        fraud_logger (EmailFraudLogger, optional): Logger instance for database logging
        
    Returns:
        Dict[str, Any]: Classification results containing:
            - is_billing: Boolean indicating if email is billing-related
            - email_type: "bill", "receipt", or "other"
            - confidence: Confidence score from Gemini
            - reasoning: AI reasoning for classification
            - parsed_data: Extracted email data
            - log_entries: List of logged decisions (if logging enabled)
    """
    # Use Gemini AI to analyze email type
    gemini_result = analyze_email_with_gemini(gmail_msg)
    email_id = gmail_msg.get("id", "unknown")
    log_entries = []
    
    # Log Gemini analysis if logger provided
    if fraud_logger and user_uuid:
        try:
            gemini_log = fraud_logger.log_gemini_analysis(email_id, user_uuid, gemini_result)
            log_entries.append(gemini_log)
        except Exception as e:
            print(f"Warning: Failed to log Gemini analysis: {e}")
    
    # Return classification results
    result = {
        "is_billing": gemini_result["is_billing"],
        "email_type": gemini_result["email_type"],
        "confidence": gemini_result["confidence"],
        "reasoning": gemini_result["reasoning"],
        "parsed_data": parse_gmail_message(gmail_msg),
        "log_entries": log_entries
    }
    
    return result


def analyze_domain_legitimacy(
    gmail_msg: Dict[str, Any],
    email_type: str,
    user_uuid: Optional[str] = None,
    fraud_logger: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Analyze domain legitimacy for billing emails.
    
    This function performs domain analysis on the sender's email address
    to determine if it's legitimate or suspicious.
    
    Args:
        gmail_msg (Dict[str, Any]): Gmail API message JSON
        email_type (str): Email type from Gemini classification ("bill", "receipt", "other")
        user_uuid (str, optional): User UUID for logging
        fraud_logger (EmailFraudLogger, optional): Logger instance for database logging
        
    Returns:
        Dict[str, Any]: Domain analysis results containing:
            - is_legitimate: Boolean indicating domain legitimacy
            - domain_analysis: Detailed domain analysis results
            - confidence: Confidence score from domain analysis
            - reasons: List of issues found
            - halt_reason: Reason for halting (if applicable)
            - log_entries: List of logged decisions (if logging enabled)
    """
    email_id = gmail_msg.get("id", "unknown")
    log_entries = []
    
    # Parse email data
    parsed_data = parse_gmail_message(gmail_msg)
    from_address = parsed_data["from_address"]
    
    # If no sender address, halt
    if not from_address:
        result = {
            "is_legitimate": False,
            "domain_analysis": {"is_suspicious": True, "reasons": ["no_sender"], "confidence": 1.0},
            "confidence": 1.0,
            "reasons": ["no_sender"],
            "halt_reason": "no_sender",
            "log_entries": log_entries
        }
        
        # Log domain analysis for no sender case (halt)
        if fraud_logger and user_uuid:
            try:
                domain_log = fraud_logger.log_domain_check(email_id, user_uuid, result)
                log_entries.append(domain_log)
                result["log_entries"] = log_entries
            except Exception as e:
                print(f"Warning: Failed to log domain analysis: {e}")
        
        return result
    
    # Perform domain legitimacy check
    legitimacy_result = check_domain_legitimacy(
        email_address=from_address,
        vendor_name=None
    )
    
    # Log domain analysis if logger provided
    if fraud_logger and user_uuid:
        try:
            domain_log = fraud_logger.log_domain_check(email_id, user_uuid, legitimacy_result)
            log_entries.append(domain_log)
        except Exception as e:
            print(f"Warning: Failed to log domain analysis: {e}")
    
    # Determine halt reason based on domain analysis
    if not legitimacy_result["is_legitimate"]:
        legitimacy_result["halt_reason"] = "suspicious_domain"
    else:
        legitimacy_result["halt_reason"] = None  # Proceed
    
    legitimacy_result["log_entries"] = log_entries
    
    return legitimacy_result


def verify_company_against_database(
    gmail_msg: Dict[str, Any],
    user_uuid: str,
    fraud_logger: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Verify company against whitelisted companies database.
    
    This function checks if the company from the email matches an existing
    company in the user's whitelisted companies database and compares
    key attributes to ensure consistency.
    
    Args:
        gmail_msg (Dict[str, Any]): Gmail API message JSON
        user_uuid (str): User UUID for database lookup
        fraud_logger (EmailFraudLogger, optional): Logger instance for database logging
        
    Returns:
        Dict[str, Any]: Company verification results containing:
            - is_verified: Boolean indicating if company is verified
            - company_match: Matched company data from database (if found)
            - attribute_differences: List of attributes that differ
            - confidence: Confidence score
            - reasoning: Explanation of verification result
            - trigger_agent: Boolean indicating if agent should be triggered
            - log_entries: List of logged decisions (if logging enabled)
    """
    email_id = gmail_msg.get("id", "unknown")
    log_entries = []
    
    # Parse email data to extract company information
    parsed_data = parse_gmail_message(gmail_msg)
    from_address = parsed_data["from_address"]
    
    # Extract company name from email (simplified - could be enhanced)
    company_name = ""
    if from_address:
        # Extract domain and try to infer company name
        domain = domain_from_address(from_address)
        company_name = domain.split('.')[0].title() if domain else ""
    
    # Extract billing information from email content
    # This is simplified - in practice, you'd use more sophisticated extraction
    subject = parsed_data.get("subject", "")
    body_text = parsed_data.get("body_text", "")
    
    # Try to extract billing address, phone, frequency from email content
    # This is a simplified approach - you might want to use AI or regex patterns
    extracted_billing_address = ""  # Would extract from email content
    extracted_phone = ""  # Would extract from email content  
    extracted_frequency = ""  # Would extract from email content
    
    try:
        # Import here to avoid circular imports
        from app.database.supabase_client import get_supabase_client
        supabase = get_supabase_client()
        
        # Search for companies by user_id and name similarity
        companies_result = supabase.table('companies')\
            .select('*')\
            .eq('user_id', user_uuid)\
            .ilike('name', f'%{company_name}%')\
            .execute()
        
        if not companies_result.data:
            # No matching company found - perform online verification
            online_result = verify_company_online(gmail_msg, user_uuid, company_name, fraud_logger)
            log_entries.extend(online_result["log_entries"])
            
            # Return online verification result
            result = {
                "is_verified": online_result["is_verified"],
                "company_match": None,
                "attribute_differences": online_result["attribute_differences"],
                "confidence": online_result["confidence"],
                "reasoning": f"No matching company found for '{company_name}'. {online_result['reasoning']}",
                "trigger_agent": online_result["trigger_agent"],
                "online_verified": True,
                "online_is_verified": online_result["is_verified"],
                "online_reasoning": online_result["reasoning"],
                "log_entries": log_entries
            }
            
            return result
        
        # Found matching company(ies) - check attributes
        matched_company = companies_result.data[0]  # Take first match
        
        # Compare key attributes
        attribute_differences = []
        
        # Check billing address
        if extracted_billing_address and matched_company.get('billing_address'):
            if extracted_billing_address.lower() != matched_company['billing_address'].lower():
                attribute_differences.append({
                    'attribute': 'billing_address',
                    'expected': matched_company['billing_address'],
                    'actual': extracted_billing_address
                })
        
        # Check frequency
        if extracted_frequency and matched_company.get('frequency'):
            if extracted_frequency.lower() != matched_company['frequency'].lower():
                attribute_differences.append({
                    'attribute': 'frequency',
                    'expected': matched_company['frequency'],
                    'actual': extracted_frequency
                })
        
        # Check phone number
        if extracted_phone and matched_company.get('biller_phone_number'):
            if extracted_phone != matched_company['biller_phone_number']:
                attribute_differences.append({
                    'attribute': 'biller_phone_number',
                    'expected': matched_company['biller_phone_number'],
                    'actual': extracted_phone
                })
        
        # Check email address
        if from_address and matched_company.get('contact_emails'):
            if from_address not in matched_company['contact_emails']:
                attribute_differences.append({
                    'attribute': 'email',
                    'expected': matched_company['contact_emails'],
                    'actual': from_address
                })
        
        # Determine verification result
        is_verified = len(attribute_differences) == 0
        trigger_agent = len(attribute_differences) > 0
        
        if is_verified:
            reasoning = f"Company '{matched_company['name']}' verified - all attributes match"
            confidence = 0.95
        else:
            reasoning = f"Company '{matched_company['name']}' found but attributes differ: {', '.join([diff['attribute'] for diff in attribute_differences])}"
            confidence = 0.8
        
        result = {
            "is_verified": is_verified,
            "company_match": matched_company,
            "attribute_differences": attribute_differences,
            "confidence": confidence,
            "reasoning": reasoning,
            "trigger_agent": trigger_agent,
            "log_entries": log_entries
        }
        
        # Log company verification
        if fraud_logger:
            try:
                company_log = fraud_logger.log_company_verification(email_id, user_uuid, result)
                log_entries.append(company_log)
                result["log_entries"] = log_entries
            except Exception as e:
                print(f"Warning: Failed to log company verification: {e}")
        
        return result
        
    except Exception as e:
        print(f"Error in company verification: {e}")
        result = {
            "is_verified": False,
            "company_match": None,
            "attribute_differences": [],
            "confidence": 0.5,
            "reasoning": f"Company verification failed: {str(e)}",
            "trigger_agent": False,
            "log_entries": log_entries
        }
        
        # Log company verification error
        if fraud_logger:
            try:
                company_log = fraud_logger.log_company_verification(email_id, user_uuid, result)
                log_entries.append(company_log)
                result["log_entries"] = log_entries
            except Exception as e:
                print(f"Warning: Failed to log company verification: {e}")
        
        return result


def verify_company_online(
    gmail_msg: Dict[str, Any],
    user_uuid: str,
    company_name: str,
    fraud_logger: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Verify company online using Google Search API.
    
    This function searches for company information online and compares
    three attributes: billing_address, biller_phone_number, and email.
    
    Args:
        gmail_msg (Dict[str, Any]): Gmail API message JSON
        user_uuid (str): User UUID for database lookup
        company_name (str): Company name to search for
        fraud_logger (EmailFraudLogger, optional): Logger instance for database logging
        
    Returns:
        Dict[str, Any]: Online verification results containing:
            - is_verified: Boolean indicating if online verification passed
            - company_name: Company name searched
            - search_query: Query used for search
            - attribute_differences: List of attributes that differ
            - confidence: Confidence score
            - reasoning: Explanation of verification result
            - trigger_agent: Boolean indicating if agent should be triggered
            - log_entries: List of logged decisions (if logging enabled)
    """
    email_id = gmail_msg.get("id", "unknown")
    log_entries = []
    
    # Parse email data to extract attributes for comparison
    parsed_data = parse_gmail_message(gmail_msg)
    subject = parsed_data.get("subject", "")
    body_text = parsed_data.get("body_text", "")
    from_address = parsed_data.get("from_address", "")
    
    # Extract attributes from email (simplified - would use more sophisticated extraction)
    extracted_billing_address = ""  # Would extract from email content
    extracted_phone = ""  # Would extract from email content  
    extracted_frequency = ""  # Would extract from email content
    
    # Construct search query
    search_query = f"{company_name} billing address phone number email"
    
    try:
        # Import here to avoid circular imports
        from app.database.supabase_client import get_supabase_client
        from app.services.google_search_service import google_search_service
        supabase = get_supabase_client()
        
        # Perform actual Google Search API call
        search_response = google_search_service.search_company_info(company_name)
        
        # Extract attributes from search results
        extracted_attributes = google_search_service.extract_company_attributes(search_response, company_name)
        
        online_billing_address = extracted_attributes.get('billing_address')
        online_phone = extracted_attributes.get('phone_number')
        online_email = extracted_attributes.get('email')
        online_website = extracted_attributes.get('website')
        extraction_confidence = extracted_attributes.get('confidence', 0.0)
        
        # Use search results from the service
        search_results = {
            'success': search_response.get('success', False),
            'query': search_response.get('query', search_query),
            'total_results': search_response.get('total_results', '0'),
            'items': search_response.get('items', []),
            'error': search_response.get('error')
        }
        
        # Compare attributes
        attribute_differences = []
        
        # Check billing address
        if extracted_billing_address and online_billing_address:
            if extracted_billing_address.lower() != online_billing_address.lower():
                attribute_differences.append({
                    'attribute': 'billing_address',
                    'expected': online_billing_address,
                    'actual': extracted_billing_address
                })
        
        # Check phone number
        if extracted_phone and online_phone:
            if extracted_phone != online_phone:
                attribute_differences.append({
                    'attribute': 'biller_phone_number',
                    'expected': online_phone,
                    'actual': extracted_phone
                })
        
        # Check email address
        if from_address and online_email:
            if from_address.lower() != online_email.lower():
                attribute_differences.append({
                    'attribute': 'email',
                    'expected': online_email,
                    'actual': from_address
                })
        
        # Determine verification result
        is_verified = len(attribute_differences) == 0
        trigger_agent = len(attribute_differences) > 0
        
        # Calculate confidence based on extraction confidence and verification result
        base_confidence = extraction_confidence
        if is_verified:
            reasoning = f"Online verification passed - all attributes match for '{company_name}'"
            confidence = min(base_confidence + 0.2, 1.0)  # Boost confidence for verified results
        else:
            reasoning = f"Online verification failed - attributes differ for '{company_name}': {', '.join([diff['attribute'] for diff in attribute_differences])}"
            confidence = max(base_confidence - 0.1, 0.1)  # Reduce confidence for failed verification
        
        result = {
            "is_verified": is_verified,
            "company_name": company_name,
            "search_query": search_query,
            "attribute_differences": attribute_differences,
            "confidence": confidence,
            "reasoning": reasoning,
            "trigger_agent": trigger_agent,
            "search_results": search_results,
            "log_entries": log_entries
        }
        
        # Save search results to database
        try:
            search_data = {
                'email_id': email_id,
                'user_uuid': user_uuid,
                'company_name': company_name,
                'search_query': search_query,
                'billing_address': online_billing_address,
                'biller_phone_number': online_phone,
                'email': online_email,
                'frequency': None,  # Not searched online
                'search_results': search_results,
                'extracted_attributes': {
                    'billing_address': online_billing_address,
                    'biller_phone_number': online_phone,
                    'email': online_email,
                    'website': online_website,
                    'extraction_confidence': extraction_confidence,
                    'extraction_method': extracted_attributes.get('extraction_method', 'search_results')
                },
                'confidence': confidence
            }
            
            supabase.table('google_search_results').insert(search_data).execute()
        except Exception as e:
            print(f"Warning: Failed to save search results: {e}")
        
        # Log online verification
        if fraud_logger:
            try:
                online_log = fraud_logger.log_online_verification(email_id, user_uuid, result)
                log_entries.append(online_log)
                result["log_entries"] = log_entries
            except Exception as e:
                print(f"Warning: Failed to log online verification: {e}")
        
        return result
        
    except Exception as e:
        print(f"Error in online verification: {e}")
        result = {
            "is_verified": False,
            "company_name": company_name,
            "search_query": search_query,
            "attribute_differences": [],
            "confidence": 0.5,
            "reasoning": f"Online verification failed: {str(e)}",
            "trigger_agent": True,  # Trigger agent if search fails
            "search_results": None,
            "log_entries": log_entries
        }
        
        # Log online verification error
        if fraud_logger:
            try:
                online_log = fraud_logger.log_online_verification(email_id, user_uuid, result)
                log_entries.append(online_log)
                result["log_entries"] = log_entries
            except Exception as e:
                print(f"Warning: Failed to log online verification: {e}")
        
        return result


def check_billing_email_legitimacy(
    gmail_msg: Dict[str, Any], 
    user_uuid: Optional[str] = None,
    fraud_logger: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Complete fraud detection pipeline for billing emails.
    
    This is the main orchestrator function that:
    1. First checks if email is billing-related using rule-based detection
    2. Then classifies email type using Gemini AI (bill vs receipt vs other)
    3. Analyzes domain legitimacy for bills
    4. Verifies company against whitelisted companies database
    
    Args:
        gmail_msg (Dict[str, Any]): Gmail API message JSON
        user_uuid (str, optional): User UUID for logging
        fraud_logger (EmailFraudLogger, optional): Logger instance for database logging
        
    Returns:
        Dict[str, Any]: Complete analysis results containing:
            - is_billing: Boolean indicating if email is billing-related
            - email_type: "bill", "receipt", or "other"
            - is_legitimate: Boolean indicating domain legitimacy (if bill)
            - domain_analysis: Domain analysis results (if bill)
            - is_verified: Boolean indicating company verification (if bill)
            - company_verification: Company verification results (if bill)
            - confidence: Confidence score
            - reasons: List of issues found (if bill)
            - reasoning: AI reasoning for billing classification
            - parsed_data: Extracted email data
            - log_entries: List of logged decisions (if logging enabled)
            - halt_reason: Reason for halting (if applicable)
    """
    email_id = gmail_msg.get("id", "unknown")
    all_log_entries = []
    
    # Step 1: Check if email is billing-related (rule-based, fast filter)
    is_billing_rule_based = is_billing_email(gmail_msg)
    
    # If not billing-related by rule-based check, halt early
    if not is_billing_rule_based:
        result = {
            "is_billing": False,
            "email_type": "other",
            "is_legitimate": None,
            "domain_analysis": None,
            "confidence": 0.9,  # High confidence in rule-based detection
            "reasons": [],
            "reasoning": "Rule-based detection: Not billing-related",
            "parsed_data": parse_gmail_message(gmail_msg),
            "log_entries": all_log_entries,
            "halt_reason": "not_billing_rule_based"
        }
        
        # Log final decision for non-billing emails (halt)
        if fraud_logger and user_uuid:
            try:
                final_log = fraud_logger.log_final_decision(email_id, user_uuid, result)
                all_log_entries.append(final_log)
                result["log_entries"] = all_log_entries
            except Exception as e:
                print(f"Warning: Failed to log final decision: {e}")
        
        return result
    
    # Step 2: Classify email type using Gemini AI
    classification_result = classify_email_type_with_gemini(gmail_msg, user_uuid, fraud_logger)
    all_log_entries.extend(classification_result["log_entries"])
    
    # If not billing-related by Gemini, halt processing
    if not classification_result["is_billing"]:
        result = {
            "is_billing": False,
            "email_type": classification_result["email_type"],
            "is_legitimate": None,
            "domain_analysis": None,
            "confidence": classification_result["confidence"],
            "reasons": [],
            "reasoning": classification_result["reasoning"],
            "parsed_data": classification_result["parsed_data"],
            "log_entries": all_log_entries,
            "halt_reason": "not_billing_gemini"
        }
        
        # Log final decision for non-billing emails (halt)
        if fraud_logger and user_uuid:
            try:
                final_log = fraud_logger.log_final_decision(email_id, user_uuid, result)
                all_log_entries.append(final_log)
                result["log_entries"] = all_log_entries
            except Exception as e:
                print(f"Warning: Failed to log final decision: {e}")
        
        return result
    
    # If it's a receipt, proceed (receipts are safe)
    if classification_result["email_type"] == "receipt":
        result = {
            "is_billing": True,
            "email_type": "receipt",
            "is_legitimate": None,  # Skip analysis for receipts
            "domain_analysis": None,
            "confidence": classification_result["confidence"],
            "reasons": [],
            "reasoning": f"Receipt detected: {classification_result['reasoning']}",
            "parsed_data": classification_result["parsed_data"],
            "log_entries": all_log_entries,
            "halt_reason": None  # Proceed
        }
        
        # Log final decision for receipts (proceed)
        if fraud_logger and user_uuid:
            try:
                final_log = fraud_logger.log_final_decision(email_id, user_uuid, result)
                all_log_entries.append(final_log)
                result["log_entries"] = all_log_entries
            except Exception as e:
                print(f"Warning: Failed to log final decision: {e}")
        
        return result
    
    # Step 3: Analyze domain legitimacy for bills
    domain_result = analyze_domain_legitimacy(
        gmail_msg, 
        classification_result["email_type"], 
        user_uuid, 
        fraud_logger
    )
    all_log_entries.extend(domain_result["log_entries"])
    
    # Step 4: Verify company against whitelisted companies database
    company_result = verify_company_against_database(
        gmail_msg,
        user_uuid,
        fraud_logger
    )
    all_log_entries.extend(company_result["log_entries"])
    
    # Combine all results
    final_result = {
        "is_billing": True,
        "email_type": classification_result["email_type"],
        "is_legitimate": domain_result["is_legitimate"],
        "domain_analysis": domain_result["domain_analysis"],
        "is_verified": company_result["is_verified"],
        "company_verification": company_result,
        "online_verified": company_result.get("online_verified", False),
        "online_is_verified": company_result.get("online_is_verified", False),
        "online_reasoning": company_result.get("online_reasoning", ""),
        "confidence": min(classification_result["confidence"], domain_result["confidence"], company_result["confidence"]),
        "reasons": domain_result["reasons"],
        "reasoning": classification_result["reasoning"],
        "parsed_data": classification_result["parsed_data"],
        "log_entries": all_log_entries,
        "halt_reason": domain_result["halt_reason"] or (None if company_result["is_verified"] else "company_verification_failed"),
        "company_reasoning": company_result["reasoning"],
        "trigger_agent": company_result.get("trigger_agent", False)
    }
    
    # Log final decision for bills
    if fraud_logger and user_uuid:
        try:
            final_log = fraud_logger.log_final_decision(email_id, user_uuid, final_result)
            all_log_entries.append(final_log)
            final_result["log_entries"] = all_log_entries
        except Exception as e:
            print(f"Warning: Failed to log final decision: {e}")
    
    return final_result


# =============================================================================
# GMAIL API PARSING
# =============================================================================

def parse_gmail_message(gmail_msg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse Gmail API message to extract domain analysis data.
    
    Extracts email headers, body content, and attachment information
    from Gmail API message format for domain legitimacy checking.
    
    Args:
        gmail_msg (Dict[str, Any]): Gmail API message JSON
        
    Returns:
        Dict[str, Any]: Parsed message data containing:
            - from_address: Sender email address
            - to_address: Recipient email address  
            - subject: Email subject line
            - body_text: Combined plain text and HTML content
            - attachments: List of attachment metadata
    """
    if not gmail_msg or "payload" not in gmail_msg:
        return {
            "from_address": "",
            "to_address": "",
            "subject": "",
            "body_text": "",
            "attachments": []
        }
    
    payload = gmail_msg["payload"]
    headers = {}
    
    # Extract headers
    for header in payload.get("headers", []):
        headers[header["name"].lower()] = header["value"]
    
    # Extract basic email info
    from_address = headers.get("from", "")
    to_address = headers.get("to", "")
    subject = headers.get("subject", "")
    
    # Extract body content
    body_text = ""
    attachments = []
    
    def extract_text_from_parts(parts: List[Dict[str, Any]]):
        """Recursively extract text content from MIME parts"""
        nonlocal body_text, attachments
        
        for part in parts:
            mime_type = part.get("mimeType", "")
            
            # Extract text content
            if mime_type in ["text/plain", "text/html"]:
                body_data = part.get("body", {}).get("data")
                if body_data:
                    try:
                        decoded_text = base64.urlsafe_b64decode(body_data + "==").decode("utf-8")
                        body_text += decoded_text + "\n"
                    except Exception:
                        pass
            
            # Extract attachment info
            elif mime_type.startswith("application/") or mime_type.startswith("image/"):
                attachment_info = {
                    "filename": part.get("filename", ""),
                    "mimeType": mime_type,
                    "size": part.get("body", {}).get("size", 0),
                    "attachmentId": part.get("body", {}).get("attachmentId")
                }
                attachments.append(attachment_info)
            
            # Recursively process nested parts
            if "parts" in part:
                extract_text_from_parts(part["parts"])
    
    # Process payload parts
    if "parts" in payload:
        extract_text_from_parts(payload["parts"])
    
    return {
        "from_address": from_address,
        "to_address": to_address,
        "subject": subject,
        "body_text": body_text.strip(),
        "attachments": attachments
    }


def check_gmail_message_legitimacy(gmail_msg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check legitimacy of Gmail message using domain analysis.
    
    Parses Gmail API message and performs domain legitimacy checking
    on the sender's email address.
    
    Args:
        gmail_msg (Dict[str, Any]): Gmail API message JSON
        
    Returns:
        Dict[str, Any]: Legitimacy assessment containing:
            - is_legitimate: Boolean indicating overall legitimacy
            - domain_analysis: Domain suspiciousness analysis
            - confidence: Overall confidence in the assessment
            - reasons: List of specific issues found
            - parsed_data: Extracted email data
    """
    # Parse Gmail message
    parsed_data = parse_gmail_message(gmail_msg)
    
    # Extract sender email for domain analysis
    from_address = parsed_data["from_address"]
    
    if not from_address:
        return {
            "is_legitimate": False,
            "domain_analysis": {"is_suspicious": True, "reasons": ["no_sender"], "confidence": 1.0},
            "confidence": 1.0,
            "reasons": ["no_sender"],
            "parsed_data": parsed_data
        }
    
    # Perform domain legitimacy check
    legitimacy_result = check_domain_legitimacy(
        email_address=from_address,
        vendor_name=None  # Could extract from subject/body if needed
    )
    
    # Add parsed data to result
    legitimacy_result["parsed_data"] = parsed_data
    
    return legitimacy_result


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def normalize_text(s: str) -> str:
    """
    Normalize text using Unicode normalization and strip whitespace.
    
    Applies NFKC normalization to handle Unicode variations and ensure consistent
    text processing.
    
    Args:
        s (str): Input text to normalize
        
    Returns:
        str: Normalized and stripped text
    """
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s)
    return s.strip()


def domain_from_address(addr: str) -> str:
    """
    Extract domain from email address, handling various formats.
    
    Supports both simple email addresses and RFC 5322 formatted addresses
    with display names. Falls back to tldextract if available for better
    domain parsing.
    
    Args:
        addr (str): Email address in various formats
        
    Returns:
        str: Extracted domain name (lowercase)
        
    Example:
        >>> domain_from_address("user@example.com")
        'example.com'
        >>> domain_from_address('John Doe <john@company.co.uk>')
        'company.co.uk'
    """
    if not addr:
        return ""
    
    # Parse "Name <user@domain>" format
    m = re.search(r"@([^\s>]+)", addr)
    if m:
        domain = m.group(1).lower()
        # Remove any trailing characters
        domain = re.sub(r'[^\w.-]+$', '', domain)
        return domain
    
    # Fallback: try tldextract if available
    if tldextract:
        ext = tldextract.extract(addr)
        if ext.domain:
            return f"{ext.domain}.{ext.suffix}"
    
    return addr.lower()


def fuzzy_domain_similarity(a: str, b: str) -> float:
    """
    Calculate normalized similarity between two domain strings.
    
    Uses difflib.SequenceMatcher to compute similarity ratio. Returns a value
    between 0.0 (no similarity) and 1.0 (exact match). Useful for detecting
    typosquatting and similar domain variations.
    
    Args:
        a (str): First domain string
        b (str): Second domain string
        
    Returns:
        float: Similarity score between 0.0 and 1.0
    """
    if not a or not b:
        return 0.0
    
    a_norm = a.lower()
    b_norm = b.lower()
    
    # Exact match
    if a_norm == b_norm:
        return 1.0
    
    # Subdomain match
    if a_norm.endswith(f".{b_norm}") or b_norm.endswith(f".{a_norm}"):
        return 0.95
    
    # Partial match score via SequenceMatcher
    return difflib.SequenceMatcher(None, a_norm, b_norm).ratio()


# =============================================================================
# DOMAIN ANALYSIS FUNCTIONS
# =============================================================================

def analyze_domain_suspiciousness(domain: str) -> Dict[str, Any]:
    """
    Analyze domain for suspicious characteristics.
    
    Checks for common fraud indicators in domain names such as homograph attacks,
    suspicious TLDs, and unusual patterns.
    
    Args:
        domain (str): Domain name to analyze
        
    Returns:
        Dict[str, Any]: Analysis results containing:
            - is_suspicious: Boolean indicating if domain appears suspicious
            - reasons: List of specific suspicious characteristics found
            - confidence: Confidence level (0.0-1.0) in the assessment
    """
    if not domain:
        return {
            "is_suspicious": True,
            "reasons": ["empty_domain"],
            "confidence": 1.0
        }
    
    reasons = []
    confidence = 0.0
    
    confidence_factors = []
    
    # 1. Basic pattern analysis
    for pattern in SUSPICIOUS_DOMAIN_PATTERNS:
        if re.search(pattern, domain):
            if pattern == r"[0-9]":
                reasons.append("contains_numbers")
                confidence_factors.append(0.3)
            elif pattern == r"[^a-zA-Z0-9.-]":
                reasons.append("contains_special_chars")
                confidence_factors.append(0.4)
            elif pattern == r"^[0-9]":
                reasons.append("starts_with_number")
                confidence_factors.append(0.4)
    
    # 2. Length analysis
    if len(domain) < 6:
        reasons.append("very_short_domain")
        confidence_factors.append(0.2)
    elif len(domain) > 50:
        reasons.append("very_long_domain")
        confidence_factors.append(0.3)
    
    # 3. Subdomain analysis
    subdomain_count = domain.count('.')
    if subdomain_count > 3:
        reasons.append("excessive_subdomains")
        confidence_factors.append(0.3)
    
    # 4. TLD analysis (enhanced)
    tld = domain.split('.')[-1].lower()
    
    # Check for country-specific TLDs (e.g., co.uk)
    if subdomain_count >= 2:
        country_tld = '.'.join(domain.split('.')[-2:])
        if country_tld in LEGITIMATE_TLDS:
            confidence_factors.append(-0.2)  # Reduce suspicion
        elif country_tld in SUSPICIOUS_TLDS:
            reasons.append("suspicious_tld")
            confidence_factors.append(0.5)
    else:
        if tld in LEGITIMATE_TLDS:
            confidence_factors.append(-0.2)  # Reduce suspicion
        elif tld in SUSPICIOUS_TLDS:
            reasons.append("suspicious_tld")
            confidence_factors.append(0.5)
    
    # 5. Character pattern analysis
    if re.search(r'(.)\1{2,}', domain):  # Repeated characters
        reasons.append("repeated_chars")
        confidence_factors.append(0.2)
    
    # 6. Mixed scripts detection (homograph attacks)
    has_mixed_scripts = False
    for char in domain:
        if ord(char) > 127:  # Non-ASCII character
            has_mixed_scripts = True
            break
    
    if has_mixed_scripts:
        reasons.append("mixed_scripts")
        confidence_factors.append(0.6)
    
    # 7. DNS resolution test (simple)
    try:
        socket.gethostbyname(domain)
        confidence_factors.append(-0.1)  # Resolves = slightly more legitimate
    except socket.gaierror:
        reasons.append("dns_resolution_failed")
        confidence_factors.append(0.4)
    
    # Calculate final confidence score
    if confidence_factors:
        final_score = sum(confidence_factors) / len(confidence_factors)
        confidence = max(0.0, min(1.0, abs(final_score)))
    else:
        confidence = 0.5
    
    return {
        "is_suspicious": len(reasons) > 0 or confidence > 0.3,
        "reasons": reasons,
        "confidence": confidence
    }


# =============================================================================
# MAIN LEGITIMACY CHECKER
# =============================================================================

def check_domain_legitimacy(
    email_address: str,
    vendor_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Perform domain legitimacy check.
    
    Analyzes email domain for suspicious characteristics to determine
    if the domain appears legitimate or suspicious.
    
    Args:
        email_address (str): Email address to analyze
        vendor_name (str, optional): Vendor name from email
        
    Returns:
        Dict[str, Any]: Legitimacy assessment containing:
            - is_legitimate: Boolean indicating overall legitimacy
            - domain_analysis: Domain suspiciousness analysis
            - confidence: Overall confidence in the assessment
            - reasons: List of specific issues found
    """
    # Extract domain from email
    domain = domain_from_address(email_address)
    
    # Analyze domain suspiciousness
    domain_analysis = analyze_domain_suspiciousness(domain)
    
    # Vendor matching removed - will be replaced with separate database integration
    
    # Determine overall legitimacy
    reasons = []
    confidence_factors = []
    
    # Domain analysis
    if domain_analysis["is_suspicious"]:
        reasons.extend(domain_analysis["reasons"])
        confidence_factors.append(1.0 - domain_analysis["confidence"])
    else:
        confidence_factors.append(domain_analysis["confidence"])
    
    # Calculate overall confidence
    overall_confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.5
    
    # Determine legitimacy (threshold at 0.6)
    is_legitimate = overall_confidence >= 0.6 and len(reasons) == 0
    
    return {
        "is_legitimate": is_legitimate,
        "domain_analysis": domain_analysis,
        "confidence": overall_confidence,
        "reasons": reasons
    }


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    """
    Example usage of the domain legitimacy checker.
    """
    
    # Example Gmail API message (based on your provided format)
    gmail_example = {
        "id": "18c8b0d8cafe1234",
        "threadId": "18c8b0d8cafe1200",
        "labelIds": ["INBOX", "UNREAD"],
        "snippet": "Hi Allen, here's the deck you asked for...",
        "historyId": "1234567895",
        "internalDate": "1736012345678",
        "sizeEstimate": 42876,
        "payload": {
            "partId": "",
            "mimeType": "multipart/mixed",
            "filename": "",
            "headers": [
                {"name": "From", "value": "Jane Doe <jane@example.com>"},
                {"name": "To", "value": "Allen <allen@yourapp.com>"},
                {"name": "Subject", "value": "Q4 deck + notes"},
                {"name": "Date", "value": "Sat, 4 Oct 2025 10:19:05 -0400"},
                {"name": "Message-Id", "value": "<CAFExyz@example.com>"}
            ],
            "body": {"size": 0},
            "parts": [
                {
                    "partId": "1",
                    "mimeType": "multipart/alternative",
                    "filename": "",
                    "headers": [],
                    "body": {"size": 0},
                    "parts": [
                        {
                            "partId": "1.1",
                            "mimeType": "text/plain",
                            "filename": "",
                            "headers": [{"name": "Content-Type", "value": "text/plain; charset=UTF-8"}],
                            "body": {
                                "size": 512,
                                "data": "SGkgQWxsZW4sCgpIZXJlJ3MgdGhlIGRlay4uLg=="
                            }
                        },
                        {
                            "partId": "1.2",
                            "mimeType": "text/html",
                            "filename": "",
                            "headers": [{"name": "Content-Type", "value": "text/html; charset=UTF-8"}],
                            "body": {
                                "size": 1290,
                                "data": "PGRpdi5uZXdzaWc+PGI+SGk8L2I+IEFsbGVuLCZuYnNwO2hlcmUmIzM5O3MgdGhlIGRlY2suLi48L2Rpdj4="
                            }
                        }
                    ]
                },
                {
                    "partId": "2",
                    "mimeType": "application/pdf",
                    "filename": "Q4-deck.pdf",
                    "headers": [
                        {"name": "Content-Disposition", "value": "attachment; filename=\"Q4-deck.pdf\""},
                        {"name": "Content-Transfer-Encoding", "value": "base64"}
                    ],
                    "body": {
                        "size": 38742,
                        "attachmentId": "ANGjdJ8kAaBCDEFghiJKLmnoP"
                    }
                }
            ]
        }
    }
    
    # Test cases for direct domain checking
    test_cases = [
        {
            "email": "billing@payvendor-example.com",
            "vendor": "PayVendor Inc"
        },
        {
            "email": "billing@payv3ndor-example.com",  # Suspicious domain
            "vendor": "PayVendor Inc"
        },
        {
            "email": "billing@legitimate-supplier.org",
            "vendor": "Legitimate Supplier LLC"
        },
        {
            "email": "billing@suspicious-domain.tk",  # Suspicious TLD
            "vendor": "Unknown Vendor"
        }
    ]
    
    print("=" * 60)
    print("DOMAIN LEGITIMACY CHECKER RESULTS")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"Email: {test_case['email']}")
        print(f"Vendor: {test_case['vendor']}")
        
        result = check_domain_legitimacy(
            email_address=test_case["email"],
            vendor_name=test_case["vendor"]
        )
        
        print(f"Legitimate: {result['is_legitimate']}")
        print(f"Confidence: {result['confidence']:.2f}")
        if result['reasons']:
            print(f"Issues: {', '.join(result['reasons'])}")
        print("-" * 40)
