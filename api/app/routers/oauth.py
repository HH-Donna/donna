from fastapi import APIRouter, Depends, HTTPException, Request
from app.auth import verify_token
from app.models import OAuthTokenRequest, OAuthTokenResponse
from app.database import store_user_oauth_token
import json

router = APIRouter(prefix="/oauth", tags=["oauth"])


@router.post("/store", response_model=OAuthTokenResponse)
async def store_oauth_tokens(request: OAuthTokenRequest, token: str = Depends(verify_token)):
    """
    Store OAuth tokens for a user in the public.user_oauth_tokens table.
    This endpoint can be called by the frontend after successful OAuth authentication.
    """
    try:
        # Store the OAuth tokens using the database function
        result = await store_user_oauth_token(
            user_uuid=request.user_id,
            provider=request.provider,
            access_token=request.access_token,
            refresh_token=request.refresh_token,
            scopes=request.scopes,
            expires_in=request.expires_in
        )
        
        return OAuthTokenResponse(
            message=result.get('message', f'OAuth tokens stored successfully for {request.provider}'),
            user_id=request.user_id,
            provider=request.provider,
            stored=result.get('success', True)
        )
            
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to store OAuth tokens: {str(e)}"
        )


@router.post("/webhook/supabase")
async def supabase_oauth_webhook(request: Request):
    """
    Webhook endpoint that Supabase can call after successful OAuth authentication.
    This will automatically store the OAuth tokens when a user authenticates.
    
    This endpoint expects Supabase webhook payload with user and session data.
    """
    try:
        payload = await request.json()
        
        # Extract user and session information from Supabase webhook
        event_type = payload.get('type')
        user_data = payload.get('record', {})
        
        if event_type not in ['INSERT', 'UPDATE'] or not user_data:
            return {"status": "ignored", "reason": "Not a relevant auth event"}
        
        user_id = user_data.get('id')
        provider_token = user_data.get('provider_token')
        provider_refresh_token = user_data.get('provider_refresh_token')
        
        # Extract provider and scopes from user metadata
        user_metadata = user_data.get('user_metadata', {})
        raw_user_metadata = user_data.get('raw_user_meta_data', {})
        
        # Try to get provider info
        provider = 'google'  # Default to Google
        scopes = []
        
        # Look for provider information in various places
        if 'provider' in user_metadata:
            provider = user_metadata['provider']
        elif 'iss' in raw_user_metadata and 'google' in raw_user_metadata['iss']:
            provider = 'google'
        
        # Extract scopes if available
        if 'scope' in raw_user_metadata:
            scopes = raw_user_metadata['scope'].split(' ') if isinstance(raw_user_metadata['scope'], str) else []
        
        # Only store tokens if we have the necessary data and it's a Google OAuth
        if user_id and provider_token and provider == 'google':
            # Check if Gmail scopes are present
            gmail_scopes = [
                'https://www.googleapis.com/auth/gmail.readonly',
                'https://mail.google.com/',
                'https://www.googleapis.com/auth/gmail'
            ]
            
            has_gmail_scope = any(scope in scopes for scope in gmail_scopes)
            
            if has_gmail_scope:
                # Store the OAuth tokens
                result = await store_user_oauth_token(
                    user_uuid=user_id,
                    provider=provider,
                    access_token=provider_token,
                    refresh_token=provider_refresh_token,
                    scopes=scopes,
                    expires_in=3600  # Default 1 hour, will be updated when token refreshes
                )
                
                return {
                    "status": "success",
                    "message": f"OAuth tokens stored for user {user_id}",
                    "result": result
                }
            else:
                return {
                    "status": "ignored", 
                    "reason": "No Gmail scopes found in OAuth token"
                }
        else:
            return {
                "status": "ignored",
                "reason": "Missing required OAuth data or not Google provider"
            }
            
    except Exception as e:
        # Don't raise HTTP exceptions for webhooks, just log and return error status
        return {
            "status": "error",
            "message": f"Failed to process OAuth webhook: {str(e)}"
        }
