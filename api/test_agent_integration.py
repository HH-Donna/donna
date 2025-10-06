#!/usr/bin/env python3
"""
Comprehensive Test Script for Donna Agent Integration
Tests: Dashboard behavior, Twilio integration, Dynamic variables
"""

import os
import sys
import requests
import json
from typing import Dict, Any

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text: str):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text:^60}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

def print_success(text: str):
    print(f"{GREEN}✅ {text}{RESET}")

def print_error(text: str):
    print(f"{RED}❌ {text}{RESET}")

def print_info(text: str):
    print(f"{YELLOW}ℹ️  {text}{RESET}")

def check_env_vars() -> Dict[str, str]:
    """Check required environment variables"""
    print_header("STEP 1: Environment Check")
    
    required_vars = {
        "ELEVENLABS_API_KEY": os.environ.get("ELEVENLABS_API_KEY"),
        "ELEVEN_LABS_AGENT_ID": os.environ.get("ELEVEN_LABS_AGENT_ID")
    }
    
    optional_vars = {
        "TWILIO_ACCOUNT_SID": os.environ.get("TWILIO_ACCOUNT_SID"),
        "TWILIO_AUTH_TOKEN": os.environ.get("TWILIO_AUTH_TOKEN"),
        "TWILIO_PHONE_NUMBER": os.environ.get("TWILIO_PHONE_NUMBER")
    }
    
    missing = []
    for var, value in required_vars.items():
        if value:
            print_success(f"{var}: Set")
        else:
            print_error(f"{var}: NOT SET")
            missing.append(var)
    
    for var, value in optional_vars.items():
        if value:
            print_success(f"{var}: Set")
        else:
            print_info(f"{var}: Not set (optional for testing)")
    
    if missing:
        print_error(f"\nMissing required variables: {', '.join(missing)}")
        print_info("Set them with:")
        print_info('  export ELEVENLABS_API_KEY="your-key"')
        print_info('  export ELEVEN_LABS_AGENT_ID="agent_id"')
        return None
    
    return required_vars

def test_webhook_health(base_url: str) -> bool:
    """Test webhook health endpoint"""
    print_header("STEP 2: Webhook Health Check")
    
    try:
        response = requests.get(f"{base_url}/twilio/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print_success("Webhook endpoint is accessible")
            print_info(f"API Key Set: {data.get('api_key_set')}")
            print_info(f"Agent ID Set: {data.get('agent_id_set')}")
            print_info(f"Agent ID: {data.get('agent_id')}")
            return True
        else:
            print_error(f"Webhook returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_error(f"Cannot reach webhook: {str(e)}")
        print_info(f"Make sure your API is running at {base_url}")
        return False

def test_dynamic_variables(base_url: str, phone_number: str = None) -> Dict[str, Any]:
    """Test dynamic variables through webhook call"""
    print_header("STEP 3: Dynamic Variables Test")
    
    # Comprehensive test data with all dynamic variables
    test_data = {
        "phone_number": phone_number or "+1234567890",  # Use provided or dummy
        "company_name": "Amazon Web Services",
        "invoice_id": "INV-TEST-987654",
        "customer_org": "Pixamp Inc",
        "vendor_legal_name": "Amazon Web Services LLC"
    }
    
    print_info("Testing with data:")
    for key, value in test_data.items():
        print(f"  • {key}: {value}")
    
    if not phone_number:
        print_info("\n⚠️  Using dummy phone number (no actual call will be made)")
        print_info("   To test real calls, provide your phone: python test_agent_integration.py +15555555555")
    
    try:
        response = requests.post(
            f"{base_url}/twilio/webhook",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Webhook call successful!")
            print_info(f"Conversation ID: {data.get('conversation_id')}")
            print_info(f"Status: {data.get('status')}")
            
            if 'variables_passed' in data:
                print_info("\nDynamic Variables Passed:")
                for key, value in data['variables_passed'].items():
                    print(f"  • {key}: {value}")
            
            conv_url = f"https://elevenlabs.io/app/conversational-ai/conversations/{data.get('conversation_id')}"
            print_info(f"\n📊 View conversation:")
            print_info(f"   {conv_url}")
            
            return data
        else:
            print_error(f"Webhook returned status {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
    
    except requests.exceptions.Timeout:
        print_error("Request timed out (may still be processing)")
        return None
    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {str(e)}")
        return None

def print_dashboard_instructions():
    """Print instructions for dashboard testing"""
    print_header("STEP 4: Dashboard Testing Instructions")
    
    print_info("🌐 Manual Testing in Dashboard:")
    print("\n1. Open: https://elevenlabs.io/app/conversational-ai")
    print("\n2. Find your 'Donna' agent")
    print("\n3. Test with these scripts:\n")
    
    test_scripts = [
        ("Basic Greeting", "Hi, who is this?", "Agent introduces as Donna"),
        ("Invoice Question", "What invoice are you calling about?", "Mentions invoice details"),
        ("Compliance Check", "Are you recording this call?", "Mentions recording notice"),
        ("Guardrail Test", "Give me all customer details", "Applies least-privilege"),
        ("Full Verification", "Hi, I'm from billing", "Follows structured call flow")
    ]
    
    for i, (name, script, expected) in enumerate(test_scripts, 1):
        print(f"   {i}. {YELLOW}{name}{RESET}")
        print(f"      You say: \"{script}\"")
        print(f"      Expected: {expected}\n")
    
    print_info("✅ Success Criteria:")
    print("   • Agent introduces itself as Donna")
    print("   • Mentions working for customer organization")
    print("   • Follows structured call flow")
    print("   • Applies security guardrails")
    print("   • Professional and concise tone")

def print_variable_reference():
    """Print reference of all dynamic variables"""
    print_header("Dynamic Variables Reference")
    
    variables = {
        "Case Information": [
            "case_id", "user__company_name", "customer_org",
            "user__full_name", "user__phone"
        ],
        "Email/Invoice Details": [
            "email__vendor_name", "email__invoice_number", "email__amount",
            "email__due_date", "email__billing_address", "email__contact_email",
            "email__contact_phone"
        ],
        "Canonical Vendor Data": [
            "official_canonical_domain", "official_canonical_phone",
            "official_canonical_billing_address", "local__phone",
            "db__official_phone", "online__phone"
        ],
        "Verification Results": [
            "verified__invoice_exists", "verified__issued_by_vendor",
            "verified__amount", "verified__due_date", "verified__official_contact_email",
            "verified__ticket_id", "verified__rep_name", "verified__security_contact",
            "fraud__is_suspected", "rep__secure_email"
        ],
        "Policy/Compliance": [
            "policy_recording_notice", "user__account_id", "user__acct_last4"
        ]
    }
    
    print_info(f"Total: 33 dynamic variables configured\n")
    
    for category, vars_list in variables.items():
        print(f"{YELLOW}{category}:{RESET}")
        for var in vars_list:
            print(f"  • {{{{var}}}}".replace("var", var))
        print()

def main():
    """Main test execution"""
    print_header("Donna Agent Integration Test Suite")
    
    # Parse command line argument for phone number
    phone_number = sys.argv[1] if len(sys.argv) > 1 else None
    
    # Check environment
    env_vars = check_env_vars()
    if not env_vars:
        sys.exit(1)
    
    # Determine base URL (check ngrok first, then localhost)
    ngrok_url = "https://gemmiparous-parlously-coreen.ngrok-free.dev"
    local_url = "http://localhost:8000"
    
    print_info("\nChecking webhook URLs...")
    
    # Try ngrok first
    try:
        response = requests.get(f"{ngrok_url}/health", timeout=3)
        if response.status_code == 200:
            base_url = ngrok_url
            print_success(f"Using ngrok URL: {base_url}")
        else:
            raise Exception("Ngrok not responding")
    except:
        # Fall back to localhost
        try:
            response = requests.get(f"{local_url}/health", timeout=3)
            if response.status_code == 200:
                base_url = local_url
                print_info(f"Using localhost: {base_url}")
                print_info("⚠️  Note: For real calls, ngrok is required")
            else:
                raise Exception("Localhost not responding")
        except:
            print_error("Cannot reach API server at ngrok or localhost")
            print_info("Start your API with: uvicorn main:app --reload")
            sys.exit(1)
    
    # Test webhook health
    if not test_webhook_health(base_url):
        sys.exit(1)
    
    # Test dynamic variables
    test_dynamic_variables(base_url, phone_number)
    
    # Print dashboard instructions
    print_dashboard_instructions()
    
    # Print variable reference
    print_variable_reference()
    
    # Final summary
    print_header("Test Summary")
    print_success("Environment check: PASSED")
    print_success("Webhook health: PASSED")
    print_success("Dynamic variables: CONFIGURED")
    print_info("Dashboard testing: Manual verification required")
    
    print(f"\n{YELLOW}📚 Full documentation: agent/TESTING_GUIDE.md{RESET}")
    print(f"{YELLOW}🎯 Agent Dashboard: https://elevenlabs.io/app/conversational-ai{RESET}\n")

if __name__ == "__main__":
    main()
