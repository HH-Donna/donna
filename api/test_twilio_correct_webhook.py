"""
Proper Twilio + ElevenLabs Integration using Native Webhook

When you import a Twilio number into ElevenLabs, it automatically configures
a webhook URL. We need to use that instead of trying to connect directly
to the WebSocket.
"""

from twilio.rest import Client
import os

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "+1234567890")
TEST_PHONE_NUMBER = os.getenv("TEST_PHONE_NUMBER", "+1234567890")

ELEVENLABS_AGENT_ID = os.getenv("ELEVEN_LABS_AGENT_ID")

print("=" * 70)
print("🎯 Twilio Native Integration Test")
print("=" * 70)

# Check the Twilio number configuration
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

print("\n🔍 Checking Twilio number configuration...")

try:
    # Get phone number details
    phone_numbers = client.incoming_phone_numbers.list(
        phone_number=TWILIO_PHONE_NUMBER
    )
    
    if phone_numbers:
        number = phone_numbers[0]
        print(f"\n📞 Phone Number: {number.phone_number}")
        print(f"  SID: {number.sid}")
        print(f"  Friendly Name: {number.friendly_name}")
        print(f"\n📋 Voice Configuration:")
        print(f"  Voice URL: {number.voice_url}")
        print(f"  Voice Method: {number.voice_method}")
        print(f"  Voice Fallback URL: {number.voice_fallback_url}")
        print(f"  Status Callback: {number.status_callback}")
        
        if not number.voice_url:
            print(f"\n❌ PROBLEM FOUND!")
            print(f"  Voice URL is not configured!")
            print(f"\n💡 SOLUTION:")
            print(f"  The ElevenLabs import should have set this automatically.")
            print(f"  The Voice URL should point to an ElevenLabs webhook.")
            print(f"\n  Expected format:")
            print(f"  https://api.elevenlabs.io/v1/convai/twilio/inbound/{ELEVENLABS_AGENT_ID}")
            print(f"  OR similar ElevenLabs webhook URL")
            print(f"\n🔧 TO FIX:")
            print(f"  1. Go to ElevenLabs dashboard")
            print(f"  2. Phone Numbers tab")
            print(f"  3. Re-import or reconfigure the Twilio number")
            print(f"  4. ElevenLabs should auto-configure the webhook")
        else:
            print(f"\n✅ Voice URL is configured!")
            print(f"\n📞 Now testing call...")
            
            # For outbound calls, we need to use ElevenLabs' outbound endpoint
            # The voice_url is for inbound calls
            print(f"\n💡 NOTE:")
            print(f"  The voice_url configured is for INBOUND calls")
            print(f"  For OUTBOUND calls, we need a different approach")
            print(f"\n  Either:")
            print(f"  1. Use ElevenLabs dashboard 'Make Outbound Call' button")
            print(f"  2. Use ElevenLabs' native outbound API (if available)")
            print(f"  3. Create our own webhook server that bridges Twilio <> ElevenLabs")
        
    else:
        print(f"\n❌ Phone number {TWILIO_PHONE_NUMBER} not found in Twilio account!")
        print(f"  Make sure the number is active")
        
except Exception as e:
    print(f"\n❌ Error: {e}")

print("\n" + "=" * 70)
print("\n🎯 DIAGNOSIS:")
print("=" * 70)
print("""
The issue: Direct WebSocket connections aren't supported this way.

ElevenLabs Native Integration works like this:

FOR INBOUND CALLS:
1. ElevenLabs sets a webhook URL on your Twilio number
2. When someone calls, Twilio hits that webhook
3. ElevenLabs responds with TwiML to connect the call
4. Works automatically!

FOR OUTBOUND CALLS:
Option 1: ElevenLabs Dashboard (Easiest)
  - Use the "Make Outbound Call" button in ElevenLabs
  - This handles everything automatically

Option 2: Create Bridge Server (Advanced)
  - Your server receives call request
  - Initiates Twilio call to a webhook YOU control
  - Your webhook connects to ElevenLabs WebSocket
  - Requires running a server with WebSocket support

Option 3: Wait for ElevenLabs Outbound API
  - The public outbound call API may not be available yet
  - Check ElevenLabs documentation for updates

RECOMMENDED: Use the ElevenLabs dashboard for testing outbound calls.
""")
