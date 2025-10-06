"""
Test Outbound Call via ElevenLabs + Twilio Integration

This script initiates an outbound call using ElevenLabs' native Twilio integration.
The agent (Donna) will call the specified phone number to verify invoice information.
"""

import os
import sys
import httpx
import json
import time

# Credentials
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVEN_LABS_AGENT_ID = os.getenv("ELEVEN_LABS_AGENT_ID")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "+1234567890")

# Test data
TEST_PHONE_NUMBER = "+13473580012"  # Your phone number
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
    # Verification fields (to be filled during call)
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

def get_phone_number_id():
    """Get the phone_number_id for our imported Twilio number"""
    print("🔍 Looking up phone number ID...")
    
    url = "https://api.elevenlabs.io/v1/convai/phone-numbers"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                # Handle both dict and list responses
                if isinstance(data, dict):
                    phone_numbers = data.get('phone_numbers', [])
                elif isinstance(data, list):
                    phone_numbers = data
                else:
                    phone_numbers = []
                
                print(f"   Found {len(phone_numbers)} imported phone number(s)")
                
                if not phone_numbers:
                    print(f"\n❌ No phone numbers imported yet!")
                    print(f"\n📋 Please import your Twilio number first:")
                    print(f"   1. Go to: https://elevenlabs.io/app/conversational-ai")
                    print(f"   2. Click 'Phone Numbers' tab")
                    print(f"   3. Import Twilio number: {TWILIO_PHONE_NUMBER}")
                    print(f"   4. Use your Twilio Account SID from environment")
                    print(f"\n   OR see: ../agent/TWILIO_INTEGRATION_GUIDE.md")
                    sys.exit(1)
                
                # List all numbers for debugging
                for pn in phone_numbers:
                    number = pn.get('phone_number', 'N/A')
                    pn_id = pn.get('phone_number_id', 'N/A')
                    print(f"   - {number} (ID: {pn_id})")
                    
                    if number == TWILIO_PHONE_NUMBER:
                        print(f"✅ Found matching phone number ID: {pn_id}")
                        return pn_id
                
                print(f"\n❌ Phone number {TWILIO_PHONE_NUMBER} not found in imported numbers")
                print(f"   Available numbers: {[pn.get('phone_number') for pn in phone_numbers]}")
                print(f"\n📋 Please import this number via dashboard first!")
                sys.exit(1)
            else:
                print(f"❌ Failed to list phone numbers: {response.status_code}")
                print(f"   Response: {response.text}")
                print(f"\n💡 Try importing via dashboard instead:")
                print(f"   https://elevenlabs.io/app/conversational-ai")
                sys.exit(1)
                
    except Exception as e:
        print(f"❌ Error getting phone number ID: {e}")
        print(f"\n💡 Try importing via dashboard:")
        print(f"   https://elevenlabs.io/app/conversational-ai")
        sys.exit(1)

def initiate_outbound_call(phone_number_id: str, destination_number: str, variables: dict):
    """Initiate an outbound call using ElevenLabs API"""
    print(f"\n📞 Initiating outbound call...")
    print(f"   From: {TWILIO_PHONE_NUMBER} (via ElevenLabs)")
    print(f"   To: {destination_number}")
    print(f"   Agent: {ELEVEN_LABS_AGENT_ID}")
    
    url = f"https://api.elevenlabs.io/v1/convai/phone-number/{phone_number_id}/call"
    
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "agent_id": ELEVEN_LABS_AGENT_ID,
        "to_phone_number": destination_number,
        "dynamic_variables": variables
    }
    
    print(f"\n📋 Dynamic Variables (first 5):")
    for i, (key, value) in enumerate(list(variables.items())[:5]):
        print(f"   {key}: {value}")
    print(f"   ... and {len(variables) - 5} more variables")
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                call_id = data.get('call_id', 'N/A')
                conversation_id = data.get('conversation_id', 'N/A')
                
                print(f"\n✅ Call initiated successfully!")
                print(f"   Call ID: {call_id}")
                print(f"   Conversation ID: {conversation_id}")
                print(f"   Status: {data.get('status', 'N/A')}")
                
                print(f"\n📱 Your phone ({destination_number}) should ring shortly!")
                print(f"   Donna will introduce herself and ask about the invoice.")
                print(f"\n💡 Tips for testing:")
                print(f"   - Answer the call and engage with Donna")
                print(f"   - Confirm you're the right person for billing verification")
                print(f"   - Donna will ask about invoice {variables['email__invoice_number']}")
                print(f"   - You can verify or dispute the invoice details")
                print(f"   - Test the agent's handling of edge cases (wrong number, transfer, etc.)")
                
                return data
            else:
                print(f"\n❌ Failed to initiate call")
                print(f"   Status Code: {response.status_code}")
                print(f"   Response: {response.text}")
                
                # Provide helpful error messages
                if response.status_code == 404:
                    print(f"\n💡 Error 404: Phone number not found")
                    print(f"   Make sure you ran import_twilio_number.py first")
                elif response.status_code == 401:
                    print(f"\n💡 Error 401: Unauthorized")
                    print(f"   Check your ELEVENLABS_API_KEY")
                elif response.status_code == 400:
                    print(f"\n💡 Error 400: Bad Request")
                    print(f"   Check the phone number format and agent ID")
                
                sys.exit(1)
                
    except Exception as e:
        print(f"❌ Error initiating call: {e}")
        sys.exit(1)

def get_conversation_status(conversation_id: str):
    """Check the status of a conversation"""
    print(f"\n🔍 Checking conversation status...")
    
    url = f"https://api.elevenlabs.io/v1/convai/conversations/{conversation_id}"
    
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Status: {data.get('status', 'N/A')}")
                print(f"   Duration: {data.get('duration_seconds', 0)} seconds")
                return data
            else:
                print(f"   Could not fetch status: {response.status_code}")
                return None
                
    except Exception as e:
        print(f"   Error checking status: {e}")
        return None

if __name__ == "__main__":
    print("=" * 70)
    print("🎯 ElevenLabs Outbound Call Test")
    print("=" * 70)
    
    # Parse command line arguments
    destination = TEST_PHONE_NUMBER
    if len(sys.argv) > 1:
        destination = sys.argv[1]
        if not destination.startswith('+'):
            destination = f"+{destination}"
    
    print(f"\n📋 Test Configuration:")
    print(f"   Destination: {destination}")
    print(f"   Test Case: Invoice verification for {TEST_INVOICE_DATA['vendor__legal_name']}")
    print(f"   Invoice #: {TEST_INVOICE_DATA['email__invoice_number']}")
    print(f"   Amount: {TEST_INVOICE_DATA['email__amount']}")
    
    # Step 1: Get phone number ID
    phone_number_id = get_phone_number_id()
    
    # Step 2: Initiate the call
    result = initiate_outbound_call(phone_number_id, destination, TEST_INVOICE_DATA)
    
    # Step 3: Monitor the call
    conversation_id = result.get('conversation_id')
    if conversation_id:
        print(f"\n⏳ Monitoring call progress...")
        print(f"   (Call may take a few moments to connect)")
        
        # Wait a bit before checking status
        time.sleep(5)
        get_conversation_status(conversation_id)
        
        print(f"\n📊 View full conversation history:")
        print(f"   https://elevenlabs.io/app/conversational-ai/conversations/{conversation_id}")
    
    print("\n" + "=" * 70)
    print("✅ Test initiated! Answer your phone to speak with Donna.")
    print("=" * 70)
    print(f"\n💡 After the call:")
    print(f"   1. Check the conversation history in ElevenLabs dashboard")
    print(f"   2. Review the transcript and analyze agent performance")
    print(f"   3. Test dynamic variable substitution")
    print(f"   4. Verify the call flow matches the agent prompt")
