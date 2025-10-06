"""
CORRECT Implementation: ElevenLabs + Twilio Outbound Call

Based on working call: CA50b6311ad90d5f58437dd8e433eac214

Flow:
1. Create conversation via ElevenLabs API
2. Get conversation_id
3. Initiate Twilio call with conversation_id in WebSocket
"""

from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream
import httpx
import os

# Credentials
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "+1234567890")

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVEN_LABS_AGENT_ID = os.getenv("ELEVEN_LABS_AGENT_ID")

TEST_PHONE_NUMBER = os.getenv("TEST_PHONE_NUMBER", "+1234567890")

# Test data with dynamic variables
dynamic_variables = {
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
print("🎯 Correct ElevenLabs + Twilio Flow")
print("=" * 70)

print("\n📋 Step 1: Create conversation via ElevenLabs API...")

try:
    # Step 1: Create conversation
    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            "https://api.elevenlabs.io/v1/convai/conversation",
            headers={
                "xi-api-key": ELEVENLABS_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "agent_id": ELEVEN_LABS_AGENT_ID,
                "dynamic_variables": dynamic_variables
            }
        )
        
        print(f"  Status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            conversation_id = data.get('conversation_id')
            
            if conversation_id:
                print(f"  ✅ Conversation created: {conversation_id}")
            else:
                print(f"  ⚠️  Response: {data}")
                print(f"  Trying to extract conversation_id from response...")
                # Sometimes the structure might be different
                conversation_id = data.get('id') or data.get('conversationId')
                
            if not conversation_id:
                print(f"  ❌ No conversation_id in response!")
                print(f"  Full response: {data}")
                exit(1)
                
        else:
            print(f"  ❌ Failed to create conversation")
            print(f"  Response: {response.text}")
            exit(1)
    
    # Step 2: Create TwiML with conversation_id
    print(f"\n📋 Step 2: Create TwiML with conversation_id...")
    
    twiml_response = VoiceResponse()
    connect = twiml_response.connect()
    
    # Use the CORRECT WebSocket URL format from the working call
    stream = Stream(url='wss://api.us.elevenlabs.io/v1/convai/conversation')
    stream.parameter(name='conversation_id', value=conversation_id)
    
    connect.append(stream)
    twiml_str = str(twiml_response)
    
    print(f"  ✅ TwiML created")
    print(f"  WebSocket: wss://api.us.elevenlabs.io/v1/convai/conversation")
    print(f"  Conversation ID: {conversation_id}")
    
    # Step 3: Initiate Twilio call
    print(f"\n📋 Step 3: Initiate Twilio call...")
    
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    
    call = twilio_client.calls.create(
        from_=TWILIO_PHONE_NUMBER,
        to=TEST_PHONE_NUMBER,
        twiml=twiml_str
    )
    
    print(f"\n✅ CALL INITIATED SUCCESSFULLY!")
    print(f"  Call SID: {call.sid}")
    print(f"  Status: {call.status}")
    print(f"  From: {TWILIO_PHONE_NUMBER}")
    print(f"  To: {TEST_PHONE_NUMBER}")
    
    print(f"\n📱 Your phone should ring!")
    print(f"\n🎤 When you answer, Donna will say:")
    print(f'   "Hi, this is Donna and I am calling from Pixamp Inc..."')
    
    print(f"\n🔗 Monitor this call:")
    print(f"  Twilio: https://console.twilio.com/us1/monitor/logs/calls/{call.sid}")
    print(f"  ElevenLabs: https://elevenlabs.io/app/conversational-ai/conversations/{conversation_id}")
    
    import time
    time.sleep(3)
    
    call_updated = twilio_client.calls(call.sid).fetch()
    print(f"\n⏳ Status after 3s: {call_updated.status}")
    
    if call_updated.status == 'failed':
        print(f"  ❌ Call failed: {call_updated.error_message}")
    elif call_updated.status in ['queued', 'ringing', 'in-progress']:
        print(f"  ✅ Call is active!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("🎉 This is the CORRECT implementation!")
print("=" * 70)
