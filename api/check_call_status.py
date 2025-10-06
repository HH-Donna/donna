"""
Check Twilio call status and errors
"""

from twilio.rest import Client
import os

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

# Last call SID
CALL_SID = "CAa709decb99869040e1073eda8d9952d0"

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

print("=" * 70)
print("🔍 Checking Call Status")
print("=" * 70)

try:
    call = client.calls(CALL_SID).fetch()
    
    print(f"\n📞 Call Details:")
    print(f"  Status: {call.status}")
    print(f"  Duration: {call.duration} seconds")
    print(f"  From: {call.from_formatted}")
    print(f"  To: {call.to_formatted}")
    print(f"  Direction: {call.direction}")
    print(f"  Answered By: {call.answered_by}")
    
    if call.status == 'failed':
        print(f"\n❌ Call Failed!")
        print(f"  Error Code: {call.error_code}")
        print(f"  Error Message: {call.error_message}")
    elif call.status == 'completed':
        print(f"\n✅ Call Completed!")
        if call.duration == '0' or (call.duration and int(call.duration) < 2):
            print(f"  ⚠️ But duration was very short - likely an error")
    
    # Check for events
    print(f"\n📋 Checking call events...")
    events = client.calls(CALL_SID).events.list()
    
    if events:
        print(f"  Found {len(events)} events:")
        for event in events:
            print(f"    - {event.name}")
    
except Exception as e:
    print(f"\n❌ Error: {e}")

print("\n" + "=" * 70)
print("\n💡 Common issue: WebSocket connection failed")
print("   This means the WebSocket URL or auth is incorrect.")
print("=" * 70)
