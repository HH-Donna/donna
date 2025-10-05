import base64
import json
import sys
import os
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime
from app.database import get_user_oauth_token, update_user_access_token
from app.database.gmail_watch import get_gmail_watch
from app.database.supabase_client import get_supabase_client
from app.services import create_gmail_service, get_email_attachments
from app.services.attachment_parser import process_attachments

# Add ml directory to path for domain_checker import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../ml'))
from domain_checker import is_billing_email, classify_email_type_with_gemini


router = APIRouter(prefix="/pubsub", tags=["pubsub"])


class PubSubMessage(BaseModel):
    """Pub/Sub push notification message format."""
    message: dict
    subscription: str = ""


async def process_new_email_background(user_id: str, history_id: str, email_address: str):
    """
    Background task to fetch and process new emails with fraud detection.
    
    Pipeline:
    1. Fetch new email (without attachments first)
    2. Run is_billing_email() - stop if False
    3. Setup EmailFraudLogger
    4. Run classify_email_type_with_gemini() - stop if not billing
    5. Pull attachments and parse
    6. Insert into emails table with status='processing'
    
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
        
        # Get the watch subscription
        watch = await get_gmail_watch(user_id)
        if not watch:
            print(f"⚠️  No active watch found for user {user_id}")
            return
        
        stored_history_id = watch['history_id']
        
        # List history changes (with error handling for token issues)
        try:
            history_response = gmail_service.users().history().list(
                userId='me',
                startHistoryId=stored_history_id,
                historyTypes=['messageAdded'],
                labelId='INBOX'
            ).execute()
        except Exception as history_error:
            # If token is invalid/expired, try refreshing
            if 'invalid_scope' in str(history_error) or 'invalid_grant' in str(history_error):
                print(f"      ⚠️  Token error, attempting refresh...")
                if oauth_tokens.get('refresh_token'):
                    gmail_service, creds = create_gmail_service(
                        oauth_tokens['access_token'], 
                        oauth_tokens['refresh_token'],
                        attempt_refresh=True  # Force refresh
                    )
                    # Save refreshed token
                    await update_user_access_token(user_id, 'google', creds.token)
                    print(f"      ✅ Token refreshed, retrying...")
                    
                    # Retry history list
                    history_response = gmail_service.users().history().list(
                        userId='me',
                        startHistoryId=stored_history_id,
                        historyTypes=['messageAdded'],
                        labelId='INBOX'
                    ).execute()
                else:
                    print(f"      ❌ No refresh token available, user needs to re-authenticate")
                    return
            else:
                raise
        
        changes = history_response.get('history', [])
        
        if not changes:
            print(f"   ℹ️  No new messages in history")
            return
        
        # Collect new message IDs
        new_message_ids = []
        for change in changes:
            for msg_added in change.get('messagesAdded', []):
                message_id = msg_added.get('message', {}).get('id')
                if message_id:
                    new_message_ids.append(message_id)
        
        print(f"   📧 Found {len(new_message_ids)} new messages")
        
        # Process each new message through fraud detection pipeline
        for message_id in new_message_ids:
            try:
                print(f"\n   🔍 Processing message: {message_id}")
                
                # STEP 1: Fetch email WITHOUT attachments first (faster)
                msg = gmail_service.users().messages().get(
                    userId='me',
                    id=message_id,
                    format='full'
                ).execute()
                
                # STEP 2: Run is_billing_email() - quick filter
                if not is_billing_email(msg):
                    print(f"      ⏭️  Not a billing email, skipping")
                    continue
                
                print(f"      ✅ Billing email detected")
                
                # STEP 3: Setup EmailFraudLogger (TODO: implement if needed)
                fraud_logger = None  # Will be implemented when fraud logging is needed
                
                # STEP 4: Run classify_email_type_with_gemini()
                classification = classify_email_type_with_gemini(msg, user_id, fraud_logger)
                
                if not classification['is_billing']:
                    print(f"      ⏭️  Gemini classified as non-billing: {classification['reasoning']}")
                    continue
                
                print(f"      ✅ Gemini confirmed billing email: {classification['email_type']}")
                print(f"         Confidence: {classification['confidence']}")
                
                # STEP 5: Pull attachments and parse
                print(f"      📎 Fetching attachments...")
                attachments = get_email_attachments(gmail_service, message_id)
                attachment_text = ""
                if attachments:
                    attachment_text = process_attachments(attachments)
                    print(f"      ✅ Processed {len(attachments)} attachments ({len(attachment_text)} chars)")
                
                # STEP 6: Insert into emails table (matching your schema)
                headers = {h['name']: h['value'] for h in msg['payload'].get('headers', [])}
                parsed_data = classification['parsed_data']
                
                # Parse received_at to proper timestamp
                from email.utils import parsedate_to_datetime
                received_at = None
                try:
                    if headers.get('Date'):
                        received_at = parsedate_to_datetime(headers['Date']).isoformat()
                except:
                    received_at = datetime.now().isoformat()
                
                # Combine body text and attachment text
                combined_body = parsed_data.get('body_text', '')
                if attachment_text:
                    combined_body += f"\n\n=== ATTACHMENTS ===\n{attachment_text}"
                
                email_record = {
                    'user_id': user_id,  # Link email to user
                    # company_id will be null initially, set later after biller extraction
                    'sender': headers.get('From', ''),
                    'subject': headers.get('Subject', ''),
                    'body': combined_body,
                    'received_at': received_at,
                    'label': classification['email_type'],  # 'bill', 'receipt', etc.
                    'status': 'processing',
                    'attachment_content': attachment_text if attachment_text else ''
                }
                
                supabase = get_supabase_client()
                insert_response = supabase.table('emails').insert(email_record).execute()
                
                if insert_response.data:
                    print(f"      💾 Saved email to database with status='processing'")
                    print(f"         Subject: {headers.get('Subject', '')[:50]}")
                else:
                    print(f"      ❌ Failed to save email to database")
                
            except Exception as e:
                print(f"   ❌ Error processing message {message_id}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Update stored history ID
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
