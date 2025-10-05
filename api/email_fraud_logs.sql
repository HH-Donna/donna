-- Email Fraud Logs Table
CREATE TABLE IF NOT EXISTS email_fraud_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email_id TEXT NOT NULL,
    user_uuid UUID NOT NULL REFERENCES auth.users(id),
    step TEXT NOT NULL CHECK (step IN ('gemini_analysis', 'domain_check', 'company_verification', 'online_verification', 'final_decision')),
    decision BOOLEAN NOT NULL,  -- true = proceed, false = halt
    confidence DECIMAL(3,2) CHECK (confidence >= 0.00 AND confidence <= 1.00),
    reasoning TEXT,  -- justification for the decision
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_email_fraud_logs_email_id ON email_fraud_logs(email_id);
CREATE INDEX IF NOT EXISTS idx_email_fraud_logs_user_uuid ON email_fraud_logs(user_uuid);
CREATE INDEX IF NOT EXISTS idx_email_fraud_logs_step ON email_fraud_logs(step);
CREATE INDEX IF NOT EXISTS idx_email_fraud_logs_created_at ON email_fraud_logs(created_at);

-- Google Search Results Table
CREATE TABLE IF NOT EXISTS google_search_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email_id TEXT NOT NULL,
    user_uuid UUID NOT NULL REFERENCES auth.users(id),
    company_name TEXT NOT NULL,
    search_query TEXT NOT NULL,
    billing_address TEXT,
    biller_phone_number TEXT,
    email TEXT,  -- Email address found in search results
    frequency TEXT,  -- Still tracked but not searched online
    search_results JSONB,  -- Raw Google Search API results
    extracted_attributes JSONB,  -- Extracted attributes from search results
    confidence DECIMAL(3,2) CHECK (confidence >= 0.00 AND confidence <= 1.00),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for Google Search Results
CREATE INDEX IF NOT EXISTS idx_google_search_results_email_id ON google_search_results(email_id);
CREATE INDEX IF NOT EXISTS idx_google_search_results_user_uuid ON google_search_results(user_uuid);
CREATE INDEX IF NOT EXISTS idx_google_search_results_company_name ON google_search_results(company_name);
CREATE INDEX IF NOT EXISTS idx_google_search_results_created_at ON google_search_results(created_at);

-- Function to get complete fraud analysis for an email
CREATE OR REPLACE FUNCTION get_email_fraud_analysis(p_email_id TEXT, p_user_uuid UUID)
RETURNS TABLE (
    step TEXT,
    decision BOOLEAN,
    confidence DECIMAL(3,2),
    reasoning TEXT,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        efl.step,
        efl.decision,
        efl.confidence,
        efl.reasoning,
        efl.details,
        efl.created_at
    FROM email_fraud_logs efl
    WHERE efl.email_id = p_email_id 
    AND efl.user_uuid = p_user_uuid
    ORDER BY efl.created_at ASC;
END;
$$ LANGUAGE plpgsql;

-- Function to get final decision for an email
CREATE OR REPLACE FUNCTION get_email_final_decision(p_email_id TEXT, p_user_uuid UUID)
RETURNS BOOLEAN AS $$
DECLARE
    final_decision BOOLEAN;
BEGIN
    SELECT decision INTO final_decision
    FROM email_fraud_logs
    WHERE email_id = p_email_id 
    AND user_uuid = p_user_uuid
    AND step = 'final_decision'
    ORDER BY created_at DESC
    LIMIT 1;
    
    RETURN COALESCE(final_decision, false);
END;
$$ LANGUAGE plpgsql;

-- Function to get email status for email table
CREATE OR REPLACE FUNCTION get_email_status(p_email_id TEXT, p_user_uuid UUID)
RETURNS TEXT AS $$
DECLARE
    final_decision BOOLEAN;
    status_text TEXT;
BEGIN
    SELECT decision INTO final_decision
    FROM email_fraud_logs
    WHERE email_id = p_email_id 
    AND user_uuid = p_user_uuid
    AND step = 'final_decision'
    ORDER BY created_at DESC
    LIMIT 1;
    
    IF final_decision IS NULL THEN
        status_text := 'pending';
    ELSIF final_decision = true THEN
        status_text := 'legit';
    ELSE
        status_text := 'fraud';
    END IF;
    
    RETURN status_text;
END;
$$ LANGUAGE plpgsql;
