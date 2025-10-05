from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from pydantic import BaseModel
from app.auth import verify_token
from app.models import EmailRequest
from app.database import get_user_oauth_token, update_user_access_token
from app.database.gmail_watch import save_gmail_watch, get_gmail_watch
from app.database.supabase_client import get_supabase_client
from app.services import create_gmail_service
from app.services.gmail_watch import setup_gmail_watch, stop_gmail_watch


router = APIRouter(prefix="/gmail/watch", tags=["gmail-watch"])


class WatchSetupResponse(BaseModel):
    """Response model for watch setup."""
    message: str
    user_uuid: str
    history_id: str
    expiration: int
    expires_in_days: float


@router.post("/setup", response_model=WatchSetupResponse)
async def setup_user_gmail_watch(request: EmailRequest, token: str = Depends(verify_token)):
    """
    Wire up Gmail push notifications for a user.
    Sets up watch on user's Gmail inbox and stores subscription info.
    
    This should be called once after user completes OAuth consent.
    """
    try:
        # Get user's OAuth tokens
        oauth_tokens = await get_user_oauth_token(request.user_uuid)
        
        # Create Gmail service
        gmail_service, creds = create_gmail_service(
            oauth_tokens['access_token'], 
            oauth_tokens['refresh_token'],
            attempt_refresh=False
        )
        
        # Get user's email address
        from app.services import get_user_email_address
        user_email = get_user_email_address(gmail_service)
        
        # Set up Gmail watch
        watch_data = setup_gmail_watch(gmail_service)
        
        # Save watch subscription to database (with user email for matching)
        await save_gmail_watch(
            request.user_uuid,
            watch_data['history_id'],
            watch_data['expiration'],
            watch_data['topic_name'],
            user_email
        )
        
        # Calculate days until expiration
        from datetime import datetime
        # Ensure expiration is an integer
        expiration_ms = int(watch_data['expiration'])
        expiration_dt = datetime.fromtimestamp(expiration_ms / 1000)
        days_until_expiry = (expiration_dt - datetime.now()).days
        
        return WatchSetupResponse(
            message=f"Gmail watch successfully set up for user",
            user_uuid=request.user_uuid,
            history_id=watch_data['history_id'],
            expiration=watch_data['expiration'],
            expires_in_days=days_until_expiry
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to setup Gmail watch: {str(e)}"
        )


@router.post("/stop")
async def stop_user_gmail_watch(request: EmailRequest, token: str = Depends(verify_token)):
    """
    Stop Gmail push notifications for a user.
    """
    try:
        # Get user's OAuth tokens
        oauth_tokens = await get_user_oauth_token(request.user_uuid)
        
        # Create Gmail service
        gmail_service, creds = create_gmail_service(
            oauth_tokens['access_token'], 
            oauth_tokens['refresh_token'],
            attempt_refresh=False
        )
        
        # Stop Gmail watch
        result = stop_gmail_watch(gmail_service)
        
        # Deactivate in database
        supabase = get_supabase_client()
        supabase.table('gmail_watch_subscriptions')\
            .update({'is_active': False, 'updated_at': datetime.now().isoformat()})\
            .eq('user_id', request.user_uuid)\
            .execute()
        
        return {
            'message': 'Gmail watch stopped',
            'user_uuid': request.user_uuid
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stop Gmail watch: {str(e)}"
        )


@router.get("/status")
async def get_watch_status(user_uuid: str, token: str = Depends(verify_token)):
    """
    Get the current Gmail watch status for a user.
    """
    try:
        watch = await get_gmail_watch(user_uuid)
        
        if not watch:
            return {
                'user_uuid': user_uuid,
                'is_active': False,
                'message': 'No active Gmail watch found'
            }
        
        # Calculate expiration info
        from datetime import datetime
        expiration_dt = datetime.fromtimestamp(watch['expiration'] / 1000)
        now = datetime.now()
        days_until_expiry = (expiration_dt - now).days
        hours_until_expiry = int((expiration_dt - now).total_seconds() / 3600)
        
        needs_renewal = days_until_expiry < 1  # Renew if less than 1 day left
        
        return {
            'user_uuid': user_uuid,
            'is_active': watch['is_active'],
            'history_id': watch['history_id'],
            'expiration': watch['expiration'],
            'expiration_date': expiration_dt.isoformat(),
            'days_until_expiry': days_until_expiry,
            'hours_until_expiry': hours_until_expiry,
            'needs_renewal': needs_renewal,
            'last_renewed_at': watch['last_renewed_at']
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get watch status: {str(e)}"
        )
