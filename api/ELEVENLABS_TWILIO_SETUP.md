# ElevenLabs Conversational AI + Twilio Integration Setup

This guide will help you set up ElevenLabs Conversational AI with Twilio for interactive phone verification calls.

## 🎯 What This Does

Instead of playing a pre-recorded message, your system will use an **interactive AI agent** that can:
- Have natural conversations
- Understand and respond to questions
- Adapt based on the person's responses
- Handle objections professionally
- Transfer to billing department if needed

## 📋 Prerequisites

- ✅ ElevenLabs account with Conversational AI access
- ✅ Twilio account with phone number
- ✅ API keys from both services

## 🚀 Setup Steps

### Step 1: Create Your Conversational AI Agent

1. Go to https://elevenlabs.io/app/conversational-ai
2. Click "Create Agent"
3. Configure the agent:

   **Name:** `Billing Verification Agent`
   
   **Voice:** Sarah (or your preferred voice)
   
   **Voice Settings:**
   - Stability: 0.35
   - Similarity: 0.80
   - Style/Temperature: 0.30
   - Speed: 0.90
   - Optimize Streaming Latency: 3
   
   **System Prompt:** (Copy this into the agent's prompt)
   ```
   You are a professional verification assistant conducting a security check call.

   Your Task:
   Verify if the email address is a legitimate billing email used by the company.

   Conversation Flow:

   1. Opening (Friendly & Professional):
   "Hello! This is a quick verification call regarding [company name]. Is this a good time to talk for just a moment?"
   
   2. If they say yes, explain the purpose:
   "Great! We recently received an invoice email from [email address], and I'm calling to confirm this is an official billing address used by your company. This is just a routine security check to protect against fraudulent billing emails."

   3. Ask for verification:
   "Could you please confirm if [email address] is a legitimate email address that [company name] uses to send invoices to customers?"

   4. Handle responses naturally:
   - If they confirm: "Perfect, thank you so much for confirming that. This helps us ensure the security of our billing processes. Have a great day!"
   - If they deny: "I appreciate you letting me know. Could you provide the correct billing email address we should be using?"
   - If they're unsure: "No problem at all. Would you be able to transfer me to your billing department, or should I call back at a better time?"
   - If they ask why: "This is a fraud prevention measure. We want to make sure we're only processing invoices from legitimate company email addresses."

   5. Closing:
   Always thank them for their time and end professionally.

   Important Guidelines:
   - Be warm, friendly, and professional
   - Listen actively and adapt to their responses
   - Keep the call brief (under 2 minutes)
   - If they're busy, offer to call back
   - Never be pushy or aggressive
   - Respect their decision if they can't or won't verify

   Tone:
   Professional yet conversational, like a helpful colleague making a routine check.
   ```

4. **Copy the Agent ID** (you'll need this)

### Step 2: Import Your Twilio Number into ElevenLabs

1. In ElevenLabs, go to **Phone Numbers** tab
2. Click "Import Twilio Number"
3. Enter your Twilio credentials:
   - **Phone Number:** Your Twilio number (e.g., +18887064372)
   - **Account SID:** From Twilio Console
   - **Auth Token:** From Twilio Console
4. Click "Import"
5. ElevenLabs will automatically configure the webhook

### Step 3: Assign Agent to Phone Number (Optional - for inbound)

If you want the agent to handle inbound calls:
1. Select your imported Twilio number
2. Assign your "Billing Verification Agent" to it
3. Save

### Step 4: Set Environment Variables

Add these to your `.env.local` file:

```bash
# ElevenLabs
ELEVENLABS_API_KEY=your-elevenlabs-api-key
ELEVENLABS_AGENT_ID=your-agent-id-from-step-1

# Twilio
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_PHONE_NUMBER=+18887064372
```

Or export them:

```bash
export ELEVENLABS_API_KEY='your-elevenlabs-api-key'
export ELEVENLABS_AGENT_ID='your-agent-id'
export TWILIO_ACCOUNT_SID='your-twilio-account-sid'
export TWILIO_AUTH_TOKEN='your-twilio-auth-token'
export TWILIO_PHONE_NUMBER='+18887064372'
```

### Step 5: Test the Integration

Run the test script:

```bash
cd api
source venv/bin/activate
python test_real_call.py
```

## 📞 How It Works

1. **Your system calls the API** with company name and email to verify
2. **ElevenLabs initiates the call** via Twilio to the company's phone number
3. **AI agent has a conversation** to verify the billing email
4. **Agent adapts in real-time** based on responses
5. **Call completes** and you get the conversation ID for review

## 🎯 Benefits Over Pre-recorded Messages

- ✅ **Interactive:** Can answer questions and handle objections
- ✅ **Natural:** Sounds like a real person having a conversation
- ✅ **Adaptive:** Responds appropriately to different scenarios
- ✅ **Professional:** Handles transfers and callbacks gracefully
- ✅ **Efficient:** Can gather additional information if needed

## 📊 Monitoring Calls

View all conversations in the ElevenLabs dashboard:
https://elevenlabs.io/app/conversational-ai/conversations

Each call includes:
- Full transcript
- Audio recording
- Duration
- Outcome
- Agent performance metrics

## 🔧 Troubleshooting

### "Agent ID not configured"
- Make sure you created an agent and copied the ID
- Set the `ELEVENLABS_AGENT_ID` environment variable

### "Twilio number not imported"
- Import your Twilio number in ElevenLabs dashboard first
- Verify the credentials are correct

### "Call fails immediately"
- Check Twilio account has credits
- Verify phone number format (+1XXXXXXXXXX)
- Check ElevenLabs agent is active

## 💡 Tips

1. **Test with your own number first** to hear how the agent sounds
2. **Review transcripts** to improve the agent's prompt
3. **Monitor conversation metrics** to optimize performance
4. **Update the prompt** based on real-world responses

## 🎉 You're Done!

Your fraud detection system now has an intelligent AI agent that can have natural conversations to verify billing emails!
