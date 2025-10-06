"""
End-to-End Call Test - Ready on Command
========================================
This script prepares an outbound call test and waits for user confirmation before executing.
Press ENTER when ready to initiate the call.
"""

import os
import sys
import httpx
import json
import time
from datetime import datetime

# Credentials
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "sk_9af95a2fca8ea120a514561389ef270c6e3c2235b3da347a")
ELEVEN_LABS_AGENT_ID = os.getenv("ELEVEN_LABS_AGENT_ID", "agent_2601k6rm4bjae2z9amfm5w1y6aps")
PHONE_NUMBER_ID = "phnum_4801k6sa89eqfpnsfjsxbr40phen"
TWILIO_PHONE_NUMBER = "+18887064372"

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

def verify_setup():
    """Verify that all necessary configuration is in place"""
    print("🔍 Verifying test setup...")
    
    issues = []
    
    if not ELEVENLABS_API_KEY or ELEVENLABS_API_KEY == "your_api_key_here":
        issues.append("❌ ELEVENLABS_API_KEY not set")
    else:
        print(f"   ✅ API Key: {ELEVENLABS_API_KEY[:15]}...")
    
    if not ELEVEN_LABS_AGENT_ID:
        issues.append("❌ ELEVEN_LABS_AGENT_ID not set")
    else:
        print(f"   ✅ Agent ID: {ELEVEN_LABS_AGENT_ID}")
    
    if not PHONE_NUMBER_ID:
        issues.append("❌ PHONE_NUMBER_ID not set")
    else:
        print(f"   ✅ Phone Number ID: {PHONE_NUMBER_ID}")
    
    print(f"   ✅ Test Phone: {TEST_PHONE_NUMBER}")
    print(f"   ✅ From Number: {TWILIO_PHONE_NUMBER}")
    
    if issues:
        print("\n⚠️  Configuration Issues:")
        for issue in issues:
            print(f"   {issue}")
        return False
    
    print("   ✅ All configuration valid")
    return True

def initiate_outbound_call(destination_number: str, variables: dict):
    """Initiate an outbound call using ElevenLabs Twilio API"""
    print(f"\n🚀 INITIATING CALL...")
    print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    url = "https://api.elevenlabs.io/v1/convai/twilio/outbound-call"
    
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "agent_id": ELEVEN_LABS_AGENT_ID,
        "agent_phone_number_id": PHONE_NUMBER_ID,
        "to_number": destination_number,
        "conversation_initiation_client_data": {
            "dynamic_variables": variables
        }
    }
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload, headers=headers)
            
            print(f"\n📊 Response Status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                data = response.json()
                
                call_id = data.get('call_id', 'N/A')
                conversation_id = data.get('conversation_id', 'N/A')
                
                print(f"\n✅ CALL INITIATED SUCCESSFULLY!")
                print(f"   Call ID: {call_id}")
                print(f"   Conversation ID: {conversation_id}")
                print(f"   Status: {data.get('status', 'N/A')}")
                
                print(f"\n📱 Phone {destination_number} should ring shortly!")
                
                print(f"\n💬 Expected First Message:")
                print(f"   'Hi, this is Donna calling from {variables['customer_org']} about case {variables['case_id']}.'")
                print(f"   'I'm calling to verify an invoice from {variables['email__vendor_name']}—'")
                print(f"   'invoice {variables['email__invoice_number']} for {variables['email__amount']}, due {variables['email__due_date']}.'")
                
                if conversation_id != 'N/A':
                    print(f"\n🔗 Monitor conversation in real-time:")
                    print(f"   https://elevenlabs.io/app/conversational-ai/conversations/{conversation_id}")
                
                return data
            else:
                print(f"\n❌ CALL FAILED")
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.text}")
                
                if response.status_code == 404:
                    print(f"\n💡 404 Error: Endpoint or resource not found")
                    print(f"   - Check phone number is imported in ElevenLabs dashboard")
                    print(f"   - Verify agent has Twilio integration enabled")
                elif response.status_code == 401:
                    print(f"\n💡 401 Error: Unauthorized")
                    print(f"   - Check API key is valid")
                elif response.status_code == 400:
                    print(f"\n💡 400 Error: Bad Request")
                    print(f"   - Check phone number format")
                    print(f"   - Verify all required fields")
                
                return None
                
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

def monitor_call(conversation_id: str, duration_seconds: int = 30):
    """Monitor call status for a specified duration"""
    print(f"\n⏱️  Monitoring call for {duration_seconds} seconds...")
    
    url = f"https://api.elevenlabs.io/v1/convai/conversations/{conversation_id}"
    headers = {"xi-api-key": ELEVENLABS_API_KEY}
    
    start_time = time.time()
    checks = 0
    
    try:
        with httpx.Client(timeout=30.0) as client:
            while time.time() - start_time < duration_seconds:
                checks += 1
                response = client.get(url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status', 'unknown')
                    duration = data.get('duration_seconds', 0)
                    
                    print(f"   Check #{checks}: Status={status}, Duration={duration}s")
                    
                    if status in ['completed', 'ended', 'failed']:
                        print(f"\n   ✅ Call {status}")
                        return data
                
                time.sleep(5)  # Check every 5 seconds
            
            print(f"\n   ⏰ Monitoring period ended")
            return None
            
    except Exception as e:
        print(f"   ⚠️  Error monitoring: {e}")
        return None

if __name__ == "__main__":
    print("=" * 80)
    print("🎯 END-TO-END CALL TEST - READY ON COMMAND")
    print("=" * 80)
    
    # Parse command line arguments
    destination = TEST_PHONE_NUMBER
    if len(sys.argv) > 1:
        destination = sys.argv[1]
        if not destination.startswith('+'):
            destination = f"+{destination}"
    
    print(f"\n📋 Test Configuration:")
    print(f"   Target Phone: {destination}")
    print(f"   From Number: {TWILIO_PHONE_NUMBER}")
    print(f"   Agent: Donna (ID: {ELEVEN_LABS_AGENT_ID})")
    print(f"\n📄 Test Scenario:")
    print(f"   Customer: {TEST_INVOICE_DATA['customer_org']}")
    print(f"   Vendor: {TEST_INVOICE_DATA['vendor__legal_name']}")
    print(f"   Invoice: {TEST_INVOICE_DATA['email__invoice_number']}")
    print(f"   Amount: ${TEST_INVOICE_DATA['email__amount']}")
    print(f"   Due Date: {TEST_INVOICE_DATA['email__due_date']}")
    
    # Verify setup
    if not verify_setup():
        print("\n❌ Setup verification failed. Please fix issues and try again.")
        sys.exit(1)
    
    # Wait for user confirmation
    print("\n" + "=" * 80)
    print("✅ TEST READY!")
    print("=" * 80)
    print("\n⏸️  Waiting for your command...")
    print("\n   Type 'GO' and press ENTER to initiate the call")
    print("   Or press Ctrl+C to cancel\n")
    
    try:
        user_input = input(">>> ").strip().upper()
        
        if user_input in ['GO', 'YES', 'Y', 'START']:
            print("\n🎬 GO SIGNAL RECEIVED!")
            print("=" * 80)
            
            # Initiate the call
            result = initiate_outbound_call(destination, TEST_INVOICE_DATA)
            
            if result:
                conversation_id = result.get('conversation_id')
                
                if conversation_id:
                    # Monitor for 30 seconds
                    monitor_call(conversation_id, duration_seconds=30)
                
                print("\n" + "=" * 80)
                print("✅ END-TO-END TEST COMPLETED")
                print("=" * 80)
                
                print(f"\n📊 Next Steps:")
                print(f"   1. Review the call in ElevenLabs dashboard")
                print(f"   2. Check the transcript and agent performance")
                print(f"   3. Verify dynamic variables were substituted correctly")
                print(f"   4. Test fraud detection logic")
                
            else:
                print("\n" + "=" * 80)
                print("❌ TEST FAILED")
                print("=" * 80)
                sys.exit(1)
        else:
            print(f"\n❌ Test cancelled (received: '{user_input}')")
            print("   Expected 'GO', 'YES', 'Y', or 'START'")
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n\n❌ Test cancelled by user (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        sys.exit(1)
