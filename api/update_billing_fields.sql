-- Migration to split billing_info into two separate fields
-- Run this in your Supabase SQL Editor

-- Add new columns
ALTER TABLE public.companies 
  ADD COLUMN IF NOT EXISTS biller_billing_details TEXT DEFAULT '',
  ADD COLUMN IF NOT EXISTS user_billing_details TEXT DEFAULT '';

-- Add comments
COMMENT ON COLUMN public.companies.biller_billing_details IS 'Biller''s bank account, IBAN, sort code for paying them';
COMMENT ON COLUMN public.companies.user_billing_details IS 'User''s payment method used (e.g., "Card ending 1234")';

-- Drop the old billing_info column
ALTER TABLE public.companies DROP COLUMN IF EXISTS billing_info;
