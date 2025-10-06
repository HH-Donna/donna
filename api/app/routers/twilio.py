"""
Twilio Integration Router
Handles webhook endpoints for ElevenLabs callContact_tool
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
import os
import httpx

router = APIRouter()

class CallRequest(BaseModel):
    """Request model for initiating a call via Twilio"""
    phone_number: str
    company_name: str
    invoice_id: Optional[str] = ""
    customer_org: Optional[str] = "Pixamp, Inc"
    vendor_legal_name: Optional[str] = ""

@router.post("/twilio/webhook")
async def initiate_call(request: CallRequest):
    """
    Webhook endpoint for ElevenLabs callContact_tool
    Initiates a phone call using ElevenLabs + Twilio integration
    
    This endpoint is called by the ElevenLabs agent when it uses the callContact_tool.
    """
    try:
        # Get credentials
        api_key = os.environ.get("ELEVENLABS_API_KEY")
        agent_id = os.environ.get("ELEVEN_LABS_AGENT_ID")
        
        if not api_key or not agent_id:
            raise HTTPException(
                status_code=500,
                detail="Missing ELEVENLABS_API_KEY or ELEVEN_LABS_AGENT_ID environment variables"
            )
        
        # Prepare dynamic variables for the conversation
        variables = {
            # Case info
            "case_id": f"CALL-{request.invoice_id}" if request.invoice_id else "CALL-UNKNOWN",
            "customer_org": request.customer_org,
            "user__company_name": request.customer_org,
            
            # Email/Invoice details
            "email__vendor_name": request.vendor_legal_name or request.company_name,
            "email__invoice_number": request.invoice_id,
            "vendor__legal_name": request.vendor_legal_name or request.company_name,
            
            # These would come from the fraud detection pipeline in production
            "email__amount": "TBD",
            "email__due_date": "TBD",
            "official_canonical_domain": "TBD",
            "official_canonical_phone": request.phone_number,
            
            # Policy
            "policy_recording_notice": "This call may be recorded for quality assurance purposes"
        }
        
        # Use ElevenLabs API to initiate signed out conversation
        # This will trigger a phone call via Twilio
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.elevenlabs.io/v1/convai/conversation",
                headers={
                    "xi-api-key": api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "agent_id": agent_id,
                    "phone_number": request.phone_number,
                    "variables": variables
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"ElevenLabs API error: {response.text}"
                )
            
            data = response.json()
            conversation_id = data.get("conversation_id")
            
            print(f"✅ Call initiated:")
            print(f"   Phone: {request.phone_number}")
            print(f"   Company: {request.company_name}")
            print(f"   Invoice: {request.invoice_id}")
            print(f"   Conversation ID: {conversation_id}")
            
            return {
                "success": True,
                "conversation_id": conversation_id,
                "status": "call_initiated",
                "message": f"Call initiated to {request.phone_number}",
                "variables_passed": variables
            }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error initiating call: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate call: {str(e)}")


@router.get("/twilio/health")
async def twilio_health():
    """Health check endpoint for Twilio integration"""
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    agent_id = os.environ.get("ELEVEN_LABS_AGENT_ID")
    
    return {
        "status": "healthy",
        "api_key_set": bool(api_key),
        "agent_id_set": bool(agent_id),
        "agent_id": agent_id if agent_id else None
    }
