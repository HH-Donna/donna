-- SQL Code to Update Schema for Verification Status Support
-- Run these statements to safely update the existing schema

-- 1. Add verification_status column to email_fraud_logs table (if it doesn't exist)
ALTER TABLE email_fraud_logs 
ADD COLUMN IF NOT EXISTS verification_status TEXT CHECK (verification_status IN ('legit', 'call', 'pending'));

-- 2. Create index for verification_status on email_fraud_logs (if it doesn't exist)
CREATE INDEX IF NOT EXISTS idx_email_fraud_logs_verification_status 
ON email_fraud_logs(verification_status);

-- 3. Create google_search_results table if it doesn't exist (with new fields)
CREATE TABLE IF NOT EXISTS google_search_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email_id TEXT NOT NULL,
    user_uuid UUID NOT NULL REFERENCES auth.users(id),
    company_name TEXT NOT NULL,
    search_query TEXT NOT NULL,
    billing_address TEXT,
    biller_phone_number TEXT,
    email TEXT,
    frequency TEXT,
    search_results JSONB,
    extracted_attributes JSONB,
    confidence DECIMAL(3,2) CHECK (confidence >= 0.00 AND confidence <= 1.00),
    verification_status TEXT CHECK (verification_status IN ('legit', 'call', 'pending')),
    phone_match BOOLEAN,
    address_match BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Add verification_status column to google_search_results table (if it doesn't exist)
ALTER TABLE google_search_results 
ADD COLUMN IF NOT EXISTS verification_status TEXT CHECK (verification_status IN ('legit', 'call', 'pending'));

-- 5. Add phone_match column to google_search_results table (if it doesn't exist)
ALTER TABLE google_search_results 
ADD COLUMN IF NOT EXISTS phone_match BOOLEAN;

-- 6. Add address_match column to google_search_results table (if it doesn't exist)
ALTER TABLE google_search_results 
ADD COLUMN IF NOT EXISTS address_match BOOLEAN;

-- 7. Create indexes for google_search_results table (if they don't exist)
CREATE INDEX IF NOT EXISTS idx_google_search_results_email_id ON google_search_results(email_id);
CREATE INDEX IF NOT EXISTS idx_google_search_results_user_uuid ON google_search_results(user_uuid);
CREATE INDEX IF NOT EXISTS idx_google_search_results_company_name ON google_search_results(company_name);
CREATE INDEX IF NOT EXISTS idx_google_search_results_verification_status ON google_search_results(verification_status);
CREATE INDEX IF NOT EXISTS idx_google_search_results_created_at ON google_search_results(created_at);

-- 8. Update get_email_fraud_analysis function to include verification_status
-- Drop existing function first to change return type
DROP FUNCTION IF EXISTS get_email_fraud_analysis(TEXT, UUID);

CREATE OR REPLACE FUNCTION get_email_fraud_analysis(p_email_id TEXT, p_user_uuid UUID)
RETURNS TABLE (
    step TEXT,
    decision BOOLEAN,
    verification_status TEXT,
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
        efl.verification_status,
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

-- 9. Update get_email_final_decision function (keep existing logic)
-- Drop existing function first to avoid return type conflicts
DROP FUNCTION IF EXISTS get_email_final_decision(TEXT, UUID);

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

-- 10. Update get_email_status function to use verification_status
-- Drop existing function first to avoid return type conflicts
DROP FUNCTION IF EXISTS get_email_status(TEXT, UUID);

CREATE OR REPLACE FUNCTION get_email_status(p_email_id TEXT, p_user_uuid UUID)
RETURNS TEXT AS $$
DECLARE
    verification_status TEXT;
    status_text TEXT;
BEGIN
    -- Get the verification status from the most recent online_verification step
    SELECT efl.verification_status INTO verification_status
    FROM email_fraud_logs efl
    WHERE efl.email_id = p_email_id 
    AND efl.user_uuid = p_user_uuid
    AND efl.step = 'online_verification'
    ORDER BY efl.created_at DESC
    LIMIT 1;
    
    -- Map verification status to email status
    IF verification_status IS NULL THEN
        status_text := 'pending';
    ELSIF verification_status = 'legit' THEN
        status_text := 'legit';
    ELSIF verification_status = 'call' THEN
        status_text := 'call';
    ELSE
        status_text := 'pending';
    END IF;
    
    RETURN status_text;
END;
$$ LANGUAGE plpgsql;

-- 11. Create new function to get verification details
-- Drop existing function first to avoid conflicts
DROP FUNCTION IF EXISTS get_email_verification_details(TEXT, UUID);

CREATE OR REPLACE FUNCTION get_email_verification_details(p_email_id TEXT, p_user_uuid UUID)
RETURNS TABLE (
    verification_status TEXT,
    phone_match BOOLEAN,
    address_match BOOLEAN,
    confidence DECIMAL(3,2),
    reasoning TEXT,
    details JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        efl.verification_status,
        (efl.details->>'phone_match')::BOOLEAN as phone_match,
        (efl.details->>'address_match')::BOOLEAN as address_match,
        efl.confidence,
        efl.reasoning,
        efl.details
    FROM email_fraud_logs efl
    WHERE efl.email_id = p_email_id 
    AND efl.user_uuid = p_user_uuid
    AND efl.step = 'online_verification'
    ORDER BY efl.created_at DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- 12. Verify the updates worked
SELECT 'Schema update completed successfully' as status;
