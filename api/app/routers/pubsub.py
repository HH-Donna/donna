import base64
import json
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from pydantic import BaseModel
from app.database import get_user_oauth_token, update_user_access_token
from app.database.gmail_watch import get_gmail_watch
from app.database.supabase_client import get_supabase_client
from app.services import create_gmail_service, get_email_attachments
from app.services.attachment_parser import process_attachments


router = APIRouter(prefix="/pubsub", tags=["pubsub"])


class PubSubMessage(BaseModel):
    """Pub/Sub push notification message format."""
    message: dict
    subscription: str = ""


async def process_new_email_background(user_id: str, history_id: str, email_address: str):
    """
    Background task to fetch and process new emails from Gmail.
    
    Args:
        user_id: User's UUID
        history_id: Gmail history ID from notification
        email_address: User's email address from notification
    """
    try:
        print(f"🔔 Processing new email notification for user {user_id}")
        print(f"   Email: {email_address}, History ID: {history_id}")
        
        # Get user's OAuth tokens
        oauth_tokens = await get_user_oauth_token(user_id)
        
        # Create Gmail service
        gmail_service, creds = create_gmail_service(
            oauth_tokens['access_token'], 
            oauth_tokens['refresh_token'],
            attempt_refresh=False
        )
        
        # Get the watch subscription to compare history IDs
        watch = await get_gmail_watch(user_id)
        if not watch:
            print(f"⚠️  No active watch found for user {user_id}")
            return
        
        stored_history_id = watch['history_id']
        
        # List history changes since last known history ID
        try:
            history_response = gmail_service.users().history().list(
                userId='me',
                startHistoryId=stored_history_id,
                historyTypes=['messageAdded'],  # Only new messages
                labelId='INBOX'
            ).execute()
            
            changes = history_response.get('history', [])
            
            if not changes:
                print(f"   ℹ️  No new messages in history")
                return
            
            # Process each new message
            new_messages = []
            for change in changes:
                messages_added = change.get('messagesAdded', [])
                for msg_added in messages_added:
                    message = msg_added.get('message', {})
                    message_id = message.get('id')
                    
                    if message_id:
                        new_messages.append(message_id)
            
            print(f"   📧 Found {len(new_messages)} new messages")
            
            # Fetch full details for each new message
            for message_id in new_messages:
                try:
                    # Get message details
                    msg = gmail_service.users().messages().get(
                        userId='me',
                        id=message_id,
                        format='full'
                    ).execute()
                    
                    # Extract headers
                    headers = {h['name']: h['value'] for h in msg['payload'].get('headers', [])}
                    
                    # Get attachments
                    attachments = get_email_attachments(gmail_service, message_id)
                    
                    # Extract text from attachments
                    attachment_text = ""
                    if attachments:
                        attachment_text = process_attachments(attachments)
                    
                    email_data = {
                        'message_id': message_id,
                        'from': headers.get('From', ''),
                        'to': headers.get('To', ''),
                        'subject': headers.get('Subject', ''),
                        'date': headers.get('Date', ''),
                        'snippet': msg.get('snippet', ''),
                        'has_attachments': len(attachments) > 0,
                        'attachment_count': len(attachments),
                        'attachment_text_length': len(attachment_text)
                    }
                    
                    print(f"   ✅ Fetched email: {email_data['subject'][:50]}")
                    print(f"      From: {email_data['from']}")
                    print(f"      Attachments: {email_data['attachment_count']}")
                    
                    # TODO: Store email in database or trigger biller extraction
                    # For now, just log the email data
                    
                except Exception as e:
                    print(f"   ❌ Error fetching message {message_id}: {e}")
                    continue
            
            # Update stored history ID to the latest
            if history_response.get('historyId'):
                new_history_id = history_response['historyId']
                supabase = get_supabase_client()
                supabase.table('gmail_watch_subscriptions')\
                    .update({'history_id': new_history_id})\
                    .eq('user_id', user_id)\
                    .eq('is_active', True)\
                    .execute()
                print(f"   📝 Updated history ID to {new_history_id}")
            
        except Exception as e:
            print(f"❌ Error fetching history: {e}")
            
    except Exception as e:
        print(f"❌ Error processing notification for user {user_id}: {e}")
        import traceback
        traceback.print_exc()


@router.post("/gmail/push")
async def receive_gmail_push(request: Request, background_tasks: BackgroundTasks):
    """
    Receive Gmail push notifications from Google Cloud Pub/Sub.
    
    This endpoint is called by Pub/Sub when new emails arrive.
    Returns 200 OK immediately and processes in background.
    """
    try:
        # Parse Pub/Sub message
        body = await request.json()
        
        # Pub/Sub sends data in this format:
        # {
        #   "message": {
        #     "data": "base64-encoded-json",
        #     "messageId": "...",
        #     "publishTime": "..."
        #   },
        #   "subscription": "..."
        # }
        
        message = body.get('message', {})
        data_encoded = message.get('data', '')
        
        if not data_encoded:
            print("⚠️  No data in Pub/Sub message")
            return {"status": "ignored", "reason": "No data"}
        
        # Decode the base64 data
        data_decoded = base64.b64decode(data_encoded).decode('utf-8')
        notification_data = json.loads(data_decoded)
        
        # Gmail notification format:
        # {
        #   "emailAddress": "user@gmail.com",
        #   "historyId": "1234567"
        # }
        
        email_address = notification_data.get('emailAddress')
        history_id = notification_data.get('historyId')
        
        if not email_address or not history_id:
            print(f"⚠️  Invalid notification data: {notification_data}")
            return {"status": "ignored", "reason": "Invalid data"}
        
        print(f"📬 Received Gmail notification:")
        print(f"   Email: {email_address}")
        print(f"   History ID: {history_id}")
        
        # Find user by email address from watch subscriptions
        supabase = get_supabase_client()
        
        watch_response = supabase.table('gmail_watch_subscriptions')\
            .select('user_id')\
            .eq('user_email', email_address)\
            .eq('is_active', True)\
            .execute()
        
        if not watch_response.data:
            print(f"⚠️  No active watch found for email {email_address}")
            return {"status": "ignored", "reason": "No watch for this email"}
        
        user_id = watch_response.data[0]['user_id']
        print(f"   👤 Processing for user: {user_id}")
        
        # Process in background
        background_tasks.add_task(
            process_new_email_background,
            user_id,
            history_id,
            email_address
        )
        
        # Return 200 OK immediately (required by Pub/Sub)
        return {
            "status": "accepted",
            "message": "Notification received and processing in background",
            "email": email_address,
            "history_id": history_id
        }
        
    except Exception as e:
        print(f"❌ Error processing Pub/Sub notification: {e}")
        import traceback
        traceback.print_exc()
        
        # Still return 200 to acknowledge receipt (prevents retries)
        return {
            "status": "error",
            "message": str(e)
        }
