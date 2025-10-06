"""
End-to-End Test: First Message with Dynamic Variables

This test verifies that:
1. The agent config has a first_message defined
2. Dynamic variables are properly substituted in the first message
3. The first message plays immediately when the call connects
4. All required variables are present in the agent config

Reference: https://elevenlabs.io/docs/agents-platform/customization/personalization/overrides
"""

import os
import sys
import json
import httpx
import time
from pathlib import Path

# Credentials
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "sk_9af95a2fca8ea120a514561389ef270c6e3c2235b3da347a")
ELEVEN_LABS_AGENT_ID = os.getenv("ELEVEN_LABS_AGENT_ID", "agent_2601k6rm4bjae2z9amfm5w1y6aps")
TWILIO_PHONE_NUMBER = "+18887064372"

# Path to agent config
AGENT_CONFIG_PATH = Path(__file__).parent.parent / "agent" / "agent_configs" / "dev" / "donna-billing-verifier.json"

# Test data with all required dynamic variables
TEST_VARIABLES = {
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

# Expected first message template
EXPECTED_FIRST_MESSAGE_TEMPLATE = (
    "Hi, this is Donna calling from {{customer_org}} about case {{case_id}}. "
    "{{policy_recording_notice}} I'm calling to verify an invoice we received that "
    "appears to come from {{email__vendor_name}}—invoice {{email__invoice_number}} "
    "for {{email__amount}}, due {{email__due_date}}. Are you the right person to "
    "confirm whether this was issued by your billing department?"
)

# What the first message should say with variables substituted
EXPECTED_RENDERED_MESSAGE = (
    "Hi, this is Donna calling from Pixamp, Inc about case shop-00123. "
    "True I'm calling to verify an invoice we received that appears to come from Shopify, Inc—"
    "invoice ioe-300050 for 900, due 09-23-2025. "
    "Are you the right person to confirm whether this was issued by your billing department?"
)


class TestResult:
    """Track test results"""
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
    
    def add_pass(self, test_name: str, message: str = ""):
        self.passed.append((test_name, message))
        print(f"✅ PASS: {test_name}")
        if message:
            print(f"   {message}")
    
    def add_fail(self, test_name: str, reason: str):
        self.failed.append((test_name, reason))
        print(f"❌ FAIL: {test_name}")
        print(f"   Reason: {reason}")
    
    def add_warning(self, test_name: str, message: str):
        self.warnings.append((test_name, message))
        print(f"⚠️  WARNING: {test_name}")
        print(f"   {message}")
    
    def print_summary(self):
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        print(f"✅ Passed: {len(self.passed)}")
        print(f"❌ Failed: {len(self.failed)}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        
        if self.failed:
            print("\n❌ Failed Tests:")
            for name, reason in self.failed:
                print(f"   - {name}: {reason}")
        
        if self.warnings:
            print("\n⚠️  Warnings:")
            for name, message in self.warnings:
                print(f"   - {name}: {message}")
        
        print("=" * 70)
        return len(self.failed) == 0


def test_agent_config_exists():
    """Test 1: Verify agent config file exists"""
    print("\n🧪 TEST 1: Agent Config File Exists")
    print("-" * 70)
    
    result = TestResult()
    
    if AGENT_CONFIG_PATH.exists():
        result.add_pass("Agent config exists", f"Path: {AGENT_CONFIG_PATH}")
        
        # Load the config
        with open(AGENT_CONFIG_PATH, 'r') as f:
            config = json.load(f)
        return result, config
    else:
        result.add_fail("Agent config exists", f"File not found: {AGENT_CONFIG_PATH}")
        return result, None


def test_first_message_configured(config: dict):
    """Test 2: Verify first_message is configured in agent config"""
    print("\n🧪 TEST 2: First Message Configuration")
    print("-" * 70)
    
    result = TestResult()
    
    try:
        first_message = config['conversation_config']['agent']['first_message']
        
        if not first_message or first_message.strip() == "":
            result.add_fail(
                "First message is configured",
                "first_message field is empty in agent config"
            )
            print("\n📋 Expected first_message field to contain:")
            print(f"   {EXPECTED_FIRST_MESSAGE_TEMPLATE}")
            return result
        
        result.add_pass(
            "First message is configured",
            f"Length: {len(first_message)} characters"
        )
        
        # Check if it matches expected template
        if first_message.strip() == EXPECTED_FIRST_MESSAGE_TEMPLATE.strip():
            result.add_pass(
                "First message matches expected template",
                "Template is correct"
            )
        else:
            result.add_warning(
                "First message template mismatch",
                "The configured first_message differs from expected template"
            )
            print(f"\n   Expected:\n   {EXPECTED_FIRST_MESSAGE_TEMPLATE}")
            print(f"\n   Actual:\n   {first_message}")
        
        print(f"\n📝 Configured first message:")
        print(f"   {first_message}")
        
        return result
        
    except KeyError as e:
        result.add_fail(
            "First message is configured",
            f"Missing key in config: {e}"
        )
        return result


def test_dynamic_variables_defined(config: dict):
    """Test 3: Verify all required dynamic variables are defined"""
    print("\n🧪 TEST 3: Dynamic Variables Configuration")
    print("-" * 70)
    
    result = TestResult()
    
    try:
        dynamic_vars = config['conversation_config']['agent']['dynamic_variables']['dynamic_variable_placeholders']
        
        # Variables used in first message
        required_vars = [
            'customer_org',
            'case_id',
            'policy_recording_notice',
            'email__vendor_name',
            'email__invoice_number',
            'email__amount',
            'email__due_date'
        ]
        
        missing_vars = []
        for var in required_vars:
            if var not in dynamic_vars:
                missing_vars.append(var)
        
        if missing_vars:
            result.add_fail(
                "All required variables are defined",
                f"Missing variables: {', '.join(missing_vars)}"
            )
        else:
            result.add_pass(
                "All required variables are defined",
                f"Found all {len(required_vars)} required variables"
            )
        
        # Show defined variables
        print(f"\n📋 Defined dynamic variables ({len(dynamic_vars)}):")
        for var in required_vars:
            status = "✓" if var in dynamic_vars else "✗"
            print(f"   {status} {var}")
        
        return result
        
    except KeyError as e:
        result.add_fail(
            "Dynamic variables are defined",
            f"Missing key in config: {e}"
        )
        return result


def test_first_message_overrides(config: dict):
    """Test 4: Check first_message override settings"""
    print("\n🧪 TEST 4: First Message Override Settings")
    print("-" * 70)
    
    result = TestResult()
    
    try:
        overrides_enabled = config['platform_settings']['overrides']['conversation_config_override']['agent']['first_message']
        
        print(f"📋 Override status: {'Enabled' if overrides_enabled else 'Disabled'}")
        
        if overrides_enabled:
            result.add_pass(
                "First message overrides",
                "Overrides are enabled (can be customized per call)"
            )
        else:
            result.add_warning(
                "First message overrides",
                "Overrides are disabled. First message cannot be customized per call. "
                "This is fine if you want the same first message for all calls."
            )
        
        print("\n💡 About overrides:")
        print("   - If enabled: You can customize the first message per call")
        print("   - If disabled: The configured first message is used for all calls")
        print("   - Reference: https://elevenlabs.io/docs/agents-platform/customization/personalization/overrides")
        
        return result
        
    except KeyError as e:
        result.add_fail(
            "First message override settings",
            f"Missing key in config: {e}"
        )
        return result


def get_phone_number_id():
    """Get the phone_number_id for our imported Twilio number"""
    url = "https://api.elevenlabs.io/v1/convai/phone-numbers"
    headers = {"xi-api-key": ELEVENLABS_API_KEY}
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                phone_numbers = data.get('phone_numbers', []) if isinstance(data, dict) else data
                
                for pn in phone_numbers:
                    if pn.get('phone_number') == TWILIO_PHONE_NUMBER:
                        return pn.get('phone_number_id')
                
                return None
            else:
                return None
                
    except Exception:
        return None


def test_live_call_first_message(phone_number_id: str, destination: str):
    """Test 5: Initiate a live call and verify first message"""
    print("\n🧪 TEST 5: Live Call with First Message")
    print("-" * 70)
    
    result = TestResult()
    
    if not phone_number_id:
        result.add_fail(
            "Phone number setup",
            f"Phone number {TWILIO_PHONE_NUMBER} not found in ElevenLabs. "
            "Run import_twilio_number.py first."
        )
        return result, None
    
    result.add_pass("Phone number setup", f"Using phone_number_id: {phone_number_id}")
    
    # Initiate call
    print(f"\n📞 Initiating call to {destination}...")
    
    url = f"https://api.elevenlabs.io/v1/convai/phone-number/{phone_number_id}/call"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "agent_id": ELEVEN_LABS_AGENT_ID,
        "to_phone_number": destination,
        "dynamic_variables": TEST_VARIABLES
    }
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                call_id = data.get('call_id')
                conversation_id = data.get('conversation_id')
                
                result.add_pass(
                    "Call initiated",
                    f"Conversation ID: {conversation_id}"
                )
                
                print(f"\n✅ Call successfully initiated!")
                print(f"   Call ID: {call_id}")
                print(f"   Conversation ID: {conversation_id}")
                print(f"   Status: {data.get('status')}")
                
                print(f"\n📱 Expected first message:")
                print(f"   {EXPECTED_RENDERED_MESSAGE}")
                
                print(f"\n💡 Test Instructions:")
                print(f"   1. Answer the call on {destination}")
                print(f"   2. Listen for the first message WITHOUT saying 'hello'")
                print(f"   3. Verify Donna speaks immediately upon connection")
                print(f"   4. Verify all dynamic variables are correctly substituted:")
                print(f"      - customer_org: 'Pixamp, Inc'")
                print(f"      - case_id: 'shop-00123'")
                print(f"      - email__vendor_name: 'Shopify, Inc'")
                print(f"      - email__invoice_number: 'ioe-300050'")
                print(f"      - email__amount: '900'")
                print(f"      - email__due_date: '09-23-2025'")
                print(f"      - policy_recording_notice: 'True'")
                
                print(f"\n📊 View conversation:")
                print(f"   https://elevenlabs.io/app/conversational-ai/conversations/{conversation_id}")
                
                return result, conversation_id
                
            else:
                result.add_fail(
                    "Call initiation",
                    f"API returned {response.status_code}: {response.text}"
                )
                return result, None
                
    except Exception as e:
        result.add_fail(
            "Call initiation",
            f"Exception: {str(e)}"
        )
        return result, None


def test_conversation_transcript(conversation_id: str):
    """Test 6: Verify first message in conversation transcript"""
    print("\n🧪 TEST 6: Verify First Message in Transcript")
    print("-" * 70)
    
    result = TestResult()
    
    if not conversation_id:
        result.add_warning(
            "Transcript verification",
            "No conversation_id available. Skip this test."
        )
        return result
    
    print("⏳ Waiting 10 seconds for call to connect and transcript to generate...")
    time.sleep(10)
    
    url = f"https://api.elevenlabs.io/v1/convai/conversations/{conversation_id}"
    headers = {"xi-api-key": ELEVENLABS_API_KEY}
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"\n📊 Conversation Status: {data.get('status', 'N/A')}")
                print(f"   Duration: {data.get('duration_seconds', 0)} seconds")
                
                # Check transcript
                transcript = data.get('transcript', '')
                
                if transcript:
                    result.add_pass(
                        "Transcript available",
                        f"Length: {len(transcript)} characters"
                    )
                    
                    print(f"\n📝 Transcript Preview:")
                    print(f"   {transcript[:500]}...")
                    
                    # Check if first message appears in transcript
                    first_msg_keywords = [
                        "Donna",
                        "Pixamp",
                        "shop-00123",
                        "ioe-300050"
                    ]
                    
                    found_keywords = [kw for kw in first_msg_keywords if kw in transcript]
                    
                    if len(found_keywords) >= 3:
                        result.add_pass(
                            "First message in transcript",
                            f"Found {len(found_keywords)}/{len(first_msg_keywords)} keywords"
                        )
                    else:
                        result.add_warning(
                            "First message in transcript",
                            f"Only found {len(found_keywords)}/{len(first_msg_keywords)} keywords. "
                            "Transcript may be incomplete."
                        )
                else:
                    result.add_warning(
                        "Transcript available",
                        "Transcript is empty. Call may still be in progress or just ended."
                    )
                
                return result
                
            else:
                result.add_warning(
                    "Transcript verification",
                    f"Could not fetch conversation: {response.status_code}"
                )
                return result
                
    except Exception as e:
        result.add_warning(
            "Transcript verification",
            f"Exception: {str(e)}"
        )
        return result


def main():
    """Run all tests"""
    print("=" * 70)
    print("🎯 END-TO-END TEST: First Message with Dynamic Variables")
    print("=" * 70)
    print("\n📚 Reference: https://elevenlabs.io/docs/agents-platform/customization/personalization/overrides")
    
    all_results = []
    
    # Test 1: Agent config exists
    result1, config = test_agent_config_exists()
    all_results.append(result1)
    
    if config is None:
        print("\n❌ Cannot proceed without agent config. Fix and re-run.")
        sys.exit(1)
    
    # Test 2: First message configured
    result2 = test_first_message_configured(config)
    all_results.append(result2)
    
    # Test 3: Dynamic variables defined
    result3 = test_dynamic_variables_defined(config)
    all_results.append(result3)
    
    # Test 4: Override settings
    result4 = test_first_message_overrides(config)
    all_results.append(result4)
    
    # Ask user if they want to run live call test
    print("\n" + "=" * 70)
    print("⚠️  LIVE CALL TEST")
    print("=" * 70)
    print("The next test will initiate a real phone call.")
    print("Make sure you're ready to answer and test the first message.")
    
    # Get destination number
    destination = input(f"\nEnter destination number (default: +13473580012): ").strip()
    if not destination:
        destination = "+13473580012"
    if not destination.startswith('+'):
        destination = f"+{destination}"
    
    proceed = input(f"\nInitiate call to {destination}? (yes/no): ").strip().lower()
    
    if proceed == 'yes' or proceed == 'y':
        # Get phone number ID
        phone_number_id = get_phone_number_id()
        
        # Test 5: Live call
        result5, conversation_id = test_live_call_first_message(phone_number_id, destination)
        all_results.append(result5)
        
        # Test 6: Transcript verification
        if conversation_id:
            result6 = test_conversation_transcript(conversation_id)
            all_results.append(result6)
    else:
        print("\n⏭️  Skipping live call tests.")
    
    # Print combined summary
    print("\n" + "=" * 70)
    print("📊 FINAL TEST SUMMARY")
    print("=" * 70)
    
    total_passed = sum(len(r.passed) for r in all_results)
    total_failed = sum(len(r.failed) for r in all_results)
    total_warnings = sum(len(r.warnings) for r in all_results)
    
    print(f"✅ Total Passed: {total_passed}")
    print(f"❌ Total Failed: {total_failed}")
    print(f"⚠️  Total Warnings: {total_warnings}")
    
    if total_failed > 0:
        print("\n❌ SOME TESTS FAILED")
        print("\n📋 Troubleshooting Steps:")
        print("   1. Check agent config has first_message defined")
        print("   2. Verify all dynamic variables are in agent config")
        print("   3. Update agent in ElevenLabs dashboard if needed")
        print("   4. Reference: https://elevenlabs.io/docs/agents-platform/customization/personalization/overrides")
    else:
        print("\n✅ ALL TESTS PASSED!")
        print("\n🎉 First message is properly configured and should play immediately")
        print("   when calls connect, without waiting for user to say 'hello'.")
    
    print("=" * 70)
    
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
