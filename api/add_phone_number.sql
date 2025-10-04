-- Add biller_phone_number field to companies table
-- Run this in your Supabase SQL Editor

ALTER TABLE public.companies 
  ADD COLUMN IF NOT EXISTS biller_phone_number TEXT DEFAULT '';

COMMENT ON COLUMN public.companies.biller_phone_number IS 'Biller''s contact phone number (extracted from email footer/signature/attachments)';
