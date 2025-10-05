# ElevenLabs Agents Platform + Twilio Webhook Setup Guide

## Overview

This guide walks you through setting up the ElevenLabs Agents Platform CLI with Twilio webhook integration for your Donna phone verification system. The setup allows ElevenLabs agents to make phone calls through your existing Twilio integration for company verification purposes.

## What We've Accomplished

✅ **Installed ElevenLabs Agents Platform CLI**  
✅ **Initialized project structure**  
✅ **Created agent configuration** (`Donna Phone Verification Agent`)  
✅ **Created Twilio webhook tool configuration**  
✅ **Added FastAPI webhook endpoint** (`/api/twilio/webhook`)  
✅ **Updated main FastAPI application** to include the webhook router  

## Project Structure Created

```
donna-web-app/
├── agents.json                           # Agent registry
├── tools.json                           # Tool registry  
├── agents.lock                          # Version lock file
├── agent_configs/
│   └── dev/
│       └── donna-phone-verification-agent.json
├── tool_configs/
│   └── twilio-verification-webhook.json
└── api/
    └── app/
        └── routers/
            └── twilio_webhook.py         # New webhook endpoint
```

## Configuration Files

### 1. Agent Configuration (`agent_configs/dev/donna-phone-verification-agent.json`)

```json
{
  "name": "Donna Phone Verification Agent",
  "conversation_config": {
    "agent": {
      "prompt": "You are Donna, a professional phone verification assistant...",
      "llm": {
        "model": "eleven-multilingual-v1",
        "temperature": 0.1
      },
      "language": "en",
      "tools": ["Twilio Phone Verification Webhook"]
    },
    "tts": {
      "model": "eleven-multilingual-v1", 
      "voice_id": "EXAVITQu4vr4xnSDxMaL",
      "audio_format": {
        "format": "pcm",
        "sample_rate": 44100
      }
    },
    "asr": {
      "model": "nova-2-general",
      "language": "auto"
    },
    "conversation": {
      "max_duration_seconds": 1800,
      "text_only": false,
      "client_events": []
    }
  },
  "platform_settings": {
    "widget": {
      "conversation_starters": [],
      "branding": {}
    }
  },
  "tags": ["environment:dev", "phone-verification", "fraud-detection"]
}
```

### 2. Twilio Webhook Tool (`tool_configs/twilio-verification-webhook.json`)

```json
{
  "name": "Twilio Phone Verification Webhook",
  "description": "Webhook tool for making phone calls through Twilio for company verification",
  "type": "webhook",
  "config": {
    "url": "https://your-domain.com/api/twilio/webhook",
    "method": "POST",
    "headers": {
      "Content-Type": "application/json",
      "Authorization": "Bearer {{TWILIO_WEBHOOK_TOKEN}}"
    },
    "timeout": 30000,
    "retry_policy": {
      "max_retries": 3,
      "backoff_multiplier": 2
    }
  },
  "parameters": {
    "company_name": {
      "type": "string",
      "description": "Name of the company to verify",
      "required": true
    },
    "phone_number": {
      "type": "string", 
      "description": "Phone number to call for verification",
      "required": true
    },
    "email_to_verify": {
      "type": "string",
      "description": "Email address to verify with the company",
      "required": true
    },
    "verification_context": {
      "type": "string",
      "description": "Additional context about why verification is needed",
      "required": false
    }
  }
}
```

## Next Steps to Complete Setup

### 1. Deploy Your FastAPI Application

Make sure your FastAPI application is running and accessible at a public URL. The webhook endpoint will be available at:

```
POST https://your-domain.com/api/twilio/webhook
```

### 2. Update Webhook URL in Tool Configuration

Update the `url` field in `tool_configs/twilio-verification-webhook.json` with your actual domain:

```json
{
  "config": {
    "url": "https://your-actual-domain.com/api/twilio/webhook"
  }
}
```

### 3. Set Up Authentication Token

Add a webhook authentication token to your environment variables:

```bash
# Add to your .env.local file
TWILIO_WEBHOOK_TOKEN=your-secure-random-token-here
```

### 4. Sync Agent to ElevenLabs Platform

Run the sync command to upload your agent configuration:

```bash
cd /Users/howardchao/Documents/GitHub/donna-web-app
export ELEVENLABS_API_KEY="sk_9af95a2fca8ea120a514561389ef270c6e3c2235b3da347a"
agents sync --env dev
```

### 5. Test the Webhook Endpoint

Test your webhook endpoint with a sample request:

```bash
curl -X POST https://your-domain.com/api/twilio/webhook/test \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Test Company",
    "phone_number": "+1234567890", 
    "email_to_verify": "test@example.com",
    "verification_context": "Testing webhook integration"
  }'
```

### 6. Configure ElevenLabs Agent ID

Once the agent is synced, you'll get an agent ID. Update your environment variables:

```bash
# Add to your .env.local file  
ELEVEN_LABS_AGENT_ID=agent_xxxxxxxxxxxxx
```

## Integration with Existing System

The webhook integrates with your existing `ElevenLabsAgent` service:

- **Input**: Receives structured requests from ElevenLabs agents
- **Processing**: Uses your existing `verify_company_by_call()` method
- **Output**: Returns standardized response format for ElevenLabs

## API Endpoints Created

### Main Webhook Endpoint
- **URL**: `POST /api/twilio/webhook`
- **Purpose**: Handle phone verification requests from ElevenLabs agents
- **Authentication**: Bearer token via `TWILIO_WEBHOOK_TOKEN`

### Health Check
- **URL**: `GET /api/twilio/webhook/status`  
- **Purpose**: Verify webhook service is running

### Test Endpoint
- **URL**: `POST /api/twilio/webhook/test`
- **Purpose**: Test webhook without making actual calls

## Environment Variables Required

```bash
# ElevenLabs Configuration
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
ELEVEN_LABS_AGENT_ID=agent_xxxxxxxxxxxxx

# Twilio Configuration  
TWILIO_ACCOUNT_SID=your_twilio_account_sid_here
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
TWILIO_PHONE_NUMBER=your_twilio_phone_number_here

# Webhook Security
TWILIO_WEBHOOK_TOKEN=your-secure-random-token-here
```

## Troubleshooting

### CLI Issues
If you encounter terminal interaction issues with the CLI, you can:

1. **Use the web interface**: Log into [ElevenLabs Dashboard](https://elevenlabs.io) and manually create agents
2. **Use API directly**: Make direct API calls to ElevenLabs Agents API
3. **Fix terminal environment**: Ensure your terminal supports interactive mode

### Webhook Issues
- Check that your FastAPI application is running and accessible
- Verify the webhook URL is correct and publicly accessible
- Ensure authentication tokens are properly configured
- Check logs for any errors in the webhook processing

## Benefits of This Setup

1. **Version Control**: Agent configurations are stored as code
2. **Environment Management**: Separate dev/staging/prod configurations
3. **Tool Integration**: Seamless integration with your existing Twilio setup
4. **Scalability**: Easy to add more agents and tools
5. **Monitoring**: Built-in status and health check endpoints

## Next Development Steps

1. **Add Production Environment**: Create `agent_configs/prod/` with production settings
2. **Enhance Agent Prompts**: Refine the verification conversation flow
3. **Add More Tools**: Integrate additional verification methods
4. **Monitoring**: Add logging and analytics to track verification success rates
5. **Testing**: Create comprehensive test suites for the webhook integration

This setup provides a solid foundation for integrating ElevenLabs agents with your existing Twilio phone verification system, following the "agents as code" approach recommended by ElevenLabs.
