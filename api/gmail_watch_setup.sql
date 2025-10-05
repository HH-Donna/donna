-- Create table to track Gmail watch subscriptions per user
-- Run this in your Supabase SQL Editor

CREATE TABLE IF NOT EXISTS public.gmail_watch_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    history_id TEXT NOT NULL,
    expiration BIGINT NOT NULL,  -- Unix timestamp in milliseconds
    topic_name TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    last_renewed_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create unique constraint (one active watch per user)
CREATE UNIQUE INDEX IF NOT EXISTS idx_gmail_watch_user 
    ON public.gmail_watch_subscriptions(user_id) 
    WHERE is_active = true;

-- Create index for expiration checks (to find watches that need renewal)
CREATE INDEX IF NOT EXISTS idx_gmail_watch_expiration 
    ON public.gmail_watch_subscriptions(expiration) 
    WHERE is_active = true;

-- Enable RLS
ALTER TABLE public.gmail_watch_subscriptions ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view their own watch subscriptions" 
    ON public.gmail_watch_subscriptions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Service role can manage all watch subscriptions" 
    ON public.gmail_watch_subscriptions
    FOR ALL USING (auth.role() = 'service_role');

-- Add comments
COMMENT ON TABLE public.gmail_watch_subscriptions IS 'Tracks Gmail push notification watch subscriptions per user';
COMMENT ON COLUMN public.gmail_watch_subscriptions.history_id IS 'Gmail history ID from watch response';
COMMENT ON COLUMN public.gmail_watch_subscriptions.expiration IS 'Unix timestamp (ms) when watch expires (max 7 days)';
COMMENT ON COLUMN public.gmail_watch_subscriptions.topic_name IS 'Google Cloud Pub/Sub topic name';
COMMENT ON COLUMN public.gmail_watch_subscriptions.is_active IS 'Whether this watch is currently active';
