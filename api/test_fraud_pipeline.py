#!/usr/bin/env python3
"""
Test the complete fraud detection pipeline with simulated emails.
This bypasses Gmail and directly tests the processing logic.
"""

import os
import sys
import base64
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ml'))

from dotenv import load_dotenv
from app.database.supabase_client import get_supabase_client
from app.services.fraud_logger import create_fraud_logger
from domain_checker import is_billing_email, classify_email_type_with_gemini, analyze_domain_legitimacy, verify_company_against_database

load_dotenv()


def create_test_gmail_message(sender, subject, body_text):
    """Create a mock Gmail API message."""
    body_encoded = base64.urlsafe_b64encode(body_text.encode()).decode()
    
    return {
        "id": f"test_{hash(sender + subject)}",
        "threadId": f"thread_{hash(sender)}",
        "payload": {
            "headers": [
                {"name": "From", "value": sender},
                {"name": "To", "value": "allen.brd.75@gmail.com"},
                {"name": "Subject", "value": subject},
                {"name": "Date", "value": datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")}
            ],
            "parts": [
                {
                    "mimeType": "text/plain",
                    "body": {"data": body_encoded}
                }
            ]
        }
    }


def run_test_case(test_name, sender, subject, body, user_uuid):
    """Run a single test case through the fraud detection pipeline."""
    print(f"\n{'='*80}")
    print(f"TEST: {test_name}")
    print(f"{'='*80}")
    print(f"From: {sender}")
    print(f"Subject: {subject}")
    print()
    
    # Create test message
    msg = create_test_gmail_message(sender, subject, body)
    
    # Setup
    supabase = get_supabase_client()
    fraud_logger = create_fraud_logger(supabase)
    
    # STEP 1: is_billing_email
    print("1️⃣ Rule-based billing detection...")
    is_billing = is_billing_email(msg)
    print(f"   Result: {'✅ Billing' if is_billing else '❌ Not billing'}")
    
    if not is_billing:
        print("   ⏭️  Stopping - not a billing email")
        return
    
    # STEP 2: Gemini classification
    print("\n2️⃣ Gemini classification...")
    classification = classify_email_type_with_gemini(msg, user_uuid, fraud_logger)
    print(f"   Is Billing: {classification['is_billing']}")
    print(f"   Type: {classification['email_type']}")
    print(f"   Confidence: {classification['confidence']}")
    print(f"   Reasoning: {classification['reasoning']}")
    
    if not classification['is_billing']:
        print("   ⏭️  Stopping - Gemini says not billing")
        return
    
    # STEP 3: Domain legitimacy
    print("\n3️⃣ Domain legitimacy analysis...")
    domain_analysis = analyze_domain_legitimacy(msg, classification['email_type'], user_uuid, fraud_logger)
    print(f"   Is Legitimate: {domain_analysis['is_legitimate']}")
    print(f"   Confidence: {domain_analysis['confidence']:.2f}")
    print(f"   Reasons: {domain_analysis['reasons']}")
    
    if not domain_analysis['is_legitimate']:
        print("   🚨 FRAUDULENT - Would move to spam")
        print(f"   Final Label: fraudulent")
        return
    
    # STEP 4: Company verification
    print("\n4️⃣ Company verification...")
    company_verification = verify_company_against_database(msg, user_uuid, fraud_logger)
    print(f"   Is Verified: {company_verification['is_verified']}")
    print(f"   Confidence: {company_verification['confidence']:.2f}")
    print(f"   Reasoning: {company_verification['reasoning']}")
    
    if company_verification.get('company_match'):
        print(f"   Matched Company: {company_verification['company_match']['name']}")
    
    # STEP 5: Determine final label
    print("\n5️⃣ Final determination...")
    if company_verification['is_verified']:
        print(f"   ✅ Company verified")
        # In real flow, would extract invoice data and check for changes here
        final_label = 'safe'
    elif company_verification.get('trigger_agent'):
        print(f"   ⚠️  Needs manual review")
        final_label = 'unsure'
    else:
        print(f"   ⚠️  Not verified")
        final_label = 'unsure'
    
    print(f"\n📊 FINAL RESULT:")
    print(f"   Label: {final_label}")
    print(f"   Status: processed")
    
    company_match = company_verification.get('company_match')
    if company_match:
        print(f"   Company ID: {company_match.get('id', 'None')}")
    else:
        print(f"   Company ID: None (not matched)")


def main():
    user_uuid = 'a33138b1-09c3-43ec-a1f2-af3bebed78b7'
    
    print("="*80)
    print("FRAUD DETECTION PIPELINE TEST SUITE")
    print("="*80)
    
    # TEST 1: Safe - Google Cloud (exact match)
    run_test_case(
        "SAFE - Google Cloud",
        "payments-noreply@google.com",
        "Google Cloud Platform Invoice - October 2025",
        """
        Google Cloud EMEA Limited
        Velasco, Clanwilliam Place, Dublin 2, Ireland
        
        Invoice Number: INV-2025-10-04-001
        Account Number: 1987-2824-6290
        Total Amount Due: £45.50
        
        Payment will be automatically charged.
        """
    , user_uuid)
    
    # TEST 2: Safe - Shopify
    run_test_case(
        "SAFE - Shopify",
        "billing@shopify.com",
        "Shopify Invoice #413943929",
        """
        Shopify Inc.
        151 O'Connor Street, Ground floor
        Ottawa ON, K2P 2L8, Canada
        
        Invoice: 413943929
        Monthly Subscription: $29.00
        Total: $31.50
        
        Payment Method: Mastercard ending in 0204
        """
    , user_uuid)
    
    # TEST 3: Unsure - New Company
    run_test_case(
        "UNSURE - Unknown Company",
        "billing@newcompany.com",
        "Invoice from New Company Ltd",
        """
        New Company Ltd
        456 Unknown Street, London, UK
        
        Invoice Number: NC-2025-001
        Total Amount Due: £500.00
        
        Bank: NatWest, Sort: 11-22-33, Account: 44556677
        """
    , user_uuid)
    
    # TEST 4: Fraudulent - Suspicious domain
    run_test_case(
        "FRAUDULENT - Typosquatting",
        "billing@g00gle.com",  # Typosquatting with zeros
        "Google Cloud Invoice - URGENT",
        """
        Google Cloud Services
        Pay immediately to avoid service interruption.
        
        Total: $999.99
        
        Bank Details:
        Account: 12345678
        """
    , user_uuid)
    
    # TEST 5: Fraudulent - Suspicious TLD
    run_test_case(
        "FRAUDULENT - Suspicious TLD",
        "billing@company.tk",  # .tk is suspicious TLD
        "Invoice Payment Required",
        """
        Legitimate Company Inc.
        Invoice: INV-001
        Amount: £250.00
        """
    , user_uuid)
    
    print(f"\n{'='*80}")
    print("TEST SUITE COMPLETE")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
