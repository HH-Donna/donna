-- Add invoice data fields and unsure_about array to emails table
-- Run this in your Supabase SQL Editor

ALTER TABLE public.emails 
  ADD COLUMN IF NOT EXISTS billing_address TEXT,
  ADD COLUMN IF NOT EXISTS payment_method TEXT,
  ADD COLUMN IF NOT EXISTS biller_billing_details TEXT,
  ADD COLUMN IF NOT EXISTS contact_email TEXT,
  ADD COLUMN IF NOT EXISTS user_account_number TEXT,
  ADD COLUMN IF NOT EXISTS biller_phone_number TEXT,
  ADD COLUMN IF NOT EXISTS invoice_number TEXT,
  ADD COLUMN IF NOT EXISTS amount NUMERIC(10, 2),
  ADD COLUMN IF NOT EXISTS unsure_about TEXT[] DEFAULT '{}';

-- Add comments for documentation
COMMENT ON COLUMN public.emails.billing_address IS 'Biller''s billing address extracted from invoice';
COMMENT ON COLUMN public.emails.payment_method IS 'Payment method extracted from invoice';
COMMENT ON COLUMN public.emails.biller_billing_details IS 'Biller''s bank account details for payment';
COMMENT ON COLUMN public.emails.contact_email IS 'Biller''s contact email from invoice';
COMMENT ON COLUMN public.emails.user_account_number IS 'User''s account/customer number with this biller';
COMMENT ON COLUMN public.emails.biller_phone_number IS 'Biller''s contact phone number';
COMMENT ON COLUMN public.emails.invoice_number IS 'Invoice or reference number';
COMMENT ON COLUMN public.emails.amount IS 'Invoice amount in currency (e.g., 150.00 for £150.00)';
COMMENT ON COLUMN public.emails.unsure_about IS 'Array of fields that had changes detected (e.g., ["billing_address", "biller_billing_details"])';

-- Create index for querying by invoice number
CREATE INDEX IF NOT EXISTS idx_emails_invoice_number 
  ON public.emails(invoice_number) 
  WHERE invoice_number IS NOT NULL;

-- Create index for querying unsure emails
CREATE INDEX IF NOT EXISTS idx_emails_unsure_about 
  ON public.emails USING GIN (unsure_about) 
  WHERE unsure_about IS NOT NULL AND array_length(unsure_about, 1) > 0;
