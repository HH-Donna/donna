-- Add user_account_number field to companies table
-- Run this in your Supabase SQL Editor

ALTER TABLE public.companies 
  ADD COLUMN IF NOT EXISTS user_account_number TEXT DEFAULT '';

COMMENT ON COLUMN public.companies.user_account_number IS 'User''s account/client/customer number with this biller (e.g., "Account: A-12345", "Customer ID: 98765")';
