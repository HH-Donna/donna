"""
Standalone Test Runner for Database-Triggered Agent Calls
==========================================================

This script runs all tests without requiring pytest.
Run with: python3 run_database_trigger_tests.py
"""

import sys
import traceback
from unittest.mock import Mock, patch
from datetime import datetime

# Import test module
sys.path.insert(0, '.')

try:
    from test_database_trigger_calls import (
        test_01_successful_call_initiation,
        test_02_database_fetch_unsure_emails,
        test_03_dynamic_variable_mapping,
        test_04_phone_number_determination,
        test_05_database_update_on_call_initiation,
        test_06_missing_all_phone_numbers,
        test_07_malformed_email_data,
        test_08_null_and_empty_dynamic_variables,
        test_09_concurrent_call_triggers,
        test_10_api_failure_handling,
        valid_email_data,
        minimal_email_data,
        mock_supabase_client,
        mock_api_success,
        mock_api_failure
    )
except ImportError as e:
    print(f"❌ Error importing tests: {e}")
    print("Make sure test_database_trigger_calls.py is in the same directory")
    sys.exit(1)


def run_test(test_func, *args):
    """Run a single test function and report results"""
    test_name = test_func.__name__.replace('test_', 'TEST ').replace('_', ' ').upper()
    
    try:
        test_func(*args)
        print(f"✅ PASSED: {test_name}")
        return True
    except AssertionError as e:
        print(f"❌ FAILED: {test_name}")
        print(f"   Assertion Error: {e}")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ ERROR: {test_name}")
        print(f"   Exception: {e}")
        traceback.print_exc()
        return False


def create_fixtures():
    """Create test fixtures"""
    valid_email = {
        "id": "email_12345",
        "label": "unsure",
        "vendor_name": "Spotify",
        "invoice_number": "INV-300050",
        "amount": 900.00,
        "due_date": "2025-11-15",
        "contact_phone": "+14155551234",
        "contact_email": "billing@spotify.com",
        "billing_address": "123 Main St",
        "local_phone": "+18001234567",
        "db_phone": None,
        "online_phone": None,
        "official_phone": "+18005551234",
        "customer_org": "Pixamp, Inc",
        "created_at": "2025-10-05T10:00:00Z"
    }
    
    minimal_email = {
        "id": "email_minimal",
        "label": "unsure",
        "vendor_name": "Unknown Vendor",
        "contact_phone": "+14155551234"
    }
    
    # Create mock Supabase client
    mock_supabase = Mock()
    
    # Create mock API success response
    mock_api_ok = Mock()
    mock_api_ok.return_value = {
        'conversation_id': 'conv_test_12345',
        'status': 'initiated',
        'created_at': datetime.utcnow().isoformat()
    }
    
    # Create mock API failure response  
    mock_api_fail = Mock()
    mock_api_fail.return_value = None
    
    return valid_email, minimal_email, mock_supabase, mock_api_ok, mock_api_fail


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("DATABASE-TRIGGERED AGENT CALL TEST SUITE")
    print("="*80)
    print("\nRunning 10 comprehensive tests (5 basic + 5 edge cases)\n")
    
    # Create fixtures
    valid_email, minimal_email, mock_supabase, mock_api_ok, mock_api_fail = create_fixtures()
    
    # Track results
    results = []
    
    # BASIC FUNCTIONALITY TESTS
    print("\n" + "-"*80)
    print("BASIC FUNCTIONALITY TESTS (5)")
    print("-"*80)
    
    with patch('services.email_to_call_service.get_supabase_client', return_value=mock_supabase):
        with patch('services.outbound_call_service._make_api_request', mock_api_ok):
            results.append(run_test(test_01_successful_call_initiation, valid_email, mock_supabase, mock_api_ok))
            results.append(run_test(test_02_database_fetch_unsure_emails, mock_supabase))
            results.append(run_test(test_03_dynamic_variable_mapping, valid_email))
            results.append(run_test(test_04_phone_number_determination, valid_email))
            results.append(run_test(test_05_database_update_on_call_initiation, mock_supabase, mock_api_ok))
    
    # EDGE CASE TESTS
    print("\n" + "-"*80)
    print("EDGE CASE TESTS (5)")
    print("-"*80)
    
    with patch('services.email_to_call_service.get_supabase_client', return_value=mock_supabase):
        results.append(run_test(test_06_missing_all_phone_numbers, minimal_email, mock_supabase))
        results.append(run_test(test_07_malformed_email_data, mock_supabase))
        results.append(run_test(test_08_null_and_empty_dynamic_variables))
        
        with patch('services.outbound_call_service._make_api_request', mock_api_ok):
            results.append(run_test(test_09_concurrent_call_triggers, valid_email, mock_supabase, mock_api_ok))
        
        with patch('services.outbound_call_service._make_api_request', mock_api_fail):
            results.append(run_test(test_10_api_failure_handling, valid_email, mock_supabase, mock_api_fail))
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(results)
    failed = len(results) - passed
    
    print(f"\n  Total Tests: {len(results)}")
    print(f"  ✅ Passed: {passed}")
    print(f"  ❌ Failed: {failed}")
    print(f"  Success Rate: {passed/len(results)*100:.1f}%")
    
    print("\n" + "="*80)
    
    if failed > 0:
        print("\n⚠️  Some tests failed. Review the output above for details.")
        sys.exit(1)
    else:
        print("\n✅ All tests passed! Database trigger system is working correctly.")
        sys.exit(0)


if __name__ == "__main__":
    main()
