"""
Twilio Webhook Router for ElevenLabs Agents Platform Integration

This router handles webhook calls from ElevenLabs agents to make phone verification calls
through Twilio for company verification purposes.
"""

import os
import logging
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any, Optional
from app.services.eleven_agent import eleven_agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/twilio", tags=["twilio-webhook"])


class TwilioVerificationRequest(BaseModel):
    """Request model for Twilio phone verification webhook."""
    company_name: str
    phone_number: str
    email_to_verify: str
    verification_context: Optional[str] = None


class TwilioVerificationResponse(BaseModel):
    """Response model for Twilio phone verification webhook."""
    success: bool
    call_sid: Optional[str] = None
    status: Optional[str] = None
    verified: Optional[bool] = None
    notes: Optional[str] = None
    error: Optional[str] = None


@router.post("/webhook", response_model=TwilioVerificationResponse)
async def twilio_verification_webhook(request: TwilioVerificationRequest):
    """
    Webhook endpoint for ElevenLabs agents to initiate phone verification calls.
    
    This endpoint receives requests from ElevenLabs agents and uses the existing
    ElevenLabs + Twilio integration to make verification calls.
    
    Args:
        request: TwilioVerificationRequest containing company and contact details
        
    Returns:
        TwilioVerificationResponse with call results
    """
    try:
        logger.info(f"📞 Received Twilio verification webhook request:")
        logger.info(f"   Company: {request.company_name}")
        logger.info(f"   Phone: {request.phone_number}")
        logger.info(f"   Email: {request.email_to_verify}")
        logger.info(f"   Context: {request.verification_context}")
        
        # Use the existing ElevenLabs agent service to make the call
        call_result = await eleven_agent.verify_company_by_call(
            company_name=request.company_name,
            phone_number=request.phone_number,
            email=request.email_to_verify
        )
        
        logger.info(f"📞 Call result: {call_result}")
        
        # Map the result to the webhook response format
        response = TwilioVerificationResponse(
            success=call_result.get('success', False),
            call_sid=call_result.get('call_sid'),
            status=call_result.get('call_status'),
            verified=call_result.get('verified', False),
            notes=call_result.get('message'),
            error=call_result.get('error')
        )
        
        logger.info(f"✅ Webhook response prepared: {response}")
        return response
        
    except Exception as e:
        error_msg = f"Error in Twilio verification webhook: {str(e)}"
        logger.error(error_msg)
        
        return TwilioVerificationResponse(
            success=False,
            error=error_msg
        )


@router.get("/webhook/status")
async def webhook_status():
    """
    Health check endpoint for the Twilio webhook.
    
    Returns:
        Dict with status information
    """
    return {
        "status": "healthy",
        "service": "Twilio Verification Webhook",
        "version": "1.0.0",
        "endpoints": {
            "verification": "/twilio/webhook",
            "status": "/twilio/webhook/status"
        }
    }


@router.post("/webhook/test")
async def test_webhook(request: TwilioVerificationRequest):
    """
    Test endpoint for the Twilio verification webhook.
    
    This endpoint allows testing the webhook integration without making actual calls.
    
    Args:
        request: TwilioVerificationRequest with test data
        
    Returns:
        TwilioVerificationResponse with test results
    """
    try:
        logger.info(f"🧪 Testing Twilio verification webhook:")
        logger.info(f"   Company: {request.company_name}")
        logger.info(f"   Phone: {request.phone_number}")
        logger.info(f"   Email: {request.email_to_verify}")
        
        # Return a test response without making an actual call
        return TwilioVerificationResponse(
            success=True,
            call_sid="test_call_sid_12345",
            status="test_initiated",
            verified=False,
            notes="This is a test response - no actual call was made",
            error=None
        )
        
    except Exception as e:
        error_msg = f"Error in test webhook: {str(e)}"
        logger.error(error_msg)
        
        return TwilioVerificationResponse(
            success=False,
            error=error_msg
        )
