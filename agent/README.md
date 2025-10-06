# Donna Agent - ElevenLabs CLI Configuration

## Overview

This directory contains the ElevenLabs agent configuration for **Donna**, a professional billing verification assistant. Donna calls companies to verify if specific email addresses are legitimate billing contacts.

## Project Structure

```
agent/
├── README.md                           # This file
├── agents.json                         # Agent registry
├── agents.lock                         # Lock file with agent IDs and hashes
├── tools.json                          # Tool definitions registry
├── tests.json                          # Test configurations
├── agent_configs/                      # Environment-specific configurations
│   ├── dev/
│   │   └── donna-billing-verifier.json    # Development configuration
│   ├── prod/
│   │   └── donna-billing-verifier.json    # Production configuration
│   └── staging/                        # (Future use)
└── tool_configs/                       # Tool configuration files
```

## Agent Configuration

### Donna Billing Verifier

**Purpose**: Professional phone agent that calls companies to verify billing email addresses.

**Key Features**:
- **Professional Tone**: Maintains respectful, concise communication
- **Clear Objective**: Focused solely on email verification
- **Time-Efficient**: Designed for conversations under 2 minutes
- **Smart ASR**: Configured with billing-specific keywords
- **Evaluation Criteria**: Built-in quality metrics

### Configuration Highlights

#### Voice Settings (TTS)
- **Model**: `eleven_turbo_v2_5` - Fast, high-quality voice
- **Voice ID**: `pNInz6obpgDQGcFmaJgB` - Professional tone
- **Stability**: 0.5 - Balanced consistency
- **Similarity Boost**: 0.75 - Natural voice reproduction

#### Speech Recognition (ASR)
- **Quality**: High
- **Provider**: ElevenLabs
- **Keywords**: billing, invoice, email, verify, confirm, legitimate, official

#### Conversation Settings
- **Max Duration**: 180 seconds (3 minutes)
- **Turn Timeout**: 7 seconds
- **Client Events**: audio, interruption, agent_response, user_transcript

#### AI Model
- **LLM**: GPT-4o
- **Temperature**: 0.1 (Very precise, consistent)
- **Max Tokens**: 500 (Concise responses)

### Agent Prompt

Donna introduces herself professionally and explains she's verifying billing information. The conversation follows this structure:

1. Polite introduction
2. Clear statement of the email address to verify
3. Direct question: "Is this an official billing email for your company?"
4. Professional thank you
5. Note any concerns if verification fails

### First Message

```
Hello, this is Donna calling. I'm reaching out to verify some billing information 
for your company. Do you have a moment to help me confirm an email address?
```

## CLI Commands Reference

### Prerequisites

```bash
# Install the ElevenLabs CLI globally
npm install -g @elevenlabs/agents-cli

# Verify installation
agents --version
```

### Authentication

```bash
# Login with your ElevenLabs API key
agents login

# Or set environment variable
export ELEVENLABS_API_KEY="your-api-key-here"
```

### Agent Management

```bash
# Check agent status
agents status

# Check specific environment
agents status --env dev
agents status --env prod

# Sync agent to ElevenLabs platform
agents sync --env dev
agents sync --env prod

# Preview changes before sync (dry run)
agents sync --env dev --dry-run
```

### Import/Export

```bash
# Import existing agent from platform
agents fetch --env prod

# List all agents on platform
agents fetch --list
```

### Widget Generation

```bash
# Generate HTML embed code for the agent
agents widget "Donna Billing Verifier" --env prod
```

## Environment Differences

### Development (`dev`)
- **Audio Storage**: Disabled (privacy)
- **Tags**: `environment:dev`
- **Use Case**: Testing and development

### Production (`prod`)
- **Audio Storage**: Enabled (for quality assurance)
- **Tags**: `environment:prod`
- **Use Case**: Live phone verification calls

## Integration with Donna System

The agent integrates into the fraud detection pipeline at the verification stage:

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
🎯 CALL DONNA AGENT ← This agent
  ↓
Final Decision
```

### When Donna is Triggered

Donna makes a verification call when:
1. Email passes initial checks
2. Company is found but attributes differ
3. Online verification is inconclusive
4. Manual verification is needed

### Expected Use Case

```python
# Example: Triggering Donna from the fraud detection system
from app.services.donna_agent import verify_company_by_call

result = verify_company_by_call(
    company_name="Google Cloud",
    phone_number="+1-650-253-0000",
    email_address="billing@googlecloud.com"
)

# Result structure:
# {
#   "success": True/False,
#   "verified": True/False,
#   "call_status": "completed",
#   "transcript": "...",
#   "confidence": 0.95
# }
```

## Deployment Workflow

### 1. Development Phase
```bash
cd /Users/voyager/Documents/GitHub/donna/agent

# Make changes to agent_configs/dev/donna-billing-verifier.json
# Test locally or sync to dev environment
agents sync --env dev --dry-run  # Preview
agents sync --env dev             # Deploy
```

### 2. Testing Phase
```bash
# Use the ElevenLabs dashboard to test the agent
# Or use the widget in a test webpage
agents widget "Donna Billing Verifier" --env dev
```

### 3. Production Deployment
```bash
# Update production config if needed
# Review changes
agents sync --env prod --dry-run

# Deploy to production
agents sync --env prod

# Verify deployment
agents status --env prod
```

## CI/CD Integration

Example GitHub Actions workflow:

```yaml
name: Deploy Donna Agent

on:
  push:
    branches: [main]
    paths:
      - 'agent/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install ElevenLabs CLI
        run: npm install -g @elevenlabs/agents-cli
      
      - name: Deploy to Production
        env:
          ELEVENLABS_API_KEY: ${{ secrets.ELEVENLABS_API_KEY }}
        run: |
          cd agent
          agents sync --env prod --dry-run
          agents sync --env prod
          agents status --env prod
```

## Evaluation Criteria

The agent is evaluated on:

1. **Verification Clarity**: Agent clearly states the email address to be verified
2. **Professional Tone**: Agent maintains professional and respectful tone throughout
3. **Brevity**: Conversation is concise and under 2 minutes
4. **Confirmation Obtained**: Agent successfully obtains clear confirmation or denial

## Troubleshooting

### CLI Issues

If you encounter "paths[0] undefined" error:
- This appears to be a CLI bug when using certain commands
- The configuration files are correct
- You can manually upload configurations via the ElevenLabs dashboard

### Authentication Issues

```bash
# Check if API key is set
echo $ELEVENLABS_API_KEY

# Re-login
agents login
```

### Configuration Validation

```bash
# Validate JSON syntax
cat agent_configs/dev/donna-billing-verifier.json | jq .
cat agent_configs/prod/donna-billing-verifier.json | jq .
```

## Next Steps

1. **Authenticate**: Run `agents login` with your ElevenLabs API key
2. **Sync Agent**: Deploy the agent with `agents sync --env dev`
3. **Test**: Use the ElevenLabs dashboard to test phone calls
4. **Integrate**: Connect the agent to your fraud detection pipeline
5. **Monitor**: Review call transcripts and evaluation metrics

## Resources

- [ElevenLabs Agents CLI Documentation](https://elevenlabs.io/docs/agents-platform/libraries/agents-cli)
- [ElevenLabs Agents Dashboard](https://elevenlabs.io/app/conversational-ai)
- [Agent Testing Guide](../api/ELEVEN_AGENT_TEST_RESULTS.md)
- [Twilio Integration Setup](../api/ELEVENLABS_TWILIO_SETUP.md)

## Support

For issues with:
- **Agent Configuration**: Modify JSON files in `agent_configs/`
- **CLI Problems**: Check [ElevenLabs CLI GitHub](https://github.com/elevenlabs/elevenlabs-agents-cli)
- **Voice/Model Issues**: See [ElevenLabs Agents Platform Docs](https://elevenlabs.io/docs/agents-platform)
