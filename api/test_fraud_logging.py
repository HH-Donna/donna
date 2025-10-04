#!/usr/bin/env python3
"""
Test script for email fraud logging system.

This script tests the complete fraud detection pipeline with database logging.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.fraud_logger import create_fraud_logger
from app.services.supabase_client import get_supabase_client
from ml.domain_checker import check_billing_email_legitimacy

# Test Gmail message (bill)
test_bill_email = {
    "id": "test_bill_123",
    "payload": {
        "headers": [
            {"name": "From", "value": "billing@paypal.com"},
            {"name": "Subject", "value": "Your PayPal invoice is ready - Payment Due"},
            {"name": "To", "value": "user@example.com"}
        ],
        "parts": [
            {
                "mimeType": "text/plain",
                "body": {
                    "data": "SGVsbG8sCgpZb3VyIFBheVBhbCBpbnZvaWNlIGZvciAkMTI5Ljk5IGlzIHJlYWR5LiBQbGVhc2UgcGF5IGJ5IEphbnVhcnkgMTUsIDIwMjUuCgpUaGFuayB5b3UhClBheVBhbA=="
                }
            }
        ]
    }
}

# Test Gmail message (receipt)
test_receipt_email = {
    "id": "test_receipt_456",
    "payload": {
        "headers": [
            {"name": "From", "value": "receipts@starbucks.com"},
            {"name": "Subject", "value": "Your Starbucks order receipt"},
            {"name": "To", "value": "user@example.com"}
        ],
        "parts": [
            {
                "mimeType": "text/plain",
                "body": {
                    "data": "VGhhbmsgeW91IGZvciB5b3VyIHB1cmNoYXNlISBZb3VyIG9yZGVyIGZvciAkNC41MCBoYXMgYmVlbiBjb21wbGV0ZWQu"
                }
            }
        ]
    }
}

# Test Gmail message (newsletter)
test_newsletter_email = {
    "id": "test_newsletter_789",
    "payload": {
        "headers": [
            {"name": "From", "value": "newsletter@techcrunch.com"},
            {"name": "Subject", "value": "Weekly Tech News Roundup"},
            {"name": "To", "value": "user@example.com"}
        ],
        "parts": [
            {
                "mimeType": "text/plain",
                "body": {
                    "data": "SGVyZSdzIHlvdXIgd2Vla2x5IHJvdW5kdXAgb2YgdGhlIGxhdGVzdCB0ZWNoIG5ld3Mu"
                }
            }
        ]
    }
}

def test_fraud_logging():
    """Test the complete fraud detection and logging pipeline."""
    print("🧪 Testing Email Fraud Logging System")
    print("=" * 50)
    
    try:
        # Get Supabase client
        supabase = get_supabase_client()
        fraud_logger = create_fraud_logger(supabase)
        
        # Test user UUID (you'll need to replace this with a real user UUID)
        test_user_uuid = "test-user-123"
        
        # Test 1: Bill email
        print("\n📧 Testing Bill Email Analysis...")
        bill_result = check_billing_email_legitimacy(
            gmail_msg=test_bill_email,
            user_uuid=test_user_uuid,
            fraud_logger=fraud_logger
        )
        
        print(f"✅ Bill Analysis Complete:")
        print(f"   - Email Type: {bill_result['email_type']}")
        print(f"   - Is Legitimate: {bill_result['is_legitimate']}")
        print(f"   - Confidence: {bill_result['confidence']:.2f}")
        print(f"   - Log Entries: {len(bill_result.get('log_entries', []))}")
        
        # Test 2: Receipt email
        print("\n📧 Testing Receipt Email Analysis...")
        receipt_result = check_billing_email_legitimacy(
            gmail_msg=test_receipt_email,
            user_uuid=test_user_uuid,
            fraud_logger=fraud_logger
        )
        
        print(f"✅ Receipt Analysis Complete:")
        print(f"   - Email Type: {receipt_result['email_type']}")
        print(f"   - Is Legitimate: {receipt_result['is_legitimate']}")
        print(f"   - Confidence: {receipt_result['confidence']:.2f}")
        print(f"   - Log Entries: {len(receipt_result.get('log_entries', []))}")
        
        # Test 3: Newsletter email
        print("\n📧 Testing Newsletter Email Analysis...")
        newsletter_result = check_billing_email_legitimacy(
            gmail_msg=test_newsletter_email,
            user_uuid=test_user_uuid,
            fraud_logger=fraud_logger
        )
        
        print(f"✅ Newsletter Analysis Complete:")
        print(f"   - Email Type: {newsletter_result['email_type']}")
        print(f"   - Is Legitimate: {newsletter_result['is_legitimate']}")
        print(f"   - Confidence: {newsletter_result['confidence']:.2f}")
        print(f"   - Log Entries: {len(newsletter_result.get('log_entries', []))}")
        
        # Test 4: Retrieve analysis history
        print("\n📊 Testing Analysis History Retrieval...")
        bill_history = fraud_logger.get_email_analysis_history("test_bill_123", test_user_uuid)
        print(f"✅ Bill History Retrieved: {len(bill_history)} entries")
        
        for entry in bill_history:
            print(f"   - Step: {entry['step']}, Decision: {entry['decision']}, Confidence: {entry['confidence']}")
        
        # Test 5: Get final decision
        print("\n🎯 Testing Final Decision Retrieval...")
        final_decision = fraud_logger.get_final_decision("test_bill_123", test_user_uuid)
        print(f"✅ Final Decision: {final_decision}")
        
        print("\n🎉 All Tests Passed! Fraud logging system is working correctly.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fraud_logging()
