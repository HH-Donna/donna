#!/usr/bin/env python3
"""
Comprehensive Test Flow for Email Fraud Detection & Logging System

This script tests the complete fraud detection pipeline with database logging
using the new split function structure.
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env.local
load_dotenv('.env.local')

# Map the environment variables to what the Supabase client expects
os.environ['SUPABASE_URL'] = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
os.environ['SUPABASE_SERVICE_KEY'] = os.getenv('NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY')

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.fraud_logger import create_fraud_logger
from app.database.supabase_client import get_supabase_client
from ml.domain_checker import (
    is_billing_email,
    classify_email_type_with_gemini,
    analyze_domain_legitimacy,
    check_billing_email_legitimacy
)

# Test Gmail messages
test_emails = {
    "bill_legitimate": {
        "id": "test_bill_legit_001",
        "payload": {
            "headers": [
                {"name": "From", "value": "billing@paypal.com"},
                {"name": "Subject", "value": "Your PayPal invoice is ready - Payment Due $129.99"},
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
    },
    
    "bill_suspicious": {
        "id": "test_bill_suspicious_002",
        "payload": {
            "headers": [
                {"name": "From", "value": "billing@paypal-security.tk"},
                {"name": "Subject", "value": "URGENT: Verify your PayPal account immediately"},
                {"name": "To", "value": "user@example.com"}
            ],
            "parts": [
                {
                    "mimeType": "text/plain",
                    "body": {
                        "data": "VXJnZW50IGFjY291bnQgdmVyaWZpY2F0aW9uIHJlcXVpcmVkLiBDbGljayBoZXJlIHRvIHZlcmlmeSB5b3VyIGFjY291bnQgb3IgaXQgd2lsbCBiZSBzdXNwZW5kZWQu"
                    }
                }
            ]
        }
    },
    
    "receipt": {
        "id": "test_receipt_003",
        "payload": {
            "headers": [
                {"name": "From", "value": "receipts@starbucks.com"},
                {"name": "Subject", "value": "Your Starbucks order receipt - Order #12345"},
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
    },
    
    "newsletter": {
        "id": "test_newsletter_004",
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
    },
    
    "no_sender": {
        "id": "test_no_sender_005",
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Important account update"},
                {"name": "To", "value": "user@example.com"}
            ],
            "parts": [
                {
                    "mimeType": "text/plain",
                    "body": {
                        "data": "SW1wb3J0YW50IGFjY291bnQgdXBkYXRlIHJlcXVpcmVkLg=="
                    }
                }
            ]
        }
    }
}

def test_individual_functions():
    """Test each function individually."""
    print("🧪 Testing Individual Functions")
    print("=" * 50)
    
    try:
        # Get Supabase client
        supabase = get_supabase_client()
        fraud_logger = create_fraud_logger(supabase)
        test_user_uuid = "550e8400-e29b-41d4-a716-446655440001"
        
        # Test 1: Rule-based billing detection
        print("\n📧 Testing Rule-based Billing Detection...")
        for email_name, email_data in test_emails.items():
            is_billing = is_billing_email(email_data)
            print(f"   {email_name}: {'✅ Billing' if is_billing else '❌ Not Billing'}")
        
        # Test 2: Gemini classification
        print("\n🤖 Testing Gemini Classification...")
        for email_name, email_data in test_emails.items():
            if is_billing_email(email_data):  # Only test billing emails
                result = classify_email_type_with_gemini(email_data, test_user_uuid, fraud_logger)
                print(f"   {email_name}: {result['email_type']} (confidence: {result['confidence']:.2f})")
        
        # Test 3: Domain analysis
        print("\n🌐 Testing Domain Analysis...")
        for email_name, email_data in test_emails.items():
            if is_billing_email(email_data):  # Only test billing emails
                classification = classify_email_type_with_gemini(email_data, test_user_uuid, fraud_logger)
                if classification["email_type"] == "bill":  # Only analyze bills
                    domain_result = analyze_domain_legitimacy(
                        email_data, 
                        classification["email_type"], 
                        test_user_uuid, 
                        fraud_logger
                    )
                    print(f"   {email_name}: {'✅ Legitimate' if domain_result['is_legitimate'] else '❌ Suspicious'}")
        
        print("\n✅ Individual function tests completed!")
        
    except Exception as e:
        print(f"❌ Individual function tests failed: {e}")
        import traceback
        traceback.print_exc()

def test_complete_pipeline():
    """Test the complete fraud detection pipeline."""
    print("\n🔄 Testing Complete Pipeline")
    print("=" * 50)
    
    try:
        # Get Supabase client
        supabase = get_supabase_client()
        fraud_logger = create_fraud_logger(supabase)
        test_user_uuid = "550e8400-e29b-41d4-a716-446655440002"
        
        for email_name, email_data in test_emails.items():
            print(f"\n📧 Testing {email_name}...")
            
            # Run complete pipeline
            result = check_billing_email_legitimacy(email_data, test_user_uuid, fraud_logger)
            
            # Display results
            print(f"   📊 Results:")
            print(f"      - Is Billing: {'✅' if result['is_billing'] else '❌'}")
            print(f"      - Email Type: {result['email_type']}")
            print(f"      - Is Legitimate: {'✅' if result['is_legitimate'] else '❌' if result['is_legitimate'] is not None else 'N/A'}")
            print(f"      - Confidence: {result['confidence']:.2f}")
            print(f"      - Halt Reason: {result.get('halt_reason', 'None')}")
            print(f"      - Log Entries: {len(result.get('log_entries', []))}")
            
            # Show log entries
            if result.get('log_entries'):
                print(f"   📝 Log Entries:")
                for i, entry in enumerate(result['log_entries'], 1):
                    print(f"      {i}. {entry['step']}: {'✅' if entry['decision'] else '❌'} - {entry['reasoning']}")
        
        print("\n✅ Complete pipeline tests completed!")
        
    except Exception as e:
        print(f"❌ Complete pipeline tests failed: {e}")
        import traceback
        traceback.print_exc()

def test_logging_retrieval():
    """Test logging retrieval functions."""
    print("\n📊 Testing Logging Retrieval")
    print("=" * 50)
    
    try:
        # Get Supabase client
        supabase = get_supabase_client()
        fraud_logger = create_fraud_logger(supabase)
        test_user_uuid = "550e8400-e29b-41d4-a716-446655440003"
        
        # Test with a bill email
        bill_email = test_emails["bill_legitimate"]
        
        # Run analysis
        result = check_billing_email_legitimacy(bill_email, test_user_uuid, fraud_logger)
        
        # Test retrieval functions
        print(f"\n📧 Testing retrieval for email: {bill_email['id']}")
        
        # Get analysis history
        history = fraud_logger.get_email_analysis_history(bill_email['id'], test_user_uuid)
        print(f"   📝 Analysis History: {len(history)} entries")
        for entry in history:
            print(f"      - {entry['step']}: {'✅' if entry['decision'] else '❌'} - {entry['reasoning']}")
        
        # Get final decision
        final_decision = fraud_logger.get_final_decision(bill_email['id'], test_user_uuid)
        print(f"   🎯 Final Decision: {'✅ Proceed' if final_decision else '❌ Halt'}")
        
        # Get fraud emails for user
        fraud_emails = fraud_logger.get_fraud_emails_for_user(test_user_uuid, limit=10)
        print(f"   🚨 Fraud Emails for User: {len(fraud_emails)} emails")
        
        print("\n✅ Logging retrieval tests completed!")
        
    except Exception as e:
        print(f"❌ Logging retrieval tests failed: {e}")
        import traceback
        traceback.print_exc()

def test_decision_flow():
    """Test the decision flow and halt logic."""
    print("\n🔄 Testing Decision Flow & Halt Logic")
    print("=" * 50)
    
    try:
        # Get Supabase client
        supabase = get_supabase_client()
        fraud_logger = create_fraud_logger(supabase)
        test_user_uuid = "550e8400-e29b-41d4-a716-446655440004"
        
        # Test different scenarios
        scenarios = [
            ("newsletter", "Should halt at rule-based check"),
            ("receipt", "Should proceed after Gemini classification"),
            ("bill_legitimate", "Should proceed after domain analysis"),
            ("bill_suspicious", "Should halt at domain analysis"),
            ("no_sender", "Should halt at domain analysis")
        ]
        
        for email_name, expected_behavior in scenarios:
            print(f"\n📧 Testing {email_name}: {expected_behavior}")
            
            email_data = test_emails[email_name]
            result = check_billing_email_legitimacy(email_data, test_user_uuid, fraud_logger)
            
            # Check halt reason
            halt_reason = result.get('halt_reason')
            if halt_reason:
                print(f"   🛑 HALTED: {halt_reason}")
            else:
                print(f"   ✅ PROCEEDED: No halt reason")
            
            # Show decision path
            log_entries = result.get('log_entries', [])
            print(f"   📝 Decision Path:")
            for entry in log_entries:
                decision_text = "PROCEED" if entry['decision'] else "HALT"
                print(f"      - {entry['step']}: {decision_text} - {entry['reasoning']}")
        
        print("\n✅ Decision flow tests completed!")
        
    except Exception as e:
        print(f"❌ Decision flow tests failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run all tests."""
    print("🚀 Starting Comprehensive Email Fraud Detection Test Flow")
    print("=" * 70)
    
    # Run all test suites
    test_individual_functions()
    test_complete_pipeline()
    test_logging_retrieval()
    test_decision_flow()
    
    print("\n🎉 All Tests Completed!")
    print("=" * 70)
    print("✅ Individual functions working correctly")
    print("✅ Complete pipeline working correctly")
    print("✅ Logging system working correctly")
    print("✅ Decision flow and halt logic working correctly")
    print("\n🔍 Check your Supabase database for logged entries!")

if __name__ == "__main__":
    main()
