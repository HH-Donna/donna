"""
Integrated Conversational AI Phone Call Router
Uses ElevenLabs Conversational AI + Twilio for intelligent verification calls
"""
import os
import json
import time
import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/call", tags=["conversational-calling"])

class CallRequest(BaseModel):
    phone_number: str
    company_name: str
    email: str

@router.post("/conversational")
async def make_conversational_call(request: CallRequest):
    """Make an intelligent conversational AI call using ElevenLabs + Twilio"""
    
    try:
        # Get environment variables
        elevenlabs_api_key = os.getenv('ELEVENLABS_API_KEY')
        agent_id = os.getenv('ELEVENLABS_AGENT_ID', 'agent_2601k6rm4bjae2z9amfm5w1y6aps')
        phone_number_id = os.getenv('ELEVENLABS_PHONE_NUMBER_ID', 'phnum_4801k6sa89eqfpnsfjsxbr40phen')
        
        if not elevenlabs_api_key:
            raise HTTPException(status_code=500, detail="ElevenLabs API key not configured")
        
        # Format phone number
        phone = request.phone_number.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        if not phone.startswith("+"):
            if phone.startswith("1") and len(phone) == 11:
                phone = "+" + phone
            elif len(phone) == 10:
                phone = "+1" + phone
            else:
                phone = "+1" + phone
        
        print(f"\n🎯 Making Conversational AI Call:")
        print(f"   To: {phone}")
        print(f"   Company: {request.company_name}")
        print(f"   Email: {request.email}")
        print(f"   Agent: Donna ({agent_id})")
        
        # ElevenLabs Twilio outbound call endpoint  
        url = "https://api.elevenlabs.io/v1/convai/twilio/outbound-call"
        
        # Simplified dynamic variables structure
        call_payload = {
            "agent_id": agent_id,
            "agent_phone_number_id": phone_number_id,
            "to_number": phone,
            "dynamic_variables": {
                "vendor__legal_name": request.company_name,
                "customer_org": request.company_name
            }
        }
        
        headers = {
            "xi-api-key": elevenlabs_api_key,
            "Content-Type": "application/json"
        }
        
        print(f"\n📞 Calling ElevenLabs API...")
        print(f"   URL: {url}")
        print(f"   Payload: {json.dumps(call_payload, indent=2)}")
        
        # Make the API call
        response = requests.post(url, headers=headers, json=call_payload, timeout=30)
        
        print(f"\n📋 Response Status: {response.status_code}")
        print(f"   Response Headers: {dict(response.headers)}")
        print(f"   Response Text: {response.text}")
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                conversation_id = response_data.get('conversation_id')
                call_sid = response_data.get('call_sid')
                
                return {
                    "success": True,
                    "message": "🎉 Conversational AI call initiated successfully!",
                    "call_details": {
                        "conversation_id": conversation_id,
                        "call_sid": call_sid,
                        "to_number": phone,
                        "company_name": request.company_name,
                        "email": request.email,
                        "agent_id": agent_id,
                        "call_type": "elevenlabs_conversational",
                        "timestamp": int(time.time())
                    },
                    "raw_response": response_data
                }
            except json.JSONDecodeError:
                return {
                    "success": True,
                    "message": "Call initiated (non-JSON response)",
                    "response_text": response.text,
                    "status_code": response.status_code
                }
        else:
            # Handle error responses
            try:
                error_data = response.json()
                error_message = error_data.get('detail', {}).get('message', str(error_data))
            except:
                error_message = response.text
                
            return {
                "success": False,
                "error": f"ElevenLabs API Error ({response.status_code}): {error_message}",
                "status_code": response.status_code,
                "response_text": response.text
            }
            
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=408, detail="ElevenLabs API timeout - request took too long")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Network error calling ElevenLabs API: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.get("/status/{conversation_id}")
async def get_call_status(conversation_id: str):
    """Get the status of a conversational AI call"""
    
    try:
        elevenlabs_api_key = os.getenv('ELEVENLABS_API_KEY')
        if not elevenlabs_api_key:
            raise HTTPException(status_code=500, detail="ElevenLabs API key not configured")
        
        url = f"https://api.elevenlabs.io/v1/convai/conversations/{conversation_id}"
        headers = {"xi-api-key": elevenlabs_api_key}
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to get call status: {response.text}"
            )
            
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Network error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
