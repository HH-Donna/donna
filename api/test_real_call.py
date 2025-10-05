#!/usr/bin/env python3
"""
Real Phone Call Test

Tests the ElevenLabs agent by making an actual phone call.
"""

import asyncio
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.eleven_agent import eleven_agent


async def test_real_call():
    """Test a real phone call"""
    print("\n" + "="*60)
    print("📞 REAL PHONE CALL TEST")
    print("="*60)
    
    # Test configuration
    test_phone = "3473580012"
    test_company = "Test Company"
    test_email = "billing@testcompany.com"
    
    print(f"\n📋 Call Details:")
    print(f"   Company: {test_company}")
    print(f"   Phone: {test_phone}")
    print(f"   Email: {test_email}")
    print()
    
    # Check if credentials are configured
    if not eleven_agent.elevenlabs_api_key:
        print("❌ ERROR: ELEVENLABS_API_KEY not configured")
        print("   Please set the ELEVENLABS_API_KEY environment variable")
        return False
    
    if not eleven_agent.twilio_account_sid or not eleven_agent.twilio_auth_token:
        print("❌ ERROR: Twilio credentials not configured")
        print("   Please set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN")
        return False
    
    if not eleven_agent.twilio_phone_number:
        print("❌ ERROR: TWILIO_PHONE_NUMBER not configured")
        print("   Please set your Twilio phone number")
        return False
    
    print(f"✅ ElevenLabs API Key: {eleven_agent.elevenlabs_api_key[:10]}...")
    print(f"✅ Twilio Account SID: {eleven_agent.twilio_account_sid[:10]}...")
    print(f"✅ Twilio Phone: {eleven_agent.twilio_phone_number}")
    print()
    
    # Make the call
    print("🔄 Initiating call...")
    print("-" * 60)
    
    result = await eleven_agent.verify_company_by_call(
        company_name=test_company,
        phone_number=test_phone,
        email=test_email
    )
    
    print("-" * 60)
    print("\n📊 Call Result:")
    print(f"   Success: {result.get('success')}")
    print(f"   Status: {result.get('call_status', 'N/A')}")
    
    if result.get('success'):
        print(f"   Call SID: {result.get('call_sid', 'N/A')}")
        print(f"   Call Status: {result.get('call_status', 'N/A')}")
        print(f"   Phone: {result.get('phone_number')}")
        print(f"   Company: {result.get('company_name')}")
        print(f"   Message: {result.get('message', 'N/A')}")
        
        print("\n✅ CALL INITIATED SUCCESSFULLY!")
        print("   The phone should ring shortly...")
        print(f"\n   Track your call at: https://console.twilio.com/us1/monitor/logs/calls/{result.get('call_sid')}")
        
    else:
        print(f"   Error: {result.get('error', 'Unknown error')}")
        
        print("\n❌ CALL FAILED")
        print("\n💡 Troubleshooting:")
        print("   1. Verify your Twilio credentials are correct")
        print("   2. Check your Twilio phone number is verified")
        print("   3. Ensure your Twilio account has credits")
        print("   4. Verify ElevenLabs API key is correct")
    
    return result.get('success', False)


if __name__ == "__main__":
    success = asyncio.run(test_real_call())
    sys.exit(0 if success else 1)
