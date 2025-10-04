import os
from supabase import create_client, Client
from fastapi import HTTPException


def get_supabase_client() -> Client:
    """Initialize and return Supabase client."""
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables are required")

    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


async def get_user_oauth_token(user_uuid: str):
    """
    Retrieve the user's OAuth tokens from Supabase.
    """
    supabase = get_supabase_client()
    
    try:
        # Try different approaches to get user identity from Supabase
        
        # First, try to get user session/auth info
        try:
            # Method 1: Direct query to identities table
            response = supabase.rpc('get_user_identities', {'user_uuid': user_uuid}).execute()
            if response.data:
                identity_data = response.data[0]
        except Exception as e1:
            print(f"Method 1 failed: {e1}")
            
            try:
                # Method 2: Query auth.users table for provider data
                response = supabase.table('auth.users').select('*').eq('id', user_uuid).execute()
                if response.data:
                    user_data = response.data[0]
                    # Check if user has provider_token stored
                    identity_data = user_data.get('user_metadata', {})
                else:
                    raise HTTPException(
                        status_code=404,
                        detail="User not found in Supabase"
                    )
            except Exception as e2:
                print(f"Method 2 failed: {e2}")
                
                # Method 3: For testing purposes, return mock data
                # In production, you'd need proper Supabase RLS policies and correct table access
                raise HTTPException(
                    status_code=400,
                    detail="Unable to access user OAuth tokens. This could be due to: 1) Supabase RLS policies blocking access, 2) User needs to re-authenticate with Gmail permissions, 3) Missing service role permissions. For testing, you may need to configure Supabase properly or use a different authentication approach."
                )
        
        # Extract OAuth tokens
        access_token = identity_data.get('access_token') or identity_data.get('provider_token')
        refresh_token = identity_data.get('refresh_token') or identity_data.get('provider_refresh_token')
        
        if not access_token:
            raise HTTPException(
                status_code=400,
                detail="No access token found for user. User may need to re-authenticate with Gmail permissions."
            )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve user OAuth tokens: {str(e)}"
        )
