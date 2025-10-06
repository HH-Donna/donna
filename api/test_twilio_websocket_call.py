"""
Proper Twilio + ElevenLabs WebSocket Integration Test

This uses Twilio's API to initiate a call and connects it to ElevenLabs via WebSocket.
"""

from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream
import os

# Credentials
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "+1234567890")

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVEN_LABS_AGENT_ID = os.getenv("ELEVEN_LABS_AGENT_ID")

TEST_PHONE_NUMBER = os.getenv("TEST_PHONE_NUMBER", "+1234567890")

print("=" * 70)
print("🎯 Twilio + ElevenLabs WebSocket Test")
print("=" * 70)

print("\n📋 Configuration:")
print(f"  From: {TWILIO_PHONE_NUMBER}")
print(f"  To: {TEST_PHONE_NUMBER}")
print(f"  Agent: {ELEVEN_LABS_AGENT_ID}")

# Initialize Twilio client
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Create TwiML that connects to ElevenLabs via WebSocket
twiml_response = VoiceResponse()
connect = twiml_response.connect()

# ElevenLabs WebSocket endpoint for Twilio
# This is the correct endpoint format for ElevenLabs Conversational AI
stream = Stream(url=f'wss://api.elevenlabs.io/v1/convai/conversation?agent_id={ELEVEN_LABS_AGENT_ID}')

# Add ElevenLabs API key as parameter
stream.parameter(name='api_key', value=ELEVENLABS_API_KEY)

# Add dynamic variables as parameters
stream.parameter(name='customer_org', value='Pixamp Inc')
stream.parameter(name='vendor__legal_name', value='Amazon Web Services')
stream.parameter(name='email__invoice_number', value='INV-2024-12345')
stream.parameter(name='email__amount', value='$1,250.00')
stream.parameter(name='case_id', value='TEST-001')

connect.append(stream)

twiml_str = str(twiml_response)
print(f"\n📄 TwiML Response:")
print(twiml_str)

try:
    print(f"\n📞 Initiating call via Twilio...")
    
    call = client.calls.create(
        from_=TWILIO_PHONE_NUMBER,
        to=TEST_PHONE_NUMBER,
        twiml=twiml_str
    )
    
    print(f"\n✅ Call initiated successfully!")
    print(f"  Call SID: {call.sid}")
    print(f"  Status: {call.status}")
    print(f"  Direction: {call.direction}")
    
    print(f"\n📱 Your phone should ring shortly!")
    print(f"\n💡 Monitor this call:")
    print(f"  Twilio Console: https://console.twilio.com/us1/monitor/logs/calls/{call.sid}")
    print(f"  ElevenLabs Conversations: https://elevenlabs.io/app/conversational-ai/conversations")
    
    print(f"\n⏳ Checking call status...")
    import time
    time.sleep(3)
    
    # Fetch updated call status
    call_updated = client.calls(call.sid).fetch()
    print(f"  Updated Status: {call_updated.status}")
    
    if call_updated.status == 'failed':
        print(f"\n❌ Call failed!")
        print(f"  Error Code: {call_updated.error_code}")
        print(f"  Error Message: {call_updated.error_message}")
    elif call_updated.status in ['queued', 'ringing', 'in-progress']:
        print(f"\n✅ Call is active! Answer your phone!")
    
except Exception as e:
    print(f"\n❌ Error initiating call: {e}")
    print(f"\n💡 Common issues:")
    print(f"  1. Twilio account has no credits")
    print(f"  2. Phone number not verified (trial accounts)")
    print(f"  3. Twilio number not active")
    print(f"  Check: https://console.twilio.com/")

print("\n" + "=" * 70)
