from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from app.auth import verify_token
from app.models import EmailRequest, BillerProfilesResponse
from app.database import get_user_oauth_token, update_user_access_token, save_billers_to_companies
from app.services import (
    create_gmail_service, 
    get_user_emails, 
    BillerExtractor, 
    get_user_email_address,
    batch_get_profile_pictures
)

router = APIRouter(prefix="/emails", tags=["emails"])


@router.post("/test")
async def test_email_structure(request: EmailRequest, token: str = Depends(verify_token)):
    """
    Test endpoint to verify the email fetching structure without requiring real OAuth tokens.
    Returns mock invoice email data for testing purposes.
    """
    return {
        "message": "Test invoice-related emails (mock data)",
        "user_uuid": request.user_uuid,
        "email_count": 3,
        "search_terms": ["invoice", "bill", "receipt", "payment", "due", "statement", "charge", "billing", "subscription", "renewal"],
        "emails": [
            {
                "id": "mock_email_1",
                "thread_id": "mock_thread_1",
                "from": "billing@netflix.com",
                "subject": "Your Netflix Invoice - Payment Due",
                "date": "Mon, 1 Jan 2024 12:00:00 +0000",
                "snippet": "Your monthly Netflix subscription invoice is ready. Amount due: $15.99",
                "body_preview": "Dear Customer, Your Netflix invoice for December 2023 is now available. Amount due: $15.99. Payment due date: January 15, 2024...",
                "invoice_indicators": ["invoice", "payment", "due", "amount due"]
            },
            {
                "id": "mock_email_2", 
                "thread_id": "mock_thread_2",
                "from": "noreply@aws.amazon.com",
                "subject": "AWS Billing Statement - Account 123456789",
                "date": "Tue, 2 Jan 2024 08:30:00 +0000",
                "snippet": "Your AWS billing statement is ready for review. Total charges: $89.45",
                "body_preview": "AWS Billing Statement for December 2023. Account: 123456789. Total charges: $89.45. Services used: EC2, S3, Lambda...",
                "invoice_indicators": ["billing", "statement", "total", "charges"]
            },
            {
                "id": "mock_email_3",
                "thread_id": "mock_thread_3", 
                "from": "receipts@uber.com",
                "subject": "Receipt for your Uber ride",
                "date": "Wed, 3 Jan 2024 19:45:00 +0000",
                "snippet": "Thanks for riding with Uber. Your trip total was $12.50",
                "body_preview": "Receipt for your Uber ride on January 3, 2024. Trip total: $12.50. Payment method: **** 1234...",
                "invoice_indicators": ["receipt", "total", "payment"]
            }
        ]
    }


@router.post("/fetch")
async def fetch_user_emails(request: EmailRequest, token: str = Depends(verify_token)):
    """
    Fetch user's invoice-related Gmail emails from the past 3 months.
    Searches for emails containing invoice, bill, receipt, payment, and other billing-related terms.
    Requires user_uuid in the request body.
    """
    try:
        # Get user's OAuth tokens from Supabase
        oauth_tokens = await get_user_oauth_token(request.user_uuid)
        
        # Create Gmail service (returns service and potentially refreshed credentials)
        gmail_service, creds = create_gmail_service(
            oauth_tokens['access_token'], 
            oauth_tokens['refresh_token']
        )
        
        # If token was refreshed, save the new access token
        if creds.token != oauth_tokens['access_token']:
            await update_user_access_token(
                request.user_uuid,
                'google',
                creds.token
            )
            print(f"Updated refreshed access token for user {request.user_uuid}")
        
        # Fetch emails from the past 3 months
        emails = await get_user_emails(gmail_service, days_back=90, include_attachments=True)
        
        return {
            "message": "Invoice-related emails fetched successfully",
            "user_uuid": request.user_uuid,
            "email_count": len(emails),
            "search_terms": ["invoice", "bill", "receipt", "payment", "due", "statement", "charge", "billing", "subscription", "renewal"],
            "emails": emails
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.post("/attachments/test")
async def test_attachments(request: EmailRequest, token: str = Depends(verify_token)):
    """
    Test endpoint to verify attachment downloading and text extraction.
    Returns details about attachments found in invoice emails.
    """
    try:
        # Get user's OAuth tokens
        oauth_tokens = await get_user_oauth_token(request.user_uuid)
        
        # Create Gmail service
        gmail_service, creds = create_gmail_service(
            oauth_tokens['access_token'], 
            oauth_tokens['refresh_token']
        )
        
        # Fetch emails with attachments
        emails = await get_user_emails(
            gmail_service, 
            days_back=90,
            include_attachments=True
        )
        
        # Analyze attachments
        attachment_summary = []
        total_attachments = 0
        emails_with_attachments = 0
        
        for email in emails[:10]:  # Check first 10 emails
            if 'attachments' in email and email['attachments']:
                emails_with_attachments += 1
                email_info = {
                    'subject': email.get('subject', ''),
                    'from': email.get('from', ''),
                    'attachments': []
                }
                
                for att in email['attachments']:
                    total_attachments += 1
                    
                    # Try to extract text
                    from app.services.attachment_parser import extract_text_from_attachment
                    extracted_text = extract_text_from_attachment(att)
                    
                    att_info = {
                        'filename': att.get('filename', ''),
                        'mime_type': att.get('mime_type', ''),
                        'size': att.get('size', 0),
                        'text_extracted': len(extracted_text) > 0,
                        'text_length': len(extracted_text),
                        'text_preview': extracted_text[:200] if extracted_text else ''
                    }
                    email_info['attachments'].append(att_info)
                
                attachment_summary.append(email_info)
        
        return {
            'message': f'Analyzed {len(emails)} emails',
            'total_emails_checked': len(emails[:10]),
            'emails_with_attachments': emails_with_attachments,
            'total_attachments': total_attachments,
            'details': attachment_summary
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )


def process_billers_background(user_uuid: str, oauth_tokens: dict):
    """
    Background task to extract and save biller profiles.
    This runs synchronously in a background thread.
    """
    import asyncio
    
    async def async_process():
        try:
            print(f"🔄 Starting background biller extraction for user {user_uuid}")
            
            # Create Gmail service
            gmail_service, creds = create_gmail_service(
                oauth_tokens['access_token'], 
                oauth_tokens['refresh_token']
            )
            
            # If token was refreshed, save it
            if creds.token != oauth_tokens['access_token']:
                await update_user_access_token(user_uuid, 'google', creds.token)
                print(f"🔄 Updated refreshed access token for user {user_uuid}")
            
            # Get user email to filter sent emails
            user_email = get_user_email_address(gmail_service)
            print(f"👤 User email: {user_email}")
            
            # Fetch emails with attachments
            emails = await get_user_emails(
                gmail_service, 
                days_back=90,
                include_attachments=True
            )
            
            if not emails:
                print(f"⚠️  No invoice emails found for user {user_uuid}")
                return
            
            # Extract biller profiles
            extractor = BillerExtractor(user_email=user_email)
            profiles = extractor.extract_biller_profiles(emails)
            
            # Cleanup extractor resources
            await extractor.cleanup()
            
            # Fetch profile pictures
            print(f"🖼️  Fetching profile pictures for {len(profiles)} billers...")
            # Collect all unique email addresses from all billers
            all_email_addresses = []
            for p in profiles:
                all_email_addresses.extend(p.contact_emails)
            unique_emails = list(set(all_email_addresses))
            
            profile_pictures = batch_get_profile_pictures(unique_emails, creds)
            
            # Update profiles with pictures (check all their contact emails)
            for profile in profiles:
                for email in profile.contact_emails:
                    if email in profile_pictures:
                        profile.profile_picture_url = profile_pictures[email]
                        break  # Use first found picture
            
            pictures_found = sum(1 for p in profiles if p.profile_picture_url)
            print(f"🖼️  Found {pictures_found}/{len(profiles)} profile pictures")
            
            # Save to database
            save_results = await save_billers_to_companies(user_uuid, profiles)
            print(f"✅ Background processing complete: Saved {save_results['saved']}/{save_results['total']} billers")
            
            if save_results['failed'] > 0:
                print(f"⚠️  Failed to save {save_results['failed']} billers: {save_results['errors']}")
            
            # Cleanup: Give a moment for any pending async operations
            await asyncio.sleep(0.1)
                
        except Exception as e:
            print(f"❌ Background processing error for user {user_uuid}: {e}")
            import traceback
            traceback.print_exc()
    
    # Run the async function in a new event loop (background thread safe)
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, create task
            asyncio.create_task(async_process())
        else:
            # If no running loop, run it
            loop.run_until_complete(async_process())
    except RuntimeError:
        # Create new event loop if needed
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(async_process())
        loop.close()


@router.post("/billers/extract")
async def extract_biller_profiles(
    request: EmailRequest, 
    background_tasks: BackgroundTasks,
    token: str = Depends(verify_token)
):
    """
    Extract unique biller profiles from user's invoice emails.
    Returns immediately with 200 OK and processes in the background.
    
    This endpoint:
    1. Validates user OAuth tokens
    2. Starts background processing
    3. Returns immediately
    
    Background processing:
    - Fetches invoice emails from past 3 months
    - Downloads and parses attachments (PDFs)
    - Uses AI to extract biller information
    - Fetches profile pictures from Google Contacts
    - Saves all billers to database
    """
    try:
        # Get user's OAuth tokens from Supabase (quick validation)
        oauth_tokens = await get_user_oauth_token(request.user_uuid)
        
        # Add background task
        background_tasks.add_task(
            process_billers_background,
            request.user_uuid,
            oauth_tokens
        )
        
        # Return immediately
        return {
            "message": "Biller extraction started in background",
            "user_uuid": request.user_uuid,
            "status": "processing",
            "note": "Check your database in a few moments for extracted billers"
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )
