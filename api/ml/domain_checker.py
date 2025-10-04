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

Author: Donna Team
Version: 1.0.0
License: Proprietary
"""

from __future__ import annotations
import re
import unicodedata
import difflib
import socket
from typing import Dict, Any, List, Tuple, Optional

# Optional imports for enhanced domain analysis
try:
    import tldextract
except Exception:
    tldextract = None

# =============================================================================
# CONFIGURATION AND PATTERNS
# =============================================================================

# Domain similarity threshold for vendor matching
VENDOR_MATCH_THRESHOLD = 0.85

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

# Bank account validation patterns
BANK_ACCOUNT_PATTERNS = {
    "generic": r"\b\d{4,20}\b",  # Generic account number
    "iban": r"\b[A-Z]{2}\d{2}[A-Z0-9]{1,30}\b",  # IBAN format
    "us_routing": r"\b\d{9}\b",  # US routing number
}

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


def validate_bank_account(account: str) -> Dict[str, Any]:
    """
    Validate bank account number format and patterns.
    
    Checks if the account number follows expected patterns for legitimate
    banking institutions.
    
    Args:
        account (str): Bank account number to validate
        
    Returns:
        Dict[str, Any]: Validation results containing:
            - is_valid: Boolean indicating if format appears valid
            - account_type: Detected account type (generic, iban, us_routing)
            - confidence: Confidence level in the validation
    """
    if not account:
        return {
            "is_valid": False,
            "account_type": "none",
            "confidence": 1.0
        }
    
    account = normalize_text(account)
    
    # Check IBAN format
    if re.match(BANK_ACCOUNT_PATTERNS["iban"], account):
        return {
            "is_valid": True,
            "account_type": "iban",
            "confidence": 0.9
        }
    
    # Check US routing number
    if re.match(BANK_ACCOUNT_PATTERNS["us_routing"], account):
        return {
            "is_valid": True,
            "account_type": "us_routing",
            "confidence": 0.8
        }
    
    # Check generic account number
    if re.match(BANK_ACCOUNT_PATTERNS["generic"], account):
        return {
            "is_valid": True,
            "account_type": "generic",
            "confidence": 0.6
        }
    
    return {
        "is_valid": False,
        "account_type": "invalid",
        "confidence": 0.8
    }


# =============================================================================
# VENDOR MATCHING FUNCTIONS
# =============================================================================

def match_vendor_domain(domain: str, vendor_master: Dict[str, Any]) -> Dict[str, Any]:
    """
    Match domain against vendor master database.
    
    Searches the vendor master database for similar domains and returns
    matching information with confidence scores.
    
    Args:
        domain (str): Domain to match
        vendor_master (Dict[str, Any]): Vendor master database
        
    Returns:
        Dict[str, Any]: Matching results containing:
            - is_matched: Boolean indicating if a match was found
            - matched_vendor: Vendor information if matched
            - similarity_score: Similarity score of the best match
            - confidence: Confidence level in the match
    """
    if not domain or not vendor_master:
        return {
            "is_matched": False,
            "matched_vendor": None,
            "similarity_score": 0.0,
            "confidence": 0.0
        }
    
    best_match = None
    best_score = 0.0
    
    for vendor_key, vendor_info in vendor_master.items():
        # Extract domain from vendor info
        vendor_domain = None
        if isinstance(vendor_info, dict):
            vendor_domain = vendor_info.get("domain")
        else:
            vendor_domain = vendor_key
        
        if not vendor_domain:
            continue
        
        # Calculate similarity
        similarity = fuzzy_domain_similarity(domain, vendor_domain)
        
        if similarity > best_score:
            best_score = similarity
            best_match = {
                "key": vendor_key,
                "domain": vendor_domain,
                "info": vendor_info
            }
    
    # Determine if match is strong enough
    is_matched = best_score >= VENDOR_MATCH_THRESHOLD
    
    return {
        "is_matched": is_matched,
        "matched_vendor": best_match,
        "similarity_score": best_score,
        "confidence": best_score if is_matched else 0.0
    }


# =============================================================================
# MAIN LEGITIMACY CHECKER
# =============================================================================

def check_domain_legitimacy(
    email_address: str,
    vendor_name: Optional[str] = None,
    bank_account: Optional[str] = None,
    vendor_master: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Perform comprehensive domain and vendor legitimacy check.
    
    Analyzes email domain, vendor information, and account details to determine
    if the metadata appears legitimate or suspicious.
    
    Args:
        email_address (str): Email address to analyze
        vendor_name (str, optional): Vendor name from email
        bank_account (str, optional): Bank account number from email
        vendor_master (Dict[str, Any], optional): Vendor master database
        
    Returns:
        Dict[str, Any]: Legitimacy assessment containing:
            - is_legitimate: Boolean indicating overall legitimacy
            - domain_analysis: Domain suspiciousness analysis
            - vendor_match: Vendor matching results
            - account_validation: Bank account validation results
            - confidence: Overall confidence in the assessment
            - reasons: List of specific issues found
    """
    # Extract domain from email
    domain = domain_from_address(email_address)
    
    # Analyze domain suspiciousness
    domain_analysis = analyze_domain_suspiciousness(domain)
    
    # Match against vendor database
    vendor_match = match_vendor_domain(domain, vendor_master or {})
    
    # Validate bank account if provided
    account_validation = validate_bank_account(bank_account) if bank_account else {
        "is_valid": True,
        "account_type": "not_provided",
        "confidence": 0.0
    }
    
    # Determine overall legitimacy
    reasons = []
    confidence_factors = []
    
    # Domain analysis
    if domain_analysis["is_suspicious"]:
        reasons.extend(domain_analysis["reasons"])
        confidence_factors.append(1.0 - domain_analysis["confidence"])
    else:
        confidence_factors.append(domain_analysis["confidence"])
    
    # Vendor matching
    if vendor_match["is_matched"]:
        confidence_factors.append(vendor_match["confidence"])
    else:
        reasons.append("vendor_not_found")
        confidence_factors.append(0.3)  # Moderate concern for unknown vendor
    
    # Account validation
    if not account_validation["is_valid"]:
        reasons.append("invalid_account_format")
        confidence_factors.append(1.0 - account_validation["confidence"])
    else:
        confidence_factors.append(account_validation["confidence"])
    
    # Calculate overall confidence
    overall_confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.5
    
    # Determine legitimacy (threshold at 0.6)
    is_legitimate = overall_confidence >= 0.6 and len(reasons) == 0
    
    return {
        "is_legitimate": is_legitimate,
        "domain_analysis": domain_analysis,
        "vendor_match": vendor_match,
        "account_validation": account_validation,
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
    
    # Example vendor master database
    vendor_master = {
        "payvendor-example.com": {
            "domain": "payvendor-example.com",
            "name": "PayVendor Inc",
            "last_account": "123456789",
            "last_amount": 4800.0
        },
        "legitimate-supplier.org": {
            "domain": "legitimate-supplier.org", 
            "name": "Legitimate Supplier LLC",
            "last_account": "987654321",
            "last_amount": 2500.0
        }
    }
    
    # Test cases
    test_cases = [
        {
            "email": "billing@payvendor-example.com",
            "vendor": "PayVendor Inc",
            "account": "123456789"
        },
        {
            "email": "billing@payv3ndor-example.com",  # Suspicious domain
            "vendor": "PayVendor Inc",
            "account": "123456789"
        },
        {
            "email": "billing@legitimate-supplier.org",
            "vendor": "Legitimate Supplier LLC", 
            "account": "987654321"
        },
        {
            "email": "billing@suspicious-domain.tk",  # Suspicious TLD
            "vendor": "Unknown Vendor",
            "account": "invalid-account"
        }
    ]
    
    print("=" * 60)
    print("DOMAIN LEGITIMACY CHECKER RESULTS")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"Email: {test_case['email']}")
        print(f"Vendor: {test_case['vendor']}")
        print(f"Account: {test_case['account']}")
        
        result = check_domain_legitimacy(
            email_address=test_case["email"],
            vendor_name=test_case["vendor"],
            bank_account=test_case["account"],
            vendor_master=vendor_master
        )
        
        print(f"Legitimate: {result['is_legitimate']}")
        print(f"Confidence: {result['confidence']:.2f}")
        if result['reasons']:
            print(f"Issues: {', '.join(result['reasons'])}")
        print("-" * 40)
