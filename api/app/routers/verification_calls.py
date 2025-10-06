"""
Verification Calls Router
=========================
API endpoints for triggering and managing outbound verification calls.

This router provides endpoints to:
- Trigger verification calls for unsure emails
- Process batch unsure emails
- Check call status
- Manual trigger for specific emails
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import Optional, Dict, Any
import logging

from services.email_to_call_service import (
    trigger_verification_call,
    process_batch_unsure_emails,
    fetch_unsure_emails
)
from services.outbound_call_service import get_conversation_details

router = APIRouter(prefix="/verification-calls", tags=["verification-calls"])
logger = logging.getLogger(__name__)


@router.post("/trigger")
async def trigger_call(
    background_tasks: BackgroundTasks,
    email_id: Optional[str] = None,
    run_in_background: bool = True
) -> Dict[str, Any]:
    """
    Trigger a verification call for an unsure email.
    
    Args:
        email_id: Optional specific email ID. If not provided, uses latest unsure email.
        run_in_background: If True, runs the call in background and returns immediately.
        
    Returns:
        Call initiation result with conversation_id and dashboard_url
        
    Example:
        POST /verification-calls/trigger
        POST /verification-calls/trigger?email_id=12345
    """
    
    logger.info(f"Triggering verification call (email_id={email_id}, background={run_in_background})")
    
    if run_in_background:
        # Run in background and return immediately
        background_tasks.add_task(trigger_verification_call, email_id=email_id)
        return {
            "success": True,
            "message": "Verification call scheduled in background",
            "email_id": email_id,
            "background": True
        }
    else:
        # Run synchronously and wait for result
        result = trigger_verification_call(email_id=email_id)
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result.get('error', 'Failed to trigger call'))
        
        return result


@router.post("/trigger-batch")
async def trigger_batch_calls(
    background_tasks: BackgroundTasks,
    max_emails: int = Query(default=10, ge=1, le=50),
    run_in_background: bool = True
) -> Dict[str, Any]:
    """
    Trigger verification calls for multiple unsure emails.
    
    Args:
        max_emails: Maximum number of emails to process (1-50)
        run_in_background: If True, runs in background
        
    Returns:
        Batch processing results
        
    Example:
        POST /verification-calls/trigger-batch?max_emails=5
    """
    
    logger.info(f"Triggering batch calls (max={max_emails}, background={run_in_background})")
    
    if run_in_background:
        background_tasks.add_task(process_batch_unsure_emails, max_emails=max_emails)
        return {
            "success": True,
            "message": f"Batch processing scheduled for up to {max_emails} emails",
            "background": True
        }
    else:
        result = process_batch_unsure_emails(max_emails=max_emails)
        return result


@router.get("/pending")
async def get_pending_emails() -> Dict[str, Any]:
    """
    Get list of emails pending verification calls.
    
    Returns:
        List of unsure emails that haven't had calls initiated yet
        
    Example:
        GET /verification-calls/pending
    """
    
    logger.info("Fetching pending verification emails")
    
    emails = fetch_unsure_emails(limit=50, processed=False)
    
    return {
        "success": True,
        "count": len(emails),
        "emails": [
            {
                "id": email.get("id"),
                "vendor_name": email.get("vendor_name"),
                "invoice_number": email.get("invoice_number"),
                "amount": email.get("amount"),
                "created_at": email.get("created_at"),
                "label": email.get("label")
            }
            for email in emails
        ]
    }


@router.get("/status/{conversation_id}")
async def get_call_status(conversation_id: str) -> Dict[str, Any]:
    """
    Get status of a verification call by conversation ID.
    
    Args:
        conversation_id: ElevenLabs conversation ID
        
    Returns:
        Conversation details and status
        
    Example:
        GET /verification-calls/status/conv_xxx
    """
    
    logger.info(f"Fetching status for conversation: {conversation_id}")
    
    details = get_conversation_details(conversation_id)
    
    if not details:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {
        "success": True,
        "conversation_id": conversation_id,
        "status": details.get("status"),
        "duration_seconds": details.get("duration_seconds"),
        "details": details
    }


@router.post("/webhook/email-classified")
async def email_classified_webhook(
    background_tasks: BackgroundTasks,
    email_id: str,
    label: str
) -> Dict[str, Any]:
    """
    Webhook endpoint to be called when an email is classified.
    
    If the email is labeled as "unsure", automatically triggers a verification call.
    
    Args:
        email_id: The email ID that was classified
        label: The classification label (legit, fraud, unsure)
        
    Returns:
        Action taken
        
    Example:
        POST /verification-calls/webhook/email-classified
        {
            "email_id": "12345",
            "label": "unsure"
        }
    """
    
    logger.info(f"Email classified webhook: email_id={email_id}, label={label}")
    
    if label == "unsure":
        # Automatically trigger verification call
        background_tasks.add_task(trigger_verification_call, email_id=email_id)
        
        return {
            "success": True,
            "action": "verification_call_triggered",
            "email_id": email_id,
            "label": label,
            "message": f"Verification call scheduled for email {email_id}"
        }
    else:
        return {
            "success": True,
            "action": "no_action",
            "email_id": email_id,
            "label": label,
            "message": f"No action needed for label '{label}'"
        }
