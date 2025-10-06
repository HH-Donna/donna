"""
Email Trigger - Automatic Verification Call System
===================================================
This module monitors Supabase for emails with label='unsure' and automatically
triggers verification calls using outbound_call_service.py

Usage:
    # Run as a service (continuously monitors database)
    python api/email_trigger.py --mode service --interval 30
    
    # Run once (process all pending emails)
    python api/email_trigger.py --mode once
    
    # Webhook mode (call from Supabase Edge Function)
    python api/email_trigger.py --mode webhook --port 8001

The trigger watches for:
- New emails with label='unsure'
- Emails that don't have call_initiated_at set yet
- Then automatically calls outbound_call_service.initiate_call()
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.supabase_client import get_supabase_client
from services.outbound_call_service import initiate_call

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================

# Database polling interval (seconds)
DEFAULT_POLL_INTERVAL = 30

# Maximum emails to process per cycle
MAX_EMAILS_PER_CYCLE = 10

# Minimum time between calls (seconds) to avoid rate limiting
CALL_RATE_LIMIT_DELAY = 5

# Default customer information for dynamic variables
DEFAULT_CUSTOMER_ORG = os.getenv("CUSTOMER_ORG", "Pixamp, Inc")
DEFAULT_USER_FULL_NAME = os.getenv("USER_FULL_NAME", "Sarah Johnson")
DEFAULT_USER_PHONE = os.getenv("USER_PHONE", "+14155551234")
DEFAULT_POLICY_NOTICE = (
    "This call may be recorded for quality assurance purposes. "
    "By continuing this call, you consent to recording."
)


# ============================================================================
# EMAIL TO DYNAMIC VARIABLES MAPPING
# ============================================================================

def map_email_to_dynamic_variables(email_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map Supabase email data to the 32 dynamic variables needed by the agent.
    
    Args:
        email_data: Email record from Supabase
        
    Returns:
        Complete set of 32 dynamic variables for the agent
    """
    case_id = f"CASE-{email_data.get('id', 'unknown')}"
    
    return {
        # Customer/User Information (6 variables)
        "customer_org": email_data.get("customer_org", DEFAULT_CUSTOMER_ORG),
        "user__company_name": email_data.get("user_company_name", DEFAULT_CUSTOMER_ORG),
        "user__full_name": email_data.get("user_full_name", DEFAULT_USER_FULL_NAME),
        "user__phone": email_data.get("user_phone", DEFAULT_USER_PHONE),
        "user__account_id": email_data.get("user_account_id", "N/A"),
        "user__acct_last4": email_data.get("user_acct_last4", "N/A"),
        
        # Case Information (2 variables)
        "case_id": case_id,
        "case__id": case_id,
        
        # Email/Invoice Details (7 variables)
        "email__vendor_name": email_data.get("vendor_name", "Unknown Vendor"),
        "email__invoice_number": email_data.get("invoice_number", "N/A"),
        "email__amount": str(email_data.get("amount", "0.00")),
        "email__due_date": email_data.get("due_date", "N/A"),
        "email__billing_address": email_data.get("billing_address", "N/A"),
        "email__contact_email": email_data.get("contact_email", "N/A"),
        "email__contact_phone": email_data.get("contact_phone", "N/A"),
        
        # Official/Canonical Info (6 variables)
        "official_canonical_phone": email_data.get("official_phone", "N/A"),
        "official_canonical_domain": email_data.get("official_domain", "N/A"),
        "official_canonical_billing_address": email_data.get("official_address", "N/A"),
        "db__official_phone": email_data.get("db_phone", "N/A"),
        "local__phone": email_data.get("local_phone", "N/A"),
        "online__phone": email_data.get("online_phone", "N/A"),
        
        # Verified Information (8 variables - populated during call)
        "verified__rep_name": "",
        "verified__issued_by_vendor": "",
        "verified__invoice_exists": "",
        "verified__amount": "",
        "verified__due_date": "",
        "verified__official_contact_email": "",
        "verified__ticket_id": "",
        "verified__security_contact": "",
        
        # Fraud Detection (1 variable)
        "fraud__is_suspected": "false",
        
        # System/Compliance (2 variables)
        "policy_recording_notice": DEFAULT_POLICY_NOTICE,
        "rep__secure_email": "",
    }


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
            
            logger.info(f"   📞 Selected phone from {source_name}: {phone}")
            return phone
    
    logger.error("   ❌ No valid phone number found")
    return None


# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

def fetch_pending_unsure_emails(supabase, limit: int = MAX_EMAILS_PER_CYCLE) -> List[Dict[str, Any]]:
    """
    Fetch emails that need verification calls.
    
    Criteria:
    - label = 'unsure'
    - call_initiated_at IS NULL (not yet processed)
    
    Args:
        supabase: Supabase client
        limit: Maximum number of emails to fetch
        
    Returns:
        List of email records ready for processing
    """
    try:
        response = (
            supabase.table("emails")
            .select("*")
            .eq("label", "unsure")
            .is_("call_initiated_at", "null")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        
        return response.data if response.data else []
        
    except Exception as e:
        logger.error(f"❌ Error fetching emails: {e}")
        return []


def mark_call_initiated(supabase, email_id: str, conversation_id: str) -> bool:
    """
    Mark email as having a call initiated.
    
    Args:
        supabase: Supabase client
        email_id: Email record ID
        conversation_id: ElevenLabs conversation ID
        
    Returns:
        True if successful
    """
    try:
        supabase.table("emails").update({
            "call_initiated_at": datetime.utcnow().isoformat(),
            "conversation_id": conversation_id
        }).eq("id", email_id).execute()
        
        logger.info(f"   ✅ Marked email {email_id} as call initiated")
        return True
        
    except Exception as e:
        logger.error(f"   ❌ Error marking email {email_id}: {e}")
        return False


# ============================================================================
# CORE TRIGGER LOGIC
# ============================================================================

def process_single_email(supabase, email_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single email: map variables and trigger call.
    
    This is the core function that:
    1. Maps email data to 32 dynamic variables
    2. Determines call destination
    3. Calls outbound_call_service.initiate_call()
    4. Updates database with results
    
    Args:
        supabase: Supabase client
        email_data: Email record to process
        
    Returns:
        Result dictionary with success status
    """
    email_id = email_data.get("id", "unknown")
    vendor_name = email_data.get("vendor_name", "Unknown")
    
    logger.info(f"\n{'='*80}")
    logger.info(f"📧 Processing Email: {email_id}")
    logger.info(f"   Vendor: {vendor_name}")
    logger.info(f"   Invoice: {email_data.get('invoice_number', 'N/A')}")
    logger.info(f"   Amount: {email_data.get('amount', 'N/A')}")
    
    # Step 1: Map to dynamic variables
    logger.info(f"   📋 Mapping email data to dynamic variables...")
    dynamic_vars = map_email_to_dynamic_variables(email_data)
    logger.info(f"   ✅ Mapped {len(dynamic_vars)} variables")
    
    # Step 2: Determine call destination
    logger.info(f"   📞 Determining call destination...")
    destination = determine_call_destination(email_data)
    
    if not destination:
        logger.error(f"   ❌ No valid phone number found - skipping")
        return {
            "success": False,
            "email_id": email_id,
            "error": "No valid phone number"
        }
    
    # Step 3: Initiate call using outbound_call_service.py
    logger.info(f"   🚀 Initiating call to {destination}...")
    logger.info(f"   📦 Passing {len(dynamic_vars)} dynamic variables to agent")
    
    try:
        # THIS IS THE KEY LINE - Calls your outbound_call_service.py!
        call_result = initiate_call(
            destination_number=destination,
            agent_variables=dynamic_vars,
            monitor=True,
            monitor_duration=30,
            verbose=True
        )
        
        if call_result['success']:
            conversation_id = call_result['conversation_id']
            logger.info(f"   ✅ Call initiated successfully!")
            logger.info(f"   🆔 Conversation ID: {conversation_id}")
            logger.info(f"   🔗 Dashboard: {call_result['dashboard_url']}")
            
            # Step 4: Update database
            mark_call_initiated(supabase, email_id, conversation_id)
            
            return {
                "success": True,
                "email_id": email_id,
                "conversation_id": conversation_id,
                "dashboard_url": call_result['dashboard_url']
            }
        else:
            logger.error(f"   ❌ Call failed: {call_result.get('error', 'Unknown error')}")
            return {
                "success": False,
                "email_id": email_id,
                "error": call_result.get('error')
            }
            
    except Exception as e:
        logger.error(f"   ❌ Exception during call: {e}")
        return {
            "success": False,
            "email_id": email_id,
            "error": str(e)
        }


def process_pending_emails(supabase) -> Dict[str, Any]:
    """
    Process all pending unsure emails.
    
    Returns:
        Summary of processing results
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"🔍 Checking for pending unsure emails...")
    logger.info(f"{'='*80}")
    
    # Fetch pending emails
    emails = fetch_pending_unsure_emails(supabase)
    
    if not emails:
        logger.info("   ℹ️  No pending unsure emails found")
        return {
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "results": []
        }
    
    logger.info(f"   📬 Found {len(emails)} pending email(s)")
    
    results = {
        "processed": len(emails),
        "successful": 0,
        "failed": 0,
        "results": []
    }
    
    # Process each email
    for i, email in enumerate(emails, 1):
        logger.info(f"\n--- Processing {i}/{len(emails)} ---")
        
        result = process_single_email(supabase, email)
        
        if result['success']:
            results['successful'] += 1
        else:
            results['failed'] += 1
        
        results['results'].append(result)
        
        # Rate limiting delay between calls
        if i < len(emails):
            logger.info(f"   ⏳ Waiting {CALL_RATE_LIMIT_DELAY}s before next call...")
            time.sleep(CALL_RATE_LIMIT_DELAY)
    
    # Summary
    logger.info(f"\n{'='*80}")
    logger.info(f"📊 PROCESSING COMPLETE")
    logger.info(f"   Total Processed: {results['processed']}")
    logger.info(f"   ✅ Successful: {results['successful']}")
    logger.info(f"   ❌ Failed: {results['failed']}")
    logger.info(f"{'='*80}\n")
    
    return results


# ============================================================================
# OPERATION MODES
# ============================================================================

def run_service_mode(interval: int = DEFAULT_POLL_INTERVAL):
    """
    Run as a continuous service that polls the database.
    
    This mode continuously checks for new unsure emails and processes them.
    Ideal for running as a background service or systemd daemon.
    
    Args:
        interval: Seconds between database checks
    """
    logger.info(f"🚀 Starting Email Trigger Service")
    logger.info(f"   Mode: Continuous Service")
    logger.info(f"   Poll Interval: {interval} seconds")
    logger.info(f"   Max Emails/Cycle: {MAX_EMAILS_PER_CYCLE}")
    logger.info(f"   Rate Limit Delay: {CALL_RATE_LIMIT_DELAY}s")
    logger.info(f"\n{'='*80}\n")
    
    supabase = get_supabase_client()
    
    cycle = 0
    
    try:
        while True:
            cycle += 1
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"🔄 Cycle #{cycle} - {timestamp}")
            
            # Process pending emails
            results = process_pending_emails(supabase)
            
            if results['processed'] > 0:
                logger.info(f"   Processed {results['processed']} emails")
            
            # Wait before next cycle
            logger.info(f"   😴 Sleeping for {interval} seconds...\n")
            time.sleep(interval)
            
    except KeyboardInterrupt:
        logger.info(f"\n⚠️  Service stopped by user (Ctrl+C)")
        logger.info(f"   Total cycles completed: {cycle}")
    except Exception as e:
        logger.error(f"\n❌ Service error: {e}")
        import traceback
        traceback.print_exc()


def run_once_mode():
    """
    Run once and exit.
    
    Process all pending unsure emails and then exit.
    Ideal for cron jobs or manual execution.
    """
    logger.info(f"🚀 Email Trigger - Run Once Mode")
    logger.info(f"{'='*80}\n")
    
    supabase = get_supabase_client()
    results = process_pending_emails(supabase)
    
    exit_code = 0 if results['failed'] == 0 else 1
    sys.exit(exit_code)


def run_webhook_mode(port: int = 8001):
    """
    Run as a webhook server.
    
    This mode starts a lightweight HTTP server that can be called by
    Supabase Edge Functions or other external triggers.
    
    Args:
        port: Port to listen on
    """
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import json
    
    class TriggerHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            """Handle POST requests to trigger email processing"""
            try:
                # Read request body
                content_length = int(self.headers['Content-Length'])
                body = self.rfile.read(content_length)
                data = json.loads(body.decode('utf-8'))
                
                logger.info(f"📥 Webhook triggered: {data}")
                
                # Get Supabase client
                supabase = get_supabase_client()
                
                # Check if specific email ID provided
                email_id = data.get('email_id')
                
                if email_id:
                    # Process specific email
                    email_data = supabase.table("emails").select("*").eq("id", email_id).single().execute()
                    if email_data.data:
                        result = process_single_email(supabase, email_data.data)
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(result).encode())
                    else:
                        self.send_response(404)
                        self.end_headers()
                        self.wfile.write(json.dumps({"error": "Email not found"}).encode())
                else:
                    # Process all pending
                    results = process_pending_emails(supabase)
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(results).encode())
                    
            except Exception as e:
                logger.error(f"Webhook error: {e}")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        
        def log_message(self, format, *args):
            """Suppress default HTTP logging"""
            pass
    
    logger.info(f"🚀 Email Trigger - Webhook Mode")
    logger.info(f"   Listening on port {port}")
    logger.info(f"   POST to http://localhost:{port}/ to trigger")
    logger.info(f"{'='*80}\n")
    
    server = HTTPServer(('0.0.0.0', port), TriggerHandler)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info(f"\n⚠️  Webhook server stopped")


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Email Trigger - Automatic Verification Call System"
    )
    
    parser.add_argument(
        '--mode',
        choices=['service', 'once', 'webhook'],
        default='once',
        help='Operation mode: service (continuous), once (run once), webhook (HTTP server)'
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        default=DEFAULT_POLL_INTERVAL,
        help=f'Poll interval in seconds for service mode (default: {DEFAULT_POLL_INTERVAL})'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=8001,
        help='Port for webhook mode (default: 8001)'
    )
    
    args = parser.parse_args()
    
    # Run in selected mode
    if args.mode == 'service':
        run_service_mode(interval=args.interval)
    elif args.mode == 'once':
        run_once_mode()
    elif args.mode == 'webhook':
        run_webhook_mode(port=args.port)


if __name__ == "__main__":
    main()
