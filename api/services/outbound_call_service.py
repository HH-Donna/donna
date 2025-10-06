"""
Outbound Call Service
=====================
Service module for initiating and monitoring outbound calls via ElevenLabs and Twilio.

This module provides a clean API for triggering AI agent calls with dynamic variables.

Usage:
    from app.services.outbound_call_service import initiate_call, monitor_call
    
    result = initiate_call(
        destination_number="+13473580012",
        agent_variables={"case_id": "123", "customer_org": "Acme Corp"},
        monitor=True
    )
    
    if result['success']:
        print(f"Call initiated: {result['conversation_id']}")
"""

import httpx
import time
from datetime import datetime
from typing import Optional, Dict, Any
import os

# Configuration - can be overridden via environment variables
ELEVENLABS_API_KEY = os.getenv(
    "ELEVENLABS_API_KEY",
    "sk_9af95a2fca8ea120a514561389ef270c6e3c2235b3da347a"
)
ELEVEN_LABS_AGENT_ID = os.getenv(
    "ELEVEN_LABS_AGENT_ID",
    "agent_2601k6rm4bjae2z9amfm5w1y6aps"
)
PHONE_NUMBER_ID = os.getenv(
    "PHONE_NUMBER_ID",
    "phnum_4801k6sa89eqfpnsfjsxbr40phen"
)
TWILIO_PHONE_NUMBER = os.getenv(
    "TWILIO_PHONE_NUMBER",
    "+18887064372"
)

# API Endpoints
ELEVENLABS_OUTBOUND_CALL_URL = "https://api.elevenlabs.io/v1/convai/twilio/outbound-call"
ELEVENLABS_CONVERSATION_URL = "https://api.elevenlabs.io/v1/convai/conversations"


def _normalize_phone_number(phone_number: str) -> str:
    """Ensure phone number is in E.164 format with + prefix"""
    if not phone_number.startswith('+'):
        return f"+{phone_number}"
    return phone_number


def _make_api_request(
    url: str,
    method: str = "POST",
    payload: Optional[Dict] = None,
    timeout: float = 30.0
) -> Optional[Dict[str, Any]]:
    """
    Make an API request to ElevenLabs
    
    Args:
        url: API endpoint URL
        method: HTTP method (GET, POST)
        payload: Request payload for POST requests
        timeout: Request timeout in seconds
        
    Returns:
        Response data dict if successful, None otherwise
    """
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        with httpx.Client(timeout=timeout) as client:
            if method == "POST":
                response = client.post(url, json=payload, headers=headers)
            else:  # GET
                response = client.get(url, headers=headers)
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                return None
                
    except Exception as e:
        return None


def initiate_call(
    destination_number: str,
    agent_variables: Dict[str, Any],
    agent_id: Optional[str] = None,
    phone_number_id: Optional[str] = None,
    monitor: bool = False,
    monitor_duration: int = 30,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Initiate an outbound call to a phone number with dynamic agent variables.
    
    Args:
        destination_number: Phone number to call (E.164 format, e.g., "+13473580012")
        agent_variables: Dictionary of dynamic variables for the agent conversation.
                        These are passed to the agent and can be referenced in prompts.
        agent_id: Optional override for the ElevenLabs agent ID
        phone_number_id: Optional override for the phone number ID
        monitor: Whether to monitor the call status after initiation
        monitor_duration: How long to monitor the call in seconds (default 30s)
        verbose: Whether to print detailed output to console
        
    Returns:
        Dictionary containing:
            - success: bool indicating if call was initiated
            - call_data: Response from ElevenLabs API
            - conversation_id: ID for tracking the conversation
            - dashboard_url: URL to view the conversation in ElevenLabs
            - monitoring_data: Final status if monitoring was enabled
            - error: Error message if call failed
            
    Example:
        >>> result = initiate_call(
        ...     destination_number="+13473580012",
        ...     agent_variables={
        ...         "case_id": "shop-00123",
        ...         "customer_org": "Pixamp, Inc",
        ...         "vendor__legal_name": "Spotify",
        ...         "email__invoice_number": "INV-300050",
        ...         "email__amount": "900"
        ...     },
        ...     monitor=True
        ... )
        >>> if result['success']:
        ...     print(f"Call initiated: {result['conversation_id']}")
        ...     print(f"Dashboard: {result['dashboard_url']}")
    """
    # Normalize phone number
    destination_number = _normalize_phone_number(destination_number)
    
    # Use provided IDs or fall back to defaults
    agent_id = agent_id or ELEVEN_LABS_AGENT_ID
    phone_number_id = phone_number_id or PHONE_NUMBER_ID
    
    if verbose:
        print(f"\n🚀 Initiating outbound call")
        print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   From: {TWILIO_PHONE_NUMBER}")
        print(f"   To: {destination_number}")
    
    # Prepare the API payload
    payload = {
        "agent_id": agent_id,
        "agent_phone_number_id": phone_number_id,
        "to_number": destination_number,
        "conversation_initiation_client_data": {
            "dynamic_variables": agent_variables
        }
    }
    
    # Make the API request
    call_data = _make_api_request(
        url=ELEVENLABS_OUTBOUND_CALL_URL,
        method="POST",
        payload=payload
    )
    
    # Build result
    result = {
        'success': call_data is not None,
        'call_data': call_data,
        'conversation_id': None,
        'dashboard_url': None,
        'monitoring_data': None,
        'error': None
    }
    
    if call_data:
        conversation_id = call_data.get('conversation_id')
        result['conversation_id'] = conversation_id
        
        if conversation_id:
            result['dashboard_url'] = f"https://elevenlabs.io/app/conversational-ai/conversations/{conversation_id}"
        
        if verbose:
            print(f"\n✅ Call initiated successfully!")
            print(f"   Conversation ID: {conversation_id}")
            if result['dashboard_url']:
                print(f"   Dashboard: {result['dashboard_url']}")
        
        # Monitor if requested
        if monitor and conversation_id:
            if verbose:
                print(f"\n⏳ Monitoring call for {monitor_duration}s...")
            monitoring_data = monitor_call(
                conversation_id=conversation_id,
                duration=monitor_duration,
                verbose=verbose
            )
            result['monitoring_data'] = monitoring_data
    else:
        result['error'] = "Failed to initiate call - API request failed"
        if verbose:
            print(f"\n❌ Call failed to initiate")
    
    return result


def monitor_call(
    conversation_id: str,
    duration: int = 30,
    check_interval: int = 5,
    verbose: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Monitor a call's status after initiation.
    
    Args:
        conversation_id: The conversation ID to monitor
        duration: Total time to monitor in seconds
        check_interval: How often to check status in seconds
        verbose: Whether to print status updates
        
    Returns:
        Final conversation data if call completed, None otherwise
    """
    checks = duration // check_interval
    
    for i in range(checks):
        time.sleep(check_interval)
        
        # Get conversation status
        url = f"{ELEVENLABS_CONVERSATION_URL}/{conversation_id}"
        data = _make_api_request(url, method="GET", timeout=10.0)
        
        if data:
            status = data.get('status', 'unknown')
            duration_seconds = data.get('duration_seconds', 0)
            
            if verbose:
                elapsed = (i + 1) * check_interval
                print(f"   [{elapsed}s] Status: {status}, Duration: {duration_seconds}s")
            
            # Check if call is complete
            if status in ['completed', 'ended', 'done']:
                if verbose:
                    print(f"\n✅ Call {status}")
                return data
        else:
            if verbose:
                elapsed = (i + 1) * check_interval
                print(f"   [{elapsed}s] (checking...)")
    
    if verbose:
        print(f"\n⏱️  Monitoring period ended (call may still be in progress)")
    
    return None


def get_conversation_details(conversation_id: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a conversation.
    
    Args:
        conversation_id: The conversation ID to query
        
    Returns:
        Conversation data dict if successful, None otherwise
    """
    url = f"{ELEVENLABS_CONVERSATION_URL}/{conversation_id}"
    return _make_api_request(url, method="GET", timeout=10.0)


def get_conversation_transcript(conversation_id: str) -> Optional[str]:
    """
    Get the transcript of a completed conversation.
    
    Args:
        conversation_id: The conversation ID to query
        
    Returns:
        Transcript text if available, None otherwise
    """
    data = get_conversation_details(conversation_id)
    
    if data:
        # Extract transcript from the conversation data
        # Note: Actual transcript field may vary based on ElevenLabs API
        transcript = data.get('transcript', None)
        if transcript:
            return transcript
        
        # Alternative: build transcript from messages
        messages = data.get('messages', [])
        if messages:
            transcript_lines = []
            for msg in messages:
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                transcript_lines.append(f"{role}: {content}")
            return "\n".join(transcript_lines)
    
    return None
