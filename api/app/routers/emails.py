from fastapi import APIRouter, Depends, HTTPException
from app.auth import verify_token
from app.models import EmailRequest
from app.database import get_user_oauth_token
from app.services import create_gmail_service, get_user_emails

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
        
        # Create Gmail service
        gmail_service = create_gmail_service(
            oauth_tokens['access_token'], 
            oauth_tokens['refresh_token']
        )
        
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
