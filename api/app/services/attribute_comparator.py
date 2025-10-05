"""
Attribute comparison service for detecting meaningful changes in company data.
Uses fuzzy matching and semantic comparison instead of strict equality.
"""

import re
from difflib import SequenceMatcher


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison by removing extra whitespace, punctuation, etc.
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove common punctuation that doesn't affect meaning
    text = re.sub(r'[,\.\-\(\)]', ' ', text)
    text = ' '.join(text.split())
    
    return text.strip()


def similarity_score(text1: str, text2: str) -> float:
    """
    Calculate similarity score between two texts using SequenceMatcher.
    
    Returns:
        float: Similarity score between 0.0 (completely different) and 1.0 (identical)
    """
    if not text1 or not text2:
        return 0.0
    
    normalized1 = normalize_text(text1)
    normalized2 = normalize_text(text2)
    
    return SequenceMatcher(None, normalized1, normalized2).ratio()


def are_addresses_equivalent(address1: str, address2: str, threshold: float = 0.85) -> tuple[bool, float]:
    """
    Check if two addresses are equivalent using fuzzy matching.
    
    Args:
        address1: First address
        address2: Second address
        threshold: Similarity threshold (default 0.85 = 85% similar)
        
    Returns:
        tuple: (are_equivalent, similarity_score)
    """
    if not address1 or not address2:
        return (True, 1.0)  # If one is missing, consider equivalent (no change)
    
    score = similarity_score(address1, address2)
    return (score >= threshold, score)


def are_bank_details_equivalent(details1: str, details2: str, threshold: float = 0.90) -> tuple[bool, float]:
    """
    Check if bank details are equivalent.
    Uses stricter threshold since bank details are critical.
    
    Args:
        details1: First bank details
        details2: Second bank details
        threshold: Similarity threshold (default 0.90 = 90% similar)
        
    Returns:
        tuple: (are_equivalent, similarity_score)
    """
    if not details1 or not details2:
        return (True, 1.0)
    
    # Extract account numbers for direct comparison
    account_pattern = r'\d{6,}'
    accounts1 = re.findall(account_pattern, details1)
    accounts2 = re.findall(account_pattern, details2)
    
    # If we found account numbers, compare them directly
    if accounts1 and accounts2:
        # Check if any account numbers match
        has_match = any(acc1 == acc2 for acc1 in accounts1 for acc2 in accounts2)
        if not has_match:
            return (False, 0.0)  # Different account numbers = definitely different
    
    # Fallback to fuzzy matching
    score = similarity_score(details1, details2)
    return (score >= threshold, score)


def are_phone_numbers_equivalent(phone1: str, phone2: str) -> tuple[bool, float]:
    """
    Check if phone numbers are equivalent by extracting and comparing digits.
    
    Args:
        phone1: First phone number
        phone2: Second phone number
        
    Returns:
        tuple: (are_equivalent, similarity_score)
    """
    if not phone1 or not phone2:
        return (True, 1.0)
    
    # Extract only digits (remove formatting)
    digits1 = re.sub(r'[^\d]', '', phone1)
    digits2 = re.sub(r'[^\d]', '', phone2)
    
    # Remove country codes for comparison (last 10 digits)
    if len(digits1) > 10:
        digits1 = digits1[-10:]
    if len(digits2) > 10:
        digits2 = digits2[-10:]
    
    are_equal = digits1 == digits2
    score = 1.0 if are_equal else 0.0
    
    return (are_equal, score)


def are_emails_equivalent(email1: str, emails_list: list) -> tuple[bool, float]:
    """
    Check if an email is in a list of known emails.
    
    Args:
        email1: Email to check
        emails_list: List of known emails
        
    Returns:
        tuple: (is_in_list, confidence)
    """
    if not email1:
        return (True, 1.0)
    
    if not emails_list:
        return (True, 1.0)
    
    email1_normalized = email1.lower().strip()
    
    # Check for exact match
    for email in emails_list:
        if email.lower().strip() == email1_normalized:
            return (True, 1.0)
    
    # Check for domain match (same company, different subdomain)
    domain1 = email1_normalized.split('@')[1] if '@' in email1_normalized else ''
    for email in emails_list:
        domain2 = email.lower().split('@')[1] if '@' in email else ''
        if domain1 and domain2 and domain1 == domain2:
            return (True, 0.9)  # Same domain, slightly lower confidence
    
    return (False, 0.0)


def compare_attributes(stored_company: dict, extracted_data: dict) -> list:
    """
    Compare extracted invoice data with stored company data.
    
    Args:
        stored_company: Company data from database
        extracted_data: Extracted invoice data
        
    Returns:
        list: List of attribute changes with severity levels
    """
    changes = []
    
    # Compare billing address
    if extracted_data.get('billing_address') and stored_company.get('billing_address'):
        are_equiv, score = are_addresses_equivalent(
            stored_company['billing_address'],
            extracted_data['billing_address']
        )
        if not are_equiv:
            changes.append({
                'field': 'billing_address',
                'stored': stored_company['billing_address'],
                'received': extracted_data['billing_address'],
                'similarity_score': score,
                'severity': 'high'
            })
    
    # Compare bank details (most critical)
    if extracted_data.get('biller_billing_details') and stored_company.get('biller_billing_details'):
        are_equiv, score = are_bank_details_equivalent(
            stored_company['biller_billing_details'],
            extracted_data['biller_billing_details']
        )
        if not are_equiv:
            changes.append({
                'field': 'biller_billing_details',
                'stored': stored_company['biller_billing_details'],
                'received': extracted_data['biller_billing_details'],
                'similarity_score': score,
                'severity': 'critical'
            })
    
    # Compare phone number
    if extracted_data.get('biller_phone_number') and stored_company.get('biller_phone_number'):
        are_equiv, score = are_phone_numbers_equivalent(
            stored_company['biller_phone_number'],
            extracted_data['biller_phone_number']
        )
        if not are_equiv:
            changes.append({
                'field': 'biller_phone_number',
                'stored': stored_company['biller_phone_number'],
                'received': extracted_data['biller_phone_number'],
                'similarity_score': score,
                'severity': 'medium'
            })
    
    # Compare contact email
    if extracted_data.get('contact_email') and stored_company.get('contact_emails'):
        are_equiv, score = are_emails_equivalent(
            extracted_data['contact_email'],
            stored_company['contact_emails']
        )
        if not are_equiv:
            changes.append({
                'field': 'contact_email',
                'stored': stored_company['contact_emails'],
                'received': extracted_data['contact_email'],
                'similarity_score': score,
                'severity': 'high'
            })
    
    return changes
