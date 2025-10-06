# 🚀 Quick Start Guide - Donna Agent

## ✅ Setup Complete!

Your Donna agent has been successfully imported and configured. Here's what was done:

### 📦 What's Been Set Up

1. ✅ **Agent Configuration Fetched** from ElevenLabs dashboard
2. ✅ **Dev Environment** configured at `agent_configs/dev/donna-billing-verifier.json`
3. ✅ **Prod Environment** configured at `agent_configs/prod/donna-billing-verifier.json`
4. ✅ **Registry Files** updated (`agents.json` and `agents.lock`)
5. ✅ **Edge Cases Documentation** created at `EDGE_CASES.md`

### 🔑 Your Credentials

```bash
# Agent ID
AGENT_ID: agent_2601k6rm4bjae2z9amfm5w1y6aps

# API Key
API_KEY: sk_9af95a2fca8ea120a514561389ef270c6e3c2235b3da347a

# Key ID
KEY_ID: 25e5f29f4e812e8b5e4663ade9f5459cd4e3efef8e563b2ff56346687914321f
```

**⚠️ Important:** Keep these credentials secure! Add them to your shell environment:

```bash
# Add to ~/.zshrc or ~/.bashrc for persistence
export ELEVENLABS_API_KEY="sk_9af95a2fca8ea120a514561389ef270c6e3c2235b3da347a"
export ELEVENLABS_KEY_ID="25e5f29f4e812e8b5e4663ade9f5459cd4e3efef8e563b2ff56346687914321f"
export ELEVEN_LABS_AGENT_ID="agent_2601k6rm4bjae2z9amfm5w1y6aps"
```

---

## 🎯 Next Steps

### 1. Deploy to Development Environment

```bash
cd /Users/voyager/Documents/GitHub/donna/agent

# Set API key for this session
export ELEVENLABS_API_KEY="sk_9af95a2fca8ea120a514561389ef270c6e3c2235b3da347a"

# Preview changes (dry run)
agents sync --env dev --dry-run

# Deploy to dev
agents sync --env dev
```

### 2. Test Your Agent

**Option A: ElevenLabs Dashboard**
1. Visit: https://elevenlabs.io/app/conversational-ai
2. Find "Donna" agent
3. Click "Test" to start a sample conversation
4. Verify the agent responds correctly

**Option B: API Testing**
```bash
curl -X POST https://api.elevenlabs.io/v1/convai/conversations \
  -H "xi-api-key: sk_9af95a2fca8ea120a514561389ef270c6e3c2235b3da347a" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent_2601k6rm4bjae2z9amfm5w1y6aps",
    "require_explicit_content_consent": true
  }'
```

### 3. Deploy to Production (When Ready)

```bash
# Preview production changes
agents sync --env prod --dry-run

# Deploy to production
agents sync --env prod

# Verify deployment
agents status
```

---

## 📊 Current Configuration Summary

### Development Environment (`dev`)

- **Config Path:** `agent_configs/dev/donna-billing-verifier.json`
- **Tags:** `environment:dev`, `testing`
- **Privacy Settings:**
  - Voice Recording: **Disabled** (for privacy during testing)
  - Retention: **7 days**
  - Auto-delete transcripts: **Enabled**

### Production Environment (`prod`)

- **Config Path:** `agent_configs/prod/donna-billing-verifier.json`
- **Tags:** `environment:prod`, `billing-verification`
- **Privacy Settings:**
  - Voice Recording: **Enabled** (for quality assurance)
  - Retention: **Unlimited** (or as configured)
  - Audio recording: **Enabled**

### Agent Features

✅ **Voice:** ElevenLabs Turbo V2 (high quality, low latency)  
✅ **Voice ID:** EXAVITQu4vr4xnSDxMaL  
✅ **LLM:** Claude Sonnet 4.5 (intelligent, consistent)  
✅ **Max Duration:** 600 seconds (10 minutes)  
✅ **ASR:** High quality with ElevenLabs provider  
✅ **Dynamic Variables:** `customer_org`, `vendor__legal_name`  
✅ **Tools:** Voice isolator, end call, keypad, voicemail detection  
✅ **Evaluation Criteria:** 9 comprehensive criteria configured  
✅ **Data Collection:** Fraud detection fields, reasoning trace, transcript summary

---

## 🔧 Common Commands

```bash
# Check status of all agents
agents status

# Check authentication
agents whoami

# Preview changes before deploying
agents sync --env dev --dry-run
agents sync --env prod --dry-run

# Deploy to environments
agents sync --env dev
agents sync --env prod

# Watch for changes and auto-sync (development)
agents watch

# Generate widget embed code
agents widget "Donna"

# List all configured agents
agents list-agents

# Fetch latest config from platform
agents fetch
```

---

## 🛠️ Making Configuration Changes

### 1. Edit Configuration Files

```bash
# Edit dev config
code agent_configs/dev/donna-billing-verifier.json

# Edit prod config
code agent_configs/prod/donna-billing-verifier.json
```

### 2. Validate JSON Syntax

```bash
# Validate dev config
jq . agent_configs/dev/donna-billing-verifier.json > /dev/null && echo "✅ Valid" || echo "❌ Invalid"

# Validate prod config
jq . agent_configs/prod/donna-billing-verifier.json > /dev/null && echo "✅ Valid" || echo "❌ Invalid"
```

### 3. Preview and Deploy

```bash
# Always preview first
agents sync --env dev --dry-run

# Then deploy
agents sync --env dev
```

---

## 🔍 Key Configuration Sections

### Changing the Prompt

Edit the `conversation_config.agent.prompt.prompt` field in your config:

```json
{
  "conversation_config": {
    "agent": {
      "prompt": {
        "prompt": "Your new prompt here..."
      }
    }
  }
}
```

### Changing the Voice

Edit the `conversation_config.tts.voice_id` field:

```json
{
  "conversation_config": {
    "tts": {
      "voice_id": "EXAVITQu4vr4xnSDxMaL"
    }
  }
}
```

Browse voices at: https://elevenlabs.io/app/voice-library

### Changing First Message

Edit the `conversation_config.agent.first_message` field:

```json
{
  "conversation_config": {
    "agent": {
      "first_message": "Hi, this is Donna calling from {{customer_org}}..."
    }
  }
}
```

### Adding Dynamic Variables

When starting a conversation via API, pass variables:

```python
from elevenlabs import ElevenLabs

client = ElevenLabs(api_key="sk_9af95a2fca8ea120a514561389ef270c6e3c2235b3da347a")

conversation = client.conversational_ai.start_conversation(
    agent_id="agent_2601k6rm4bjae2z9amfm5w1y6aps",
    variables={
        "customer_org": "Pixamp, Inc",
        "vendor__legal_name": "Amazon Web Services"
    }
)
```

---

## 🐛 Troubleshooting

### Issue: "401 Unauthorized"

**Solution:**
```bash
# Re-authenticate
export ELEVENLABS_API_KEY="sk_9af95a2fca8ea120a514561389ef270c6e3c2235b3da347a"
agents whoami
```

### Issue: "Agent not found"

**Solution:**
```bash
# Verify agent ID in agents.lock
cat agents.lock | jq '.agents.Donna.prod.id'

# Should be: agent_2601k6rm4bjae2z9amfm5w1y6aps
```

### Issue: "Invalid JSON"

**Solution:**
```bash
# Validate and fix
jq . agent_configs/dev/donna-billing-verifier.json

# If invalid, re-fetch
agents fetch
```

### Issue: "Changes not appearing"

**Solution:**
```bash
# Force sync
agents sync --env dev

# Clear conversations and test fresh
# End all active conversations in dashboard
```

For more troubleshooting, see **`EDGE_CASES.md`** (comprehensive edge case documentation).

---

## 📚 Integration with Fraud Detection Pipeline

### Current Pipeline Position

```
Email Arrives
  ↓
Rule-based Check
  ↓
Gemini Classification
  ↓
Domain Analysis
  ↓
Company Verification (Database)
  ↓
Online Verification (Google Search)
  ↓
[IF VERIFICATION UNCLEAR]
  ↓
🎯 CALL DONNA AGENT ← Your agent is here
  ↓
Final Decision
```

### Python Integration Example

```python
from elevenlabs import ElevenLabs
import os

# Initialize client
client = ElevenLabs(api_key=os.environ.get("ELEVENLABS_API_KEY"))

def verify_invoice_with_donna(
    company_name: str,
    vendor_legal_name: str,
    phone_number: str,
    invoice_details: dict
):
    """
    Call Donna to verify invoice with the vendor
    """
    # Start conversation
    conversation = client.conversational_ai.start_conversation(
        agent_id="agent_2601k6rm4bjae2z9amfm5w1y6aps",
        variables={
            "customer_org": company_name,
            "vendor__legal_name": vendor_legal_name
        }
    )
    
    # Initiate phone call (requires Twilio integration)
    # See: ELEVENLABS_TWILIO_SETUP.md
    
    # Return conversation ID for tracking
    return {
        "conversation_id": conversation.id,
        "status": "initiated",
        "timestamp": datetime.now().isoformat()
    }

# Example usage
result = verify_invoice_with_donna(
    company_name="Pixamp, Inc",
    vendor_legal_name="Amazon Web Services",
    phone_number="+1-206-266-1000",
    invoice_details={
        "invoice_id": "INV-12345",
        "amount": 1234.56,
        "email": "billing@scam-domain.com"
    }
)
```

### Webhook Handler (for call results)

```python
from fastapi import APIRouter, Request

router = APIRouter()

@router.post("/webhooks/elevenlabs/conversation-complete")
async def handle_conversation_complete(request: Request):
    """
    Webhook handler for when Donna completes a call
    """
    data = await request.json()
    
    conversation_id = data.get("conversation_id")
    agent_id = data.get("agent_id")
    
    # Extract fraud detection results
    is_fraudulent = data.get("data_collection", {}).get("is_fraudulent")
    reasoning_trace = data.get("data_collection", {}).get("reasoning_trace")
    transcript = data.get("data_collection", {}).get("summarized_transcript")
    
    # Update database with results
    # ... your database logic here ...
    
    return {"status": "processed"}
```

---

## 📖 Documentation Files

- **`README.md`** - Complete agent documentation and CLI reference
- **`SETUP_COMPLETE.md`** - Overview of what was set up
- **`QUICKSTART.md`** - This file (quick start guide)
- **`EDGE_CASES.md`** - Comprehensive troubleshooting and edge cases
- **`setup.sh`** - Quick deployment script

### API Documentation

- **ElevenLabs Agents:** https://elevenlabs.io/docs/agents-platform
- **CLI Documentation:** https://elevenlabs.io/docs/agents-platform/libraries/agents-cli
- **API Reference:** https://elevenlabs.io/docs/api-reference/conversational-ai

---

## 🎉 You're All Set!

Your Donna agent is ready to deploy. Here's a recommended workflow:

1. ✅ **Review Configuration** - Check `agent_configs/dev/donna-billing-verifier.json`
2. 🚀 **Deploy to Dev** - Run `agents sync --env dev`
3. 🧪 **Test** - Use ElevenLabs dashboard to test conversations
4. 🔄 **Iterate** - Make changes, validate, sync, test
5. ✅ **Deploy to Prod** - When ready, run `agents sync --env prod`
6. 📊 **Monitor** - Track conversations and evaluations in dashboard
7. 🔧 **Optimize** - Review metrics and improve prompt/settings

---

## 🆘 Need Help?

- **Edge Cases:** See `EDGE_CASES.md`
- **CLI Issues:** https://github.com/elevenlabs/elevenlabs-agents-cli/issues
- **Platform Support:** support@elevenlabs.io
- **Community:** https://elevenlabs.io/discord

---

**Setup Date:** 2025-10-05  
**Agent ID:** agent_2601k6rm4bjae2z9amfm5w1y6aps  
**Environment:** Development & Production configured  
**Status:** Ready to deploy 🚀
