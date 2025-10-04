# Refactored Email Fraud Detection System

## 🎯 **Overview**

The system has been refactored into **4 distinct functions** with better names and clear separation of concerns. Each function can be used independently or as part of the complete pipeline.

## 🔧 **Function Structure**

### **1. `is_billing_email(gmail_msg)` - Rule-based Detection**
- **Purpose**: Fast, cost-effective filter using keyword detection
- **Input**: Gmail message JSON
- **Output**: Boolean (true if billing-related)
- **Use Case**: Quick filter before expensive AI analysis
- **Performance**: ~1ms

### **2. `classify_email_type_with_gemini(gmail_msg, user_uuid, fraud_logger)` - AI Classification**
- **Purpose**: Use Gemini AI to classify email type (bill vs receipt vs other)
- **Input**: Gmail message JSON, user UUID, fraud logger
- **Output**: Classification results with confidence and reasoning
- **Use Case**: Determine if email is actually billing-related and what type
- **Performance**: ~2-3 seconds

### **3. `analyze_domain_legitimacy(gmail_msg, email_type, user_uuid, fraud_logger)` - Domain Analysis**
- **Purpose**: Analyze sender domain legitimacy for billing emails
- **Input**: Gmail message JSON, email type, user UUID, fraud logger
- **Output**: Domain analysis results with legitimacy decision
- **Use Case**: Check if sender domain is legitimate or suspicious
- **Performance**: ~500ms

### **4. `check_billing_email_legitimacy(gmail_msg, user_uuid, fraud_logger)` - Complete Pipeline**
- **Purpose**: Orchestrates the complete fraud detection pipeline
- **Input**: Gmail message JSON, user UUID, fraud logger
- **Output**: Complete analysis results with all decisions
- **Use Case**: Main function for complete fraud detection
- **Performance**: ~3-4 seconds total

## 🔄 **Decision Flow**

```
Email Arrives
     ↓
Step 1: Rule-based Check (is_billing_email)
     ↓
Decision: true/false
     ↓
If false → HALT → Status: "fraud"
     ↓
If true → Step 2: Gemini Classification (classify_email_type_with_gemini)
     ↓
Decision: true/false
     ↓
If false → HALT → Status: "fraud"
     ↓
If true → Step 3: Domain Analysis (analyze_domain_legitimacy)
     ↓
Decision: true/false
     ↓
If false → HALT → Status: "fraud"
     ↓
If true → PROCEED → Status: "legit"
```

## 📡 **API Endpoints**

### **Individual Function Endpoints**
- `POST /fraud/check-billing` - Rule-based billing detection
- `POST /fraud/classify-type` - Gemini AI classification
- `POST /fraud/analyze-domain` - Domain legitimacy analysis

### **Complete Pipeline Endpoints**
- `POST /fraud/analyze` - Complete fraud analysis
- `POST /fraud/analyze-batch` - Multiple emails

### **Retrieval Endpoints**
- `GET /fraud/history/{email_id}` - Analysis history
- `GET /fraud/final-decision/{email_id}` - Final verdict
- `GET /fraud/fraud-emails/{user_uuid}` - All fraud emails

## 🧪 **Test Flow**

### **Comprehensive Test Script**
Run `test_comprehensive_flow.py` to test:

1. **Individual Functions** - Test each function separately
2. **Complete Pipeline** - Test the full orchestration
3. **Logging Retrieval** - Test database logging and retrieval
4. **Decision Flow** - Test halt logic and decision paths

### **Test Scenarios**
- **Bill (Legitimate)**: Should proceed through all steps
- **Bill (Suspicious)**: Should halt at domain analysis
- **Receipt**: Should proceed after Gemini classification
- **Newsletter**: Should halt at rule-based check
- **No Sender**: Should halt at domain analysis

## 📊 **Logging Structure**

### **Database Schema**
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

### **Logging Examples**

#### **Bill Email (Legitimate)**
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

#### **Bill Email (Fraud)**
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

## 🚀 **Usage Examples**

### **Individual Function Usage**
```python
# Step 1: Rule-based check
is_billing = is_billing_email(gmail_message)

# Step 2: Gemini classification (only if billing)
if is_billing:
    classification = classify_email_type_with_gemini(gmail_message, user_uuid, fraud_logger)
    
    # Step 3: Domain analysis (only for bills)
    if classification["email_type"] == "bill":
        domain_result = analyze_domain_legitimacy(gmail_message, "bill", user_uuid, fraud_logger)
```

### **Complete Pipeline Usage**
```python
# Complete analysis
result = check_billing_email_legitimacy(gmail_message, user_uuid, fraud_logger)

# Check if processing should halt
if result.get("halt_reason"):
    # HALT - Update email status to "fraud"
    await update_email_status(email_id, "fraud")
else:
    # PROCEED - Update email status to "legit"
    await update_email_status(email_id, "legit")
```

## 🎯 **Benefits**

1. **Modular Design** - Each function has a single responsibility
2. **Cost Optimization** - Rule-based filter reduces AI calls
3. **Clear Decision Path** - Boolean decisions at each step
4. **Complete Audit Trail** - Every decision logged with reasoning
5. **Flexible Integration** - Use individual functions or complete pipeline
6. **Easy Testing** - Each function can be tested independently

## 🔧 **Next Steps**

1. **Run the SQL script** to create the database table
2. **Test the system** with `test_comprehensive_flow.py`
3. **Integrate with email trigger** using the appropriate endpoints
4. **Monitor logs** in Supabase for decision tracking

The refactored system provides **clear separation of concerns** while maintaining the complete fraud detection pipeline!
