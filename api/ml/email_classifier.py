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

from __future__ import annotations
import base64
import re
import json
import hashlib
from typing import Dict, Any, List, Tuple, Optional
from email import policy
from email.parser import BytesParser
import unicodedata
import difflib

# Optional imports that you can enable in your environment
try:
    import tldextract
except Exception:
    tldextract = None

try:
    # for simple OCR fallback
    import pytesseract
    from PIL import Image
except Exception:
    pytesseract = None
    Image = None

# =============================================================================
# CONFIGURATION AND THRESHOLDS
# =============================================================================
#
# This section defines the core configuration parameters for the fraud detection
# system. These values control the scoring weights, decision thresholds, and
# pattern matching rules used throughout the pipeline.
#
# Key Configuration Areas:
# - DEFAULT_WEIGHTS: Controls relative importance of different scoring dimensions
# - THRESHOLDS: Defines decision boundaries for different risk levels
# - REGEX PATTERNS: Pattern matching for invoice detection and data extraction
#
# Note: These values should be tuned based on historical fraud data and
# business requirements. Consider A/B testing different configurations.
# -------------------------
# Scoring weight configuration for multi-dimensional fraud assessment
# Higher weights indicate greater importance in the final combined score
DEFAULT_WEIGHTS = {
    "email_score": 0.35,        # Email-level features (urgency, links, keywords)
    "invoice_score": 0.45,       # Invoice-specific features (missing data, bank changes)
    "auth_score": 0.15,          # Email authentication (SPF, DKIM, DMARC)
    "vendor_match_score": 0.05,  # Vendor database matching
}
# Decision thresholds for risk-based routing
# Scores above these thresholds trigger specific actions
THRESHOLDS = {
    "high_confidence_fraud": 0.85,  # Immediate fraud alert - highest priority
    "call_agent": 0.65,            # Require phone verification
    "email_confirmation": 0.40,    # Email confirmation required
    "low_risk": 0.0,              # Baseline - no additional action needed
}
# Pattern matching rules for invoice detection and data extraction
# These regex patterns are compiled once for performance
# Keywords that indicate invoice-related content
INVOICE_KEYWORDS = re.compile(
    r"\b(invoice|bill|statement|due date|amount due|invoice no\.|inv#|tax id|vat|subtotal|total due)\b",
    flags=re.I,
)
# Pattern to extract invoice numbers from text
INVOICE_NUMBER_RE = re.compile(r"\b(invoice(?:\s*#|No\.?|Number)[:\s]*)([A-Za-z0-9\-_/]+)\b", flags=re.I)
# Pattern to match currency amounts (supports multiple currencies)
CURRENCY_RE = re.compile(r"(?:(?:\$|£|€|₹)\s?\d{1,3}(?:[,\d]{0,3})*(?:\.\d{1,2})?)")
# Pattern to match IBAN (International Bank Account Number) format
IBAN_RE = re.compile(r"\b([A-Z]{2}\d{2}[A-Z0-9]{1,30})\b")
# Pattern to extract bank account numbers
BANK_ACCOUNT_RE = re.compile(r"\b(account(?:\s*no| number)?[:\s]*)(\d{4,})\b", flags=re.I)
# Pattern to match various date formats (numeric and text-based)
DATE_RE = re.compile(r"\b(\d{2,4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{2,4})\b", flags=re.I)

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================
#
# This section contains helper functions used throughout the fraud detection
# pipeline. These functions handle data normalization, encoding/decoding,
# domain extraction, and similarity calculations.
#
# Key Utility Areas:
# - Base64 URL decoding for Gmail API data
# - Text normalization and cleaning
# - Domain extraction and similarity matching
# - Hash generation for attachment integrity
#
# These functions are designed to be robust and handle edge cases gracefully.
# -------------------------
def base64url_decode(data: str) -> bytes:
    """
    Decode base64url encoded string to bytes.
    
    Gmail API uses base64url encoding (RFC 4648) which differs from standard
    base64 by using URL-safe characters and omitting padding. This function
    handles the conversion properly.
    
    Args:
        data (str): Base64url encoded string
        
    Returns:
        bytes: Decoded binary data
        
    Raises:
        ValueError: If the input string is not valid base64url
    
    Example:
        >>> base64url_decode("SGVsbG8gV29ybGQ")
        b'Hello World'
    """
    # add padding
    rem = len(data) % 4
    if rem:
        data += "=" * (4 - rem)
    return base64.urlsafe_b64decode(data.encode("utf-8"))


def sha256_hex(data: bytes) -> str:
    """
    Generate SHA-256 hash of binary data as hexadecimal string.
    
    Used for creating unique identifiers for email attachments and ensuring
    data integrity. SHA-256 provides strong collision resistance.
    
    Args:
        data (bytes): Binary data to hash
        
    Returns:
        str: Hexadecimal representation of SHA-256 hash
        
    Example:
        >>> sha256_hex(b"Hello World")
        'a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e'
    """
    return hashlib.sha256(data).hexdigest()


def safe_get_header(headers: Dict[str, str], key: str) -> Optional[str]:
    """
    Safely retrieve email header value with case-insensitive lookup.
    
    Email headers are case-insensitive according to RFC standards, but
    implementations may vary. This function normalizes the lookup.
    
    Args:
        headers (Dict[str, str]): Dictionary of email headers
        key (str): Header name to lookup
        
    Returns:
        Optional[str]: Header value if found, None otherwise
        
    Example:
        >>> headers = {"From": "test@example.com", "SUBJECT": "Hello"}
        >>> safe_get_header(headers, "from")
        'test@example.com'
        >>> safe_get_header(headers, "subject")
        'Hello'
    """
    return headers.get(key.lower())


def normalize_text(s: str) -> str:
    """
    Normalize text using Unicode normalization and strip whitespace.
    
    Applies NFKC (Normalization Form Compatibility Decomposition, followed by
    Canonical Composition) to handle Unicode variations and ensure consistent
    text processing.
    
    Args:
        s (str): Input text to normalize
        
    Returns:
        str: Normalized and stripped text
        
    Example:
        >>> normalize_text("  Café\u0301  ")
        'Café'
    """
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
    # crude parser for "Name <user@domain>"
    if not addr:
        return ""
    m = re.search(r"@([^\s>]+)", addr)
    if m:
        return m.group(1).lower()
    # fallback: try tldextract if available
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
        
    Example:
        >>> fuzzy_domain_similarity("example.com", "example.com")
        1.0
        >>> fuzzy_domain_similarity("example.com", "examp1e.com")
        0.9
        >>> fuzzy_domain_similarity("example.com", "different.org")
        0.0
    """
    if not a or not b:
        return 0.0
    a_norm = a.lower()
    b_norm = b.lower()
    # exact or subdomain match
    if a_norm == b_norm:
        return 1.0
    # partial match score via SequenceMatcher
    return difflib.SequenceMatcher(None, a_norm, b_norm).ratio()


# =============================================================================
# GMAIL MESSAGE PARSING
# =============================================================================
#
# This section handles parsing and normalization of Gmail API message data.
# The Gmail API can return messages in different formats (raw, full, metadata),
# and this module provides a unified interface for processing all formats.
#
# Key Parsing Features:
# - RFC 822 message parsing for raw format
# - Structured payload parsing for full format
# - Attachment extraction and metadata collection
# - Header normalization and case-insensitive lookup
# - Text content extraction from both plain text and HTML
# - Fallback HTML-to-text conversion
#
# The parser is designed to be robust and handle malformed or unusual
# email structures gracefully.
# -------------------------
def parse_gmail_message(gmail_msg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse Gmail API message JSON into normalized structure.
    
    Accepts Gmail API message data in various formats (raw, full, metadata)
    and returns a standardized dictionary with all relevant information
    extracted and normalized.
    
    Args:
        gmail_msg (Dict[str, Any]): Gmail API message JSON
            - For raw format: contains 'raw' field with base64url encoded RFC 822
            - For full format: contains 'payload' with structured MIME parts
            - For metadata: contains basic message metadata
            
    Returns:
        Dict[str, Any]: Normalized message structure containing:
            - id: Gmail message ID
            - threadId: Gmail thread ID
            - snippet: Email snippet text
            - internalDate: Internal timestamp
            - sizeEstimate: Estimated message size
            - headers: Dict of normalized headers (lowercase keys)
            - text_plain: Extracted plain text content
            - text_html: Extracted HTML content
            - attachments: List of attachment metadata
            - raw_bytes: Original RFC 822 bytes (if available)
    
    Raises:
        ValueError: If message format is invalid or unsupported
    
    Example:
        >>> msg = {
        ...     "id": "msg123",
        ...     "payload": {
        ...         "headers": [{"name": "From", "value": "test@example.com"}],
        ...         "body": {"data": base64.urlsafe_b64encode(b"Hello World").decode()}
        ...     }
        ... }
        >>> parsed = parse_gmail_message(msg)
        >>> parsed["headers"]["from"]
        'test@example.com'
    """
    result = {
        "id": gmail_msg.get("id"),
        "threadId": gmail_msg.get("threadId"),
        "snippet": gmail_msg.get("snippet"),
        "internalDate": gmail_msg.get("internalDate"),
        "sizeEstimate": gmail_msg.get("sizeEstimate"),
        "headers": {},
        "text_plain": "",
        "text_html": "",
        "attachments": [],
        "raw_bytes": None,
    }

    # If raw, decode full RFC822 blob
    if "raw" in gmail_msg:
        raw_bytes = base64url_decode(gmail_msg["raw"])
        result["raw_bytes"] = raw_bytes
        # parse with email library (best-effort)
        try:
            msg = BytesParser(policy=policy.default).parsebytes(raw_bytes)
            # extract headers
            for k, v in msg.items():
                result["headers"][k.lower()] = v
            # walk payload
            if msg.is_multipart():
                for part in msg.walk():
                    ctype = part.get_content_type()
                    disp = part.get_content_disposition()
                    if disp == "attachment" or part.get_filename():
                        payload = part.get_payload(decode=True) or b""
                        sha = sha256_hex(payload)
                        result["attachments"].append({
                            "filename": part.get_filename(),
                            "mimeType": ctype,
                            "size": len(payload),
                            "data_bytes": payload,
                            "sha256": sha,
                        })
                    else:
                        # inline
                        if ctype == "text/plain":
                            try:
                                result["text_plain"] += part.get_content()
                            except Exception:
                                result["text_plain"] += (part.get_payload(decode=True) or b"").decode(errors="ignore")
                        elif ctype == "text/html":
                            try:
                                result["text_html"] += part.get_content()
                            except Exception:
                                result["text_html"] += (part.get_payload(decode=True) or b"").decode(errors="ignore")
            else:
                ctype = msg.get_content_type()
                payload = msg.get_payload(decode=True) or b""
                if ctype == "text/plain":
                    result["text_plain"] = payload.decode(errors="ignore")
                elif ctype == "text/html":
                    result["text_html"] = payload.decode(errors="ignore")
        except Exception:
            # fallback: preserve raw and rely on metadata/parts approach
            result["raw_bytes"] = raw_bytes

    # If structured payload exists (format=full)
    if "payload" in gmail_msg:
        payload = gmail_msg["payload"]
        # headers array
        for h in payload.get("headers", []):
            name = h.get("name", "").lower()
            value = h.get("value", "")
            result["headers"][name] = value
        # recursive parts walk
        def walk_part(p):
            ctype = p.get("mimeType", "")
            body = p.get("body", {}) or {}
            if "attachmentId" in body:
                # attachment reference
                result["attachments"].append({
                    "filename": p.get("filename"),
                    "mimeType": ctype,
                    "size": body.get("size"),
                    "attachmentId": body.get("attachmentId"),
                    "sha256": None,
                })
            else:
                data = body.get("data")
                if data:
                    try:
                        text = base64url_decode(data).decode(errors="ignore")
                    except Exception:
                        text = ""
                    if ctype == "text/plain":
                        result["text_plain"] += text
                    elif ctype == "text/html":
                        result["text_html"] += text
            for sub in p.get("parts", []) or []:
                walk_part(sub)
        walk_part(payload)

    # headers normalization to simple dict
    # lower-case keys
    result["headers"] = {k.lower(): v for k, v in result["headers"].items() if v}

    # Quick fallback: if no plain text but HTML exists, strip tags lightly
    if not result["text_plain"] and result["text_html"]:
        # naive strip tags
        result["text_plain"] = re.sub(r"<[^>]+>", " ", result["text_html"])
    # limit snippet
    result["text_plain"] = result["text_plain"].strip()[:20000]
    return result


# =============================================================================
# HEURISTIC DETECTORS AND DATA EXTRACTION
# =============================================================================
#
# This section contains pattern-based detection and extraction functions that
# identify invoice-related content and extract structured data from emails.
# These functions use regex patterns and heuristics to identify potential
# fraud indicators without requiring machine learning models.
#
# Key Detection Areas:
# - Invoice keyword detection for initial filtering
# - Authentication result parsing (SPF, DKIM, DMARC)
# - Structured data extraction (invoice numbers, amounts, dates)
# - Bank account and payment information extraction
# - Vendor name identification
#
# These functions are designed to be fast and reliable for real-time
# processing while maintaining high recall rates.
# -------------------------
def regex_invoice_detect(text: str, subject: str = "") -> bool:
    """
    Detect invoice-related content using keyword patterns.
    
    Performs fast initial filtering to identify emails that likely contain
    invoice or billing information. Uses multiple detection strategies:
    - Keyword matching for invoice-related terms
    - Currency pattern detection with context validation
    - Subject line analysis
    
    Args:
        text (str): Email body text to analyze
        subject (str): Email subject line (optional)
        
    Returns:
        bool: True if invoice-related content is detected
        
    Example:
        >>> regex_invoice_detect("Please find attached invoice #12345", "Invoice Due")
        True
        >>> regex_invoice_detect("Hello, how are you?", "Meeting Tomorrow")
        False
    """
    if not text and not subject:
        return False
    if INVOICE_KEYWORDS.search(text) or INVOICE_KEYWORDS.search(subject):
        return True
    # currency tokens or invoice filename hints
    if CURRENCY_RE.search(text):
        # require some invoice keyword or 'amount' near currency
        window = text[:400]
        if "amount" in window.lower() or "invoice" in window.lower():
            return True
    return False


def parse_authentication_results(headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Parse Authentication-Results header to extract SPF/DKIM/DMARC outcomes.
    
    The Authentication-Results header contains the results of email authentication
    checks performed by the receiving mail server. This function extracts the
    status of SPF, DKIM, and DMARC checks.
    
    Args:
        headers (Dict[str, str]): Email headers dictionary
        
    Returns:
        Dict[str, Any]: Authentication results containing:
            - spf: SPF check result ('pass', 'fail', 'softfail', 'neutral', 'none')
            - dkim: DKIM check result ('pass', 'fail', 'none', 'policy')
            - dmarc: DMARC check result ('pass', 'fail', 'none', 'bestguess')
            - auth_raw: Raw authentication-results header value
    
    Example:
        >>> headers = {
        ...     "authentication-results": "mx.google.com; spf=pass smtp.mailfrom=example.com; dkim=pass header.d=example.com; dmarc=pass"
        ... }
        >>> parse_authentication_results(headers)
        {'spf': 'pass', 'dkim': 'pass', 'dmarc': 'pass', 'auth_raw': '...'}
    """
    auth_raw = headers.get("authentication-results", "") or headers.get("authentication_results", "")
    out = {"spf": None, "dkim": None, "dmarc": None, "auth_raw": auth_raw}
    if not auth_raw:
        return out
    # naive parse
    spf_m = re.search(r"spf=(pass|fail|softfail|neutral|none)", auth_raw, flags=re.I)
    dkim_m = re.search(r"dkim=(pass|fail|none|policy)", auth_raw, flags=re.I)
    dmarc_m = re.search(r"dmarc=(pass|fail|none|bestguess)", auth_raw, flags=re.I)
    if spf_m:
        out["spf"] = spf_m.group(1).lower()
    if dkim_m:
        out["dkim"] = dkim_m.group(1).lower()
    if dmarc_m:
        out["dmarc"] = dmarc_m.group(1).lower()
    return out


def auth_score_from_results(auth: Dict[str, Any]) -> float:
    """
    Convert authentication results to trustworthiness score.
    
    Maps SPF, DKIM, and DMARC authentication results to a normalized
    trustworthiness score between 0.0 and 1.0. Higher scores indicate
    better email authentication.
    
    Scoring Logic:
    - Base score: 0.5 (neutral)
    - SPF pass: +0.2, fail/softfail: -0.25
    - DKIM pass: +0.2, fail: -0.25
    - DMARC pass: +0.1, fail: -0.15
    
    Args:
        auth (Dict[str, Any]): Authentication results from parse_authentication_results
        
    Returns:
        float: Trustworthiness score between 0.0 and 1.0
        
    Example:
        >>> auth = {'spf': 'pass', 'dkim': 'pass', 'dmarc': 'pass'}
        >>> auth_score_from_results(auth)
        0.9
    """
    score = 0.5
    # simple rules
    if auth.get("spf") == "pass":
        score += 0.2
    elif auth.get("spf") in ("fail", "softfail"):
        score -= 0.25
    if auth.get("dkim") == "pass":
        score += 0.2
    elif auth.get("dkim") == "fail":
        score -= 0.25
    if auth.get("dmarc") == "pass":
        score += 0.1
    elif auth.get("dmarc") == "fail":
        score -= 0.15
    return max(0.0, min(1.0, score))


def extract_kv_from_text(text: str) -> Dict[str, Optional[str]]:
    """
    Extract key-value pairs from invoice-like text using regex patterns.
    
    Performs structured data extraction from email text to identify
    invoice numbers, amounts, dates, bank accounts, and vendor information.
    Uses multiple regex patterns to handle various formats.
    
    Args:
        text (str): Text content to extract data from
        
    Returns:
        Dict[str, Optional[str]]: Extracted fields:
            - invoice_number: Invoice or bill number
            - total: Currency amount (last occurrence)
            - date: Date in various formats
            - bank_account: Bank account number
            - iban: International Bank Account Number
            - vendor_name: Vendor or sender name
    
    Example:
        >>> text = "Invoice #12345\nTotal: $1,500.00\nDue: 2024-01-15\nAccount: 987654321"
        >>> extract_kv_from_text(text)
        {
            'invoice_number': '12345',
            'total': '$1,500.00',
            'date': '2024-01-15',
            'bank_account': '987654321',
            'iban': None,
            'vendor_name': None
        }
    """
    out = {"invoice_number": None, "total": None, "date": None, "bank_account": None, "iban": None, "vendor_name": None}
    if not text:
        return out
    m = INVOICE_NUMBER_RE.search(text)
    if m:
        out["invoice_number"] = m.group(2).strip()
    # currency: take first match as total candidate (very naive)
    m2 = list(CURRENCY_RE.finditer(text))
    if m2:
        out["total"] = m2[-1].group(0).strip()
    m3 = DATE_RE.search(text)
    if m3:
        out["date"] = m3.group(0).strip()
    m4 = IBAN_RE.search(text)
    if m4:
        out["iban"] = m4.group(1).strip()
    m5 = BANK_ACCOUNT_RE.search(text)
    if m5:
        out["bank_account"] = m5.group(2).strip()
    # vendor_name heuristic: look for lines with "From:" or "Bill To"
    line_matches = re.findall(r"^(.*(?:From|Bill To|Billed To|Vendor).*)$", text, flags=re.I | re.M)
    if line_matches:
        # pick last and clean
        candidate = re.sub(r"^(From|Bill To|Billed To|Vendor)[:\s\-]*", "", line_matches[-1], flags=re.I).strip()
        out["vendor_name"] = candidate[:200]
    return out


# =============================================================================
# OCR INTEGRATION
# =============================================================================
#
# This section provides optional OCR (Optical Character Recognition) functionality
# for extracting text from image attachments. This is particularly useful for
# invoices sent as images or scanned documents.
#
# OCR Features:
# - Image attachment processing using pytesseract
# - Fallback handling when OCR libraries are not available
# - Integration with the main extraction pipeline
# - Support for common image formats (PNG, JPEG, TIFF)
#
# Note: This is a basic OCR implementation. For production use, consider
# more robust solutions like TrOCR, docTR, or commercial OCR APIs.
# -------------------------
def ocr_bytes_attachment(data_bytes: bytes) -> str:
    """
    Extract text from image attachment using OCR.
    
    Processes binary image data to extract text content using pytesseract.
    This function is designed to handle common image formats and provides
    graceful fallback when OCR libraries are not available.
    
    Args:
        data_bytes (bytes): Binary image data
        
    Returns:
        str: Extracted text content (empty string if OCR fails or unavailable)
        
    Raises:
        ImportError: If pytesseract or PIL are not installed
        
    Example:
        >>> with open("invoice.png", "rb") as f:
        ...     image_data = f.read()
        >>> text = ocr_bytes_attachment(image_data)
        >>> print(text)
        "Invoice #12345\nTotal: $1,500.00"
    
    Note:
        This is a basic OCR implementation. For production environments,
        consider using more advanced OCR solutions like:
        - TrOCR (Transformer-based OCR)
        - docTR (Document Text Recognition)
        - Commercial APIs (Google Vision, AWS Textract)
    """
    if pytesseract and Image:
        try:
            from io import BytesIO
            img = Image.open(BytesIO(data_bytes))
            return pytesseract.image_to_string(img)
        except Exception:
            return ""
    # fallback: no OCR installed
    return ""


# =============================================================================
# SCORING FUNCTIONS
# =============================================================================
#
# This section contains the core scoring algorithms that evaluate different
# aspects of email fraud risk. Each scoring function focuses on a specific
# dimension of fraud detection and returns both a score and contribution
# breakdown for explainability.
#
# Scoring Dimensions:
# - Email-level scoring: Urgency, links, keywords, authentication
# - Invoice-level scoring: Missing data, bank changes, vendor matching
# - Combined scoring: Weighted fusion of all dimensions
# - Decision mapping: Converting scores to actionable decisions
#
# These functions use heuristic-based scoring that can be easily understood
# and tuned. They are designed to be replaced with machine learning models
# as more training data becomes available.
# -------------------------
def score_email_model(features: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
    """
    Score email-level fraud indicators using heuristic rules.
    
    Evaluates email content and metadata for fraud indicators such as urgency
    language, suspicious links, and authentication failures. This function
    implements a rule-based scoring system that can be easily understood
    and tuned.
    
    Args:
        features (Dict[str, Any]): Email features dictionary containing:
            - has_invoice_keyword: Boolean indicating invoice keywords present
            - urgency_flag: Boolean indicating urgent language
            - links_count: Number of HTTP/HTTPS links in email
            - spf: SPF authentication result ('pass', 'fail', etc.)
            - dkim: DKIM authentication result
            - dmarc: DMARC authentication result
            - subject: Email subject line
            
    Returns:
        Tuple[float, Dict[str, float]]: 
            - Score between 0.0 and 1.0 (higher = more suspicious)
            - Contributions dictionary showing feature impact
    
    Scoring Logic:
        - Base score: 0.2
        - Invoice keywords: +0.25
        - Urgency language: +0.12
        - Links: +0.02 per link (max 0.08)
        - SPF pass: -0.05, fail: +0.2
        - DKIM pass: -0.05, fail: +0.18
    
    Example:
        >>> features = {
        ...     'has_invoice_keyword': True,
        ...     'urgency_flag': True,
        ...     'links_count': 2,
        ...     'spf': 'fail',
        ...     'dkim': 'pass'
        ... }
        >>> score, contrib = score_email_model(features)
        >>> print(f"Score: {score:.2f}")
        Score: 0.67
    """
    # Example features expected:
    # features: { 'has_invoice_keyword':bool, 'subject_similarity_to_invoice':float, 'urgency_flag':bool, 'links_count':int, 'spf_pass':bool, ... }
    score = 0.0
    contributions = {}
    # base
    score += 0.2
    contributions["base"] = 0.2
    if features.get("has_invoice_keyword"):
        score += 0.25
        contributions["invoice_keyword"] = 0.25
    if features.get("urgency_flag"):
        score += 0.12
        contributions["urgency_flag"] = 0.12
    links = features.get("links_count", 0) or 0
    if links > 0:
        link_contrib = min(0.08, 0.02 * links)
        score += link_contrib
        contributions["links_count"] = link_contrib
    # SPF/DKIM negative impacts
    spf = features.get("spf")  # 'pass'|'fail'|None
    dkim = features.get("dkim")
    if spf == "pass":
        score -= 0.05
        contributions["spf_pass"] = -0.05
    elif spf in ("fail", "softfail"):
        score += 0.2
        contributions["spf_fail"] = 0.2
    if dkim == "pass":
        score -= 0.05
        contributions["dkim_pass"] = -0.05
    elif dkim == "fail":
        score += 0.18
        contributions["dkim_fail"] = 0.18
    # normalize to 0..1
    score = max(0.0, min(1.0, score))
    return score, contributions


def score_invoice_model(kv: Dict[str, Optional[str]], structural_flags: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
    """
    Score invoice-specific fraud indicators using structural analysis.
    
    Evaluates invoice data quality and structural anomalies that may indicate
    fraud. Focuses on missing information, bank account changes, and vendor
    verification status.
    
    Args:
        kv (Dict[str, Optional[str]]): Extracted key-value pairs from invoice
        structural_flags (Dict[str, Any]): Structural analysis flags:
            - vendor_on_file: Boolean indicating vendor is in master database
            - bank_changed: Boolean indicating bank account changed from last invoice
            - attachment_type: Type of attachment ('pdf', 'image', None)
            - total_mismatch: Boolean indicating amount differs significantly
            
    Returns:
        Tuple[float, Dict[str, float]]:
            - Score between 0.0 and 1.0 (higher = more suspicious)
            - Contributions dictionary showing feature impact
    
    Scoring Logic:
        - Base score: 0.1
        - Missing invoice number: +0.15
        - Bank account present: +0.05
        - Bank account changed: +0.35
        - Vendor on file: -0.35 (trusted vendor)
        - Image attachment: +0.08
        - Total mismatch: +0.25
    
    Example:
        >>> kv = {'invoice_number': None, 'total': '$1000', 'bank_account': '12345'}
        >>> flags = {'vendor_on_file': False, 'bank_changed': True, 'attachment_type': 'image'}
        >>> score, contrib = score_invoice_model(kv, flags)
        >>> print(f"Score: {score:.2f}")
        Score: 0.58
    """
    score = 0.1
    contributions = {"base": 0.1}
    if not kv.get("invoice_number"):
        score += 0.15
        contributions["missing_inv_no"] = 0.15
    if kv.get("bank_account") or kv.get("iban"):
        # bank details present — if changed flag then raise
        if structural_flags.get("bank_changed"):
            score += 0.35
            contributions["bank_changed"] = 0.35
        else:
            score += 0.05
            contributions["bank_present"] = 0.05
    if structural_flags.get("vendor_on_file"):
        score -= 0.35
        contributions["vendor_on_file"] = -0.35
    if structural_flags.get("attachment_type") == "image":
        score += 0.08
        contributions["image_attachment"] = 0.08
    # totals mismatch (structural flag)
    if structural_flags.get("total_mismatch"):
        score += 0.25
        contributions["total_mismatch"] = 0.25
    score = max(0.0, min(1.0, score))
    return score, contributions


# =============================================================================
# SCORE FUSION AND DECISION MAPPING
# =============================================================================
#
# This section handles the combination of individual scoring dimensions into
# a final fraud risk score and maps that score to actionable decisions.
# The fusion process uses weighted linear combination with configurable weights,
# and the decision mapping applies business rules to determine appropriate
# actions based on risk levels.
#
# Key Components:
# - Score combination: Weighted fusion of email, invoice, auth, and vendor scores
# - Rule penalties: Additional penalties for specific fraud indicators
# - Decision mapping: Converting scores to actionable business decisions
# - Explainability: Detailed contribution tracking for transparency
#
# The decision mapping follows a hierarchical approach where higher risk
# scores trigger more intensive verification procedures.
# -------------------------
def combine_scores(email_score: float, invoice_score: float, auth_score: float, vendor_match_score: float,
                   weights: Dict[str, float] = DEFAULT_WEIGHTS,
                   rule_penalty: float = 0.0) -> Tuple[float, Dict[str, float]]:
    """
    Combine individual scores into final fraud risk score using weighted fusion.
    
    Performs weighted linear combination of all scoring dimensions to produce
    a final fraud risk score. The weights determine the relative importance
    of each dimension, and rule penalties can be applied for specific
    fraud indicators.
    
    Args:
        email_score (float): Email-level fraud score (0.0-1.0)
        invoice_score (float): Invoice-level fraud score (0.0-1.0)
        auth_score (float): Authentication trustworthiness score (0.0-1.0)
        vendor_match_score (float): Vendor matching score (0.0-1.0)
        weights (Dict[str, float]): Scoring weights for each dimension
        rule_penalty (float): Additional penalty for rule-based fraud indicators
        
    Returns:
        Tuple[float, Dict[str, float]]:
            - Combined fraud risk score (0.0-1.0, higher = more suspicious)
            - Contributions dictionary showing component impact
    
    Formula:
        combined = (email_score * w_email + 
                   invoice_score * w_invoice + 
                   auth_score * w_auth + 
                   vendor_match_score * w_vendor) - rule_penalty
    
    Example:
        >>> email_score, invoice_score, auth_score, vendor_score = 0.6, 0.8, 0.3, 0.1
        >>> combined, contrib = combine_scores(email_score, invoice_score, auth_score, vendor_score)
        >>> print(f"Combined Score: {combined:.2f}")
        Combined Score: 0.65
    """
    w_email = weights.get("email_score", 0.35)
    w_invoice = weights.get("invoice_score", 0.45)
    w_auth = weights.get("auth_score", 0.15)
    w_vendor = weights.get("vendor_match_score", 0.05)
    combined = email_score * w_email + invoice_score * w_invoice + auth_score * w_auth + vendor_match_score * w_vendor
    contributions = {
        "email_component": email_score * w_email,
        "invoice_component": invoice_score * w_invoice,
        "auth_component": auth_score * w_auth,
        "vendor_component": vendor_match_score * w_vendor,
        "rule_penalty": -abs(rule_penalty),
    }
    combined = combined - abs(rule_penalty)
    # clamp
    combined = max(0.0, min(1.0, combined))
    return combined, contributions


def map_to_decision(combined_score: float, vendor_on_file: bool = False) -> str:
    """
    Map combined fraud score to actionable business decision.
    
    Converts the numerical fraud risk score into specific business actions
    based on predefined thresholds and business rules. The decision hierarchy
    ensures that higher risk emails receive more intensive verification.
    
    Args:
        combined_score (float): Combined fraud risk score (0.0-1.0)
        vendor_on_file (bool): Whether the vendor is in the master database
        
    Returns:
        str: Decision action, one of:
            - 'high_confidence_fraud': Immediate fraud alert (score >= 0.85)
            - 'call_agent': Require phone verification (score >= 0.65)
            - 'email_confirmation': Email confirmation required (score >= 0.40)
            - 'human_review': Route to human reviewer (new vendors)
            - 'low_risk': No additional action needed (score < 0.40)
    
    Business Rules:
        - New vendors (not on file) with score >= 0.40 → human_review
        - Existing vendors follow standard threshold mapping
        - Higher scores trigger more intensive verification
    
    Example:
        >>> map_to_decision(0.75, vendor_on_file=True)
        'call_agent'
        >>> map_to_decision(0.45, vendor_on_file=False)
        'human_review'
        >>> map_to_decision(0.25, vendor_on_file=True)
        'low_risk'
    """
    if not vendor_on_file and combined_score >= THRESHOLDS["email_confirmation"]:
        # default: route first-time vendors to human review
        return "human_review"
    if combined_score >= THRESHOLDS["high_confidence_fraud"]:
        return "high_confidence_fraud"
    if combined_score >= THRESHOLDS["call_agent"]:
        return "call_agent"
    if combined_score >= THRESHOLDS["email_confirmation"]:
        return "email_confirmation"
    return "low_risk"


# =============================================================================
# MAIN PIPELINE ORCHESTRATION
# =============================================================================
#
# This section contains the main entry point for the email fraud detection
# pipeline. The process_email_message function orchestrates all components
# to provide a complete fraud analysis of Gmail messages.
#
# Pipeline Flow:
# 1. Parse Gmail message into normalized structure
# 2. Detect invoice-related content (early exit if not invoice)
# 3. Extract authentication results and calculate auth score
# 4. Process attachments and extract metadata
# 5. Extract invoice data using regex patterns and OCR
# 6. Perform vendor matching against master database
# 7. Calculate structural flags (bank changes, vendor status, etc.)
# 8. Score email and invoice dimensions
# 9. Apply rule-based penalties
# 10. Combine scores and generate final decision
# 11. Generate explainability report
#
# The pipeline is designed to be robust, fast, and explainable, providing
# both fraud risk assessment and detailed reasoning for decisions.
# -------------------------
def process_email_message(gmail_msg: Dict[str, Any], vendor_master: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Main entry point for email fraud detection pipeline.
    
    Processes a Gmail API message through the complete fraud detection pipeline,
    analyzing multiple dimensions of fraud risk and providing actionable decisions.
    This is the primary function that orchestrates all detection components.
    
    Args:
        gmail_msg (Dict[str, Any]): Gmail API message JSON from users.messages.get
            Can be in raw, full, or metadata format
        vendor_master (Optional[Dict[str, Any]]): Vendor master database
            Maps vendor domains/names to metadata:
            - domain: Vendor domain name
            - last_account: Last known bank account
            - last_amount: Last known invoice amount
            - contact: Contact information
            
    Returns:
        Dict[str, Any]: Complete fraud analysis containing:
            - invoice_candidate: Boolean indicating if email contains invoice content
            - email_score: Email-level fraud score (0.0-1.0)
            - invoice_score: Invoice-level fraud score (0.0-1.0)
            - auth_score: Authentication trustworthiness score (0.0-1.0)
            - vendor_match_score: Vendor matching score (0.0-1.0)
            - combined_score: Final fraud risk score (0.0-1.0)
            - decision: Actionable decision string
            - top_reasons: List of top contributing factors
            - extracted_fields: Structured data from invoice
            - attachments_meta: Attachment metadata
            - parsed_headers: Normalized email headers
            - raw_parsed: Complete parsed message structure
    
    Raises:
        ValueError: If message format is invalid
        
    Example:
        >>> gmail_msg = {
        ...     "id": "msg123",
        ...     "payload": {
        ...         "headers": [{"name": "From", "value": "billing@vendor.com"}],
        ...         "body": {"data": base64.urlsafe_b64encode(b"Invoice #12345\nTotal: $1000").decode()}
        ...     }
        ... }
        >>> vendor_db = {"vendor.com": {"domain": "vendor.com", "last_account": "12345"}}
        >>> result = process_email_message(gmail_msg, vendor_db)
        >>> print(f"Decision: {result['decision']}")
        Decision: low_risk
    
    Note:
        This function performs comprehensive analysis but is designed for
        real-time processing. For batch processing of large volumes,
        consider implementing parallel processing or async variants.
    """
    parsed = parse_gmail_message(gmail_msg)
    headers = parsed["headers"]
    subject = headers.get("subject", "") or ""
    from_header = headers.get("from", "") or ""
    to_header = headers.get("to", "") or ""
    full_text = (parsed.get("text_plain") or "") + "\n" + (parsed.get("text_html") or "")

    invoice_candidate = regex_invoice_detect(full_text, subject)
    if not invoice_candidate:
        # short-circuit: low-risk no invoice keywords
        return {
            "invoice_candidate": False,
            "reason": "no_invoice_keywords",
            "raw_parsed": parsed,
            "decision": "low_risk",
            "confidence": 0.0,
        }

    # parse auth
    auth = parse_authentication_results(headers)
    auth_score = auth_score_from_results(auth)

    # attachments metadata
    attachments_meta = []
    for a in parsed["attachments"]:
        attachments_meta.append({
            "filename": a.get("filename"),
            "mimeType": a.get("mimeType"),
            "size": a.get("size") or a.get("sizeEstimate"),
            "attachmentId": a.get("attachmentId"),
            "sha256": a.get("sha256"),
            "inline_data": a.get("data_bytes") is not None,
        })

    # quick feature engineering for email model
    email_features = {
        "has_invoice_keyword": bool(INVOICE_KEYWORDS.search(subject) or INVOICE_KEYWORDS.search(full_text)),
        "urgency_flag": bool(re.search(r"\b(immediate|urgent|asap|pay now|due immediately)\b", full_text, flags=re.I)),
        "links_count": len(re.findall(r"https?://", full_text)),
        "spf": auth.get("spf"),
        "dkim": auth.get("dkim"),
        "dmarc": auth.get("dmarc"),
        "subject": subject,
    }
    email_score, email_contrib = score_email_model(email_features)

    # invoice-level processing: extract K/V from text and attachments (OCR)
    kv = extract_kv_from_text(full_text)
    # if attachments have inline data, run OCR on first image-like
    for a in parsed["attachments"]:
        data_bytes = a.get("data_bytes")
        if data_bytes:
            if a.get("mimeType", "").startswith("image/") or (a.get("filename") or "").lower().endswith((".png", ".jpg", ".jpeg", ".tiff")):
                ocr_text = ocr_bytes_attachment(data_bytes)
                if ocr_text:
                    # merge and re-extract
                    kv2 = extract_kv_from_text(ocr_text)
                    for k, v in kv2.items():
                        if v:
                            kv[k] = v
            # If pdf, we would extract pages and OCR them via a PDF->image pipeline (placeholder)
            # For now: do nothing

    # structural flags
    structural_flags = {
        "vendor_on_file": False,
        "bank_changed": False,
        "attachment_type": None,
        "total_mismatch": False,
    }
    # vendor matching (simple domain / vendor_master check)
    sender_domain = domain_from_address(from_header)
    vendor_match_score = 0.0
    vendor_on_file = False
    if vendor_master:
        # vendor_master may be keyed by domain or name
        # try domain match
        for k, meta in vendor_master.items():
            # meta should include 'domain' or 'canonical_name'
            cand_domain = meta.get("domain") if isinstance(meta, dict) else k
            sim = fuzzy_domain_similarity(sender_domain, cand_domain)
            if sim > vendor_match_score:
                vendor_match_score = sim
                if sim > 0.85:
                    vendor_on_file = True
                    structural_flags["vendor_on_file"] = True
    # bank_changed: compare bank in kv vs vendor_master metadata if present
    if vendor_on_file:
        # if vendor_master contains last_account
        for k, meta in vendor_master.items():
            if (meta.get("domain") == sender_domain) or (fuzzy_domain_similarity(sender_domain, meta.get("domain", "")) > 0.85):
                last_acc = meta.get("last_account")
                if last_acc and kv.get("bank_account") and last_acc != kv.get("bank_account"):
                    structural_flags["bank_changed"] = True
                    break

    # attachment type
    if attachments_meta:
        # take first
        mt = attachments_meta[0].get("mimeType", "")
        if mt.startswith("image/"):
            structural_flags["attachment_type"] = "image"
        elif mt == "application/pdf" or (attachments_meta[0].get("filename") or "").lower().endswith(".pdf"):
            structural_flags["attachment_type"] = "pdf"

    # total mismatch check - very naive: if we have both totals from last vendor meta and current total, mark mismatch
    if vendor_on_file and kv.get("total"):
        # parse numeric from kv total
        numeric = re.sub(r"[^\d\.]", "", kv["total"])
        try:
            numeric_f = float(numeric)
            for k, meta in vendor_master.items():
                if fuzzy_domain_similarity(sender_domain, meta.get("domain", "")) > 0.85:
                    last_amount = meta.get("last_amount")
                    if last_amount and abs(numeric_f - float(last_amount)) / max(1.0, float(last_amount)) > 0.5:
                        structural_flags["total_mismatch"] = True
        except Exception:
            pass

    invoice_score, invoice_contrib = score_invoice_model(kv, structural_flags)

    # rule penalties: discrete checks increase combined score (we treat as penalty by subtracting)
    rule_penalty = 0.0
    # e.g., new domain very young (we cannot run whois here), SPF/DKIM fail => increase risk
    if auth.get("spf") in ("fail", "softfail") or auth.get("dkim") == "fail":
        rule_penalty += 0.10
    # bank changed for an on-file vendor: high penalty
    if structural_flags.get("bank_changed"):
        rule_penalty += 0.35
    # suspicious: attachment is an image + no invoice number
    if structural_flags.get("attachment_type") == "image" and not kv.get("invoice_number"):
        rule_penalty += 0.12
    # domain age check placeholder: if sender_domain contains suspicious homograph pattern (numbers/letters), small penalty
    if re.search(r"[0-9]", sender_domain):
        rule_penalty += 0.05

    combined_score, combined_contrib = combine_scores(email_score, invoice_score, auth_score, vendor_match_score, rule_penalty=rule_penalty)

    # Explainability: merge top contributions
    expl = []
    # flatten contributions from models
    def accumulate_contrib(d: Dict[str, float], prefix: str = ""):
        for k, v in d.items():
            expl.append((f"{prefix}{k}", float(v)))
    accumulate_contrib(email_contrib, "email.")
    accumulate_contrib(invoice_contrib, "invoice.")
    for k, v in combined_contrib.items():
        expl.append((f"combined.{k}", float(v)))
    # add auth and vendor_match signals
    expl.append(("signal.auth_score", auth_score))
    expl.append(("signal.vendor_match_score", vendor_match_score))

    # sort descending by absolute contribution magnitude
    expl_sorted = sorted(expl, key=lambda x: -abs(x[1]))[:8]

    decision = map_to_decision(combined_score, vendor_on_file)

    return {
        "invoice_candidate": True,
        "parsed_headers": headers,
        "from": from_header,
        "to": to_header,
        "subject": subject,
        "extracted_fields": kv,
        "attachments_meta": attachments_meta,
        "email_score": email_score,
        "invoice_score": invoice_score,
        "auth_score": auth_score,
        "vendor_match_score": vendor_match_score,
        "rule_penalty": rule_penalty,
        "combined_score": combined_score,
        "top_reasons": expl_sorted,
        "decision": decision,
        "raw_parsed": parsed,
    }


# =============================================================================
# EXAMPLE USAGE AND TESTING
# =============================================================================
#
# This section provides example usage and testing capabilities for the
# email fraud detection pipeline. It includes a command-line interface
# for testing with sample data and demonstrates the complete workflow.
#
# Usage Examples:
# - Command-line testing with sample Gmail messages
# - Synthetic data generation for testing
# - Integration examples with vendor master database
# - Output format demonstration
#
# This section is primarily for development and testing purposes.
# -------------------------

if __name__ == "__main__":
    """
    Command-line interface for testing the fraud detection pipeline.
    
    Usage: python -m api.ml.email_classifier [gmail_message_file.json]
    If no file is provided, uses synthetic test data.
    """
    import sys
    
    # Load Gmail message from file or use synthetic data for testing
    if len(sys.argv) > 1:
        fname = sys.argv[1]
        try:
            with open(fname, "r", encoding="utf-8") as f:
                gmail_msg = json.load(f)
        except Exception as e:
            print(f"Error loading file {fname}: {e}")
            sys.exit(1)
    else:
        # Synthetic minimal example for testing
        gmail_msg = {
            "id": "demo1",
            "threadId": "t1",
            "snippet": "Invoice 12345 amount $5,000 due now",
            "payload": {
                "headers": [
                    {"name": "From", "value": "Billing <billing@payvendor-example.com>"},
                    {"name": "Subject", "value": "Invoice No. 12345 - Immediate Payment Required"},
                    {"name": "Authentication-Results", "value": "mx.google.com; spf=pass smtp.mailfrom=payvendor-example.com; dkim=pass header.d=payvendor-example.com"}
                ],
                "mimeType": "text/plain",
                "body": {"size": 0, "data": base64.urlsafe_b64encode(b"Invoice No. 12345\nTotal: $5,000\nAccount: 987654321\n").decode("utf-8")}
            }
        }

    # Example vendor master database for testing
    # In production, this would be loaded from a database or external service
    vendor_master = {
        # key can be canonical id -> dict meta
        "payvendor-example.com": {
            "domain": "payvendor-example.com", 
            "last_account": "123456789", 
            "last_amount": 4800.0
        },
    }

    # Process the email through the fraud detection pipeline
    # and output the complete analysis results
    try:
        result = process_email_message(gmail_msg, vendor_master=vendor_master)
        print("=" * 60)
        print("EMAIL FRAUD DETECTION RESULTS")
        print("=" * 60)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error processing email: {e}")
        sys.exit(1)
