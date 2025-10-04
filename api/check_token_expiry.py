#!/usr/bin/env python3
"""Check OAuth token expiration time."""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

# Load environment
load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

user_id = sys.argv[1] if len(sys.argv) > 1 else 'a33138b1-09c3-43ec-a1f2-af3bebed78b7'

# Get OAuth tokens
response = supabase.table('user_oauth_tokens')\
    .select('*')\
    .eq('user_id', user_id)\
    .eq('provider', 'google')\
    .execute()

if not response.data:
    print(f"❌ No OAuth tokens found for user {user_id}")
    sys.exit(1)

token_data = response.data[0]

print(f"📊 OAuth Token Information for User: {user_id}\n")
print(f"{'='*70}")
print(f"Provider: {token_data['provider']}")
print(f"Token Expires At: {token_data.get('token_expires_at', 'Not set')}")
print(f"Last Updated: {token_data.get('updated_at', 'Not set')}")
print(f"\nAccess Token: {token_data['access_token'][:50]}...")
print(f"Refresh Token: {'✅ Present' if token_data.get('refresh_token') else '❌ Missing'}")

if token_data.get('refresh_token'):
    print(f"Refresh Token: {token_data['refresh_token'][:30]}...")

# Check expiration
if token_data.get('token_expires_at'):
    try:
        from dateutil import parser as date_parser
        expires_at = date_parser.parse(token_data['token_expires_at'])
        now = datetime.now(expires_at.tzinfo) if expires_at.tzinfo else datetime.now()
        
        # Make timezone-aware if needed
        if not now.tzinfo and expires_at.tzinfo:
            import pytz
            now = pytz.UTC.localize(now)
        elif now.tzinfo and not expires_at.tzinfo:
            expires_at = pytz.UTC.localize(expires_at)
        
        time_until_expiry = expires_at - now
        
        print(f"\n{'='*70}")
        print(f"⏰ Token Expiration Status:")
        print(f"{'='*70}")
        
        if time_until_expiry.total_seconds() > 0:
            minutes = int(time_until_expiry.total_seconds() / 60)
            seconds = int(time_until_expiry.total_seconds() % 60)
            print(f"✅ Status: VALID")
            print(f"⏱️  Time Remaining: {minutes} minutes {seconds} seconds")
            print(f"📅 Expires At: {expires_at}")
            
            if minutes < 10:
                print(f"\n⚠️  WARNING: Token expires in less than 10 minutes!")
                print(f"   Auto-refresh will happen on next API call")
        else:
            minutes_ago = int(abs(time_until_expiry.total_seconds()) / 60)
            print(f"❌ Status: EXPIRED")
            print(f"⏱️  Expired: {minutes_ago} minutes ago")
            print(f"📅 Expired At: {expires_at}")
            print(f"\n🔄 Auto-refresh will happen on next API call")
            
    except Exception as e:
        print(f"\n⚠️  Could not parse expiration: {e}")
else:
    print(f"\n⚠️  No expiration time set in database")

print(f"\n{'='*70}")
print(f"💡 Google OAuth Access Tokens:")
print(f"   - Expire after: 1 hour (3600 seconds)")
print(f"   - Auto-refresh: ✅ Enabled in our system")
print(f"   - Refresh tokens: Valid for ~6 months (or until revoked)")
print(f"{'='*70}")
