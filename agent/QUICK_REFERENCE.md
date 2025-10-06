# Quick Reference: Twilio Integration Testing

## 🔑 Credentials

```bash
# ElevenLabs
ELEVENLABS_API_KEY="YOUR_ELEVENLABS_API_KEY"
ELEVEN_LABS_AGENT_ID="YOUR_AGENT_ID"

# Twilio
TWILIO_ACCOUNT_SID="YOUR_TWILIO_ACCOUNT_SID"
TWILIO_AUTH_TOKEN="YOUR_TWILIO_AUTH_TOKEN"
TWILIO_PHONE_NUMBER="YOUR_TWILIO_PHONE_NUMBER"

# Testing
TEST_PHONE="YOUR_TEST_PHONE_NUMBER"
```

## 📋 Import Twilio Number (Do This First!)

**Dashboard Method (5 min):**
1. https://elevenlabs.io/app/conversational-ai → Phone Numbers
2. Import Phone Number → Twilio
3. Number: `+18887064372`, SID: `ACf74...`, Token: `fd96...`
4. Assign Agent: "Donna"
5. Save

## 🧪 Quick Tests

**System Architecture:** Outbound-only (Donna calls vendors, doesn't receive calls)

### 1. Outbound Call Test - Dashboard (1 min)
```
1. ElevenLabs Dashboard → Phone Numbers
2. Find +18887064372 → Outbound Call button
3. Agent: Donna, To: +13473580012
4. Send Test Call
5. Answer your phone!
```

### 2. Outbound Call Test - API (1 min)
```bash
cd /Users/voyager/Documents/GitHub/donna/api
export ELEVENLABS_API_KEY="sk_9af95a2fca8ea120a514561389ef270c6e3c2235b3da347a"
python3 test_outbound_call.py +13473580012
```

## 🎤 What Donna Should Say

> "Hi, this is Donna and I am calling from **Pixamp Inc**. I wanted to double check about an email I got regarding billing for **Amazon Web Services**—are you the right person to confirm this billing details?"

## ✅ Verification Checklist

- [ ] Phone number imported in dashboard
- [ ] Outbound call connects (dashboard) ← **TEST THIS FIRST**
- [ ] Outbound call connects (API) ← **FOR PRODUCTION**
- [ ] "Pixamp Inc" → dynamic variable working
- [ ] "Amazon Web Services" → dynamic variable working
- [ ] "INV-2024-12345" → invoice number working
- [ ] Call quality is good
- [ ] Conversation follows prompt

**Note:** No inbound testing needed - this is outbound-only!

## 🐛 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| "Phone number not found" | Import via dashboard first |
| Call doesn't connect | Check Twilio console for errors |
| Variables not substituting | Check variable names in test script |
| Donna doesn't follow prompt | Re-sync agent config |

## 📁 Key Files

- **agent/NEXT_STEPS.md** ← Detailed testing guide
- **agent/TWILIO_INTEGRATION_GUIDE.md** ← Setup documentation
- **api/test_outbound_call.py** ← Main test script
- **agent/agent_configs/prod/donna-billing-verifier.json** ← Agent config

## 🔗 Quick Links

- ElevenLabs Dashboard: https://elevenlabs.io/app/conversational-ai
- Twilio Console: https://console.twilio.com/
- ElevenLabs Docs: https://elevenlabs.io/docs/agents-platform/phone-numbers/twilio-integration/native-integration

## 📊 Test Scenarios

1. **Normal Flow**: Answer → Confirm you're billing → Verify invoice → Provide ticket
2. **Wrong Number**: Answer → Say "wrong number" → Donna apologizes & ends
3. **Suspicious**: Answer → Say "we didn't send this" → Donna asks for fraud contact
4. **Interruption**: Answer → Talk while Donna speaking → Donna stops & responds
5. **Transfer**: Answer → Say "need to transfer you" → Donna re-states purpose

## 🎯 Success = All Green

When you see this, you're done:
- ✅ Import complete
- ✅ Outbound (dashboard) passed ← **Start here**
- ✅ Outbound (API) passed ← **Then test this**
- ✅ Dynamic variables working
- ✅ Conversation quality good

**Inbound calls NOT needed** - outbound verification only!

---

**Ready to integrate with fraud detection pipeline!** 🚀
