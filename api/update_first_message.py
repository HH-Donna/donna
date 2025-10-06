"""
Update the agent's first_message directly via API

The agents CLI sync isn't updating the first_message field, so we'll do it directly.
"""

import os
import httpx

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "sk_9af95a2fca8ea120a514561389ef270c6e3c2235b3da347a")
AGENT_ID = "agent_2601k6rm4bjae2z9amfm5w1y6aps"

FIRST_MESSAGE = (
    "Hi, this is Donna calling from {{customer_org}} about case {{case_id}}. "
    "{{policy_recording_notice}} I'm calling to verify an invoice we received that "
    "appears to come from {{email__vendor_name}}—invoice {{email__invoice_number}} "
    "for {{email__amount}}, due {{email__due_date}}. Are you the right person to "
    "confirm whether this was issued by your billing department?"
)

def main():
    print("=" * 70)
    print("🔧 Updating Agent First Message via API")
    print("=" * 70)
    
    url = f"https://api.elevenlabs.io/v1/convai/agents/{AGENT_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    # Update payload - only updating the first_message
    payload = {
        "conversation_config": {
            "agent": {
                "first_message": FIRST_MESSAGE
            }
        }
    }
    
    print(f"\n📝 Agent ID: {AGENT_ID}")
    print(f"\n📋 New First Message ({len(FIRST_MESSAGE)} chars):")
    print(f"   {FIRST_MESSAGE}")
    
    print(f"\n🚀 Sending PATCH request...")
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.patch(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                print(f"\n✅ SUCCESS! Agent updated successfully!")
                print(f"   Status Code: {response.status_code}")
                
                # Verify the update
                print(f"\n🔍 Verifying update...")
                verify_response = client.get(url, headers=headers)
                if verify_response.status_code == 200:
                    data = verify_response.json()
                    first_msg = data.get('conversation_config', {}).get('agent', {}).get('first_message', '')
                    
                    if first_msg == FIRST_MESSAGE:
                        print(f"✅ VERIFIED! First message is correctly set.")
                    else:
                        print(f"⚠️  WARNING: First message may not have updated correctly.")
                        print(f"   Expected: {FIRST_MESSAGE[:50]}...")
                        print(f"   Got: {first_msg[:50]}...")
                else:
                    print(f"⚠️  Could not verify: {verify_response.status_code}")
            else:
                print(f"\n❌ FAILED to update agent")
                print(f"   Status Code: {response.status_code}")
                print(f"   Response: {response.text}")
                return 1
                
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    print("\n" + "=" * 70)
    print("✨ Agent update complete!")
    print("=" * 70)
    print("\n💡 Next: Run test_outbound_call.py to test the first message")
    
    return 0

if __name__ == "__main__":
    exit(main())
