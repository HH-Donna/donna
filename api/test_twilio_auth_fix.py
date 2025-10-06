"""
Fixed: Put API key in WebSocket URL for authentication
"""

from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream
import os

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "+1234567890")

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVEN_LABS_AGENT_ID = os.getenv("ELEVEN_LABS_AGENT_ID")

TEST_PHONE_NUMBER = os.getenv("TEST_PHONE_NUMBER", "+1234567890")

print("=" * 70)
print("🎯 Fixed WebSocket Authentication Test")
print("=" * 70)

# Initialize Twilio client
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Create TwiML - Put API key in URL for authentication!
twiml_response = VoiceResponse()
connect = twiml_response.connect()

# Build WebSocket URL with authentication
ws_url = (
    f'wss://api.elevenlabs.io/v1/convai/conversation/twilio'
    f'?agent_id={ELEVEN_LABS_AGENT_ID}'
    f'&api_key={ELEVENLABS_API_KEY}'
)

stream = Stream(url=ws_url)

# Now add dynamic variables as custom parameters
stream.parameter(name='customer_org', value='Pixamp Inc')
stream.parameter(name='vendor__legal_name', value='Amazon Web Services')
stream.parameter(name='email__invoice_number', value='INV-2024-12345')
stream.parameter(name='email__amount', value='$1,250.00')
stream.parameter(name='case_id', value='TEST-001')

connect.append(stream)

twiml_str = str(twiml_response)
print(f"\n📄 TwiML (API key in URL for auth):")
# Redact API key for display
display_twiml = twiml_str.replace(ELEVENLABS_API_KEY, "***REDACTED***")
print(display_twiml)

try:
    print(f"\n📞 Initiating call...")
    
    call = client.calls.create(
        from_=TWILIO_PHONE_NUMBER,
        to=TEST_PHONE_NUMBER,
        twiml=twiml_str
    )
    
    print(f"\n✅ Call initiated!")
    print(f"  Call SID: {call.sid}")
    print(f"  Status: {call.status}")
    
    print(f"\n📱 Your phone should ring!")
    print(f"\n🔗 Monitor:")
    print(f"  https://console.twilio.com/us1/monitor/logs/calls/{call.sid}")
    
    import time
    time.sleep(3)
    
    call_updated = client.calls(call.sid).fetch()
    print(f"\n⏳ Status after 3s: {call_updated.status}")
    
    if call_updated.status == 'failed':
        print(f"❌ Failed: {call_updated.error_message}")
    elif call_updated.status in ['queued', 'ringing', 'in-progress']:
        print(f"✅ Call active! Let it ring for 6 seconds...")
    
except Exception as e:
    print(f"\n❌ Error: {e}")

print("\n" + "=" * 70)
