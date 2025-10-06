"""
Simple Outbound Call Test - Using Agent Conversation API
"""

import httpx
import json

# Credentials
ELEVENLABS_API_KEY = "sk_9af95a2fca8ea120a514561389ef270c6e3c2235b3da347a"
ELEVEN_LABS_AGENT_ID = "agent_2601k6rm4bjae2z9amfm5w1y6aps"
TWILIO_PHONE_NUMBER = "+18887064372"
TEST_PHONE_NUMBER = "+13473580012"

# Test data
variables = {
    "case_id": "TEST-001",
    "customer_org": "Pixamp Inc",
    "user__company_name": "Pixamp Inc",
    "vendor__legal_name": "Amazon Web Services",
    "email__vendor_name": "AWS",
    "email__invoice_number": "INV-2024-12345",
    "email__amount": "$1,250.00",
    "email__due_date": "2024-10-15",
    "official_canonical_phone": "+1-206-266-4064",
}

print("=" * 70)
print("🎯 Simple Outbound Call Test")
print("=" * 70)
print(f"\nConfiguration:")
print(f"  Agent: {ELEVEN_LABS_AGENT_ID}")
print(f"  From: {TWILIO_PHONE_NUMBER}")
print(f"  To: {TEST_PHONE_NUMBER}")
print(f"  Invoice: {variables['email__invoice_number']}")

# Try the conversation/phone endpoint
url = "https://api.elevenlabs.io/v1/convai/conversation/phone"

headers = {
    "xi-api-key": ELEVENLABS_API_KEY,
    "Content-Type": "application/json"
}

payload = {
    "agent_id": ELEVEN_LABS_AGENT_ID,
    "from_phone_number": TWILIO_PHONE_NUMBER,
    "to_phone_number": TEST_PHONE_NUMBER,
    "dynamic_variables": variables
}

print(f"\n📞 Attempting call via: {url}")

try:
    with httpx.Client(timeout=30.0) as client:
        response = client.post(url, json=payload, headers=headers)
        
        print(f"\n📊 Response:")
        print(f"  Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"  Body: {json.dumps(data, indent=2)}")
            
            if response.status_code in [200, 201]:
                print(f"\n✅ SUCCESS! Call initiated!")
                print(f"\n📱 Your phone should ring shortly!")
                
                if 'conversation_id' in data:
                    conv_id = data['conversation_id']
                    print(f"\n🔗 View conversation:")
                    print(f"   https://elevenlabs.io/app/conversational-ai/conversations/{conv_id}")
            else:
                print(f"\n⚠️  Unexpected status code")
                
        except Exception as e:
            print(f"  Body (raw): {response.text}")
            
except Exception as e:
    print(f"\n❌ Error: {e}")

print("\n" + "=" * 70)
print("\n💡 If this doesn't work, use the dashboard method:")
print("   1. Go to https://elevenlabs.io/app/conversational-ai")
print("   2. Phone Numbers → NumberDonna → ••• → Make outbound call")
print("   3. Agent: Donna, To: +13473580012")
print("=" * 70)
