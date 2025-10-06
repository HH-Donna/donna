# Outbound Call Service

A clean, production-ready service for initiating and monitoring AI agent phone calls via ElevenLabs and Twilio.

## 📋 Overview

This service provides a simple API for:
- Initiating outbound calls to phone numbers
- Passing dynamic variables to AI agents
- Monitoring call status in real-time
- Retrieving conversation details and transcripts

## 🚀 Quick Start

### Basic Usage

```python
from services.outbound_call_service import initiate_call

result = initiate_call(
    destination_number="+13473580012",
    agent_variables={
        "case_id": "fraud-123",
        "customer_org": "Acme Corp",
        "vendor__legal_name": "Spotify"
    }
)

if result['success']:
    print(f"Call initiated: {result['conversation_id']}")
```

### With Monitoring

```python
result = initiate_call(
    destination_number="+13473580012",
    agent_variables={"case_id": "123"},
    monitor=True,
    monitor_duration=60,  # Monitor for 60 seconds
    verbose=True
)
```

### Silent Mode (for APIs)

```python
result = initiate_call(
    destination_number="+13473580012",
    agent_variables={"case_id": "123"},
    monitor=False,
    verbose=False  # No console output
)
```

## 📚 API Reference

### `initiate_call()`

Main function to initiate an outbound call.

**Parameters:**
- `destination_number` (str): Phone number in E.164 format (e.g., "+13473580012")
- `agent_variables` (dict): Dynamic variables passed to the AI agent
- `agent_id` (str, optional): Override the default ElevenLabs agent ID
- `phone_number_id` (str, optional): Override the default phone number ID
- `monitor` (bool, default=False): Whether to monitor call status after initiation
- `monitor_duration` (int, default=30): How long to monitor in seconds
- `verbose` (bool, default=False): Whether to print detailed output

**Returns:**
```python
{
    'success': bool,              # Whether call was initiated
    'call_data': dict,            # Raw API response
    'conversation_id': str,       # ID for tracking the conversation
    'dashboard_url': str,         # URL to ElevenLabs dashboard
    'monitoring_data': dict,      # Final status if monitored
    'error': str                  # Error message if failed
}
```

### `monitor_call()`

Monitor an ongoing call's status.

**Parameters:**
- `conversation_id` (str): The conversation ID to monitor
- `duration` (int, default=30): Total time to monitor in seconds
- `check_interval` (int, default=5): How often to check status in seconds
- `verbose` (bool, default=False): Whether to print status updates

**Returns:**
- `dict`: Final conversation data if completed, `None` otherwise

### `get_conversation_details()`

Get detailed information about a conversation.

**Parameters:**
- `conversation_id` (str): The conversation ID to query

**Returns:**
- `dict`: Conversation data if found, `None` otherwise

### `get_conversation_transcript()`

Get the transcript of a completed conversation.

**Parameters:**
- `conversation_id` (str): The conversation ID to query

**Returns:**
- `str`: Transcript text if available, `None` otherwise

## 🔧 Configuration

The service uses these environment variables (with fallback defaults):

```bash
export ELEVENLABS_API_KEY="sk_your_api_key"
export ELEVEN_LABS_AGENT_ID="agent_your_agent_id"
export PHONE_NUMBER_ID="phnum_your_phone_id"
export TWILIO_PHONE_NUMBER="+18887064372"
```

## 💡 Usage Examples

### Example 1: Fraud Verification Call

```python
from services.outbound_call_service import initiate_call

fraud_variables = {
    "case_id": "fraud-789",
    "customer_org": "Tech Startup Inc",
    "vendor__legal_name": "Amazon AWS",
    "email__invoice_number": "INV-12345",
    "email__amount": "5000",
    "fraud__is_suspected": "True"
}

result = initiate_call(
    destination_number="+13473580012",
    agent_variables=fraud_variables,
    verbose=True
)
```

### Example 2: FastAPI Integration

```python
from fastapi import FastAPI, HTTPException
from services.outbound_call_service import initiate_call

app = FastAPI()

@app.post("/api/fraud/initiate-call")
async def initiate_fraud_call(phone_number: str, case_data: dict):
    result = initiate_call(
        destination_number=phone_number,
        agent_variables=case_data,
        monitor=False,
        verbose=False
    )
    
    if not result['success']:
        raise HTTPException(status_code=500, detail=result['error'])
    
    return {
        "conversation_id": result['conversation_id'],
        "dashboard_url": result['dashboard_url']
    }
```

### Example 3: Async Call with Later Status Check

```python
from services.outbound_call_service import initiate_call, get_conversation_details

# Initiate call
result = initiate_call(
    destination_number="+13473580012",
    agent_variables={"case_id": "async-001"},
    monitor=False
)

conversation_id = result['conversation_id']

# Do other work...

# Later, check status
details = get_conversation_details(conversation_id)
if details:
    print(f"Call status: {details.get('status')}")
    print(f"Duration: {details.get('duration_seconds')}s")
```

## 🧪 Testing

### Run Test Script

```bash
# Use default test number
python api/test_e2e_launch.py

# Use custom number
python api/test_e2e_launch.py +15551234567
```

### Test Import

```bash
python -c "from services.outbound_call_service import initiate_call; print('✅ OK')"
```

## 📂 File Structure

```
api/
├── services/
│   ├── outbound_call_service.py  # Main service module
│   └── README_OUTBOUND_CALLS.md  # This file
├── test_e2e_launch.py            # Test script
└── example_call_service.py       # Usage examples
```

## 🔗 Related Documentation

- [ElevenLabs Conversational AI API](https://elevenlabs.io/docs/api-reference/conversational-ai)
- [Twilio Integration Guide](../agent/TWILIO_INTEGRATION_GUIDE.md)
- [Agent Configuration](../agent/README.md)

## 🐛 Troubleshooting

### Call not initiating

1. Check API credentials are correct
2. Verify phone number is in E.164 format (with `+`)
3. Check ElevenLabs dashboard for agent status
4. Verify Twilio phone number is configured

### Monitoring returns None

- Call may take longer than monitoring duration
- Increase `monitor_duration` parameter
- Check call status manually later using `get_conversation_details()`

### Import errors

```bash
# Make sure you're in the api directory or add it to Python path
cd /path/to/donna/api
python -c "from services.outbound_call_service import initiate_call"
```

## 📝 Notes

- Phone numbers must be in E.164 format (e.g., `+13473580012`)
- The service automatically adds `+` prefix if missing
- Monitoring is optional and non-blocking if disabled
- All functions handle errors gracefully and return `None` on failure
- Use `verbose=False` for production/API usage

## 🚦 Return Status Codes

Conversation status values:
- `initiated`: Call is being placed
- `processing`: Call is in progress
- `done`: Call completed successfully
- `completed`: Call finished
- `ended`: Call ended
- `failed`: Call failed

## 🔐 Security

- API keys should be stored in environment variables
- Never commit API keys to version control
- Use separate keys for development/production
- Rotate keys periodically
