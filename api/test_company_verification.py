#!/usr/bin/env python3
"""
Test script for verify_company_against_database function.

This script tests the company verification logic against real companies
in the database to check accuracy.
"""

import os
import sys
import json
from dotenv import load_dotenv

# Add paths
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ml'))

from app.database.supabase_client import get_supabase_client
from app.services.fraud_logger import create_fraud_logger
from domain_checker import verify_company_against_database

load_dotenv()

def create_test_gmail_message(sender_email: str, subject: str, body_text: str):
    """Create a mock Gmail API message for testing."""
    import base64
    
    # Encode body text
    body_encoded = base64.urlsafe_b64encode(body_text.encode()).decode()
    
    return {
        "id": "test_message_id",
        "threadId": "test_thread_id",
        "payload": {
            "headers": [
                {"name": "From", "value": sender_email},
                {"name": "To", "value": "test@example.com"},
                {"name": "Subject", "value": subject},
                {"name": "Date", "value": "Mon, 4 Oct 2025 12:00:00 +0000"}
            ],
            "parts": [
                {
                    "mimeType": "text/plain",
                    "body": {
                        "data": body_encoded
                    }
                }
            ]
        }
    }


def test_company_verification(user_uuid: str):
    """
    Test company verification against real companies in database.
    """
    print("="*80)
    print("COMPANY VERIFICATION ACCURACY TEST")
    print("="*80)
    
    # Get Supabase client
    supabase = get_supabase_client()
    fraud_logger = create_fraud_logger(supabase)
    
    # Get companies for this user
    companies_response = supabase.table('companies')\
        .select('*')\
        .eq('user_id', user_uuid)\
        .execute()
    
    if not companies_response.data:
        print(f"\n❌ No companies found for user {user_uuid}")
        return
    
    companies = companies_response.data
    print(f"\n✅ Found {len(companies)} companies in database\n")
    
    # Test each company
    results = []
    
    for idx, company in enumerate(companies, 1):
        print(f"\n{'='*80}")
        print(f"TEST {idx}/{len(companies)}: {company['name']}")
        print(f"{'='*80}")
        
        # Get primary email
        contact_emails = company.get('contact_emails', [])
        primary_email = contact_emails[0] if contact_emails else 'unknown@example.com'
        
        print(f"Company Info:")
        print(f"  Name: {company['name']}")
        print(f"  Domain: {company.get('domain', 'N/A')}")
        print(f"  Emails: {', '.join(contact_emails)}")
        print(f"  Address: {company.get('billing_address', 'N/A')[:60]}...")
        print(f"  Phone: {company.get('biller_phone_number', 'N/A')}")
        
        # Create test email from this company
        test_subject = f"Invoice from {company['name']}"
        test_body = f"""
        Invoice from {company['name']}
        
        Billing Address: {company.get('billing_address', '')}
        Phone: {company.get('biller_phone_number', '')}
        Payment Method: {company.get('payment_method', '')}
        
        Your account number: {company.get('user_account_number', '')}
        """
        
        test_message = create_test_gmail_message(
            primary_email,
            test_subject,
            test_body
        )
        
        # Run verification
        print(f"\nRunning verification...")
        verification_result = verify_company_against_database(
            test_message,
            user_uuid,
            fraud_logger
        )
        
        # Display results
        print(f"\n📊 Verification Results:")
        print(f"  Is Verified: {'✅ YES' if verification_result['is_verified'] else '❌ NO'}")
        print(f"  Confidence: {verification_result['confidence']}")
        print(f"  Reasoning: {verification_result['reasoning']}")
        
        if verification_result.get('company_match'):
            print(f"  Matched Company: {verification_result['company_match']['name']}")
        
        if verification_result.get('attribute_differences'):
            print(f"  ⚠️  Attribute Differences:")
            for diff in verification_result['attribute_differences']:
                print(f"     - {diff['attribute']}: expected '{diff['expected']}', got '{diff['actual']}'")
        
        if verification_result.get('trigger_agent'):
            print(f"  🚨 Trigger Agent: YES")
        
        results.append({
            'company': company['name'],
            'is_verified': verification_result['is_verified'],
            'confidence': verification_result['confidence'],
            'has_match': verification_result.get('company_match') is not None
        })
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    
    verified_count = sum(1 for r in results if r['is_verified'])
    matched_count = sum(1 for r in results if r['has_match'])
    
    print(f"\nTotal Companies Tested: {len(results)}")
    print(f"Successfully Verified: {verified_count}/{len(results)} ({verified_count/len(results)*100:.1f}%)")
    print(f"Found Matches: {matched_count}/{len(results)} ({matched_count/len(results)*100:.1f}%)")
    
    avg_confidence = sum(r['confidence'] for r in results) / len(results) if results else 0
    print(f"Average Confidence: {avg_confidence:.2f}")
    
    print(f"\n{'='*80}")


if __name__ == "__main__":
    user_uuid = sys.argv[1] if len(sys.argv) > 1 else 'a33138b1-09c3-43ec-a1f2-af3bebed78b7'
    test_company_verification(user_uuid)
