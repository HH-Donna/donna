"""
Import Twilio Number into ElevenLabs

This script imports your Twilio phone number into ElevenLabs using their native integration.
Run this once to set up the Twilio integration.
"""

import os
import sys
import httpx
import json

# Credentials
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVEN_LABS_AGENT_ID = os.getenv("ELEVEN_LABS_AGENT_ID")

# Twilio credentials
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

def import_twilio_number():
    """Import Twilio number into ElevenLabs"""
    print("🔧 Importing Twilio number into ElevenLabs...")
    print(f"   Phone: {TWILIO_PHONE_NUMBER}")
    print(f"   Twilio SID: {TWILIO_ACCOUNT_SID}")
    
    url = "https://api.elevenlabs.io/v1/convai/phone-number/import-twilio"
    
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "phone_number": TWILIO_PHONE_NUMBER,
        "twilio_account_sid": TWILIO_ACCOUNT_SID,
        "twilio_auth_token": TWILIO_AUTH_TOKEN,
        "label": "Donna Billing Verifier",
        "agent_id": ELEVEN_LABS_AGENT_ID  # Assign agent for inbound calls
    }
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Successfully imported Twilio number!")
                print(f"   Phone Number ID: {data.get('phone_number_id', 'N/A')}")
                print(f"   Status: {data.get('status', 'N/A')}")
                print(f"   Capabilities: {data.get('capabilities', 'N/A')}")
                return data
            elif response.status_code == 409:
                print(f"ℹ️  Phone number already imported (409 Conflict)")
                print(f"   Response: {response.text}")
                return {"status": "already_imported"}
            else:
                print(f"❌ Failed to import phone number")
                print(f"   Status Code: {response.status_code}")
                print(f"   Response: {response.text}")
                sys.exit(1)
                
    except Exception as e:
        print(f"❌ Error importing phone number: {e}")
        sys.exit(1)

def list_phone_numbers():
    """List all imported phone numbers"""
    print("\n📋 Listing imported phone numbers...")
    
    url = "https://api.elevenlabs.io/v1/convai/phone-numbers"
    
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                phone_numbers = data.get('phone_numbers', [])
                
                if not phone_numbers:
                    print("   No phone numbers found")
                    return []
                
                print(f"   Found {len(phone_numbers)} phone number(s):")
                for pn in phone_numbers:
                    print(f"\n   📞 {pn.get('phone_number', 'N/A')}")
                    print(f"      ID: {pn.get('phone_number_id', 'N/A')}")
                    print(f"      Label: {pn.get('label', 'N/A')}")
                    print(f"      Provider: {pn.get('provider', 'N/A')}")
                    print(f"      Agent ID: {pn.get('agent_id', 'Not assigned')}")
                    
                return phone_numbers
            else:
                print(f"❌ Failed to list phone numbers")
                print(f"   Status Code: {response.status_code}")
                print(f"   Response: {response.text}")
                return []
                
    except Exception as e:
        print(f"❌ Error listing phone numbers: {e}")
        return []

if __name__ == "__main__":
    print("=" * 60)
    print("🎯 ElevenLabs Twilio Integration Setup")
    print("=" * 60)
    
    # First, try to list existing phone numbers
    existing_numbers = list_phone_numbers()
    
    # Check if our number is already imported
    our_number_imported = any(
        pn.get('phone_number') == TWILIO_PHONE_NUMBER 
        for pn in existing_numbers
    )
    
    if our_number_imported:
        print(f"\n✅ Phone number {TWILIO_PHONE_NUMBER} is already imported!")
        print("   You can proceed with making outbound calls.")
    else:
        # Import the number
        print("\n")
        result = import_twilio_number()
        
        # List again to confirm
        print("\n")
        list_phone_numbers()
    
    print("\n" + "=" * 60)
    print("✅ Setup complete! You can now make outbound calls.")
    print("=" * 60)
