import os
from datetime import datetime, timedelta
from googleapiclient.errors import HttpError
from fastapi import HTTPException


def setup_gmail_watch(service, topic_name: str = None):
    """
    Set up Gmail push notifications for a user.
    
    Args:
        service: Gmail API service
        topic_name: Google Cloud Pub/Sub topic (defaults to env var)
        
    Returns:
        dict with historyId and expiration
    """
    if not topic_name:
        topic_name = os.getenv("GMAIL_PUBSUB_TOPIC")
        if not topic_name:
            raise ValueError("GMAIL_PUBSUB_TOPIC environment variable is required")
    
    try:
        # Call Gmail watch endpoint
        request_body = {
            'topicName': topic_name,
            'labelIds': ['INBOX'],
            'labelFilterBehavior': 'INCLUDE'
        }
        
        response = service.users().watch(userId='me', body=request_body).execute()
        
        return {
            'history_id': response.get('historyId'),
            'expiration': response.get('expiration'),  # Unix timestamp in milliseconds
            'topic_name': topic_name
        }
        
    except HttpError as error:
        raise HTTPException(
            status_code=error.resp.status,
            detail=f"Failed to setup Gmail watch: {error}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to setup Gmail watch: {str(e)}"
        )


def stop_gmail_watch(service):
    """
    Stop Gmail push notifications for a user.
    
    Args:
        service: Gmail API service
    """
    try:
        service.users().stop(userId='me').execute()
        return {'success': True, 'message': 'Gmail watch stopped'}
    except HttpError as error:
        # If watch doesn't exist, that's okay
        if error.resp.status == 404:
            return {'success': True, 'message': 'No active watch to stop'}
        raise HTTPException(
            status_code=error.resp.status,
            detail=f"Failed to stop Gmail watch: {error}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stop Gmail watch: {str(e)}"
        )


def calculate_renewal_time(expiration_ms: int) -> datetime:
    """
    Calculate when to renew the watch (1 day before expiration).
    
    Args:
        expiration_ms: Expiration timestamp in milliseconds
        
    Returns:
        datetime when renewal should happen
    """
    expiration_dt = datetime.fromtimestamp(expiration_ms / 1000)
    # Renew 1 day before expiration for safety
    renewal_dt = expiration_dt - timedelta(days=1)
    return renewal_dt


def should_renew_watch(expiration_ms: int) -> bool:
    """
    Check if a watch subscription should be renewed.
    
    Args:
        expiration_ms: Expiration timestamp in milliseconds
        
    Returns:
        True if watch should be renewed
    """
    renewal_time = calculate_renewal_time(expiration_ms)
    return datetime.now() >= renewal_time
