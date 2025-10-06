"""
End-to-End Call Test - Launch Immediately
==========================================
This module provides a test wrapper for the outbound call service.
Can be used as a library or run as a standalone test script.

Usage as library:
    from test_e2e_launch import launch_e2e_call
    
    result = launch_e2e_call(
        destination_number="+13473580012",
        variables={...},
        monitor=True
    )

Usage as script:
    python test_e2e_launch.py [phone_number]
    
Note: For production use, import from services.outbound_call_service instead
"""

import sys
from typing import Optional, Dict, Any
from services.outbound_call_service import initiate_call

# Test configuration
TEST_PHONE_NUMBER = "+13473580012"
TEST_INVOICE_DATA = {
    "case_id": "shop-00123",
    "customer_org": "Pixamp, Inc",
    "user__company_name": "Allen",
    "vendor__legal_name": "Spotify",
    "email__vendor_name": "Shopify, Inc",
    "email__invoice_number": "ioe-300050",
    "email__amount": "900",
    "email__due_date": "09-23-2025",
    "email__billing_address": "101 Avenue of the Americas, New York, NY 10013, USA",
    "email__contact_email": "allen@pixamp.com",
    "email__contact_phone": "347-555-9876",
    "official_canonical_domain": "spotify.com",
    "official_canonical_phone": "212-555-0404",
    "official_canonical_billing_address": "101 Avenue of the Americas, New York, NY 10013, USA",
    "local__phone": "347333333",
    "db__official_phone": "212-555-0404",
    "online__phone": "800-555-0199",
    "user__full_name": "Allen Taylor",
    "user__phone": "347-555-9876",
    "user__account_id": "SP-98765-AL",
    "user__acct_last4": "1234",
    "policy_recording_notice": "True",
    "verified__invoice_exists": "True",
    "verified__issued_by_vendor": "Shopify, Inc",
    "verified__amount": "900",
    "verified__due_date": "09-23-2025",
    "verified__official_contact_email": "allen@pixamp.com",
    "verified__ticket_id": "SP-1234567",
    "verified__rep_name": "Jessica Moore",
    "verified__security_contact": "security@spotify.com",
    "fraud__is_suspected": "False",
    "rep__secure_email": "allen.support@spotify.com",
    "call_contact_tool": "SpotifyLiveSupport",
    "case__id": "987654321"
}


def launch_e2e_call(
    destination_number: str,
    variables: Optional[Dict[str, Any]] = None,
    monitor: bool = True,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Convenience wrapper for launching an end-to-end call test.
    
    This function wraps the outbound_call_service.initiate_call() function
    with test-specific defaults.
    
    Args:
        destination_number: Phone number to call (E.164 format, e.g., "+13473580012")
        variables: Dictionary of dynamic variables for the agent conversation.
                   If None, uses TEST_INVOICE_DATA
        monitor: Whether to monitor the call status after initiation
        verbose: Whether to print detailed output
        
    Returns:
        Dictionary containing:
            - success: bool indicating if call was initiated
            - call_data: Response from ElevenLabs API
            - conversation_id: ID for tracking the conversation
            - dashboard_url: URL to view conversation
            - monitoring_data: Final status if monitoring was enabled
            - error: Error message if call failed
            
    Example:
        >>> result = launch_e2e_call(
        ...     destination_number="+13473580012",
        ...     variables={"case_id": "test-123", "customer_org": "Acme Corp"},
        ...     monitor=True
        ... )
        >>> if result['success']:
        ...     print(f"Call initiated: {result['conversation_id']}")
    """
    # Use default test data if no variables provided
    if variables is None:
        variables = TEST_INVOICE_DATA
    
    # Use the service module to initiate the call
    result = initiate_call(
        destination_number=destination_number,
        agent_variables=variables,
        monitor=monitor,
        monitor_duration=30,
        verbose=verbose
    )
    
    return result

if __name__ == "__main__":
    print("=" * 80)
    print("🎯 END-TO-END CALL TEST - LAUNCHING NOW!")
    print("=" * 80)
    
    # Parse command line arguments
    destination = TEST_PHONE_NUMBER
    if len(sys.argv) > 1:
        destination = sys.argv[1]
    
    print(f"\n📋 Configuration:")
    print(f"   Target: {destination}")
    print(f"   Scenario: Invoice verification for {TEST_INVOICE_DATA['vendor__legal_name']}")
    print(f"   Invoice: {TEST_INVOICE_DATA['email__invoice_number']} (${TEST_INVOICE_DATA['email__amount']})")
    
    # Launch the call using the new callable function
    result = launch_e2e_call(
        destination_number=destination,
        variables=TEST_INVOICE_DATA,
        monitor=True,
        verbose=True
    )
    
    if result['success']:
        print("\n" + "=" * 80)
        print("✅ TEST EXECUTED")
        print("=" * 80)
        print(f"\n📝 Review:")
        print(f"   - Check your phone for the call")
        print(f"   - Review transcript in ElevenLabs dashboard")
        print(f"   - Verify agent behavior and dynamic variables")
        
        if result['conversation_id']:
            print(f"\n🔗 Conversation ID: {result['conversation_id']}")
        
    else:
        print("\n" + "=" * 80)
        print("❌ TEST FAILED")
        print("=" * 80)
        sys.exit(1)
