from fastapi import APIRouter, Depends, HTTPException
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
        emails = await get_user_emails(gmail_service, days_back=90)
        
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


@router.post("/billers/extract", response_model=BillerProfilesResponse)
async def extract_biller_profiles(request: EmailRequest, token: str = Depends(verify_token)):
    """
    Extract unique biller profiles from user's invoice emails.
    
    This endpoint:
    1. Fetches invoice-related emails from the past 3 months
    2. Downloads and analyzes email content and attachments
    3. Uses AI to extract structured biller information
    4. Deduplicates and returns unique biller profiles
    
    Each profile includes:
    - Company/individual name and contact info
    - Full address
    - Payment method
    - Billing/bank details
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
        
        # Get the user's email address to filter out their sent emails
        user_email = get_user_email_address(gmail_service)
        print(f"👤 User email: {user_email}")
        
        # Fetch emails with full content and attachments
        emails = await get_user_emails(
            gmail_service, 
            days_back=90,
            include_attachments=True  # Include attachments for better extraction
        )
        
        if not emails:
            return BillerProfilesResponse(
                message="No invoice emails found in the past 3 months",
                user_uuid=request.user_uuid,
                total_billers=0,
                profiles=[]
            )
        
        # Extract biller profiles using AI (pass user email to filter sent emails)
        extractor = BillerExtractor(user_email=user_email)
        profiles = extractor.extract_biller_profiles(emails)
        
        # Fetch profile pictures from Google Contacts/People API
        print(f"🖼️  Fetching profile pictures for {len(profiles)} billers...")
        email_addresses = [p.email_address for p in profiles if p.email_address]
        profile_pictures = batch_get_profile_pictures(email_addresses, creds)
        
        # Update profiles with profile pictures
        for profile in profiles:
            if profile.email_address in profile_pictures:
                profile.profile_picture_url = profile_pictures[profile.email_address]
        
        pictures_found = sum(1 for p in profiles if p.profile_picture_url)
        print(f"🖼️  Found {pictures_found}/{len(profiles)} profile pictures")
        
        # Save billers to Supabase companies table
        save_results = await save_billers_to_companies(request.user_uuid, profiles)
        print(f"💾 Saved {save_results['saved']}/{save_results['total']} billers to database")
        
        if save_results['failed'] > 0:
            print(f"⚠️  Failed to save {save_results['failed']} billers: {save_results['errors']}")
        
        return BillerProfilesResponse(
            message=f"Successfully extracted {len(profiles)} unique biller profiles and saved {save_results['saved']} to database",
            user_uuid=request.user_uuid,
            total_billers=len(profiles),
            profiles=profiles
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )
