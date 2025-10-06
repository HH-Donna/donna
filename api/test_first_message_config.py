"""
Quick Config Test: First Message Configuration

This test verifies the agent config is properly set up for first message.
No live calls are made - this only validates configuration.
"""

import json
from pathlib import Path

AGENT_CONFIG_PATH = Path(__file__).parent.parent / "agent" / "agent_configs" / "dev" / "donna-billing-verifier.json"

def main():
    print("=" * 70)
    print("🔍 FIRST MESSAGE CONFIGURATION TEST")
    print("=" * 70)
    
    # Load config
    with open(AGENT_CONFIG_PATH, 'r') as f:
        config = json.load(f)
    
    print(f"\n✅ Agent config loaded: {AGENT_CONFIG_PATH.name}")
    
    # Check first message
    first_message = config['conversation_config']['agent']['first_message']
    
    if not first_message or first_message.strip() == "":
        print("\n❌ FAIL: First message is not configured!")
        return 1
    
    print(f"\n✅ First message configured ({len(first_message)} chars)")
    print(f"\n📝 First Message Template:")
    print(f"   {first_message}")
    
    # Check dynamic variables
    dynamic_vars = config['conversation_config']['agent']['dynamic_variables']['dynamic_variable_placeholders']
    
    required_vars = [
        'customer_org',
        'case_id', 
        'policy_recording_notice',
        'email__vendor_name',
        'email__invoice_number',
        'email__amount',
        'email__due_date'
    ]
    
    print(f"\n📋 Required Dynamic Variables:")
    all_found = True
    for var in required_vars:
        found = var in dynamic_vars
        status = "✅" if found else "❌"
        print(f"   {status} {var}")
        if not found:
            all_found = False
    
    if not all_found:
        print("\n❌ FAIL: Some required variables are missing!")
        return 1
    
    print(f"\n✅ All {len(required_vars)} required variables are defined")
    
    # Check override settings
    overrides_enabled = config['platform_settings']['overrides']['conversation_config_override']['agent']['first_message']
    
    print(f"\n📊 First Message Overrides: {'Enabled ✅' if overrides_enabled else 'Disabled ⚠️'}")
    
    if not overrides_enabled:
        print("   Note: Overrides disabled means the same first message will be")
        print("   used for all calls. This is fine for most use cases.")
    
    # Show example with variables substituted
    example_message = first_message
    substitutions = {
        '{{customer_org}}': 'Pixamp Inc',
        '{{case_id}}': 'FRAUD-2024-001',
        '{{policy_recording_notice}}': 'This call may be recorded for quality assurance.',
        '{{email__vendor_name}}': 'AWS',
        '{{email__invoice_number}}': 'INV-2024-12345',
        '{{email__amount}}': '$1,250.00',
        '{{email__due_date}}': 'October 15, 2024'
    }
    
    for var, value in substitutions.items():
        example_message = example_message.replace(var, value)
    
    print(f"\n💬 Example First Message (with variables):")
    print(f"   \"{example_message}\"")
    
    print("\n" + "=" * 70)
    print("✅ CONFIGURATION TEST PASSED!")
    print("=" * 70)
    print("\n💡 Next Steps:")
    print("   1. The first message is properly configured")
    print("   2. When you make a call, Donna will speak this message immediately")
    print("   3. The message will NOT wait for the user to say 'hello'")
    print("   4. Dynamic variables will be automatically substituted")
    print("\n📞 To test with a real call, run:")
    print("   python3 test_first_message_live.py +1234567890")
    
    return 0

if __name__ == "__main__":
    exit(main())
