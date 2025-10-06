"""
Direct Outbound Call Test

This script attempts to initiate an outbound call using ElevenLabs' signed-out conversation API.
This is an alternative approach that may work without explicitly importing the Twilio number first.
"""

import os
import sys
import httpx
import json

# Credentials
ELEVENLABS_API_KEY = "sk_9af95a2fca8ea120a514561389ef270c6e3c2235b3da347a"
ELEVEN_LABS_AGENT_ID = "agent_2601k6rm4bjae2z9amfm5w1y6aps"
TEST_PHONE_NUMBER = "+13473580012"

# Test invoice data
TEST_DATA = {
    "case_id": "TEST-001",
    "customer_org": "Pixamp Inc",
    "user__company_name": "Pixamp Inc",
    "vendor__legal_name": "Amazon Web Services",
    "email__vendor_name": "AWS",
    "email__invoice_number": "INV-2024-12345",
    "email__amount": "$1,250.00",
    "email__due_date": "2024-10-15",
    "email__billing_address": "123 Main St, San Francisco, CA 94105",
    "email__contact_email": "billing@example.com",
    "email__contact_phone": "+1-800-555-0100",
    "official_canonical_domain": "aws.amazon.com",
    "official_canonical_phone": "+1-206-266-4064",
    "official_canonical_billing_address": "410 Terry Ave N, Seattle, WA 98109",
    "local__phone": "+1-206-266-4064",
    "db__official_phone": "+1-206-266-4064",
    "online__phone": "+1-206-266-4064",
    "user__full_name": "John Doe",
    "user__phone": "+1-555-123-4567",
    "user__account_id": "ACCT-9876543210",
    "user__acct_last4": "3210",
    "policy_recording_notice": "This call may be recorded for quality assurance purposes.",
}

def test_signed_out_call():
    """
    Try to initiate an outbound call using the signed-out conversation endpoint.
    This endpoint is typically used for web widget conversations but may support phone calls.
    """
    print("=" * 70)
    print("🎯 Testing ElevenLabs Outbound Call (Direct Method)")
    print("=" * 70)
    
    destination = TEST_PHONE_NUMBER
    if len(sys.argv) > 1:
        destination = sys.argv[1]
        if not destination.startswith('+'):
            destination = f"+{destination}"
    
    print(f"\n📋 Configuration:")
    print(f"   Agent ID: {ELEVEN_LABS_AGENT_ID}")
    print(f"   Destination: {destination}")
    print(f"   Vendor: {TEST_DATA['vendor__legal_name']}")
    print(f"   Invoice: {TEST_DATA['email__invoice_number']}")
    print(f"   Amount: {TEST_DATA['email__amount']}")
    
    # Try the signed-out conversation endpoint
    url = "https://api.elevenlabs.io/v1/convai/conversation"
    
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    # Method 1: Try with phone_number parameter
    payload_phone = {
        "agent_id": ELEVEN_LABS_AGENT_ID,
        "mode": "phone",
        "phone_number": destination,
        "dynamic_variables": TEST_DATA
    }
    
    print(f"\n📞 Attempting to initiate call...")
    print(f"   Method: Signed-out conversation with phone mode")
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload_phone, headers=headers)
            
            print(f"\n📊 Response Status: {response.status_code}")
            print(f"📄 Response Body:")
            try:
                data = response.json()
                print(json.dumps(data, indent=2))
                
                if response.status_code == 200 or response.status_code == 201:
                    print(f"\n✅ Call initiated successfully!")
                    conversation_id = data.get('conversation_id')
                    if conversation_id:
                        print(f"   Conversation ID: {conversation_id}")
                        print(f"   View: https://elevenlabs.io/app/conversational-ai/conversations/{conversation_id}")
                    
                    print(f"\n📱 Your phone should ring shortly!")
                    return True
                else:
                    print(f"\n⚠️  Unexpected response")
                    return False
                    
            except Exception as e:
                print(response.text)
                print(f"\n❌ Error parsing response: {e}")
                return False
                
    except Exception as e:
        print(f"\n❌ Request failed: {e}")
        return False

def print_instructions():
    """Print manual setup instructions"""
    print("\n" + "=" * 70)
    print("📚 Manual Setup Required")
    print("=" * 70)
    print(f"""
If the API method doesn't work, please follow these steps:

1️⃣  **Import Twilio Number via Dashboard**
   
   a. Go to: https://elevenlabs.io/app/conversational-ai
   b. Click "Phone Numbers" tab
   c. Click "Import Phone Number" or "Add Phone Number"
   d. Select "Twilio" as provider
   e. Fill in:
      - Label: "Donna Billing Verifier"
      - Phone Number: YOUR_TWILIO_PHONE_NUMBER
      - Twilio Account SID: YOUR_TWILIO_ACCOUNT_SID
      - Twilio Auth Token: YOUR_TWILIO_AUTH_TOKEN
   f. Assign Agent: Select "Donna"
   g. Save

2️⃣  **Test Inbound Call**
   
   Call +18887064372 from your phone (+13473580012)
   Donna should answer and greet you!

3️⃣  **Test Outbound Call (Dashboard)**
   
   a. In Phone Numbers tab, find +18887064372
   b. Click "Outbound Call" button
   c. Select "Donna" agent
   d. Enter destination: +13473580012
   e. Click "Send Test Call"
   f. Answer your phone!

4️⃣  **Test Dynamic Variables**
   
   During the call, listen for:
   - "Pixamp Inc" (should substitute {{customer_org}})
   - "Amazon Web Services" (should substitute {{vendor__legal_name}})
   - "INV-2024-12345" (should substitute {{email__invoice_number}})

5️⃣  **Review Call History**
   
   - Go to Calls History in dashboard
   - Find your test call
   - Review transcript
   - Verify dynamic variables were substituted correctly

📖 For detailed instructions, see:
   {os.path.dirname(os.path.abspath(__file__))}/../agent/TWILIO_INTEGRATION_GUIDE.md
""")

if __name__ == "__main__":
    success = test_signed_out_call()
    
    if not success:
        print(f"\n⚠️  API method may not be available or requires dashboard setup first.")
        print_instructions()
    
    print("\n" + "=" * 70)
