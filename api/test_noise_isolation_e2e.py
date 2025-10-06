"""
Noise Isolation End-to-End Call Test

This test makes an actual phone call to verify the noise isolation feature works
during live conversations. It tests the full integration of the voice_isolator tool
within an ElevenLabs conversation.

Prerequisites:
- Unit test must pass first (python3 test_noise_isolation.py)
- ElevenLabs agent must be configured with voice_isolator tool
- Twilio phone number must be properly linked

Test Flow:
1. Verify voice_isolator tool is available in agent config
2. Initiate outbound call using ElevenLabs API
3. During the call, the agent can use voice_isolator tool if needed
4. Verify call completes successfully
"""

import os
import sys
import httpx
import json
import time

# Credentials
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "sk_9af95a2fca8ea120a514561389ef270c6e3c2235b3da347a")
ELEVEN_LABS_AGENT_ID = os.getenv("ELEVEN_LABS_AGENT_ID", "agent_2601k6rm4bjae2z9amfm5w1y6aps")
PHONE_NUMBER_ID = "phnum_4801k6sa89eqfpnsfjsxbr40phen"
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

def verify_voice_isolator_in_agent():
    """Verify the agent has the voice_isolator tool configured"""
    print("\n🔍 Verifying voice_isolator tool is in agent configuration...")
    
    config_path = "/Users/voyager/Documents/GitHub/donna/agent/agent_configs/dev/donna-billing-verifier.json"
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        tools = config.get('conversation_config', {}).get('agent', {}).get('prompt', {}).get('tools', [])
        
        voice_isolator = None
        for tool in tools:
            if tool.get('name') == 'voice_isolator':
                voice_isolator = tool
                break
        
        if voice_isolator:
            print(f"   ✅ voice_isolator tool found in agent config")
            print(f"   📋 Tool: {voice_isolator.get('name')}")
            print(f"   🔗 API: {voice_isolator.get('api_schema', {}).get('url', 'N/A')}")
            return True
        else:
            print(f"   ❌ voice_isolator tool NOT found in agent config")
            print(f"   Available tools: {[t.get('name') for t in tools]}")
            return False
    except Exception as e:
        print(f"   ❌ Error checking configuration: {str(e)}")
        return False

def initiate_test_call(destination_number: str, variables: dict):
    """Initiate an outbound call to test noise isolation"""
    print(f"\n📞 Initiating test call with noise isolation feature...")
    print(f"   Agent ID: {ELEVEN_LABS_AGENT_ID}")
    print(f"   Phone Number ID: {PHONE_NUMBER_ID}")
    print(f"   To: {destination_number}")
    print(f"   Test Case: {variables['case_id']}")
    
    url = "https://api.elevenlabs.io/v1/convai/twilio/outbound-call"
    
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "agent_id": ELEVEN_LABS_AGENT_ID,
        "agent_phone_number_id": PHONE_NUMBER_ID,
        "to_number": destination_number,
        "conversation_initiation_client_data": {
            "dynamic_variables": variables
        }
    }
    
    print(f"\n📋 Request Details:")
    print(f"   URL: {url}")
    print(f"   Case ID: {variables['case_id']}")
    print(f"   Vendor: {variables['vendor__legal_name']}")
    print(f"   Invoice: {variables['email__invoice_number']}")
    
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
                
                print(f"\n📱 Your phone ({destination_number}) should ring shortly!")
                print(f"\n💡 Test Instructions:")
                print(f"   1. Answer the phone when it rings")
                print(f"   2. Listen to Donna's introduction")
                print(f"   3. Try speaking with background noise")
                print(f"   4. The voice_isolator tool should help clean audio if needed")
                print(f"   5. Complete the conversation naturally")
                
                print(f"\n🎯 What to Verify:")
                print(f"   ✓ Call connects successfully")
                print(f"   ✓ Donna mentions: {variables['vendor__legal_name']}")
                print(f"   ✓ Invoice reference: {variables['email__invoice_number']}")
                print(f"   ✓ Audio quality is good (noise isolation working)")
                print(f"   ✓ Conversation flows naturally")
                
                if conversation_id != 'N/A':
                    print(f"\n🔗 View conversation details:")
                    print(f"   https://elevenlabs.io/app/conversational-ai/conversations/{conversation_id}")
                    print(f"\n   In the dashboard you can:")
                    print(f"   - Review the transcript")
                    print(f"   - Check if voice_isolator tool was used")
                    print(f"   - Verify audio quality metrics")
                
                return {
                    "success": True,
                    "call_id": call_id,
                    "conversation_id": conversation_id,
                    "data": data
                }
            else:
                print(f"\n❌ Failed to initiate call")
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
                
    except Exception as e:
        print(f"❌ Error initiating call: {e}")
        import traceback
        traceback.print_exc()
        return None

def monitor_conversation(conversation_id: str, duration: int = 60):
    """
    Monitor the conversation for a specified duration
    This is optional - mainly for automated testing
    """
    print(f"\n⏳ Monitoring conversation for {duration} seconds...")
    print(f"   (You can safely interrupt this with Ctrl+C)")
    
    try:
        for i in range(duration):
            time.sleep(1)
            if (i + 1) % 10 == 0:
                print(f"   ... {i + 1}s elapsed")
    except KeyboardInterrupt:
        print(f"\n⏸️  Monitoring interrupted by user")

if __name__ == "__main__":
    print("=" * 80)
    print("🎯 NOISE ISOLATION END-TO-END CALL TEST")
    print("=" * 80)
    
    # Parse command line arguments
    destination = TEST_PHONE_NUMBER
    if len(sys.argv) > 1:
        destination = sys.argv[1]
        if not destination.startswith('+'):
            destination = f"+{destination}"
    
    print(f"\n📋 Test Configuration:")
    print(f"   Test Case: Noise Isolation Feature")
    print(f"   Destination: {destination}")
    print(f"   Customer: {TEST_INVOICE_DATA['customer_org']}")
    print(f"   Vendor: {TEST_INVOICE_DATA['vendor__legal_name']}")
    print(f"   Invoice: {TEST_INVOICE_DATA['email__invoice_number']}")
    
    # Step 1: Verify voice_isolator is configured
    print("\n" + "=" * 80)
    print("STEP 1: Verify Voice Isolator Configuration")
    print("=" * 80)
    
    if not verify_voice_isolator_in_agent():
        print("\n❌ TEST FAILED: voice_isolator tool not found in agent configuration")
        print("\n💡 Fix:")
        print("   - Ensure agent/agent_configs/dev/donna-billing-verifier.json contains voice_isolator tool")
        print("   - Run: python3 test_noise_isolation.py (unit test) first")
        sys.exit(1)
    
    # Step 2: Initiate the call
    print("\n" + "=" * 80)
    print("STEP 2: Initiate Test Call")
    print("=" * 80)
    
    result = initiate_test_call(destination, TEST_INVOICE_DATA)
    
    if not result:
        print("\n" + "=" * 80)
        print("❌ TEST FAILED: Could not initiate call")
        print("=" * 80)
        print("\n💡 Troubleshooting:")
        print("   1. Check API credentials are correct")
        print("   2. Verify phone number is properly configured")
        print("   3. Check agent ID is valid")
        print("   4. Review error messages above")
        sys.exit(1)
    
    # Step 3: Monitor (optional)
    print("\n" + "=" * 80)
    print("STEP 3: Call In Progress")
    print("=" * 80)
    
    conversation_id = result.get('conversation_id')
    
    print(f"\n✅ Call has been initiated!")
    print(f"\n📱 Please answer your phone and complete the test conversation.")
    print(f"\n⏱️  The test will wait for 2 minutes...")
    print(f"   (Press Ctrl+C to skip waiting)")
    
    try:
        monitor_conversation(conversation_id, duration=120)
    except KeyboardInterrupt:
        print(f"\n⏭️  Skipping wait...")
    
    # Step 4: Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    print(f"\n✅ END-TO-END TEST COMPLETED!")
    print(f"\n📋 Results:")
    print(f"   ✓ voice_isolator tool is configured in agent")
    print(f"   ✓ Call was initiated successfully")
    print(f"   ✓ Conversation ID: {conversation_id}")
    
    print(f"\n🔍 Manual Verification Required:")
    print(f"   1. Did the call connect?")
    print(f"   2. Was audio quality good?")
    print(f"   3. Did Donna handle background noise well?")
    print(f"   4. Was the conversation natural?")
    
    print(f"\n🔗 Review in Dashboard:")
    if conversation_id != 'N/A':
        print(f"   https://elevenlabs.io/app/conversational-ai/conversations/{conversation_id}")
    
    print(f"\n💡 What to Check in Dashboard:")
    print(f"   - Conversation transcript")
    print(f"   - Tool usage logs (was voice_isolator called?)")
    print(f"   - Audio quality metrics")
    print(f"   - Any errors or warnings")
    
    print("\n" + "=" * 80)
    print("✅ TEST EXECUTION COMPLETED")
    print("=" * 80)
    print(f"\nPlease review the conversation in the dashboard to verify")
    print(f"the noise isolation feature worked as expected.")
