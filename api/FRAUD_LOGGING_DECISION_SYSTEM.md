# Boolean Decision System for Email Fraud Detection

## 🎯 **Overview**

The system now uses **boolean decisions** (`true`/`false`) at each step to determine whether to proceed or halt processing. Each decision is logged with reasoning, and the final status is posted to the email table.

## 🔄 **Decision Flow**

```
Email Arrives
     ↓
Step 1: Gemini Analysis
     ↓
Decision: true (billing) / false (other)
     ↓
If false → HALT → Status: "fraud"
     ↓
If true → Step 2: Domain Check (bills only)
     ↓
Decision: true (legitimate) / false (suspicious)
     ↓
If false → HALT → Status: "fraud"
     ↓
If true → PROCEED → Status: "legit"
```

## 📊 **Database Schema**

### **Updated `email_fraud_logs` Table**
```sql
CREATE TABLE email_fraud_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email_id TEXT NOT NULL,
    user_uuid UUID NOT NULL REFERENCES auth.users(id),
    step TEXT NOT NULL CHECK (step IN ('gemini_analysis', 'domain_check', 'final_decision')),
    decision BOOLEAN NOT NULL,  -- true = proceed, false = halt
    confidence DECIMAL(3,2) CHECK (confidence >= 0.00 AND confidence <= 1.00),
    reasoning TEXT,  -- justification for the decision
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## 🎯 **Decision Logic**

### **Step 1: Gemini Analysis**
- **Input**: Gmail message
- **Decision**: `true` if billing-related (bill or receipt), `false` if other
- **Reasoning**: "Email type: bill - Contains payment request"
- **Action**: If `false` → HALT, If `true` → Continue

### **Step 2: Domain Check (Bills Only)**
- **Input**: Sender email address
- **Decision**: `true` if legitimate domain, `false` if suspicious
- **Reasoning**: "Domain analysis: No issues found" or "Suspicious TLD detected"
- **Action**: If `false` → HALT, If `true` → PROCEED

### **Step 3: Final Decision**
- **Input**: Combined results
- **Decision**: `true` if safe to proceed, `false` if fraud detected
- **Reasoning**: "Bill analysis: Legitimate" or "Suspicious domain"
- **Status**: "legit" if `true`, "fraud" if `false`

## 📝 **Logging Examples**

### **Bill Email (Legitimate)**
```json
[
  {
    "step": "gemini_analysis",
    "decision": true,
    "confidence": 0.95,
    "reasoning": "Email type: bill - Contains payment request"
  },
  {
    "step": "domain_check",
    "decision": true,
    "confidence": 0.90,
    "reasoning": "Domain analysis: No issues found"
  },
  {
    "step": "final_decision",
    "decision": true,
    "confidence": 0.90,
    "reasoning": "Bill analysis: Legitimate"
  }
]
```
**Result**: Status = "legit", Halt Reason = null

### **Bill Email (Fraud)**
```json
[
  {
    "step": "gemini_analysis",
    "decision": true,
    "confidence": 0.88,
    "reasoning": "Email type: bill - Contains urgent payment request"
  },
  {
    "step": "domain_check",
    "decision": false,
    "confidence": 0.85,
    "reasoning": "Domain analysis: Suspicious TLD, no DNS resolution"
  },
  {
    "step": "final_decision",
    "decision": false,
    "confidence": 0.85,
    "reasoning": "Bill analysis: Suspicious domain"
  }
]
```
**Result**: Status = "fraud", Halt Reason = "suspicious_domain"

### **Newsletter Email**
```json
[
  {
    "step": "gemini_analysis",
    "decision": false,
    "confidence": 0.90,
    "reasoning": "Email type: other - Newsletter content"
  },
  {
    "step": "final_decision",
    "decision": false,
    "confidence": 0.90,
    "reasoning": "Not billing-related: other"
  }
]
```
**Result**: Status = "fraud", Halt Reason = "not_billing"

## 🚀 **Integration Points**

### **For Email Trigger System**
```python
# Call fraud analysis
result = check_billing_email_legitimacy(gmail_message, user_uuid, fraud_logger)

# Check if processing should halt
if result.get("halt_reason"):
    # HALT - Update email status to "fraud"
    await update_email_status(email_id, "fraud")
    # Trigger fraud alert
    await send_fraud_alert(result)
else:
    # PROCEED - Update email status to "legit"
    await update_email_status(email_id, "legit")
    # Continue normal processing
```

### **For Email Table Status**
```python
# Get final status for email table
status = fraud_logger.get_email_status(email_id, user_uuid)
# Returns: "legit", "fraud", or "pending"

# Update email table
await update_email_table(email_id, {"status": status})
```

## 🎯 **Benefits**

1. **Simple Decision Logic** - Clear true/false at each step
2. **Early Halt** - Stop processing as soon as fraud is detected
3. **Clear Status** - Email table gets definitive "legit" or "fraud" status
4. **Complete Audit Trail** - Every decision logged with reasoning
5. **LLM Context** - Full analysis history for call agents

## 🔧 **API Response Format**

```json
{
  "email_id": "gmail_123",
  "is_billing": true,
  "email_type": "bill",
  "is_legitimate": true,
  "confidence": 0.90,
  "reasoning": "Bill analysis: Legitimate",
  "halt_reason": null,
  "log_entries": [...],
  "status": "legit"
}
```

## 📈 **Next Steps**

1. **Run updated SQL** to create boolean decision table
2. **Test the halt logic** with sample emails
3. **Integrate with email trigger** system
4. **Update email table** with status field
5. **Connect to call agent** for LLM context

The system now provides **clear go/no-go decisions** at each step, making it easy to integrate with your email processing pipeline!
