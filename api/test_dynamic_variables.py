"""
Dynamic Variables Test - Email to Agent Call Pipeline
======================================================
This test demonstrates the complete workflow of:
1. Fetching an "unsure" labeled email from Supabase
2. Mapping email data to dynamic variables
3. Enriching with external data sources
4. Initiating an agent call with full context

Based on ElevenLabs Dynamic Variables documentation:
https://elevenlabs.io/docs/agents-platform/customization/personalization/dynamic-variables

Usage:
    python api/test_dynamic_variables.py
    python api/test_dynamic_variables.py --email-id <specific_id>
    python api/test_dynamic_variables.py --dry-run
"""

import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional
import argparse

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.supabase_client import get_supabase_client
from services.outbound_call_service import initiate_call


# ============================================================================
# CONFIGURATION
# ============================================================================

# Default values for testing
DEFAULT_CUSTOMER_ORG = "Pixamp, Inc"
DEFAULT_USER_FULL_NAME = "Sarah Johnson"
DEFAULT_USER_PHONE = "+14155551234"
DEFAULT_POLICY_NOTICE = "This call may be recorded for quality assurance purposes."

# Test phone number (your number or a test number)
DEFAULT_DESTINATION_NUMBER = "+13473580012"


# ============================================================================
# DATA MAPPING FUNCTIONS
# ============================================================================

def fetch_latest_unsure_email(supabase, email_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Fetch the latest email with label='unsure' from Supabase.
    
    Args:
        supabase: Supabase client instance
        email_id: Optional specific email ID to fetch
        
    Returns:
        Email data dict or None if not found
    """
    try:
        if email_id:
            # Fetch specific email
            response = supabase.table("emails").select("*").eq("id", email_id).single().execute()
            return response.data if response.data else None
        else:
            # Fetch latest unsure email
            response = (
                supabase.table("emails")
                .select("*")
                .eq("label", "unsure")
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
            
    except Exception as e:
        print(f"❌ Error fetching email from Supabase: {e}")
        return None


def map_email_to_dynamic_variables(email_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map Supabase email data to ElevenLabs dynamic variables.
    
    This function transforms the email database schema into the format
    expected by the Donna agent's system prompt.
    
    Args:
        email_data: Raw email data from Supabase
        
    Returns:
        Dictionary of dynamic variables ready for agent initialization
    """
    
    # Generate case ID from email ID
    case_id = f"CASE-{email_data.get('id', 'unknown')}"
    
    # Extract email-specific fields (from the suspicious email)
    email_vars = {
        "email__vendor_name": email_data.get("vendor_name", "Unknown Vendor"),
        "email__invoice_number": email_data.get("invoice_number", "N/A"),
        "email__amount": email_data.get("amount", "0.00"),
        "email__due_date": email_data.get("due_date", "N/A"),
        "email__billing_address": email_data.get("billing_address", "N/A"),
        "email__contact_email": email_data.get("contact_email", "N/A"),
        "email__contact_phone": email_data.get("contact_phone", "N/A"),
    }
    
    # Extract official/canonical information (from trusted sources)
    # These should come from database lookups or Google Search results
    official_vars = {
        "official_canonical_phone": email_data.get("official_phone", "N/A"),
        "official_canonical_domain": email_data.get("official_domain", "N/A"),
        "official_canonical_billing_address": email_data.get("official_address", "N/A"),
        "db__official_phone": email_data.get("db_phone", "N/A"),
        "local__phone": email_data.get("local_phone", "N/A"),
        "online__phone": email_data.get("online_phone", "N/A"),
    }
    
    # Customer/User information
    customer_vars = {
        "customer_org": email_data.get("customer_org", DEFAULT_CUSTOMER_ORG),
        "user__company_name": email_data.get("user_company_name", DEFAULT_CUSTOMER_ORG),
        "user__full_name": email_data.get("user_full_name", DEFAULT_USER_FULL_NAME),
        "user__phone": email_data.get("user_phone", DEFAULT_USER_PHONE),
        "user__account_id": email_data.get("user_account_id", "ACC-123456789"),
        "user__acct_last4": email_data.get("user_acct_last4", "4421"),
    }
    
    # Case information
    case_vars = {
        "case_id": case_id,
        "case__id": case_id,
    }
    
    # System/Compliance
    system_vars = {
        "policy_recording_notice": DEFAULT_POLICY_NOTICE,
    }
    
    # Initialize verified fields as empty (will be populated by tool responses during call)
    verified_vars = {
        "verified__rep_name": "",
        "verified__issued_by_vendor": "",
        "verified__invoice_exists": "",
        "verified__amount": "",
        "verified__due_date": "",
        "verified__official_contact_email": "",
        "verified__ticket_id": "",
        "verified__security_contact": "",
    }
    
    # Fraud detection
    fraud_vars = {
        "fraud__is_suspected": "false",
    }
    
    # Combine all variables
    dynamic_variables = {
        **email_vars,
        **official_vars,
        **customer_vars,
        **case_vars,
        **system_vars,
        **verified_vars,
        **fraud_vars,
    }
    
    return dynamic_variables


def enrich_with_external_data(email_data: Dict[str, Any], dynamic_vars: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich dynamic variables with external data sources.
    
    This could include:
    - Google Search results for official vendor contact info
    - Database lookups for known legitimate billers
    - Previous verification history
    
    Args:
        email_data: Original email data
        dynamic_vars: Current dynamic variables
        
    Returns:
        Enriched dynamic variables
    """
    
    # TODO: Implement actual external data enrichment
    # For now, this is a placeholder showing where enrichment would happen
    
    vendor_name = dynamic_vars.get("email__vendor_name", "")
    
    # Example: Query Google Search service for official contact
    # from app.services.google_search_service import search_vendor_contact
    # official_contact = search_vendor_contact(vendor_name)
    # if official_contact:
    #     dynamic_vars["official_canonical_phone"] = official_contact.get("phone")
    #     dynamic_vars["official_canonical_domain"] = official_contact.get("domain")
    
    # Example: Query legitimate billers database
    # from app.database.companies import get_legitimate_biller
    # biller = get_legitimate_biller(vendor_name)
    # if biller:
    #     dynamic_vars["db__official_phone"] = biller.get("phone")
    
    return dynamic_vars


def extract_destination_phone(email_data: Dict[str, Any]) -> str:
    """
    Determine which phone number to call.
    
    Priority order:
    1. Local/preferred phone
    2. Database official phone
    3. Online found phone
    4. Default test number
    
    Args:
        email_data: Email data containing potential phone numbers
        
    Returns:
        Phone number in E.164 format
    """
    
    # Try to extract from various sources
    phone = (
        email_data.get("local_phone") or
        email_data.get("db_phone") or
        email_data.get("online_phone") or
        email_data.get("official_phone") or
        DEFAULT_DESTINATION_NUMBER
    )
    
    # Ensure E.164 format
    if not phone.startswith('+'):
        phone = f"+{phone}"
    
    return phone


# ============================================================================
# MAIN TEST FUNCTIONS
# ============================================================================

def test_variable_mapping_only(email_data: Dict[str, Any]):
    """Test only the variable mapping without making a call"""
    print("\n" + "="*80)
    print("🧪 VARIABLE MAPPING TEST (DRY RUN)")
    print("="*80)
    
    print(f"\n📧 Email Data:")
    print(f"   ID: {email_data.get('id')}")
    print(f"   From: {email_data.get('sender')}")
    print(f"   Subject: {email_data.get('subject')}")
    print(f"   Label: {email_data.get('label')}")
    print(f"   Created: {email_data.get('created_at')}")
    
    # Map to dynamic variables
    dynamic_vars = map_email_to_dynamic_variables(email_data)
    
    # Enrich with external data
    dynamic_vars = enrich_with_external_data(email_data, dynamic_vars)
    
    print(f"\n📋 Mapped Dynamic Variables ({len(dynamic_vars)} total):")
    print("\n   🏢 Customer/User Information:")
    for key in ['customer_org', 'user__company_name', 'user__full_name', 'user__phone']:
        print(f"      {key}: {dynamic_vars.get(key, 'N/A')}")
    
    print("\n   📁 Case Information:")
    for key in ['case_id', 'case__id']:
        print(f"      {key}: {dynamic_vars.get(key, 'N/A')}")
    
    print("\n   📨 Email/Invoice Details:")
    for key in ['email__vendor_name', 'email__invoice_number', 'email__amount', 
                'email__due_date', 'email__contact_phone']:
        print(f"      {key}: {dynamic_vars.get(key, 'N/A')}")
    
    print("\n   ✅ Official/Canonical Info:")
    for key in ['official_canonical_phone', 'official_canonical_domain', 
                'db__official_phone', 'local__phone', 'online__phone']:
        print(f"      {key}: {dynamic_vars.get(key, 'N/A')}")
    
    print("\n   🔍 Fraud Detection:")
    print(f"      fraud__is_suspected: {dynamic_vars.get('fraud__is_suspected', 'N/A')}")
    
    print("\n   📞 Call Destination:")
    destination = extract_destination_phone(email_data)
    print(f"      Would call: {destination}")
    
    return dynamic_vars


def test_full_pipeline(email_data: Dict[str, Any], monitor: bool = True):
    """Test the complete pipeline including actual call initiation"""
    print("\n" + "="*80)
    print("🚀 FULL PIPELINE TEST - EMAIL TO AGENT CALL")
    print("="*80)
    
    print(f"\n📧 Processing Email:")
    print(f"   ID: {email_data.get('id')}")
    print(f"   Vendor: {email_data.get('vendor_name', 'Unknown')}")
    print(f"   Label: {email_data.get('label')}")
    
    # Step 1: Map email data to dynamic variables
    print(f"\n📋 Step 1: Mapping email data to dynamic variables...")
    dynamic_vars = map_email_to_dynamic_variables(email_data)
    print(f"   ✅ Mapped {len(dynamic_vars)} variables")
    
    # Step 2: Enrich with external data
    print(f"\n🔍 Step 2: Enriching with external data sources...")
    dynamic_vars = enrich_with_external_data(email_data, dynamic_vars)
    print(f"   ✅ Enrichment complete")
    
    # Step 3: Determine destination phone
    print(f"\n📞 Step 3: Determining call destination...")
    destination_phone = extract_destination_phone(email_data)
    print(f"   ✅ Will call: {destination_phone}")
    
    # Step 4: Initiate call with dynamic variables
    print(f"\n🎯 Step 4: Initiating agent call with dynamic variables...")
    print(f"   Agent will receive context for case: {dynamic_vars.get('case_id')}")
    
    result = initiate_call(
        destination_number=destination_phone,
        agent_variables=dynamic_vars,
        monitor=monitor,
        monitor_duration=30,
        verbose=True
    )
    
    # Step 5: Report results
    print(f"\n📊 Step 5: Call Results:")
    if result['success']:
        print(f"   ✅ Call initiated successfully!")
        print(f"   📍 Conversation ID: {result['conversation_id']}")
        print(f"   🔗 Dashboard: {result['dashboard_url']}")
        
        if result.get('monitoring_data'):
            monitoring = result['monitoring_data']
            print(f"\n   📈 Monitoring Data:")
            print(f"      Status: {monitoring.get('status', 'unknown')}")
            print(f"      Duration: {monitoring.get('duration_seconds', 0)}s")
    else:
        print(f"   ❌ Call failed: {result.get('error', 'Unknown error')}")
    
    return result


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Test dynamic variables pipeline from Supabase email to agent call"
    )
    parser.add_argument(
        '--email-id',
        type=str,
        help='Specific email ID to test (otherwise uses latest unsure email)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Only test variable mapping without making actual call'
    )
    parser.add_argument(
        '--no-monitor',
        action='store_true',
        help='Do not monitor call status after initiation'
    )
    parser.add_argument(
        '--destination',
        type=str,
        help=f'Override destination phone number (default: {DEFAULT_DESTINATION_NUMBER})'
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("🧪 DYNAMIC VARIABLES TEST - SUPABASE EMAIL → AGENT CALL")
    print("="*80)
    print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize Supabase client
    print(f"\n🔌 Connecting to Supabase...")
    try:
        supabase = get_supabase_client()
        print(f"   ✅ Connected successfully")
    except Exception as e:
        print(f"   ❌ Failed to connect: {e}")
        return 1
    
    # Fetch email data
    print(f"\n📥 Fetching email data...")
    if args.email_id:
        print(f"   Looking for email ID: {args.email_id}")
    else:
        print(f"   Looking for latest email with label='unsure'")
    
    email_data = fetch_latest_unsure_email(supabase, args.email_id)
    
    if not email_data:
        print(f"   ❌ No email found!")
        print(f"\n💡 Tips:")
        print(f"   - Ensure emails table has rows with label='unsure'")
        print(f"   - Check Supabase connection and permissions")
        print(f"   - Use --email-id to specify a specific email")
        return 1
    
    print(f"   ✅ Found email: {email_data.get('id')}")
    
    # Override destination if provided
    if args.destination:
        email_data['local_phone'] = args.destination
        print(f"   📞 Overriding destination: {args.destination}")
    
    # Run test based on mode
    try:
        if args.dry_run:
            test_variable_mapping_only(email_data)
        else:
            test_full_pipeline(email_data, monitor=not args.no_monitor)
        
        print("\n" + "="*80)
        print("✅ TEST COMPLETE")
        print("="*80 + "\n")
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
