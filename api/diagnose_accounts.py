#!/usr/bin/env python3
"""
Account Diagnostic Tool
Identifies why outbound calls are failing
"""

from twilio.rest import Client
import os

# Credentials
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TARGET_NUMBER = os.getenv("TEST_PHONE_NUMBER", "+1234567890")

print("=" * 70)
print("🔍 TWILIO ACCOUNT DIAGNOSTIC")
print("=" * 70)

try:
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    
    # Get account info
    account = client.api.accounts(TWILIO_ACCOUNT_SID).fetch()
    print(f"\n📊 Account Information:")
    print(f"  Status: {account.status}")
    print(f"  Type: {account.type}")
    
    # Get balance
    balance = client.api.accounts(TWILIO_ACCOUNT_SID).balance.fetch()
    print(f"  Balance: {balance.balance} {balance.currency}")
    
    # Check if trial
    is_trial = (account.type == "Trial")
    print(f"\n🎫 Account Type: {'TRIAL ⚠️' if is_trial else 'PAID ✅'}")
    
    if is_trial:
        print(f"\n⚠️  TRIAL ACCOUNT RESTRICTION:")
        print(f"  Trial accounts can ONLY call verified numbers!")
        print(f"  This is likely why your calls are failing.")
    
    # List verified numbers
    print(f"\n📋 Verified Caller IDs:")
    verified = client.outgoing_caller_ids.list()
    
    if verified:
        for v in verified:
            print(f"  ✓ {v.phone_number}")
    else:
        print(f"  ❌ NO VERIFIED NUMBERS FOUND!")
    
    # Check if target is verified
    is_verified = any(v.phone_number == TARGET_NUMBER for v in verified)
    
    print(f"\n🎯 Target Number Analysis:")
    print(f"  Number: {TARGET_NUMBER}")
    print(f"  Verified: {'YES ✅' if is_verified else 'NO ❌'}")
    
    if is_trial and not is_verified:
        print(f"\n🔴 PROBLEM IDENTIFIED!")
        print(f"  Your account is TRIAL and {TARGET_NUMBER} is NOT VERIFIED.")
        print(f"  This is why calls are failing!")
        
        print(f"\n🔧 SOLUTION:")
        print(f"  1. Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/verified")
        print(f"  2. Click 'Add a new Caller ID'")
        print(f"  3. Enter: {TARGET_NUMBER}")
        print(f"  4. Choose: Call verification")
        print(f"  5. Complete verification")
        print(f"  6. Retry your outbound call")
        
        print(f"\n  OR upgrade account:")
        print(f"  1. Go to: https://console.twilio.com/billing")
        print(f"  2. Add $20 to account")
        print(f"  3. Account auto-upgrades")
        print(f"  4. Can call any number without verification")
        
    elif is_verified:
        print(f"\n✅ Number is verified! Issue is elsewhere.")
        print(f"  Check:")
        print(f"  1. ElevenLabs quota/usage")
        print(f"  2. Agent configuration")
        print(f"  3. Phone number integration")
    
    print(f"\n" + "=" * 70)
    print(f"✅ Diagnostic Complete")
    print(f"=" * 70)
    
except Exception as e:
    print(f"\n❌ Error running diagnostic: {e}")
    print(f"  Check your Twilio credentials are correct")

