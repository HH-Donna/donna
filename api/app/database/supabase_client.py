import os
from supabase import create_client, Client
from fastapi import HTTPException


def get_supabase_client() -> Client:
    """Initialize and return Supabase client."""
    SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY")

    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise ValueError("NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY environment variables are required")

    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


async def get_user_oauth_token(user_uuid: str, provider: str = 'google'):
    """
    Retrieve the user's OAuth tokens from the public.user_oauth_tokens table.
    """
    supabase = get_supabase_client()
    
    try:
        # Direct table query instead of using database function
        response = supabase.table('user_oauth_tokens').select('*').eq('user_id', user_uuid).eq('provider', provider).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=404,
                detail=f"No {provider} OAuth tokens found for user. User may need to authenticate with {provider} and grant Gmail permissions."
            )
        
        token_data = response.data[0]
        access_token = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token') or ''  # Ensure it's a string, not None
        scopes = token_data.get('scopes', [])
        
        if not access_token:
            raise HTTPException(
                status_code=400,
                detail=f"No valid access token found for user. User may need to re-authenticate with {provider} and grant Gmail permissions."
            )
        
        # Check if Gmail scope is present
        gmail_scopes = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://mail.google.com/',
            'https://www.googleapis.com/auth/gmail'
        ]
        
        has_gmail_scope = any(scope in scopes for scope in gmail_scopes)
        if not has_gmail_scope:
            raise HTTPException(
                status_code=403,
                detail="User has not granted Gmail permissions. Please re-authenticate with Gmail access."
            )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'scopes': scopes
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve user OAuth tokens: {str(e)}"
        )


async def update_user_access_token(user_uuid: str, provider: str, new_access_token: str):
    """
    Update just the access token for a user (after refresh).
    """
    supabase = get_supabase_client()
    
    try:
        from datetime import datetime
        
        # Update only the access token (no expiry tracking)
        response = supabase.table('user_oauth_tokens').update({
            'access_token': new_access_token,
            'updated_at': datetime.now().isoformat()
        }).eq('user_id', user_uuid).eq('provider', provider).execute()
        
        if response.data:
            return {
                'success': True,
                'message': 'Access token updated successfully'
            }
        else:
            print(f"Warning: Failed to update access token for user {user_uuid}")
            return {
                'success': False,
                'message': 'Failed to update access token'
            }
            
    except Exception as e:
        print(f"Error updating access token: {e}")
        return {
            'success': False,
            'message': str(e)
        }


async def store_user_oauth_token(user_uuid: str, provider: str, access_token: str, 
                               refresh_token: str = None, scopes: list = None, 
                               expires_in: int = None):
    """
    Store OAuth tokens in the public.user_oauth_tokens table.
    No expiry tracking - will refresh on-demand when API calls fail.
    """
    supabase = get_supabase_client()
    
    try:
        from datetime import datetime
        
        # Direct table upsert without expiry tracking
        data = {
            'user_id': user_uuid,
            'provider': provider,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'scopes': scopes or [],
            'updated_at': datetime.now().isoformat()
        }
        
        # Try to upsert (insert or update) with proper conflict resolution
        response = supabase.table('user_oauth_tokens').upsert(
            data, 
            on_conflict='user_id,provider'
        ).execute()
        
        if response.data:
            return {
                'success': True,
                'message': 'OAuth tokens stored successfully',
                'user_id': user_uuid,
                'provider': provider
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to store OAuth tokens - no data returned"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to store OAuth tokens: {str(e)}"
        )
