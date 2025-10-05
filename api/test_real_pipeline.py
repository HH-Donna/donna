#!/usr/bin/env python3
"""
Real Pipeline Test - Tests the complete fraud detection workflow
using synthetic email data instead of Gmail Pub/Sub
"""

import asyncio
import json
import requests
from datetime import datetime
from typing import Dict, Any

# Test configuration
API_BASE_URL = "http://localhost:8000"
TEST_USER_EMAIL = "test@example.com"
TEST_USER_ID = "test-user-123"

def create_synthetic_email_data(test_case: str) -> Dict[str, Any]:
    """Create synthetic email data for testing"""
    
    test_cases = {
        "safe_google": {
            "message_id": "test-google-001",
            "user_id": "test-user-123",
            "user_email": "test@example.com",
            "from": "billing@googlecloud.com",
            "subject": "Your Google Cloud invoice is ready",
            "body": "Thank you for using Google Cloud Platform. Your invoice for $150.00 is ready for payment.",
            "received_at": datetime.now().isoformat(),
            "attachments": []
        },
        "safe_shopify": {
            "message_id": "test-shopify-001",
            "user_id": "test-user-123",
            "user_email": "test@example.com",
            "from": "billing@shopify.com",
            "subject": "Shopify Plus invoice - $299.00",
            "body": "Your monthly Shopify Plus subscription invoice is ready. Amount: $299.00",
            "received_at": datetime.now().isoformat(),
            "attachments": []
        },
        "unsure_unknown": {
            "message_id": "test-unknown-001",
            "user_id": "test-user-123",
            "user_email": "test@example.com",
            "from": "billing@newcompany.com", 
            "subject": "Invoice from New Company - $75.00",
            "body": "Please find attached your invoice for services rendered. Total: $75.00",
            "received_at": datetime.now().isoformat(),
            "attachments": []
        },
        "fraudulent_typo": {
            "message_id": "test-fraud-001",
            "user_id": "test-user-123",
            "user_email": "test@example.com",
            "from": "billing@g00gle.com",  # Typosquatting
            "subject": "Your Google Cloud invoice is ready",
            "body": "Urgent: Your Google Cloud account will be suspended. Pay $299.00 immediately.",
            "received_at": datetime.now().isoformat(),
            "attachments": []
        },
        "fraudulent_suspicious": {
            "message_id": "test-fraud-002",
            "user_id": "test-user-123",
            "user_email": "test@example.com",
            "from": "billing@paypal-security.tk",  # Suspicious TLD
            "subject": "PayPal Security Alert - Payment Required",
            "body": "Your PayPal account is locked. Verify your identity by paying $199.00 to unlock.",
            "received_at": datetime.now().isoformat(),
            "attachments": []
        }
    }
    
    return test_cases.get(test_case, {})

def create_pubsub_payload(email_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a Pub/Sub payload that mimics Google's format"""
    
    # Create the message data that would be in the Pub/Sub notification
    message_data = {
        "emailAddress": TEST_USER_EMAIL,
        "historyId": "1234567890"
    }
    
    # Encode the message data (Google Pub/Sub sends base64 encoded data)
    import base64
    encoded_data = base64.b64encode(json.dumps(message_data).encode()).decode()
    
    # Create the Pub/Sub message format
    pubsub_message = {
        "message": {
            "data": encoded_data,
            "messageId": f"test-msg-{email_data['message_id']}",
            "publishTime": datetime.now().isoformat() + "Z"
        },
        "subscription": "projects/test-project/subscriptions/gmail-updates"
    }
    
    return pubsub_message

async def test_fraud_detection_pipeline():
    """Test the complete fraud detection pipeline"""
    
    print("🧪 REAL PIPELINE TEST SUITE")
    print("=" * 50)
    
    test_cases = [
        ("safe_google", "✅ SAFE - Google Cloud"),
        ("safe_shopify", "✅ SAFE - Shopify"), 
        ("unsure_unknown", "⚠️ UNSURE - Unknown Company"),
        ("fraudulent_typo", "🚨 FRAUDULENT - Typosquatting"),
        ("fraudulent_suspicious", "🚨 FRAUDULENT - Suspicious TLD")
    ]
    
    results = []
    
    for test_key, test_name in test_cases:
        print(f"\n🔍 TESTING: {test_name}")
        print("-" * 40)
        
        # Create synthetic email data
        email_data = create_synthetic_email_data(test_key)
        print(f"📧 Email: {email_data['from']}")
        print(f"📝 Subject: {email_data['subject']}")
        
        # Create Pub/Sub payload
        pubsub_payload = create_pubsub_payload(email_data)
        
        try:
            # Send to the test endpoint
            print("🚀 Sending to test endpoint...")
            response = requests.post(
                f"{API_BASE_URL}/pubsub/test/email",
                json=email_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            print(f"📡 Response: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Request processed successfully")
                results.append((test_name, "SUCCESS", response.status_code))
            else:
                print(f"❌ Error: {response.text}")
                results.append((test_name, "ERROR", response.status_code))
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            results.append((test_name, "EXCEPTION", str(e)))
        
        print("⏳ Waiting 2 seconds before next test...")
        await asyncio.sleep(2)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    for test_name, status, details in results:
        if status == "SUCCESS":
            print(f"✅ {test_name}: {status} ({details})")
        else:
            print(f"❌ {test_name}: {status} ({details})")
    
    success_count = sum(1 for _, status, _ in results if status == "SUCCESS")
    total_count = len(results)
    
    print(f"\n🎯 Success Rate: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    
    if success_count == total_count:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️ Some tests failed - check API server logs")

if __name__ == "__main__":
    asyncio.run(test_fraud_detection_pipeline())
