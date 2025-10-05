#!/usr/bin/env python3
"""
Unit Test: ElevenLabs Agent Phone Call

This script tests the ElevenLabs agent by making a real call to a test phone number.
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the parent directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.eleven_agent import eleven_agent


async def test_call_phone_number():
    """Test calling a specific phone number with the ElevenLabs agent."""
    
    print("\n" + "="*70)
    print("📞 ELEVENLABS AGENT UNIT TEST")
    print("="*70)
    
    # Test configuration
    test_phone = "+13473580012"  # Phone number to call
    test_company = "Test Company Inc."
    test_email = "billing@testcompany.com"
    test_user_uuid = os.getenv('TEST_USER_UUID', 'a33138b1-09c3-43ec-a1f2-af3bebed78b7')
    
    print(f"\n📋 Call Configuration:")
    print(f"   Phone: {test_phone}")
    print(f"   Company: {test_company}")
    print(f"   Email: {test_email}")
    print(f"   User UUID: {test_user_uuid}")
    
    # Check API configuration
    print(f"\n🔑 API Configuration:")
    if eleven_agent.api_key:
        print(f"   ✅ ElevenLabs API Key: {eleven_agent.api_key[:10]}...")
    else:
        print(f"   ❌ ElevenLabs API Key: NOT SET")
        print(f"\n⚠️  Please set ELEVENLABS_API_KEY in your .env file")
        return
    
    print(f"   Agent ID: {eleven_agent.agent_id}")
    print(f"   Phone Number ID: {eleven_agent.phone_number_id}")
    
    # Confirm before making the call (skip if --no-confirm flag)
    skip_confirm = '--no-confirm' in sys.argv or '-y' in sys.argv
    
    if not skip_confirm:
        print(f"\n{'='*70}")
        print(f"⚠️  WARNING: This will initiate a REAL phone call!")
        print(f"{'='*70}")
        print(f"\nPress Enter to proceed with the call, or Ctrl+C to cancel...")
        
        try:
            input()
        except KeyboardInterrupt:
            print(f"\n\n❌ Call cancelled by user")
            return
    else:
        print(f"\n🚀 Auto-confirming call (--no-confirm flag set)")
    
    # Make the call
    print(f"\n{'='*70}")
    print("📞 INITIATING CALL")
    print(f"{'='*70}")
    
    try:
        result = await eleven_agent.verify_company_by_call(
            company_name=test_company,
            phone_number=test_phone,
            email=test_email,
            user_uuid=test_user_uuid
        )
        
        print(f"\n{'='*70}")
        print("📊 CALL RESULT")
        print(f"{'='*70}")
        
        if result.get('success'):
            print(f"\n✅ Call Initiated Successfully!")
            print(f"\n📞 Call Details:")
            print(f"   Phone Number: {result.get('phone_number', 'N/A')}")
            print(f"   Company Name: {result.get('company_name', 'N/A')}")
            print(f"   Email: {result.get('email', 'N/A')}")
            
            print(f"\n🆔 Tracking Information:")
            print(f"   Conversation ID: {result.get('conversation_id', 'N/A')}")
            print(f"   Call SID: {result.get('call_sid', 'N/A')}")
            print(f"   Agent ID: {result.get('agent_id', 'N/A')}")
            
            print(f"\n📈 Status:")
            print(f"   Call Status: {result.get('call_status', 'N/A')}")
            print(f"   Verified: {result.get('verified', False)}")
            print(f"   Timestamp: {result.get('timestamp', 'N/A')}")
            
            if result.get('note'):
                print(f"\n💡 Note:")
                print(f"   {result.get('note')}")
            
            # Show raw response if available
            if result.get('raw_response'):
                print(f"\n📄 Raw API Response:")
                import json
                print(f"   {json.dumps(result.get('raw_response'), indent=2)}")
            
            # Check call status after a few seconds
            conversation_id = result.get('conversation_id')
            if conversation_id:
                print(f"\n{'='*70}")
                print("⏳ Waiting 5 seconds before checking call status...")
                print(f"{'='*70}")
                await asyncio.sleep(5)
                
                print(f"\n🔍 Fetching call status...")
                status_result = await eleven_agent.get_call_status(conversation_id)
                
                if status_result.get('success'):
                    print(f"✅ Call Status Retrieved:")
                    status_data = status_result.get('data', {})
                    print(f"   Status: {status_data.get('status', 'N/A')}")
                    print(f"   Analysis: {status_data.get('analysis', {})}")
                else:
                    print(f"❌ Failed to get call status: {status_result.get('error')}")
            
        else:
            print(f"\n❌ Call Failed!")
            print(f"\n🚨 Error Details:")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            print(f"   Phone: {result.get('phone_number', 'N/A')}")
            print(f"   Company: {result.get('company_name', 'N/A')}")
            
            if result.get('status_code'):
                print(f"   Status Code: {result.get('status_code')}")
        
        print(f"\n{'='*70}")
        print("✅ TEST COMPLETED")
        print(f"{'='*70}")
        
        return result
        
    except Exception as e:
        print(f"\n{'='*70}")
        print("❌ TEST FAILED")
        print(f"{'='*70}")
        print(f"\nError: {str(e)}")
        
        import traceback
        print(f"\n🔍 Stack Trace:")
        traceback.print_exc()
        
        return None


async def test_with_custom_number():
    """Test with a custom phone number from command line."""
    
    if len(sys.argv) < 2:
        print("\n💡 Usage: python test_elevenlabs_call.py [phone_number] [company_name] [email]")
        print("   Example: python test_elevenlabs_call.py +13473580012 \"Test Company\" billing@test.com")
        return None
    
    phone = sys.argv[1]
    company = sys.argv[2] if len(sys.argv) > 2 else "Test Company"
    email = sys.argv[3] if len(sys.argv) > 3 else "billing@testcompany.com"
    user_uuid = os.getenv('TEST_USER_UUID', 'a33138b1-09c3-43ec-a1f2-af3bebed78b7')
    
    print("\n" + "="*70)
    print("📞 CUSTOM PHONE CALL TEST")
    print("="*70)
    print(f"\n   Phone: {phone}")
    print(f"   Company: {company}")
    print(f"   Email: {email}")
    
    print(f"\n⚠️  Press Enter to proceed, or Ctrl+C to cancel...")
    try:
        input()
    except KeyboardInterrupt:
        print(f"\n\n❌ Cancelled")
        return None
    
    result = await eleven_agent.verify_company_by_call(
        company_name=company,
        phone_number=phone,
        email=email,
        user_uuid=user_uuid
    )
    
    if result.get('success'):
        print(f"\n✅ Call initiated!")
        print(f"   Conversation ID: {result.get('conversation_id')}")
        print(f"   Call SID: {result.get('call_sid')}")
    else:
        print(f"\n❌ Call failed: {result.get('error')}")
    
    return result


if __name__ == "__main__":
    # Filter out flags from arguments
    args = [arg for arg in sys.argv[1:] if not arg.startswith('-')]
    
    # Run the test
    if len(args) > 0:
        # Custom phone number test
        asyncio.run(test_with_custom_number())
    else:
        # Default test
        asyncio.run(test_call_phone_number())
