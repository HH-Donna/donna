"""
Email to Call Service
=====================
Production service for automatically triggering verification calls
when emails with label='unsure' are detected in Supabase.

This module handles:
- Fetching unsure emails from Supabase
- Mapping email data to agent dynamic variables
- Enriching with external data sources
- Initiating outbound verification calls
- Updating email records with call results

Usage:
    from services.email_to_call_service import trigger_verification_call
    
    # Automatic: Process latest unsure email
    result = trigger_verification_call()
    
    # Manual: Process specific email
    result = trigger_verification_call(email_id="12345")
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.database.supabase_client import get_supabase_client
from services.outbound_call_service import initiate_call

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================

# Default customer information
DEFAULT_CUSTOMER_ORG = os.getenv("CUSTOMER_ORG", "Pixamp, Inc")
DEFAULT_USER_FULL_NAME = os.getenv("USER_FULL_NAME", "Sarah Johnson")
DEFAULT_USER_PHONE = os.getenv("USER_PHONE", "+14155551234")
DEFAULT_POLICY_NOTICE = (
    "This call may be recorded for quality assurance purposes. "
    "By continuing this call, you consent to recording."
)

# Call configuration
ENABLE_CALL_MONITORING = os.getenv("ENABLE_CALL_MONITORING", "true").lower() == "true"
CALL_MONITOR_DURATION = int(os.getenv("CALL_MONITOR_DURATION", "30"))


# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

def fetch_unsure_emails(limit: int = 10, processed: bool = False) -> List[Dict[str, Any]]:
    """
    Fetch unsure emails from Supabase that need verification.
    
    Args:
        limit: Maximum number of emails to fetch
        processed: If True, include already processed emails
        
    Returns:
        List of email records
    """
    try:
        supabase = get_supabase_client()
        
        query = (
            supabase.table("emails")
            .select("*")
            .eq("label", "unsure")
            .order("created_at", desc=True)
            .limit(limit)
        )
        
        # Filter out already processed emails if needed
        if not processed:
            query = query.is_("call_initiated_at", "null")
        
        response = query.execute()
        return response.data if response.data else []
        
    except Exception as e:
        logger.error(f"Error fetching unsure emails: {e}")
        return []


def fetch_email_by_id(email_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a specific email by ID.
    
    Args:
        email_id: Email record ID
        
    Returns:
        Email record or None
    """
    try:
        supabase = get_supabase_client()
        response = supabase.table("emails").select("*").eq("id", email_id).single().execute()
        return response.data if response.data else None
    except Exception as e:
        logger.error(f"Error fetching email {email_id}: {e}")
        return None


def mark_call_initiated(email_id: str, conversation_id: str, call_data: Dict[str, Any]) -> bool:
    """
    Mark an email as having a call initiated.
    
    Args:
        email_id: Email record ID
        conversation_id: ElevenLabs conversation ID
        call_data: Additional call metadata
        
    Returns:
        True if update successful
    """
    try:
        supabase = get_supabase_client()
        
        update_data = {
            "call_initiated_at": datetime.utcnow().isoformat(),
            "conversation_id": conversation_id,
            "call_metadata": call_data
        }
        
        supabase.table("emails").update(update_data).eq("id", email_id).execute()
        logger.info(f"Marked email {email_id} as call initiated")
        return True
        
    except Exception as e:
        logger.error(f"Error updating email {email_id}: {e}")
        return False


def update_verification_results(
    email_id: str,
    is_fraud: bool,
    verified_data: Dict[str, Any]
) -> bool:
    """
    Update email with verification results from the call.
    
    Args:
        email_id: Email record ID
        is_fraud: Whether fraud was detected
        verified_data: Verified information from the call
        
    Returns:
        True if update successful
    """
    try:
        supabase = get_supabase_client()
        
        # Determine new label based on verification
        new_label = "fraud" if is_fraud else "legit"
        
        update_data = {
            "label": new_label,
            "verified_at": datetime.utcnow().isoformat(),
            "verification_data": verified_data,
            "is_fraud": is_fraud
        }
        
        supabase.table("emails").update(update_data).eq("id", email_id).execute()
        logger.info(f"Updated email {email_id} with verification results: {new_label}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating verification results for {email_id}: {e}")
        return False


# ============================================================================
# DYNAMIC VARIABLE MAPPING
# ============================================================================

def map_email_to_dynamic_variables(email_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map Supabase email data to ElevenLabs agent dynamic variables.
    
    This function transforms the email database schema into the 32 dynamic
    variables expected by the Donna agent's system prompt.
    
    Args:
        email_data: Raw email data from Supabase
        
    Returns:
        Dictionary of dynamic variables
    """
    
    # Generate case ID
    case_id = f"CASE-{email_data.get('id', 'unknown')}"
    
    # Build complete variable set
    dynamic_variables = {
        # ===== Customer/User Information =====
        "customer_org": email_data.get("customer_org", DEFAULT_CUSTOMER_ORG),
        "user__company_name": email_data.get("user_company_name", DEFAULT_CUSTOMER_ORG),
        "user__full_name": email_data.get("user_full_name", DEFAULT_USER_FULL_NAME),
        "user__phone": email_data.get("user_phone", DEFAULT_USER_PHONE),
        "user__account_id": email_data.get("user_account_id", ""),
        "user__acct_last4": email_data.get("user_acct_last4", ""),
        
        # ===== Case Information =====
        "case_id": case_id,
        "case__id": case_id,
        
        # ===== Email/Invoice Details (from suspicious email) =====
        "email__vendor_name": email_data.get("vendor_name", "Unknown Vendor"),
        "email__invoice_number": email_data.get("invoice_number", "N/A"),
        "email__amount": str(email_data.get("amount", "0.00")),
        "email__due_date": email_data.get("due_date", "N/A"),
        "email__billing_address": email_data.get("billing_address", "N/A"),
        "email__contact_email": email_data.get("contact_email", "N/A"),
        "email__contact_phone": email_data.get("contact_phone", "N/A"),
        
        # ===== Official/Canonical Vendor Information =====
        "official_canonical_phone": email_data.get("official_phone", ""),
        "official_canonical_domain": email_data.get("official_domain", ""),
        "official_canonical_billing_address": email_data.get("official_address", ""),
        "db__official_phone": email_data.get("db_phone", ""),
        "local__phone": email_data.get("local_phone", ""),
        "online__phone": email_data.get("online_phone", ""),
        
        # ===== Verified Information (populated during call) =====
        "verified__rep_name": "",
        "verified__issued_by_vendor": "",
        "verified__invoice_exists": "",
        "verified__amount": "",
        "verified__due_date": "",
        "verified__official_contact_email": "",
        "verified__ticket_id": "",
        "verified__security_contact": "",
        
        # ===== Fraud Detection =====
        "fraud__is_suspected": "false",
        
        # ===== System/Compliance =====
        "policy_recording_notice": DEFAULT_POLICY_NOTICE,
        "rep__secure_email": "",
    }
    
    # Clean up empty strings to "N/A" for better UX
    for key, value in dynamic_variables.items():
        if value == "":
            if key.startswith("verified__") or key in ["rep__secure_email"]:
                # Keep empty for fields populated during call
                continue
            else:
                dynamic_variables[key] = "N/A"
    
    return dynamic_variables


def enrich_with_google_search(
    vendor_name: str,
    dynamic_vars: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Enrich dynamic variables with Google Search results for official vendor info.
    
    Args:
        vendor_name: Vendor name to search for
        dynamic_vars: Current dynamic variables
        
    Returns:
        Enriched dynamic variables
    """
    try:
        # Import here to avoid circular dependencies
        from app.services.google_search_service import search_company_contact
        
        logger.info(f"Enriching data for vendor: {vendor_name}")
        
        # Search for official contact information
        contact_info = search_company_contact(vendor_name)
        
        if contact_info:
            # Update official fields with search results
            if contact_info.get("phone"):
                dynamic_vars["online__phone"] = contact_info["phone"]
                if not dynamic_vars.get("official_canonical_phone") or dynamic_vars["official_canonical_phone"] == "N/A":
                    dynamic_vars["official_canonical_phone"] = contact_info["phone"]
            
            if contact_info.get("domain"):
                dynamic_vars["official_canonical_domain"] = contact_info["domain"]
            
            if contact_info.get("address"):
                dynamic_vars["official_canonical_billing_address"] = contact_info["address"]
            
            logger.info(f"Enrichment successful: {contact_info}")
        else:
            logger.warning(f"No enrichment data found for: {vendor_name}")
            
    except ImportError:
        logger.warning("Google search service not available, skipping enrichment")
    except Exception as e:
        logger.error(f"Error during enrichment: {e}")
    
    return dynamic_vars


def enrich_with_database_lookup(
    vendor_name: str,
    dynamic_vars: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Enrich dynamic variables with database lookup for known legitimate billers.
    
    Args:
        vendor_name: Vendor name to look up
        dynamic_vars: Current dynamic variables
        
    Returns:
        Enriched dynamic variables
    """
    try:
        # Import here to avoid circular dependencies
        from app.database.companies import get_legitimate_biller
        
        logger.info(f"Looking up vendor in database: {vendor_name}")
        
        biller = get_legitimate_biller(vendor_name)
        
        if biller:
            # Update database fields
            if biller.get("phone"):
                dynamic_vars["db__official_phone"] = biller["phone"]
            
            if biller.get("domain"):
                if not dynamic_vars.get("official_canonical_domain") or dynamic_vars["official_canonical_domain"] == "N/A":
                    dynamic_vars["official_canonical_domain"] = biller["domain"]
            
            logger.info(f"Database lookup successful: {biller}")
        else:
            logger.info(f"Vendor not found in database: {vendor_name}")
            
    except ImportError:
        logger.warning("Companies database not available, skipping database lookup")
    except Exception as e:
        logger.error(f"Error during database lookup: {e}")
    
    return dynamic_vars


def determine_call_destination(email_data: Dict[str, Any]) -> Optional[str]:
    """
    Determine which phone number to call based on priority order.
    
    Priority:
    1. local_phone (manually verified/preferred)
    2. db_phone (from legitimate billers database)
    3. online_phone (from Google Search)
    4. official_phone (from email metadata)
    5. contact_phone (from suspicious email - least trusted)
    
    Args:
        email_data: Email record data
        
    Returns:
        Phone number in E.164 format or None if no valid phone found
    """
    
    # Try sources in priority order
    phone_sources = [
        ("local_phone", "Local/Preferred"),
        ("db_phone", "Database"),
        ("online_phone", "Google Search"),
        ("official_phone", "Official"),
        ("contact_phone", "Email Contact")
    ]
    
    for field, source_name in phone_sources:
        phone = email_data.get(field)
        if phone and phone not in ["", "N/A", None]:
            # Normalize to E.164 format
            if not phone.startswith('+'):
                phone = f"+{phone}"
            
            logger.info(f"Selected phone from {source_name}: {phone}")
            return phone
    
    logger.error("No valid phone number found for call destination")
    return None


# ============================================================================
# MAIN SERVICE FUNCTIONS
# ============================================================================

def trigger_verification_call(
    email_id: Optional[str] = None,
    email_data: Optional[Dict[str, Any]] = None,
    enable_enrichment: bool = True
) -> Dict[str, Any]:
    """
    Trigger a verification call for an unsure email.
    
    This is the main entry point for the service. It:
    1. Fetches the email (if not provided)
    2. Maps email data to dynamic variables
    3. Enriches with external data sources
    4. Initiates the call
    5. Updates the database with results
    
    Args:
        email_id: Specific email ID to process (optional)
        email_data: Pre-fetched email data (optional, overrides email_id)
        enable_enrichment: Whether to enrich with external data
        
    Returns:
        Dictionary containing:
            - success: bool
            - email_id: str
            - conversation_id: str (if call initiated)
            - dashboard_url: str (if call initiated)
            - error: str (if failed)
    """
    
    logger.info("="*80)
    logger.info("🚀 TRIGGERING VERIFICATION CALL")
    logger.info("="*80)
    
    # Step 1: Get email data
    if email_data:
        logger.info(f"Using provided email data")
        email_id = email_data.get('id')
    elif email_id:
        logger.info(f"Fetching email by ID: {email_id}")
        email_data = fetch_email_by_id(email_id)
    else:
        logger.info("Fetching latest unsure email")
        emails = fetch_unsure_emails(limit=1, processed=False)
        email_data = emails[0] if emails else None
        if email_data:
            email_id = email_data.get('id')
    
    if not email_data:
        error_msg = "No email data available"
        logger.error(f"❌ {error_msg}")
        return {"success": False, "error": error_msg}
    
    logger.info(f"📧 Processing email: {email_id}")
    logger.info(f"   Vendor: {email_data.get('vendor_name', 'Unknown')}")
    logger.info(f"   Invoice: {email_data.get('invoice_number', 'N/A')}")
    
    # Step 2: Map to dynamic variables
    logger.info("📋 Mapping email data to dynamic variables...")
    dynamic_vars = map_email_to_dynamic_variables(email_data)
    logger.info(f"   ✅ Mapped {len(dynamic_vars)} variables")
    
    # Step 3: Enrich with external data
    if enable_enrichment:
        logger.info("🔍 Enriching with external data...")
        vendor_name = dynamic_vars.get("email__vendor_name", "")
        
        # Google Search enrichment
        dynamic_vars = enrich_with_google_search(vendor_name, dynamic_vars)
        
        # Database lookup enrichment
        dynamic_vars = enrich_with_database_lookup(vendor_name, dynamic_vars)
        
        logger.info("   ✅ Enrichment complete")
    else:
        logger.info("⏭️  Skipping enrichment (disabled)")
    
    # Step 4: Determine call destination
    logger.info("📞 Determining call destination...")
    destination = determine_call_destination(email_data)
    
    if not destination:
        error_msg = "No valid phone number found for call"
        logger.error(f"❌ {error_msg}")
        return {
            "success": False,
            "email_id": email_id,
            "error": error_msg
        }
    
    logger.info(f"   ✅ Will call: {destination}")
    
    # Step 5: Initiate the call
    logger.info("🎯 Initiating outbound call...")
    logger.info(f"   Case ID: {dynamic_vars.get('case_id')}")
    
    call_result = initiate_call(
        destination_number=destination,
        agent_variables=dynamic_vars,
        monitor=ENABLE_CALL_MONITORING,
        monitor_duration=CALL_MONITOR_DURATION,
        verbose=True
    )
    
    # Step 6: Update database
    if call_result['success']:
        logger.info("✅ Call initiated successfully!")
        conversation_id = call_result['conversation_id']
        
        # Mark email as call initiated
        mark_call_initiated(
            email_id=email_id,
            conversation_id=conversation_id,
            call_data=call_result['call_data']
        )
        
        return {
            "success": True,
            "email_id": email_id,
            "conversation_id": conversation_id,
            "dashboard_url": call_result['dashboard_url'],
            "call_data": call_result['call_data']
        }
    else:
        error_msg = call_result.get('error', 'Unknown error')
        logger.error(f"❌ Call failed: {error_msg}")
        
        return {
            "success": False,
            "email_id": email_id,
            "error": error_msg
        }


def process_batch_unsure_emails(max_emails: int = 10) -> Dict[str, Any]:
    """
    Process multiple unsure emails in batch.
    
    Args:
        max_emails: Maximum number of emails to process
        
    Returns:
        Summary of batch processing results
    """
    logger.info(f"🔄 Processing batch of up to {max_emails} unsure emails")
    
    emails = fetch_unsure_emails(limit=max_emails, processed=False)
    
    if not emails:
        logger.info("No unsure emails to process")
        return {
            "success": True,
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "results": []
        }
    
    results = {
        "success": True,
        "processed": len(emails),
        "successful": 0,
        "failed": 0,
        "results": []
    }
    
    for email in emails:
        email_id = email.get('id')
        logger.info(f"\n{'='*80}")
        logger.info(f"Processing email {results['processed'] - results['successful'] - results['failed'] + 1}/{len(emails)}: {email_id}")
        
        result = trigger_verification_call(email_data=email)
        
        if result['success']:
            results['successful'] += 1
        else:
            results['failed'] += 1
        
        results['results'].append(result)
    
    logger.info(f"\n{'='*80}")
    logger.info("📊 BATCH PROCESSING COMPLETE")
    logger.info(f"   Total: {results['processed']}")
    logger.info(f"   Successful: {results['successful']}")
    logger.info(f"   Failed: {results['failed']}")
    logger.info(f"{'='*80}\n")
    
    return results
