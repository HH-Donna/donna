#!/usr/bin/env python3
"""Test Google company matching specifically."""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ml'))

from dotenv import load_dotenv
from app.database.supabase_client import get_supabase_client
from domain_checker import domain_from_address

load_dotenv()

# Test: Extract company name from Google's email
test_email = "payments-noreply@google.com"
domain = domain_from_address(test_email)
company_name_extracted = domain.split('.')[0].title()

print("="*80)
print("GOOGLE COMPANY NAME EXTRACTION TEST")
print("="*80)
print(f"\nEmail Address: {test_email}")
print(f"Extracted Domain: {domain}")
print(f"Company Name (from domain): '{company_name_extracted}'")

# Check what companies match this in database
user_uuid = 'a33138b1-09c3-43ec-a1f2-af3bebed78b7'
supabase = get_supabase_client()

print(f"\n{'='*80}")
print("DATABASE QUERY TEST")
print(f"{'='*80}")
print(f"Query: name ILIKE '%{company_name_extracted}%'")

companies_result = supabase.table('companies')\
    .select('name, domain, contact_emails')\
    .eq('user_id', user_uuid)\
    .ilike('name', f'%{company_name_extracted}%')\
    .execute()

print(f"\nMatches Found: {len(companies_result.data)}")

if companies_result.data:
    for idx, company in enumerate(companies_result.data, 1):
        print(f"\n{idx}. '{company['name']}'")
        print(f"   Domain: {company.get('domain', 'N/A')}")
        print(f"   Emails: {company.get('contact_emails', [])}")
        
        # Check if it's the right match
        is_correct = company.get('domain') == 'google.com'
        print(f"   Correct Match: {'✅ YES' if is_correct else '❌ NO'}")

print(f"\n{'='*80}")
print("ANALYSIS")
print(f"{'='*80}")
print(f"\nThe query 'name ILIKE %{company_name_extracted}%' matches any company")
print(f"with '{company_name_extracted}' anywhere in the name.")
print(f"\nThis is why 'Google' matches 'Google Cloud EMEA Limited' ✅")
print(f"But it might also match other companies with 'Google' in the name.")
print(f"\n💡 The matching allows for partial/fuzzy matching!")
print(f"{'='*80}")
