-- Add contact_emails array field to companies table
-- Run this in your Supabase SQL Editor

-- Add contact_emails array column
ALTER TABLE public.companies 
  ADD COLUMN IF NOT EXISTS contact_emails TEXT[] DEFAULT '{}';

-- Add comment
COMMENT ON COLUMN public.companies.contact_emails IS 'Array of all email addresses used by this biller (e.g., ["billing@company.com", "noreply@company.com"])';

-- Populate contact_emails from existing contact_email for existing rows
UPDATE public.companies 
SET contact_emails = ARRAY[contact_email]
WHERE contact_email IS NOT NULL 
  AND contact_email != ''
  AND (contact_emails IS NULL OR contact_emails = '{}');
