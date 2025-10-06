"""
Live Call Test: First Message

Usage: python3 test_first_message_live.py [phone_number]
Example: python3 test_first_message_live.py +13473580012

This will initiate a real call to test the first message.
"""

import os
import sys
import httpx
import json
import time
from pathlib import Path

# Credentials
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "sk_9af95a2fca8ea120a514561389ef270c6e3c2235b3da347a")
ELEVEN_LABS_AGENT_ID = os.getenv("ELEVEN_LABS_AGENT_ID", "agent_2601k6rm4bjae2z9amfm5w1y6aps")
TWILIO_PHONE_NUMBER = "+18887064372"

# Test data
TEST_VARIABLES = {
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

def get_phone_number_id():
    """Get phone number ID"""
    url = "https://api.elevenlabs.io/v1/convai/phone-numbers"
    headers = {"xi-api-key": ELEVENLABS_API_KEY}
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                phone_numbers = data.get('phone_numbers', []) if isinstance(data, dict) else data
                
                for pn in phone_numbers:
                    if pn.get('phone_number') == TWILIO_PHONE_NUMBER:
                        return pn.get('phone_number_id')
    except:
        pass
    return None

def initiate_call(phone_number_id, destination):
    """Initiate outbound call"""
    url = f"https://api.elevenlabs.io/v1/convai/phone-number/{phone_number_id}/call"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "agent_id": ELEVEN_LABS_AGENT_ID,
        "to_phone_number": destination,
        "dynamic_variables": TEST_VARIABLES
    }
    
    with httpx.Client(timeout=30.0) as client:
        response = client.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json()
    return None

def main():
    print("=" * 70)
    print("📞 LIVE FIRST MESSAGE TEST")
    print("=" * 70)
    
    # Get destination number
    if len(sys.argv) > 1:
        destination = sys.argv[1]
        if not destination.startswith('+'):
            destination = f"+{destination}"
    else:
        print("\n❌ Error: Phone number required")
        print("Usage: python3 test_first_message_live.py +1234567890")
        return 1
    
    print(f"\n📋 Test Configuration:")
    print(f"   Destination: {destination}")
    print(f"   Agent: Donna (Invoice Verifier)")
    print(f"   Case ID: {TEST_VARIABLES['case_id']}")
    print(f"   Invoice: {TEST_VARIABLES['email__invoice_number']}")
    
    # Get phone number
    print(f"\n🔍 Getting phone number ID...")
    phone_number_id = get_phone_number_id()
    
    if not phone_number_id:
        print(f"❌ Phone number {TWILIO_PHONE_NUMBER} not found!")
        print(f"   Run: python3 import_twilio_number.py")
        return 1
    
    print(f"✅ Phone number found: {phone_number_id}")
    
    # Initiate call
    print(f"\n📞 Initiating call...")
    result = initiate_call(phone_number_id, destination)
    
    if not result:
        print(f"❌ Failed to initiate call!")
        return 1
    
    call_id = result.get('call_id')
    conversation_id = result.get('conversation_id')
    
    print(f"\n✅ Call initiated successfully!")
    print(f"   Call ID: {call_id}")
    print(f"   Conversation ID: {conversation_id}")
    
    print(f"\n📱 TESTING INSTRUCTIONS:")
    print(f"=" * 70)
    print(f"1. Answer the call on {destination}")
    print(f"2. DO NOT say 'hello' first!")
    print(f"3. Listen carefully to verify:")
    print(f"   ✓ Donna speaks IMMEDIATELY without waiting")
    print(f"   ✓ She says: 'Hi, this is Donna calling from Pixamp, Inc'")
    print(f"   ✓ She mentions case ID: '{TEST_VARIABLES['case_id']}'")
    print(f"   ✓ She says the recording notice")
    print(f"   ✓ She mentions vendor: 'Shopify, Inc'")
    print(f"   ✓ She mentions invoice: '{TEST_VARIABLES['email__invoice_number']}'")
    print(f"   ✓ She mentions amount: '{TEST_VARIABLES['email__amount']}'")
    print(f"   ✓ She mentions due date: '{TEST_VARIABLES['email__due_date']}'")
    print(f"   ✓ She asks if you're the right person for billing verification")
    
    print(f"\n💡 Expected First Message:")
    print(f"   \"Hi, this is Donna calling from Pixamp, Inc about case")
    print(f"   shop-00123. True I'm calling to verify an invoice we received")
    print(f"   that appears to come from Shopify, Inc—invoice ioe-300050 for")
    print(f"   900, due 09-23-2025. Are you the right person to confirm whether")
    print(f"   this was issued by your billing department?\"")
    
    print(f"\n📊 View conversation:")
    print(f"   https://elevenlabs.io/app/conversational-ai/conversations/{conversation_id}")
    
    print(f"\n⏳ Waiting 15 seconds for call to complete...")
    time.sleep(15)
    
    # Get transcript
    print(f"\n🔍 Fetching transcript...")
    url = f"https://api.elevenlabs.io/v1/convai/conversations/{conversation_id}"
    headers = {"xi-api-key": ELEVENLABS_API_KEY}
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                transcript = data.get('transcript', '')
                
                if transcript:
                    print(f"\n📝 Transcript:")
                    print(f"   {transcript[:500]}...")
                    
                    # Check for first message keywords
                    keywords = [
                        'Donna',
                        'Pixamp',
                        'shop-00123',
                        'ioe-300050',
                        '900'
                    ]
                    
                    found = [kw for kw in keywords if kw in transcript]
                    
                    print(f"\n✅ Found {len(found)}/{len(keywords)} keywords in transcript")
                    
                    if len(found) >= 3:
                        print(f"\n✅ SUCCESS: First message appears to be working!")
                    else:
                        print(f"\n⚠️  WARNING: Some keywords missing from transcript")
                else:
                    print(f"\n⚠️  Transcript not yet available")
    except:
        print(f"\n⚠️  Could not fetch transcript")
    
    print("\n" + "=" * 70)
    print("✅ TEST COMPLETE")
    print("=" * 70)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
