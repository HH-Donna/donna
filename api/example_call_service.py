"""
Outbound Call Service - Usage Examples
======================================
Examples showing how to use the outbound_call_service module in your application.
"""

from services.outbound_call_service import (
    initiate_call,
    monitor_call,
    get_conversation_details,
    get_conversation_transcript
)


# Example 1: Basic call initiation
def example_basic_call():
    """Initiate a simple call with custom variables"""
    
    result = initiate_call(
        destination_number="+13473580012",
        agent_variables={
            "case_id": "fraud-123",
            "customer_org": "Acme Corp",
            "vendor__legal_name": "Spotify",
            "email__invoice_number": "INV-456",
            "email__amount": "1200"
        },
        verbose=True
    )
    
    if result['success']:
        print(f"\n✅ Call initiated!")
        print(f"   Conversation ID: {result['conversation_id']}")
        print(f"   Dashboard: {result['dashboard_url']}")
    else:
        print(f"\n❌ Call failed: {result['error']}")
    
    return result


# Example 2: Call with monitoring
def example_monitored_call():
    """Initiate a call and monitor its progress"""
    
    result = initiate_call(
        destination_number="+13473580012",
        agent_variables={
            "case_id": "fraud-789",
            "customer_org": "Tech Startup Inc",
            "vendor__legal_name": "Amazon AWS"
        },
        monitor=True,
        monitor_duration=60,  # Monitor for 60 seconds
        verbose=True
    )
    
    if result['monitoring_data']:
        status = result['monitoring_data'].get('status')
        duration = result['monitoring_data'].get('duration_seconds', 0)
        print(f"\n📊 Call completed with status: {status}")
        print(f"   Duration: {duration} seconds")
    
    return result


# Example 3: Silent call (no console output)
def example_silent_call():
    """Initiate a call without verbose output - useful for API endpoints"""
    
    result = initiate_call(
        destination_number="+13473580012",
        agent_variables={
            "case_id": "prod-001",
            "customer_org": "Enterprise Client",
        },
        monitor=False,
        verbose=False  # No console output
    )
    
    # Just return structured data for your API
    return {
        "success": result['success'],
        "conversation_id": result['conversation_id'],
        "error": result.get('error')
    }


# Example 4: Manual monitoring after call initiation
def example_manual_monitoring():
    """Initiate a call and monitor it separately"""
    
    # First, initiate the call without automatic monitoring
    result = initiate_call(
        destination_number="+13473580012",
        agent_variables={"case_id": "async-001"},
        monitor=False,
        verbose=True
    )
    
    if result['success']:
        conversation_id = result['conversation_id']
        
        # Do other work here...
        print("\n🔄 Doing other work while call is in progress...")
        
        # Later, manually monitor the call
        print("\n📊 Now checking call status...")
        final_status = monitor_call(
            conversation_id=conversation_id,
            duration=30,
            check_interval=5,
            verbose=True
        )
        
        if final_status:
            print(f"\n✅ Call finished: {final_status.get('status')}")
    
    return result


# Example 5: Get conversation details after call
def example_get_details(conversation_id: str):
    """Retrieve details about a completed conversation"""
    
    details = get_conversation_details(conversation_id)
    
    if details:
        print(f"\n📋 Conversation Details:")
        print(f"   ID: {details.get('conversation_id')}")
        print(f"   Status: {details.get('status')}")
        print(f"   Duration: {details.get('duration_seconds')}s")
        print(f"   Started: {details.get('start_time')}")
    
    return details


# Example 6: Get conversation transcript
def example_get_transcript(conversation_id: str):
    """Retrieve the transcript of a completed conversation"""
    
    transcript = get_conversation_transcript(conversation_id)
    
    if transcript:
        print(f"\n📝 Transcript:")
        print(transcript)
    else:
        print("\n⚠️  Transcript not available yet")
    
    return transcript


# Example 7: Use in FastAPI endpoint
def example_fastapi_integration():
    """
    Example showing how to integrate with FastAPI
    
    Note: This is pseudo-code to show the pattern
    """
    
    # In your FastAPI app:
    """
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    from services.outbound_call_service import initiate_call
    
    app = FastAPI()
    
    class CallRequest(BaseModel):
        phone_number: str
        case_id: str
        customer_org: str
        vendor_name: str
        invoice_number: str
        amount: str
    
    @app.post("/api/fraud/initiate-call")
    async def initiate_fraud_call(request: CallRequest):
        result = initiate_call(
            destination_number=request.phone_number,
            agent_variables={
                "case_id": request.case_id,
                "customer_org": request.customer_org,
                "vendor__legal_name": request.vendor_name,
                "email__invoice_number": request.invoice_number,
                "email__amount": request.amount
            },
            monitor=False,  # Don't block the API response
            verbose=False   # No console output
        )
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result['error'])
        
        return {
            "success": True,
            "conversation_id": result['conversation_id'],
            "dashboard_url": result['dashboard_url']
        }
    
    @app.get("/api/fraud/call-status/{conversation_id}")
    async def get_call_status(conversation_id: str):
        details = get_conversation_details(conversation_id)
        
        if not details:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {
            "conversation_id": conversation_id,
            "status": details.get('status'),
            "duration_seconds": details.get('duration_seconds')
        }
    """
    pass


if __name__ == "__main__":
    print("=" * 80)
    print("🔧 Outbound Call Service - Examples")
    print("=" * 80)
    
    # Uncomment to run different examples:
    # example_basic_call()
    # example_monitored_call()
    # example_silent_call()
    # example_manual_monitoring()
    
    # To use these after a call:
    # example_get_details("conv_xxxxx")
    # example_get_transcript("conv_xxxxx")
    
    print("\n💡 Import the service in your code:")
    print("   from services.outbound_call_service import initiate_call")
    print("\n📚 See function docstrings for full API documentation")
