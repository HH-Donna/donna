#!/usr/bin/env python3
"""
Test Integration of Google Search + ElevenLabs Agent

This script tests the complete integration:
1. Company verification against database
2. Google Search for company info when not found
3. ElevenLabs agent call when phone number is found
4. User info injection into agent prompt
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the parent directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from ml.domain_checker import verify_company_online
from app.database.supabase_client import get_supabase_client
from app.services.fraud_logger import EmailFraudLogger


def create_mock_gmail_message(sender: str, subject: str, body: str):
    """Create a mock Gmail message for testing."""
    return {
        "id": "test_message_123",
        "payload": {
            "headers": [
                {"name": "From", "value": sender},
                {"name": "Subject", "value": subject},
                {"name": "Date", "value": "Mon, 5 Oct 2025 10:00:00 -0400"}
            ],
            "body": {"data": body},
            "parts": []
        }
    }


async def test_integration():
    """Test the complete integration."""
    print("\n" + "="*70)
    print("🧪 TESTING GOOGLE SEARCH + ELEVENLABS INTEGRATION")
    print("="*70)
    
    # Configuration
    user_uuid = os.getenv('TEST_USER_UUID', 'a33138b1-09c3-43ec-a1f2-af3bebed78b7')
    company_name = "Shopify"  # A well-known company that should have online info
    
    # Create mock email message
    mock_message = create_mock_gmail_message(
        sender=f"billing@{company_name.lower()}.com",
        subject=f"Invoice from {company_name}",
        body="Your invoice is ready. Please review and pay."
    )
    
    print(f"\n📋 Test Configuration:")
    print(f"   User UUID: {user_uuid}")
    print(f"   Company: {company_name}")
    print(f"   Email: {mock_message['payload']['headers'][0]['value']}")
    
    # Initialize fraud logger
    try:
        supabase = get_supabase_client()
        fraud_logger = EmailFraudLogger(supabase)
        print(f"   ✅ Fraud logger initialized")
    except Exception as e:
        print(f"   ⚠️  Could not initialize fraud logger: {str(e)}")
        fraud_logger = None
    
    # Test online verification with ElevenLabs integration
    print(f"\n{'='*70}")
    print("🔍 STEP 1: Google Search for Company Info")
    print(f"{'='*70}")
    
    try:
        result = await verify_company_online(
            gmail_msg=mock_message,
            user_uuid=user_uuid,
            company_name=company_name,
            fraud_logger=fraud_logger
        )
        
        print(f"\n📊 Verification Results:")
        print(f"   Is Verified: {result.get('is_verified', False)}")
        print(f"   Verification Status: {result.get('verification_status', 'pending')}")
        print(f"   Confidence: {result.get('confidence', 0):.2f}")
        print(f"   Reasoning: {result.get('reasoning', 'N/A')}")
        
        print(f"\n🔍 Extracted Attributes:")
        print(f"   Phone: {result.get('online_phone', 'Not found')}")
        print(f"   Address: {result.get('online_address', 'Not found')}")
        print(f"   Email: {result.get('extracted_attributes', {}).get('email', 'Not found')}")
        print(f"   Website: {result.get('extracted_attributes', {}).get('website', 'Not found')}")
        
        # Check if call was initiated
        if result.get('call_initiated'):
            print(f"\n{'='*70}")
            print("📞 STEP 2: ElevenLabs Agent Call")
            print(f"{'='*70}")
            
            call_result = result.get('call_result', {})
            
            if call_result.get('success'):
                print(f"\n✅ Call Initiated Successfully!")
                print(f"   Phone Number: {call_result.get('phone_number', 'N/A')}")
                print(f"   Company: {call_result.get('company_name', 'N/A')}")
                print(f"   Conversation ID: {call_result.get('conversation_id', 'N/A')}")
                print(f"   Call SID: {call_result.get('call_sid', 'N/A')}")
                print(f"   Agent ID: {call_result.get('agent_id', 'N/A')}")
                print(f"   Status: {call_result.get('call_status', 'N/A')}")
                print(f"\n📝 Note: {call_result.get('note', 'N/A')}")
                
                print(f"\n💡 The agent will call the company with user context injected!")
                print(f"   User info (name, email, company) was dynamically added to the prompt")
            else:
                print(f"\n❌ Call Failed")
                print(f"   Error: {call_result.get('error', 'Unknown error')}")
        else:
            print(f"\n{'='*70}")
            print("⏭️  STEP 2: ElevenLabs Call Skipped")
            print(f"{'='*70}")
            
            if result.get('call_error'):
                print(f"\n❌ Error: {result.get('call_error')}")
            elif not result.get('online_phone'):
                print(f"\n⚠️  No phone number found for {company_name}")
            else:
                print(f"\n⚠️  Insufficient confidence to initiate call")
        
        print(f"\n{'='*70}")
        print("✅ TEST COMPLETED")
        print(f"{'='*70}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ TEST FAILED")
        print(f"   Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def test_with_custom_company():
    """Test with a custom company name provided by the user."""
    print("\n" + "="*70)
    print("🔧 CUSTOM COMPANY TEST")
    print("="*70)
    
    # Get company name from command line or use default
    company_name = sys.argv[1] if len(sys.argv) > 1 else None
    
    if not company_name:
        print("\n💡 Usage: python test_integration.py [company_name]")
        print("   Example: python test_integration.py \"Google Cloud\"")
        return
    
    user_uuid = os.getenv('TEST_USER_UUID', 'a33138b1-09c3-43ec-a1f2-af3bebed78b7')
    
    # Create mock email
    mock_message = create_mock_gmail_message(
        sender=f"billing@{company_name.lower().replace(' ', '')}.com",
        subject=f"Invoice from {company_name}",
        body="Your invoice is ready."
    )
    
    print(f"\n📋 Testing with company: {company_name}")
    print(f"   User UUID: {user_uuid}")
    
    try:
        supabase = get_supabase_client()
        fraud_logger = EmailFraudLogger(supabase)
    except:
        fraud_logger = None
    
    result = await verify_company_online(
        gmail_msg=mock_message,
        user_uuid=user_uuid,
        company_name=company_name,
        fraud_logger=fraud_logger
    )
    
    print(f"\n✅ Results:")
    print(f"   Phone: {result.get('online_phone', 'Not found')}")
    print(f"   Call Initiated: {result.get('call_initiated', False)}")
    
    if result.get('call_initiated'):
        call_result = result.get('call_result', {})
        print(f"   Conversation ID: {call_result.get('conversation_id', 'N/A')}")


if __name__ == "__main__":
    # Run the test
    asyncio.run(test_integration())
    
    # Optionally test with custom company
    # Uncomment the line below to enable custom company testing
    # asyncio.run(test_with_custom_company())
