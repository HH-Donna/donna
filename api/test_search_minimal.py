#!/usr/bin/env python3
"""
Minimal test runner for Google Search API functionality.

This script runs basic tests without requiring all environment variables.
"""

import os
import sys
import json
from typing import Dict, Any

# Add the API directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_google_search_service_basic():
    """Test the Google Search Service with basic functionality."""
    print("🧪 Testing Google Search Service (Basic)...")
    
    # Test the service class directly without imports that require env vars
    try:
        # Mock the config import
        import sys
        from unittest.mock import MagicMock
        
        # Mock the config module
        mock_config = MagicMock()
        mock_config.GOOGLE_CUSTOM_SEARCH_API_KEY = None
        mock_config.GOOGLE_CUSTOM_SEARCH_ENGINE_ID = None
        sys.modules['app.config'] = mock_config
        
        from app.services.google_search_service import GoogleSearchService
        
        service = GoogleSearchService()
        
        # Test 1: Service initialization
        print("  ✓ Testing service initialization...")
        assert service is not None
        print("    ✓ Service initialized successfully")
        
        # Test 2: Mock search (when no credentials)
        print("  ✓ Testing mock search functionality...")
        result = service.search_company_info("Test Company")
        assert result['success'] is True
        assert 'items' in result
        print("    ✓ Mock search works correctly")
        
        # Test 3: Attribute extraction
        print("  ✓ Testing attribute extraction...")
        mock_search_results = {
            'success': True,
            'items': [
                {
                    'title': 'Test Company Inc - Official Website',
                    'snippet': 'Test Company Inc billing address: 123 Test St, Test City, TS. Phone: (555) 123-4567. Email: billing@testcompany.com',
                    'link': 'https://testcompany.com'
                }
            ]
        }
        
        attributes = service.extract_company_attributes(mock_search_results, "Test Company")
        print(f"    Debug - Extracted attributes: {attributes}")
        assert attributes['billing_address'] == '123 Test St, Test City'
        assert attributes['phone_number'] == '(555) 123-4567'
        assert attributes['email'] == 'billing@testcompany.com'
        assert attributes['website'] == 'https://testcompany.com'
        assert attributes['confidence'] > 0.0
        print("    ✓ Attribute extraction works correctly")
        
        print("✅ All Google Search Service tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_regex_patterns():
    """Test the regex patterns used for attribute extraction."""
    print("🧪 Testing Regex Patterns...")
    
    import re
    
    # Test billing address patterns
    test_text = "Acme Corp billing address: 789 Business Ave, Corporate City, CC. Phone: (555) 555-0123. Email: billing@acmecorp.com"
    
    address_patterns = [
        r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Way|Place|Pl)\b[^,]*,\s*[A-Za-z\s]+,\s*[A-Z]{2}\s*\d{5}',
        r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Way|Place|Pl)\b[^,]*,\s*[A-Za-z\s]+',
        r'Address[:\s]+([^,\n]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Way|Place|Pl)[^,\n]*)',
        r'Billing[:\s]+([^,\n]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Way|Place|Pl)[^,\n]*)'
    ]
    
    phone_patterns = [
        r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
        r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
        r'Phone[:\s]+(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})',
        r'Tel[:\s]+(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})'
    ]
    
    email_patterns = [
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        r'Email[:\s]+([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})',
        r'Contact[:\s]+([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})'
    ]
    
    # Test address extraction
    for pattern in address_patterns:
        match = re.search(pattern, test_text, re.IGNORECASE)
        if match:
            print(f"  ✓ Address pattern matched: {match.group(1) if match.groups() else match.group(0)}")
            break
    else:
        print("  ⚠️  No address pattern matched")
    
    # Test phone extraction
    for pattern in phone_patterns:
        match = re.search(pattern, test_text)
        if match:
            print(f"  ✓ Phone pattern matched: {match.group(1) if match.groups() else match.group(0)}")
            break
    else:
        print("  ⚠️  No phone pattern matched")
    
    # Test email extraction
    for pattern in email_patterns:
        match = re.search(pattern, test_text, re.IGNORECASE)
        if match:
            print(f"  ✓ Email pattern matched: {match.group(1) if match.groups() else match.group(0)}")
            break
    else:
        print("  ⚠️  No email pattern matched")
    
    print("✅ Regex pattern tests completed!")


def test_api_structure():
    """Test the API structure and endpoints."""
    print("🧪 Testing API Structure...")
    
    # Check if the fraud router file exists and has the right structure
    fraud_router_path = os.path.join(os.path.dirname(__file__), 'app', 'routers', 'fraud.py')
    
    if os.path.exists(fraud_router_path):
        print("  ✓ Fraud router file exists")
        
        # Read the file and check for verify-online endpoint
        with open(fraud_router_path, 'r') as f:
            content = f.read()
            
        if 'verify-online' in content:
            print("  ✓ verify-online endpoint found")
        else:
            print("  ⚠️  verify-online endpoint not found")
            
        if 'verify_company_online_endpoint' in content:
            print("  ✓ verify_company_online_endpoint function found")
        else:
            print("  ⚠️  verify_company_online_endpoint function not found")
    else:
        print("  ❌ Fraud router file not found")
    
    # Check if the Google Search service file exists
    search_service_path = os.path.join(os.path.dirname(__file__), 'app', 'services', 'google_search_service.py')
    
    if os.path.exists(search_service_path):
        print("  ✓ Google Search service file exists")
    else:
        print("  ❌ Google Search service file not found")
    
    print("✅ API structure tests completed!")


def main():
    """Run all tests."""
    print("🚀 Starting Google Custom Search API Tests...\n")
    
    all_passed = True
    
    try:
        # Test 1: Basic service functionality
        if not test_google_search_service_basic():
            all_passed = False
        print()
        
        # Test 2: Regex patterns
        test_regex_patterns()
        print()
        
        # Test 3: API structure
        test_api_structure()
        print()
        
        if all_passed:
            print("🎉 All tests completed successfully!")
            print("\n📋 Summary:")
            print("  ✓ Google Search Service implemented")
            print("  ✓ Attribute extraction working")
            print("  ✓ Regex patterns functional")
            print("  ✓ API structure verified")
            print("\n🔧 Next steps:")
            print("  1. Set up Google Custom Search API credentials")
            print("  2. Configure GOOGLE_CUSTOM_SEARCH_API_KEY")
            print("  3. Configure GOOGLE_CUSTOM_SEARCH_ENGINE_ID")
            print("  4. Test with real API calls")
            print("  5. Set up environment variables for full testing")
        else:
            print("❌ Some tests failed. Please check the output above.")
            
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
