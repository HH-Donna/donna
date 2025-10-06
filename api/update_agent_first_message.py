#!/usr/bin/env python3
"""
Quick script to update agent's first_message to fix silence issue
"""

import os
import httpx
import json

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "sk_9af95a2fca8ea120a514561389ef270c6e3c2235b3da347a")
AGENT_ID = "agent_2601k6rm4bjae2z9amfm5w1y6aps"

# Remove the first_message to let the agent respond naturally
PATCH_DATA = {
    "conversation_config": {
        "agent": {
            "first_message": ""  # Empty string - agent will wait for user to speak first
        }
    }
}

url = f"https://api.elevenlabs.io/v1/convai/agents/{AGENT_ID}"

headers = {
    "xi-api-key": ELEVENLABS_API_KEY,
    "Content-Type": "application/json"
}

print(f"🔧 Updating agent {AGENT_ID}...")
print(f"   Setting first_message to empty string")

try:
    with httpx.Client(timeout=30.0) as client:
        response = client.patch(url, json=PATCH_DATA, headers=headers)
        
        if response.status_code == 200:
            print(f"\n✅ Agent updated successfully!")
            print(f"   The agent will now wait for the user to speak first")
            print(f"   instead of playing a potentially broken first_message")
        else:
            print(f"\n❌ Failed to update agent: {response.status_code}")
            print(f"   Response: {response.text}")
except Exception as e:
    print(f"\n❌ Error: {e}")
