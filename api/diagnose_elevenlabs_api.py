"""
Diagnose ElevenLabs API 404 Errors

This script tests various ElevenLabs API endpoints to identify the source of 404 errors.
"""

import httpx
import json
import os

# Credentials
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "sk_9af95a2fca8ea120a514561389ef270c6e3c2235b3da347a")
ELEVEN_LABS_AGENT_ID = os.getenv("ELEVEN_LABS_AGENT_ID", "agent_2601k6rm4bjae2z9amfm5w1y6aps")
TWILIO_PHONE_NUMBER = "+18887064372"

print("=" * 80)
print("🔍 ElevenLabs API Diagnostics")
print("=" * 80)

print(f"\n📋 Configuration:")
print(f"   API Key: {ELEVENLABS_API_KEY[:20]}...{ELEVENLABS_API_KEY[-10:]}")
print(f"   Agent ID: {ELEVEN_LABS_AGENT_ID}")
print(f"   Phone Number: {TWILIO_PHONE_NUMBER}")

headers = {
    "xi-api-key": ELEVENLABS_API_KEY,
    "Content-Type": "application/json"
}

tests = []

# Test 1: Check API Key validity by getting user info
print("\n" + "=" * 80)
print("TEST 1: Validate API Key - Get User Info")
print("=" * 80)
try:
    with httpx.Client(timeout=30.0) as client:
        response = client.get(
            "https://api.elevenlabs.io/v1/user",
            headers=headers
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Key is VALID")
            print(f"   User: {data.get('subscription', {}).get('tier', 'N/A')}")
            print(f"   Character Count: {data.get('subscription', {}).get('character_count', 'N/A')}")
            print(f"   Character Limit: {data.get('subscription', {}).get('character_limit', 'N/A')}")
            tests.append(("User Info", "✅ PASS", response.status_code))
        else:
            print(f"❌ API Key validation failed")
            print(f"   Response: {response.text}")
            tests.append(("User Info", "❌ FAIL", response.status_code))
except Exception as e:
    print(f"❌ Error: {e}")
    tests.append(("User Info", "❌ ERROR", str(e)))

# Test 2: List available agents
print("\n" + "=" * 80)
print("TEST 2: List Agents")
print("=" * 80)
try:
    with httpx.Client(timeout=30.0) as client:
        response = client.get(
            "https://api.elevenlabs.io/v1/convai/agents",
            headers=headers
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            agents = data.get('agents', []) if isinstance(data, dict) else data
            print(f"✅ Found {len(agents)} agent(s)")
            for agent in agents[:3]:  # Show first 3
                agent_id = agent.get('agent_id', 'N/A')
                name = agent.get('name', 'N/A')
                print(f"   - {name} (ID: {agent_id})")
                if agent_id == ELEVEN_LABS_AGENT_ID:
                    print(f"     ✅ THIS IS OUR AGENT!")
            tests.append(("List Agents", "✅ PASS", response.status_code))
        else:
            print(f"❌ Failed to list agents")
            print(f"   Response: {response.text}")
            tests.append(("List Agents", "❌ FAIL", response.status_code))
except Exception as e:
    print(f"❌ Error: {e}")
    tests.append(("List Agents", "❌ ERROR", str(e)))

# Test 3: Get specific agent details
print("\n" + "=" * 80)
print("TEST 3: Get Agent Details")
print("=" * 80)
try:
    with httpx.Client(timeout=30.0) as client:
        response = client.get(
            f"https://api.elevenlabs.io/v1/convai/agents/{ELEVEN_LABS_AGENT_ID}",
            headers=headers
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Agent found")
            print(f"   Name: {data.get('name', 'N/A')}")
            print(f"   Platform: {data.get('conversation_config', {}).get('agent', {}).get('prompt', {}).get('prompt', 'N/A')[:100]}...")
            tests.append(("Get Agent", "✅ PASS", response.status_code))
        else:
            print(f"❌ Failed to get agent")
            print(f"   Response: {response.text}")
            tests.append(("Get Agent", "❌ FAIL", response.status_code))
except Exception as e:
    print(f"❌ Error: {e}")
    tests.append(("Get Agent", "❌ ERROR", str(e)))

# Test 4: List phone numbers
print("\n" + "=" * 80)
print("TEST 4: List Phone Numbers")
print("=" * 80)
try:
    with httpx.Client(timeout=30.0) as client:
        response = client.get(
            "https://api.elevenlabs.io/v1/convai/phone-numbers",
            headers=headers
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            phone_numbers = data.get('phone_numbers', []) if isinstance(data, dict) else data
            print(f"✅ Found {len(phone_numbers)} phone number(s)")
            for pn in phone_numbers:
                number = pn.get('phone_number', 'N/A')
                pn_id = pn.get('phone_number_id', 'N/A')
                agent_id = pn.get('agent_id', 'Not assigned')
                print(f"   - {number} (ID: {pn_id})")
                print(f"     Agent: {agent_id}")
                if number == TWILIO_PHONE_NUMBER:
                    print(f"     ✅ THIS IS OUR NUMBER!")
            tests.append(("List Phone Numbers", "✅ PASS", response.status_code))
        else:
            print(f"❌ Failed to list phone numbers")
            print(f"   Response: {response.text}")
            tests.append(("List Phone Numbers", "❌ FAIL", response.status_code))
except Exception as e:
    print(f"❌ Error: {e}")
    tests.append(("List Phone Numbers", "❌ ERROR", str(e)))

# Test 5: Try to create a conversation (base endpoint)
print("\n" + "=" * 80)
print("TEST 5: Create Conversation (Signed-out endpoint)")
print("=" * 80)
print("   Endpoint: POST /v1/convai/conversation")
try:
    payload = {
        "agent_id": ELEVEN_LABS_AGENT_ID
    }
    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            "https://api.elevenlabs.io/v1/convai/conversation",
            headers=headers,
            json=payload
        )
        print(f"Status: {response.status_code}")
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"✅ Conversation created")
            print(f"   Conversation ID: {data.get('conversation_id', 'N/A')}")
            print(f"   Response: {json.dumps(data, indent=2)}")
            tests.append(("Create Conversation", "✅ PASS", response.status_code))
        else:
            print(f"❌ Failed to create conversation")
            print(f"   Response: {response.text}")
            tests.append(("Create Conversation", "❌ FAIL", response.status_code))
except Exception as e:
    print(f"❌ Error: {e}")
    tests.append(("Create Conversation", "❌ ERROR", str(e)))

# Test 6: Try alternative conversation endpoint
print("\n" + "=" * 80)
print("TEST 6: Create Conversation (Alternative endpoint)")
print("=" * 80)
print("   Endpoint: POST /v1/convai/conversations")
try:
    payload = {
        "agent_id": ELEVEN_LABS_AGENT_ID
    }
    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            "https://api.elevenlabs.io/v1/convai/conversations",
            headers=headers,
            json=payload
        )
        print(f"Status: {response.status_code}")
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"✅ Conversation created")
            print(f"   Response: {json.dumps(data, indent=2)}")
            tests.append(("Create Conversation (Alt)", "✅ PASS", response.status_code))
        else:
            print(f"❌ Failed to create conversation")
            print(f"   Response: {response.text}")
            tests.append(("Create Conversation (Alt)", "❌ FAIL", response.status_code))
except Exception as e:
    print(f"❌ Error: {e}")
    tests.append(("Create Conversation (Alt)", "❌ ERROR", str(e)))

# Test 7: Check for phone call endpoint variations
print("\n" + "=" * 80)
print("TEST 7: Phone Call Endpoint Variations")
print("=" * 80)

endpoints_to_test = [
    "https://api.elevenlabs.io/v1/convai/conversation/phone",
    "https://api.elevenlabs.io/v1/convai/phone/call",
    "https://api.elevenlabs.io/v1/phone/call",
]

for endpoint in endpoints_to_test:
    print(f"\n   Testing: {endpoint}")
    try:
        payload = {
            "agent_id": ELEVEN_LABS_AGENT_ID,
            "to_phone_number": "+13473580012"
        }
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                endpoint,
                headers=headers,
                json=payload
            )
            print(f"   Status: {response.status_code}")
            if response.status_code in [200, 201]:
                print(f"   ✅ This endpoint works!")
                print(f"   Response: {response.text[:200]}")
            else:
                print(f"   ❌ {response.status_code}: {response.text[:100]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

# Test 8: Check API documentation endpoint
print("\n" + "=" * 80)
print("TEST 8: API Documentation/OpenAPI Spec")
print("=" * 80)
try:
    with httpx.Client(timeout=30.0) as client:
        response = client.get(
            "https://api.elevenlabs.io/openapi.json",
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ OpenAPI spec available")
            # Could parse this to find correct endpoints
            tests.append(("OpenAPI Spec", "✅ PASS", response.status_code))
        else:
            print(f"❌ No public OpenAPI spec")
            tests.append(("OpenAPI Spec", "❌ FAIL", response.status_code))
except Exception as e:
    print(f"❌ Error: {e}")
    tests.append(("OpenAPI Spec", "❌ ERROR", str(e)))

# Summary
print("\n" + "=" * 80)
print("📊 DIAGNOSTIC SUMMARY")
print("=" * 80)
print(f"\n{'Test':<30} {'Result':<15} {'Status Code':<15}")
print("-" * 60)
for test_name, result, status in tests:
    print(f"{test_name:<30} {result:<15} {str(status):<15}")

print("\n" + "=" * 80)
print("💡 RECOMMENDATIONS")
print("=" * 80)

# Analyze results
user_info_pass = any(t[0] == "User Info" and "PASS" in t[1] for t in tests)
list_agents_pass = any(t[0] == "List Agents" and "PASS" in t[1] for t in tests)
phone_numbers_pass = any(t[0] == "List Phone Numbers" and "PASS" in t[1] for t in tests)
create_conv_pass = any(t[0] == "Create Conversation" and "PASS" in t[1] for t in tests)

if user_info_pass:
    print("\n✅ API Key is valid and working")
else:
    print("\n❌ API Key issue - check your ELEVENLABS_API_KEY")

if list_agents_pass:
    print("✅ Agent API access is working")
else:
    print("❌ Cannot access agents - may need different permissions")

if phone_numbers_pass:
    print("✅ Phone numbers API is accessible")
else:
    print("❌ Cannot access phone numbers - may need Twilio integration")

if not create_conv_pass:
    print("\n⚠️  CONVERSATION CREATION ENDPOINTS ARE NOT WORKING")
    print("   This explains the 404 errors!")
    print("\n   Possible reasons:")
    print("   1. These endpoints require account upgrade or special access")
    print("   2. The API has been deprecated or moved")
    print("   3. Documentation is outdated")
    print("   4. Need to use dashboard for phone calls")
    print("\n   ✅ RECOMMENDED: Use ElevenLabs Dashboard for outbound calls")
    print("      https://elevenlabs.io/app/conversational-ai")
else:
    print("✅ Conversation creation works!")

print("\n" + "=" * 80)
