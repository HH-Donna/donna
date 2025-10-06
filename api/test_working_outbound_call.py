"""
Working Outbound Call Test - Using CORRECT ElevenLabs API Endpoint

Based on OpenAPI spec analysis, the correct endpoint is:
POST /v1/convai/twilio/outbound-call

This endpoint requires:
- agent_id
- agent_phone_number_id (not just the phone number!)
- to_number
- conversation_initiation_client_data.dynamic_variables
"""

import os
import sys
import httpx
import json
import time

# Credentials
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "sk_9af95a2fca8ea120a514561389ef270c6e3c2235b3da347a")
ELEVEN_LABS_AGENT_ID = os.getenv("ELEVEN_LABS_AGENT_ID", "agent_2601k6rm4bjae2z9amfm5w1y6aps")  # Current working agent
PHONE_NUMBER_ID = "phnum_4801k6sa89eqfpnsfjsxbr40phen"  # From diagnostics
TEST_PHONE_NUMBER = "+13473580012"

# Test invoice data
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

def initiate_outbound_call(destination_number: str, variables: dict):
    """Initiate an outbound call using the CORRECT ElevenLabs Twilio API endpoint"""
    print(f"\n📞 Initiating outbound call...")
    print(f"   Agent ID: {ELEVEN_LABS_AGENT_ID}")
    print(f"   Phone Number ID: {PHONE_NUMBER_ID}")
    print(f"   To: {destination_number}")
    
    # THE CORRECT ENDPOINT!
    url = "https://api.elevenlabs.io/v1/convai/twilio/outbound-call"
    
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    # THE CORRECT PAYLOAD STRUCTURE!
    payload = {
        "agent_id": ELEVEN_LABS_AGENT_ID,
        "agent_phone_number_id": PHONE_NUMBER_ID,  # This was the missing piece!
        "to_number": destination_number,
        "conversation_initiation_client_data": {
            "dynamic_variables": variables  # Variables go inside this object!
        }
    }
    
    print(f"\n📋 Request Details:")
    print(f"   URL: {url}")
    print(f"   Payload structure:")
    print(json.dumps(payload, indent=2)[:500] + "...")
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload, headers=headers)
            
            print(f"\n📊 Response:")
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code in [200, 201]:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2)}")
                
                call_id = data.get('call_id', 'N/A')
                conversation_id = data.get('conversation_id', 'N/A')
                
                print(f"\n✅ CALL INITIATED SUCCESSFULLY!")
                print(f"   Call ID: {call_id}")
                print(f"   Conversation ID: {conversation_id}")
                print(f"   Status: {data.get('status', 'N/A')}")
                
                print(f"\n📱 Your phone ({destination_number}) should ring shortly!")
                print(f"\n💡 Expected behavior:")
                print(f"   - Donna will say: 'Hi, this is Donna and I am calling from Pixamp Inc...'")
                print(f"   - She will mention: Amazon Web Services")
                print(f"   - She will reference invoice: INV-2024-12345")
                print(f"   - Amount: $1,250.00")
                
                if conversation_id != 'N/A':
                    print(f"\n🔗 View conversation:")
                    print(f"   https://elevenlabs.io/app/conversational-ai/conversations/{conversation_id}")
                
                return data
            else:
                print(f"\n❌ Failed to initiate call")
                print(f"   Response: {response.text}")
                
                if response.status_code == 404:
                    print(f"\n💡 Still getting 404? Possible issues:")
                    print(f"   - Agent may need Twilio integration enabled")
                    print(f"   - Phone number may not be properly linked")
                    print(f"   - Account may not have outbound calling permissions")
                elif response.status_code == 401:
                    print(f"\n💡 401 Unauthorized:")
                    print(f"   - Check your API key")
                elif response.status_code == 400:
                    print(f"\n💡 400 Bad Request:")
                    print(f"   - Check phone number format (E.164)")
                    print(f"   - Verify agent_phone_number_id is correct")
                
                return None
                
    except Exception as e:
        print(f"❌ Error initiating call: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("=" * 80)
    print("🎯 End-to-End Outbound Call Test (CORRECT ENDPOINT)")
    print("=" * 80)
    
    # Parse command line arguments
    destination = TEST_PHONE_NUMBER
    if len(sys.argv) > 1:
        destination = sys.argv[1]
        if not destination.startswith('+'):
            destination = f"+{destination}"
    
    print(f"\n📋 Test Configuration:")
    print(f"   Destination: {destination}")
    print(f"   Customer: {TEST_INVOICE_DATA['customer_org']}")
    print(f"   Vendor: {TEST_INVOICE_DATA['vendor__legal_name']}")
    print(f"   Invoice: {TEST_INVOICE_DATA['email__invoice_number']}")
    print(f"   Amount: {TEST_INVOICE_DATA['email__amount']}")
    
    # Initiate the call
    result = initiate_outbound_call(destination, TEST_INVOICE_DATA)
    
    if result:
        print("\n" + "=" * 80)
        print("✅ TEST SUCCESSFUL!")
        print("=" * 80)
        print(f"\n📞 Answer your phone to speak with Donna!")
        
        # Wait a bit and check status if we have a conversation ID
        conversation_id = result.get('conversation_id')
        if conversation_id:
            print(f"\n⏳ Waiting 5 seconds for call to connect...")
            time.sleep(5)
            
            # Could add status check here if needed
            print(f"\n💡 After the call, review:")
            print(f"   1. Call transcript in ElevenLabs dashboard")
            print(f"   2. Verify dynamic variables were substituted")
            print(f"   3. Check call quality and flow")
    else:
        print("\n" + "=" * 80)
        print("❌ TEST FAILED")
        print("=" * 80)
        print(f"\n📋 Next steps:")
        print(f"   1. Check diagnostics: python3 diagnose_elevenlabs_api.py")
        print(f"   2. Verify phone number setup in dashboard")
        print(f"   3. Try dashboard method as fallback")
        sys.exit(1)
