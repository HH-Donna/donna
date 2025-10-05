-- Enable Supabase Realtime for emails table
-- Run this in your Supabase SQL Editor

-- Enable realtime for the emails table
ALTER PUBLICATION supabase_realtime ADD TABLE public.emails;

-- Optional: Create a function to notify on new emails
CREATE OR REPLACE FUNCTION notify_new_email()
RETURNS TRIGGER AS $$
BEGIN
  -- Perform pg_notify to send a notification
  PERFORM pg_notify(
    'new_email_' || NEW.user_id::text,
    json_build_object(
      'id', NEW.id,
      'sender', NEW.sender,
      'subject', NEW.subject,
      'label', NEW.label,
      'status', NEW.status,
      'received_at', NEW.received_at
    )::text
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for INSERT on emails
DROP TRIGGER IF EXISTS on_email_inserted ON public.emails;
CREATE TRIGGER on_email_inserted
  AFTER INSERT ON public.emails
  FOR EACH ROW
  EXECUTE FUNCTION notify_new_email();

-- Optional: Trigger for status updates
CREATE OR REPLACE FUNCTION notify_email_status_change()
RETURNS TRIGGER AS $$
BEGIN
  IF OLD.status IS DISTINCT FROM NEW.status THEN
    PERFORM pg_notify(
      'email_status_' || NEW.user_id::text,
      json_build_object(
        'id', NEW.id,
        'old_status', OLD.status,
        'new_status', NEW.status,
        'subject', NEW.subject
      )::text
    );
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS on_email_status_changed ON public.emails;
CREATE TRIGGER on_email_status_changed
  AFTER UPDATE ON public.emails
  FOR EACH ROW
  EXECUTE FUNCTION notify_email_status_change();
