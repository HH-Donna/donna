from datetime import datetime
from fastapi import HTTPException
from app.database.supabase_client import get_supabase_client


async def save_gmail_watch(user_uuid: str, history_id: str, expiration: int, topic_name: str):
    """
    Save or update Gmail watch subscription for a user.
    
    Args:
        user_uuid: User's UUID
        history_id: Gmail history ID from watch response
        expiration: Unix timestamp in milliseconds
        topic_name: Pub/Sub topic name
    """
    supabase = get_supabase_client()
    
    try:
        # Deactivate any existing watches for this user
        supabase.table('gmail_watch_subscriptions')\
            .update({'is_active': False})\
            .eq('user_id', user_uuid)\
            .execute()
        
        # Insert new watch subscription
        data = {
            'user_id': user_uuid,
            'history_id': history_id,
            'expiration': int(expiration),  # Ensure it's an integer
            'topic_name': topic_name,
            'is_active': True,
            'last_renewed_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        response = supabase.table('gmail_watch_subscriptions')\
            .insert(data)\
            .execute()
        
        if response.data:
            return {
                'success': True,
                'watch_id': response.data[0].get('id'),
                'message': 'Gmail watch subscription saved'
            }
        else:
            raise HTTPException(
                status_code=500,
                detail='Failed to save Gmail watch subscription'
            )
            
    except Exception as e:
        print(f"Error saving Gmail watch: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save Gmail watch: {str(e)}"
        )


async def get_gmail_watch(user_uuid: str):
    """
    Get active Gmail watch subscription for a user.
    
    Args:
        user_uuid: User's UUID
        
    Returns:
        Watch subscription data or None
    """
    supabase = get_supabase_client()
    
    try:
        response = supabase.table('gmail_watch_subscriptions')\
            .select('*')\
            .eq('user_id', user_uuid)\
            .eq('is_active', True)\
            .execute()
        
        if response.data:
            return response.data[0]
        return None
        
    except Exception as e:
        print(f"Error getting Gmail watch: {e}")
        return None


async def get_watches_needing_renewal():
    """
    Get all active watch subscriptions that need renewal.
    Should be called by a cron job daily.
    
    Returns:
        List of watch subscriptions that need renewal
    """
    supabase = get_supabase_client()
    
    try:
        # Get current time + 1 day in milliseconds
        renewal_threshold = int((datetime.now().timestamp() + 86400) * 1000)
        
        response = supabase.table('gmail_watch_subscriptions')\
            .select('*')\
            .eq('is_active', True)\
            .lt('expiration', renewal_threshold)\
            .execute()
        
        return response.data or []
        
    except Exception as e:
        print(f"Error getting watches for renewal: {e}")
        return []
