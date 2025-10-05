#!/usr/bin/env python3
"""
Unit tests for ElevenLabs Agent Service

Tests the phone verification functionality including:
- Script generation
- API call handling
- Error handling
- Response formatting
"""

import asyncio
import sys
import os

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.eleven_agent import ElevenLabsAgent, eleven_agent


async def test_script_generation():
    """Test verification script generation"""
    print("\n" + "="*60)
    print("TEST 1: Script Generation")
    print("="*60)
    
    agent = ElevenLabsAgent()
    
    # Test case 1: Google Cloud
    company_name = "Google Cloud"
    email = "billing@googlecloud.com"
    
    script = agent._create_verification_script(company_name, email)
    
    print(f"\n📝 Company: {company_name}")
    print(f"📧 Email: {email}")
    print(f"\n🎤 Generated Script:")
    print("-" * 60)
    print(script)
    print("-" * 60)
    
    # Verify script contains key elements
    assert company_name in script, "Script should contain company name"
    assert email in script, "Script should contain email address"
    assert "verify" in script.lower(), "Script should mention verification"
    assert "invoice" in script.lower(), "Script should mention invoices"
    
    print("\n✅ Script generation test PASSED")
    return True


async def test_verify_company_by_call():
    """Test company verification by call"""
    print("\n" + "="*60)
    print("TEST 2: Company Verification Call")
    print("="*60)
    
    agent = ElevenLabsAgent()
    
    # Test case 1: Valid company information
    test_cases = [
        {
            "company_name": "Google Cloud",
            "phone_number": "(650) 253-0000",
            "email": "billing@googlecloud.com",
            "description": "Valid Google Cloud billing"
        },
        {
            "company_name": "Shopify",
            "phone_number": "+1 (888) 746-7439",
            "email": "billing@shopify.com",
            "description": "Valid Shopify billing"
        },
        {
            "company_name": "Unknown Company",
            "phone_number": "(555) 123-4567",
            "email": "billing@unknowncompany.com",
            "description": "Unknown company"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📞 Test Case {i}: {test_case['description']}")
        print(f"   Company: {test_case['company_name']}")
        print(f"   Phone: {test_case['phone_number']}")
        print(f"   Email: {test_case['email']}")
        
        result = await agent.verify_company_by_call(
            company_name=test_case['company_name'],
            phone_number=test_case['phone_number'],
            email=test_case['email']
        )
        
        print(f"\n   📊 Result:")
        print(f"      Success: {result.get('success')}")
        print(f"      Verified: {result.get('verified')}")
        print(f"      Status: {result.get('call_status', 'N/A')}")
        
        if result.get('note'):
            print(f"      Note: {result.get('note')}")
        
        if result.get('error'):
            print(f"      Error: {result.get('error')}")
        
        # Verify response structure
        assert 'success' in result, "Result should contain 'success' field"
        assert 'verified' in result, "Result should contain 'verified' field"
        
        if result.get('success'):
            assert 'call_status' in result, "Successful result should contain 'call_status'"
            assert 'phone_number' in result, "Successful result should contain 'phone_number'"
            assert 'company_name' in result, "Successful result should contain 'company_name'"
            print(f"      ✅ Test case {i} PASSED")
        else:
            assert 'error' in result, "Failed result should contain 'error' field"
            print(f"      ⚠️  Test case {i} completed with error (expected)")
    
    print("\n✅ Company verification call test PASSED")
    return True


async def test_api_key_handling():
    """Test API key configuration handling"""
    print("\n" + "="*60)
    print("TEST 3: API Key Handling")
    print("="*60)
    
    # Test with no API key
    agent_no_key = ElevenLabsAgent()
    agent_no_key.api_key = None
    
    print("\n🔑 Testing without API key...")
    result = await agent_no_key.verify_company_by_call(
        company_name="Test Company",
        phone_number="(555) 123-4567",
        email="test@example.com"
    )
    
    print(f"   Success: {result.get('success')}")
    print(f"   Error: {result.get('error')}")
    
    assert result.get('success') == False, "Should fail without API key"
    assert 'api key' in result.get('error', '').lower(), "Error should mention API key"
    
    print("   ✅ Correctly handles missing API key")
    
    # Test with API key present
    agent_with_key = ElevenLabsAgent()
    agent_with_key.api_key = "test-api-key-12345"
    
    print("\n🔑 Testing with API key...")
    result = await agent_with_key.verify_company_by_call(
        company_name="Test Company",
        phone_number="(555) 123-4567",
        email="test@example.com"
    )
    
    print(f"   Success: {result.get('success')}")
    print(f"   Note: {result.get('note', 'N/A')}")
    
    # With API key, it should return success (mock response)
    assert result.get('success') == True, "Should succeed with API key (mock)"
    
    print("   ✅ Correctly handles API key presence")
    
    print("\n✅ API key handling test PASSED")
    return True


async def test_global_instance():
    """Test the global eleven_agent instance"""
    print("\n" + "="*60)
    print("TEST 4: Global Instance")
    print("="*60)
    
    print("\n🌐 Testing global eleven_agent instance...")
    
    # Verify it's an instance of ElevenLabsAgent
    assert isinstance(eleven_agent, ElevenLabsAgent), "Global instance should be ElevenLabsAgent"
    
    print("   ✅ Global instance is ElevenLabsAgent")
    
    # Test that it can be used
    result = await eleven_agent.verify_company_by_call(
        company_name="Test Company",
        phone_number="(555) 123-4567",
        email="test@example.com"
    )
    
    assert 'success' in result, "Global instance should work"
    print("   ✅ Global instance is functional")
    
    print("\n✅ Global instance test PASSED")
    return True


async def test_script_variations():
    """Test script generation with various inputs"""
    print("\n" + "="*60)
    print("TEST 5: Script Variations")
    print("="*60)
    
    agent = ElevenLabsAgent()
    
    test_cases = [
        ("Google Cloud", "billing@googlecloud.com"),
        ("Shopify Inc.", "invoices@shopify.com"),
        ("AWS", "billing@aws.amazon.com"),
        ("Company with Spaces", "billing@company-with-spaces.com"),
        ("123 Numeric Company", "billing@123numeric.com")
    ]
    
    for company_name, email in test_cases:
        print(f"\n📝 Testing: {company_name} ({email})")
        
        script = agent._create_verification_script(company_name, email)
        
        # Verify script quality
        assert len(script) > 50, "Script should be substantial"
        assert company_name in script, f"Script should contain '{company_name}'"
        assert email in script, f"Script should contain '{email}'"
        
        # Check for professional language
        assert any(word in script.lower() for word in ['verify', 'confirm', 'legitimate']), \
            "Script should use verification language"
        
        print(f"   ✅ Script length: {len(script)} chars")
        print(f"   ✅ Contains company name and email")
    
    print("\n✅ Script variations test PASSED")
    return True


async def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 ELEVENLABS AGENT TEST SUITE")
    print("="*60)
    
    tests = [
        ("Script Generation", test_script_generation),
        ("Company Verification Call", test_verify_company_by_call),
        ("API Key Handling", test_api_key_handling),
        ("Global Instance", test_global_instance),
        ("Script Variations", test_script_variations)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, "PASSED", None))
        except AssertionError as e:
            results.append((test_name, "FAILED", str(e)))
            print(f"\n❌ {test_name} FAILED: {e}")
        except Exception as e:
            results.append((test_name, "ERROR", str(e)))
            print(f"\n💥 {test_name} ERROR: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, status, _ in results if status == "PASSED")
    failed = sum(1 for _, status, _ in results if status == "FAILED")
    errors = sum(1 for _, status, _ in results if status == "ERROR")
    
    for test_name, status, error in results:
        if status == "PASSED":
            print(f"✅ {test_name}: {status}")
        elif status == "FAILED":
            print(f"❌ {test_name}: {status} - {error}")
        else:
            print(f"💥 {test_name}: {status} - {error}")
    
    print(f"\n🎯 Results: {passed} passed, {failed} failed, {errors} errors")
    print(f"📈 Success Rate: {passed}/{len(tests)} ({passed/len(tests)*100:.1f}%)")
    
    if passed == len(tests):
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
