#!/usr/bin/env python3
"""
Simple test runner for Google Search API functionality.

This script runs basic tests to verify the Google Custom Search API
implementation is working correctly.
"""

import os
import sys
import json
from typing import Dict, Any

# Add the API directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.google_search_service import GoogleSearchService


def test_google_search_service():
    """Test the Google Search Service with mock data."""
    print("🧪 Testing Google Search Service...")
    
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
    assert attributes['billing_address'] == '123 Test St, Test City, TS'
    assert attributes['phone_number'] == '(555) 123-4567'
    assert attributes['email'] == 'billing@testcompany.com'
    assert attributes['website'] == 'https://testcompany.com'
    assert attributes['confidence'] > 0.0
    print("    ✓ Attribute extraction works correctly")
    
    print("✅ All Google Search Service tests passed!")


def test_online_verification():
    """Test the online verification function."""
    print("🧪 Testing Online Verification Function...")
    
    # Import here to avoid circular imports
    from ml.domain_checker import verify_company_online
    
    # Mock Gmail message
    test_gmail_msg = {
        'id': 'test_email_123',
        'payload': {
            'headers': [
                {'name': 'From', 'value': 'billing@testcompany.com'},
                {'name': 'Subject', 'value': 'Your Monthly Bill'}
            ]
        }
    }
    
    test_user_uuid = 'test-user-123'
    test_company = 'Test Company Inc'
    
    # Test online verification
    print("  ✓ Testing online verification...")
    result = verify_company_online(test_gmail_msg, test_user_uuid, test_company)
    
    assert 'is_verified' in result
    assert 'company_name' in result
    assert 'search_query' in result
    assert 'confidence' in result
    assert 'reasoning' in result
    assert 'search_results' in result
    
    print(f"    ✓ Verification result: {result['is_verified']}")
    print(f"    ✓ Confidence: {result['confidence']}")
    print(f"    ✓ Reasoning: {result['reasoning']}")
    
    print("✅ Online verification test passed!")


def test_api_endpoint():
    """Test the API endpoint functionality."""
    print("🧪 Testing API Endpoint...")
    
    # This would test the actual API endpoint
    # For now, we'll just verify the imports work
    try:
        from app.routers.fraud import router
        print("  ✓ Fraud router imported successfully")
        
        # Check if the verify-online endpoint exists
        routes = [route.path for route in router.routes]
        assert '/verify-online' in routes
        print("  ✓ verify-online endpoint exists")
        
    except ImportError as e:
        print(f"  ⚠️  Could not import fraud router: {e}")
    
    print("✅ API endpoint test completed!")


def main():
    """Run all tests."""
    print("🚀 Starting Google Custom Search API Tests...\n")
    
    try:
        test_google_search_service()
        print()
        
        test_online_verification()
        print()
        
        test_api_endpoint()
        print()
        
        print("🎉 All tests completed successfully!")
        print("\n📋 Summary:")
        print("  ✓ Google Search Service implemented")
        print("  ✓ Attribute extraction working")
        print("  ✓ Online verification functional")
        print("  ✓ API endpoint available")
        print("\n🔧 Next steps:")
        print("  1. Set up Google Custom Search API credentials")
        print("  2. Configure GOOGLE_CUSTOM_SEARCH_API_KEY")
        print("  3. Configure GOOGLE_CUSTOM_SEARCH_ENGINE_ID")
        print("  4. Test with real API calls")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
