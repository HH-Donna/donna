"""
Donna Email Fraud Detection Pipeline

This module provides a comprehensive email fraud detection system specifically designed
for billing and invoice-related communications. It analyzes emails using multiple
scoring dimensions and provides actionable decisions for fraud prevention.

Key Features:
- Gmail API message parsing and normalization
- Multi-dimensional fraud scoring (email, invoice, authentication, vendor matching)
- OCR support for image attachments
- Explainable AI with contribution tracking
- Configurable thresholds and weights
- Vendor master database integration

Main Components:
1. Email Parsing: Handles Gmail API message formats (raw/full/metadata)
2. Feature Extraction: Extracts invoice data, authentication results, vendor info
3. Scoring Models: Multiple heuristic-based scoring functions
4. Decision Engine: Maps scores to actionable decisions
5. OCR Integration: Optional text extraction from image attachments

Author: Donna Team
Version: 1.0.0
License: Proprietary
"""

# Import the main functions and classes from email_classifier
from .email_classifier import (
    # Main pipeline function
    process_email_message,
    
    # Configuration constants
    DEFAULT_WEIGHTS,
    THRESHOLDS,
    
    # Pattern matching constants
    INVOICE_KEYWORDS,
    INVOICE_NUMBER_RE,
    CURRENCY_RE,
    IBAN_RE,
    BANK_ACCOUNT_RE,
    DATE_RE,
    
    # Utility functions
    base64url_decode,
    sha256_hex,
    safe_get_header,
    normalize_text,
    domain_from_address,
    fuzzy_domain_similarity,
    
    # Parsing functions
    parse_gmail_message,
    
    # Detection and extraction functions
    regex_invoice_detect,
    parse_authentication_results,
    auth_score_from_results,
    extract_kv_from_text,
    
    # OCR functions
    ocr_bytes_attachment,
    
    # Scoring functions
    score_email_model,
    score_invoice_model,
    combine_scores,
    map_to_decision,
)

# Import domain legitimacy checker functions
from .domain_checker import (
    # Configuration constants
    SUSPICIOUS_DOMAIN_PATTERNS,
    LEGITIMATE_TLDS,
    SUSPICIOUS_TLDS,
    
    # Billing email detection functions
    is_billing_email,
    check_billing_email_legitimacy,
    
    # Gmail API parsing functions
    parse_gmail_message,
    check_gmail_message_legitimacy,
    
    # Analysis functions
    analyze_domain_suspiciousness,
    check_domain_legitimacy,
)

# Define what gets imported when using "from ml import *"
__all__ = [
    # Main pipeline
    'process_email_message',
    
    # Configuration
    'DEFAULT_WEIGHTS',
    'THRESHOLDS',
    
    # Pattern constants
    'INVOICE_KEYWORDS',
    'INVOICE_NUMBER_RE', 
    'CURRENCY_RE',
    'IBAN_RE',
    'BANK_ACCOUNT_RE',
    'DATE_RE',
    
    # Utilities
    'base64url_decode',
    'sha256_hex',
    'safe_get_header',
    'normalize_text',
    'domain_from_address',
    'fuzzy_domain_similarity',
    
    # Parsing
    'parse_gmail_message',
    
    # Detection
    'regex_invoice_detect',
    'parse_authentication_results',
    'auth_score_from_results',
    'extract_kv_from_text',
    
    # OCR
    'ocr_bytes_attachment',
    
    # Scoring
    'score_email_model',
    'score_invoice_model',
    'combine_scores',
    'map_to_decision',
    
    # Domain legitimacy checker
    'SUSPICIOUS_DOMAIN_PATTERNS',
    'LEGITIMATE_TLDS',
    'SUSPICIOUS_TLDS',
    'is_billing_email',
    'check_billing_email_legitimacy',
    'parse_gmail_message',
    'check_gmail_message_legitimacy',
    'analyze_domain_suspiciousness',
    'check_domain_legitimacy',
]

# Module metadata
__version__ = "1.0.0"
__author__ = "Donna Team"
__description__ = "Email fraud detection pipeline for billing communications"
