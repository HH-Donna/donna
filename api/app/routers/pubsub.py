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
from app.services import create_gmail_service, get_email_attachments, move_email_to_spam
from app.services.attachment_parser import process_attachments
from app.services.fraud_logger import create_fraud_logger
from app.services.invoice_extractor import extract_invoice_data
from app.services.attribute_comparator import compare_attributes

# Add ml directory to path for domain_checker import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../ml'))
from domain_checker import is_billing_email, classify_email_type_with_gemini, analyze_domain_legitimacy, verify_company_against_database


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
        
        # Setup EmailFraudLogger for this user
        supabase = get_supabase_client()
        fraud_logger = create_fraud_logger(supabase)
        
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
                
                print(f"      ✅ Billing email detected (rule-based)")
                
                # STEP 3: Run classify_email_type_with_gemini() with fraud logger
                classification = classify_email_type_with_gemini(msg, user_id, fraud_logger)
                
                if not classification['is_billing']:
                    print(f"      ⏭️  Gemini classified as non-billing: {classification['reasoning']}")
                    continue
                
                print(f"      ✅ Gemini confirmed billing email: {classification['email_type']}")
                print(f"         Confidence: {classification['confidence']}")
                print(f"         Logged {len(classification.get('log_entries', []))} fraud analysis steps")
                
                # STEP 4: Analyze domain legitimacy (with fraud logger)
                print(f"      🔍 Analyzing domain legitimacy...")
                domain_analysis = analyze_domain_legitimacy(
                    msg, 
                    classification['email_type'], 
                    user_id, 
                    fraud_logger
                )
                
                # Check if domain is legitimate
                if not domain_analysis['is_legitimate']:
                    print(f"      🚨 FRAUDULENT domain detected!")
                    print(f"         Reasons: {', '.join(domain_analysis['reasons'])}")
                    print(f"         Confidence: {domain_analysis['confidence']}")
                    
                    # Move to spam/junk
                    print(f"      📤 Moving email to spam...")
                    spam_result = move_email_to_spam(gmail_service, message_id)
                    
                    if spam_result['success']:
                        print(f"      ✅ Email moved to spam successfully")
                    
                    # Pull attachments for record keeping
                    attachments = get_email_attachments(gmail_service, message_id)
                    attachment_text = process_attachments(attachments) if attachments else ''
                    
                    # Insert into database with label='fraudulent' and status='processed'
                    headers = {h['name']: h['value'] for h in msg['payload'].get('headers', [])}
                    parsed_data = classification['parsed_data']
                    
                    from email.utils import parsedate_to_datetime
                    try:
                        received_at = parsedate_to_datetime(headers['Date']).isoformat() if headers.get('Date') else datetime.now().isoformat()
                    except:
                        received_at = datetime.now().isoformat()
                    
                    combined_body = parsed_data.get('body_text', '')
                    if attachment_text:
                        combined_body += f"\n\n=== ATTACHMENTS ===\n{attachment_text}"
                    
                    email_record = {
                        'user_id': user_id,
                        'sender': headers.get('From', ''),
                        'subject': headers.get('Subject', ''),
                        'body': combined_body,
                        'received_at': received_at,
                        'label': 'fraudulent',  # Mark as fraudulent
                        'status': 'processed',   # Processing complete
                        'attachment_content': attachment_text if attachment_text else ''
                    }
                    
                    supabase = get_supabase_client()
                    supabase.table('emails').insert(email_record).execute()
                    print(f"      💾 Saved fraudulent email with label='fraudulent', status='processed'")
                    
                    # Stop processing this email
                    continue
                
                print(f"      ✅ Domain legitimate, continuing...")
                print(f"         Logged {len(domain_analysis.get('log_entries', []))} domain analysis steps")
                
                # STEP 5: Pull attachments and parse
                print(f"      📎 Fetching attachments...")
                attachments = get_email_attachments(gmail_service, message_id)
                attachment_text = ""
                if attachments:
                    attachment_text = process_attachments(attachments)
                    print(f"      ✅ Processed {len(attachments)} attachments ({len(attachment_text)} chars)")
                
                # STEP 6: Verify company against database
                print(f"      🏢 Verifying company against database...")
                company_verification = verify_company_against_database(
                    msg,
                    user_id,
                    fraud_logger
                )
                
                print(f"      {'✅' if company_verification['is_verified'] else '⚠️'} Company verification: {company_verification['reasoning']}")
                print(f"         Logged {len(company_verification.get('log_entries', []))} verification steps")
                
                # STEP 7: Extract invoice data if company is verified
                invoice_data = None
                sensitive_changes_detected = False
                attribute_changes = []
                
                if company_verification['is_verified']:
                    print(f"      📊 Extracting invoice data...")
                    headers = {h['name']: h['value'] for h in msg['payload'].get('headers', [])}
                    parsed_data = classification['parsed_data']
                    
                    invoice_data = extract_invoice_data(
                        parsed_data.get('body_text', ''),
                        attachment_text,
                        headers.get('From', '')
                    )
                    
                    print(f"      ✅ Extracted invoice data:")
                    print(f"         Invoice #: {invoice_data.get('invoice_number', 'N/A')}")
                    print(f"         Amount: £{invoice_data.get('amount', 0.0):.2f}")
                    print(f"         Account #: {invoice_data.get('user_account_number', 'N/A')}")
                    print(f"         Address: {invoice_data.get('billing_address', 'N/A')[:50]}...")
                    print(f"         Phone: {invoice_data.get('biller_phone_number', 'N/A')}")
                    
                    # STEP 7.5: Compare with stored company data using fuzzy matching
                    matched_company = company_verification.get('company_match')
                    if matched_company:
                        print(f"      🔍 Comparing with stored company data (fuzzy matching)...")
                        
                        # Use smart attribute comparison instead of exact matching
                        attribute_changes = compare_attributes(matched_company, invoice_data)
                        
                        if attribute_changes:
                            print(f"      📊 Comparison results:")
                            for change in attribute_changes:
                                print(f"         {change['field']}: {change['similarity_score']:.2f} similarity ({change['severity']})")
                        
                        # Evaluate if changes are suspicious
                        if attribute_changes:
                            sensitive_changes_detected = True
                            critical_changes = [c for c in attribute_changes if c['severity'] == 'critical']
                            high_changes = [c for c in attribute_changes if c['severity'] == 'high']
                            
                            print(f"      🚨 SENSITIVE CHANGES DETECTED!")
                            print(f"         Critical: {len(critical_changes)} (bank details)")
                            print(f"         High: {len(high_changes)} (address/email)")
                            print(f"         Total: {len(attribute_changes)} changes")
                            
                            for change in attribute_changes:
                                print(f"         ⚠️  {change['field']} ({change['severity']}):")
                                print(f"            Stored: {str(change['stored'])[:50]}...")
                                print(f"            Received: {str(change['received'])[:50]}...")
                            
                            # Log sensitive changes detection
                            try:
                                change_detection_result = {
                                    'changes_detected': True,
                                    'critical_count': len(critical_changes),
                                    'high_count': len(high_changes),
                                    'total_changes': len(attribute_changes),
                                    'changes': attribute_changes,
                                    'company_name': matched_company['name'],
                                    'requires_research': len(critical_changes) > 0 or len(high_changes) > 0
                                }
                                
                                fraud_logger.log_sensitive_changes(
                                    message_id,
                                    user_id,
                                    change_detection_result
                                )
                                print(f"         📝 Logged sensitive changes detection")
                            except Exception as log_err:
                                print(f"         ⚠️  Failed to log changes: {log_err}")
                        else:
                            print(f"      ✅ No sensitive changes detected - all data matches")
                
                # STEP 8: Insert into emails table with appropriate label
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
                
                # Determine label based on verification and sensitive changes
                if company_verification['is_verified']:
                    if sensitive_changes_detected:
                        # Company verified BUT sensitive data changed - needs investigation
                        label = 'unsure'  # High risk, needs advanced research
                        
                        critical_changes = [c for c in attribute_changes if c['severity'] == 'critical']
                        if critical_changes:
                            print(f"      🚨 Marking as UNSURE (HIGH RISK) - critical changes detected")
                            print(f"         → Needs advanced research before final determination")
                        else:
                            print(f"      ⚠️  Marking as UNSURE - sensitive changes detected")
                    else:
                        # Company verified and no changes
                        label = 'safe'
                        print(f"      ✅ Marking as SAFE - company verified, no changes")
                elif company_verification.get('trigger_agent'):
                    label = 'unsure'  # Needs manual review
                else:
                    label = 'unsure'  # Default to unsure if not verified
                
                # Build unsure_about array from detected changes
                unsure_about_fields = []
                if attribute_changes:
                    unsure_about_fields = [change['field'] for change in attribute_changes]
                
                email_record = {
                    'user_id': user_id,
                    # company_id will be set if company was matched
                    'company_id': company_verification.get('company_match', {}).get('id') if company_verification.get('company_match') else None,
                    'sender': headers.get('From', ''),
                    'subject': headers.get('Subject', ''),
                    'body': combined_body,
                    'received_at': received_at,
                    'label': label,  # 'safe', 'unsure', or 'fraudulent'
                    'status': 'processed',  # Processing complete
                    'attachment_content': attachment_text if attachment_text else '',
                    # Extracted invoice fields
                    'billing_address': invoice_data.get('billing_address') if invoice_data else None,
                    'payment_method': invoice_data.get('payment_method') if invoice_data else None,
                    'biller_billing_details': invoice_data.get('biller_billing_details') if invoice_data else None,
                    'contact_email': invoice_data.get('contact_email') if invoice_data else None,
                    'user_account_number': invoice_data.get('user_account_number') if invoice_data else None,
                    'biller_phone_number': invoice_data.get('biller_phone_number') if invoice_data else None,
                    'invoice_number': invoice_data.get('invoice_number') if invoice_data else None,
                    'amount': invoice_data.get('amount', 0.0) if invoice_data else None,
                    'unsure_about': unsure_about_fields  # Fields with detected changes
                }
                
                # Add extracted invoice data and change detection as metadata
                metadata = {}
                if invoice_data:
                    metadata['extracted_invoice_data'] = invoice_data
                
                if attribute_changes:
                    critical_count = len([c for c in attribute_changes if c['severity'] == 'critical'])
                    high_count = len([c for c in attribute_changes if c['severity'] == 'high'])
                    
                    # Determine risk level
                    if critical_count > 0:
                        risk_level = 'high'  # Critical changes = high risk
                    elif high_count > 0:
                        risk_level = 'medium'
                    else:
                        risk_level = 'low'
                    
                    metadata['sensitive_changes'] = {
                        'detected': True,
                        'risk_level': risk_level,
                        'changes': attribute_changes,
                        'critical_count': critical_count,
                        'high_count': high_count,
                        'requires_advanced_research': critical_count > 0 or high_count > 0
                    }
                
                if metadata:
                    email_record['body'] += f"\n\n=== METADATA ===\n{json.dumps(metadata, indent=2)}"
                
                supabase = get_supabase_client()
                insert_response = supabase.table('emails').insert(email_record).execute()
                
                if insert_response.data:
                    print(f"      💾 Saved email to database")
                    print(f"         Label: {label}")
                    print(f"         Status: processed")
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

@router.post("/test/email")
async def test_email_processing(request: Request, background_tasks: BackgroundTasks):
    """
    Test endpoint for fraud detection pipeline with direct JSON input.
    
    This endpoint bypasses Gmail API and processes synthetic email data directly.
    Perfect for testing the complete fraud detection workflow.
    """
    try:
        # Parse the test email data
        email_data = await request.json()
        
        print(f"🧪 TEST EMAIL PROCESSING:")
        print(f"   From: {email_data.get('from', 'N/A')}")
        print(f"   Subject: {email_data.get('subject', 'N/A')}")
        print(f"   Message ID: {email_data.get('message_id', 'N/A')}")
        
        # Extract required fields
        user_id = email_data.get('user_id', 'test-user-123')
        user_email = email_data.get('user_email', 'test@example.com')
        message_id = email_data.get('message_id', 'test-msg-001')
        
        # Create a mock email message structure
        mock_message = {
            'id': message_id,
            'threadId': f'thread-{message_id}',
            'payload': {
                'headers': [
                    {'name': 'From', 'value': email_data.get('from', '')},
                    {'name': 'To', 'value': user_email},
                    {'name': 'Subject', 'value': email_data.get('subject', '')},
                    {'name': 'Date', 'value': email_data.get('received_at', datetime.now().isoformat())}
                ],
                'body': {
                    'data': base64.b64encode(email_data.get('body', '').encode()).decode()
                }
            }
        }
        
        # Process in background using the same logic as the real pipeline
        background_tasks.add_task(
            process_test_email_background,
            user_id,
            user_email,
            mock_message,
            email_data
        )
        
        print(f"✅ Test email queued for processing")
        
        return {
            "status": "accepted",
            "message": "Test email received and processing in background",
            "user_id": user_id,
            "message_id": message_id
        }
        
    except Exception as e:
        print(f"❌ Error processing test email: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "status": "error",
            "message": str(e)
        }

async def process_test_email_background(user_id: str, user_email: str, mock_message: dict, email_data: dict):
    """
    Process test email through the complete fraud detection pipeline.
    
    This function runs the same logic as process_new_email_background but with synthetic data.
    """
    try:
        print(f"🔄 PROCESSING TEST EMAIL: {email_data.get('message_id')}")
        print(f"   User: {user_id} ({user_email})")
        print(f"   From: {email_data.get('from')}")
        print(f"   Subject: {email_data.get('subject')}")
        
        # Get user's OAuth tokens
        oauth_tokens = await get_user_oauth_token(user_id)
        if not oauth_tokens:
            print(f"❌ No OAuth tokens found for user {user_id}")
            return
        
        print(f"✅ OAuth tokens found for user {user_id}")
        
        # Create Gmail service with lazy refresh
        gmail_service = create_gmail_service(oauth_tokens, attempt_refresh=True)
        
        # Setup EmailFraudLogger for this user
        supabase = get_supabase_client()
        fraud_logger = create_fraud_logger(supabase)
        
        # Extract email headers and body
        headers = {}
        for header in mock_message['payload']['headers']:
            headers[header['name']] = header['value']
        
        # Decode body
        body_data = mock_message['payload']['body']['data']
        body_text = base64.b64decode(body_data).decode('utf-8')
        
        print(f"📧 Email Content:")
        print(f"   From: {headers.get('From', 'N/A')}")
        print(f"   Subject: {headers.get('Subject', 'N/A')}")
        print(f"   Body Length: {len(body_text)} chars")
        
        # STEP 1: Check if it's a billing email
        print(f"\n🔍 STEP 1: Checking if billing email...")
        is_billing = is_billing_email(mock_message)
        print(f"   Result: {'✅ Billing' if is_billing else '❌ Not billing'}")
        
        if not is_billing:
            print(f"⏭️  Skipping non-billing email")
            return
        
        # STEP 2: Classify email type with Gemini
        print(f"\n🤖 STEP 2: AI Classification...")
        classification = classify_email_type_with_gemini(
            headers.get('From', ''),
            headers.get('Subject', ''),
            body_text,
            user_id,
            fraud_logger
        )
        print(f"   Email Type: {classification.get('email_type', 'unknown')}")
        print(f"   Confidence: {classification.get('confidence', 0):.2f}")
        print(f"   Reasoning: {classification.get('reasoning', 'N/A')}")
        
        if classification.get('email_type') != 'invoice':
            print(f"⏭️  Skipping non-invoice email")
            return
        
        # STEP 3: Analyze domain legitimacy
        print(f"\n🌐 STEP 3: Domain Analysis...")
        domain_analysis = analyze_domain_legitimacy(mock_message, classification['email_type'], user_id, fraud_logger)
        print(f"   Domain: {domain_analysis.get('domain', 'N/A')}")
        print(f"   Is Legitimate: {domain_analysis.get('is_legitimate', False)}")
        print(f"   Confidence: {domain_analysis.get('confidence', 0):.2f}")
        print(f"   Reasons: {domain_analysis.get('reasons', [])}")
        
        if not domain_analysis.get('is_legitimate', False):
            print(f"🚨 DOMAIN NOT LEGITIMATE - Marking as fraudulent")
            # Move to spam and save as fraudulent
            try:
                move_email_to_spam(gmail_service, mock_message['id'])
                print(f"✅ Moved to spam")
            except Exception as e:
                print(f"⚠️  Could not move to spam: {e}")
            
            # Save to database as fraudulent
            email_record = {
                'user_id': user_id,
                'company_id': None,
                'sender': headers.get('From', ''),
                'subject': headers.get('Subject', ''),
                'body': body_text,
                'received_at': headers.get('Date', datetime.now().isoformat()),
                'label': 'fraudulent',
                'status': 'processed',
                'attachment_content': '',
                'billing_address': None,
                'payment_method': None,
                'biller_billing_details': None,
                'contact_email': None,
                'user_account_number': None,
                'biller_phone_number': None,
                'invoice_number': None,
                'amount': None,
                'unsure_about': []
            }
            
            result = supabase.table('emails').insert(email_record).execute()
            print(f"💾 Saved as fraudulent: {result.data}")
            return
        
        # STEP 4: Process attachments (if any)
        print(f"\n📎 STEP 4: Processing Attachments...")
        attachment_text = ''
        if email_data.get('attachments'):
            print(f"   Found {len(email_data['attachments'])} attachments")
            attachment_text = process_attachments(email_data['attachments'])
            print(f"   Extracted {len(attachment_text)} chars from attachments")
        else:
            print(f"   No attachments")
        
        # STEP 5: Verify company against database
        print(f"\n🏢 STEP 5: Company Verification...")
        company_verification = verify_company_against_database(mock_message, user_id, fraud_logger)
        print(f"   Is Verified: {company_verification.get('is_verified', False)}")
        if company_verification.get('company_match'):
            company = company_verification['company_match']
            print(f"   Company: {company.get('name', 'N/A')} (ID: {company.get('id', 'N/A')})")
        
        # STEP 6: Extract invoice data if company is verified
        invoice_data = None
        sensitive_changes_detected = False
        attribute_changes = []
        unsure_about_fields = []
        
        if company_verification.get('is_verified', False):
            print(f"\n📊 STEP 6: Invoice Data Extraction...")
            invoice_data = extract_invoice_data(body_text, attachment_text, headers.get('From', ''))
            print(f"   Billing Address: {invoice_data.get('billing_address', 'N/A')}")
            print(f"   Payment Method: {invoice_data.get('payment_method', 'N/A')}")
            print(f"   Amount: ${invoice_data.get('amount', 0):.2f}")
            
            # Check for sensitive changes
            matched_company = company_verification.get('company_match')
            if matched_company and invoice_data:
                print(f"\n🔍 STEP 7: Sensitive Change Detection...")
                attribute_changes = compare_attributes(matched_company, invoice_data)
                if attribute_changes:
                    sensitive_changes_detected = True
                    unsure_about_fields = [change['field'] for change in attribute_changes]
                    print(f"   ⚠️  SENSITIVE CHANGES DETECTED:")
                    for change in attribute_changes:
                        print(f"      - {change['field']}: '{change['old_value']}' → '{change['new_value']}'")
                    
                    # Log sensitive changes
                    fraud_logger.log_sensitive_changes(
                        mock_message['id'],
                        user_id,
                        {
                            'changes': attribute_changes,
                            'company_id': matched_company.get('id'),
                            'company_name': matched_company.get('name')
                        }
                    )
                else:
                    print(f"   ✅ No sensitive changes detected")
        
        # STEP 7: Determine final label and save
        print(f"\n🏷️  STEP 8: Final Classification...")
        
        if not company_verification.get('is_verified', False):
            label = 'unsure'
            print(f"   Label: {label} (company not verified)")
        elif sensitive_changes_detected:
            label = 'unsure'
            print(f"   Label: {label} (sensitive changes detected)")
        else:
            label = 'safe'
            print(f"   Label: {label} (verified company, no changes)")
        
        # Save to database
        email_record = {
            'user_id': user_id,
            'company_id': company_verification.get('company_match', {}).get('id') if company_verification.get('company_match') else None,
            'sender': headers.get('From', ''),
            'subject': headers.get('Subject', ''),
            'body': body_text,
            'received_at': headers.get('Date', datetime.now().isoformat()),
            'label': label,
            'status': 'processed',
            'attachment_content': attachment_text,
            'billing_address': invoice_data.get('billing_address') if invoice_data else None,
            'payment_method': invoice_data.get('payment_method') if invoice_data else None,
            'biller_billing_details': invoice_data.get('biller_billing_details') if invoice_data else None,
            'contact_email': invoice_data.get('contact_email') if invoice_data else None,
            'user_account_number': invoice_data.get('user_account_number') if invoice_data else None,
            'biller_phone_number': invoice_data.get('biller_phone_number') if invoice_data else None,
            'invoice_number': invoice_data.get('invoice_number') if invoice_data else None,
            'amount': invoice_data.get('amount', 0.0) if invoice_data else None,
            'unsure_about': unsure_about_fields
        }
        
        result = supabase.table('emails').insert(email_record).execute()
        print(f"💾 Saved to database: {result.data}")
        
        # Apply Gmail label
        try:
            apply_gmail_label(gmail_service, mock_message['id'], label)
            print(f"🏷️  Applied Gmail label: {label}")
        except Exception as e:
            print(f"⚠️  Could not apply Gmail label: {e}")
        
        print(f"\n✅ TEST EMAIL PROCESSING COMPLETE")
        print(f"   Final Label: {label}")
        print(f"   Company ID: {email_record['company_id']}")
        print(f"   Sensitive Changes: {len(attribute_changes)}")
        
    except Exception as e:
        print(f"❌ Error in test email processing: {e}")
        import traceback
        traceback.print_exc()
