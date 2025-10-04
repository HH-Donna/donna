-- Drop contact_email field and update indexes
-- Run this in your Supabase SQL Editor

-- Drop the old contact_email column
ALTER TABLE public.companies DROP COLUMN IF EXISTS contact_email;

-- Update the unique index to use first element of contact_emails array
DROP INDEX IF EXISTS idx_companies_user_email;

CREATE UNIQUE INDEX IF NOT EXISTS idx_companies_user_first_email 
  ON public.companies(user_id, (contact_emails[1])) 
  WHERE contact_emails IS NOT NULL AND array_length(contact_emails, 1) > 0;
