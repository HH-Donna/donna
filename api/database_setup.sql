-- Create public.user_oauth_tokens table to store OAuth tokens
-- This table will be accessible by the service role and can store tokens from the auth callback

CREATE TABLE IF NOT EXISTS public.user_oauth_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL DEFAULT 'google',
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    scopes TEXT[] DEFAULT '{}',
    token_expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create unique constraint to prevent duplicate provider entries per user
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_oauth_tokens_user_provider 
ON public.user_oauth_tokens(user_id, provider);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_user_oauth_tokens_user_id 
ON public.user_oauth_tokens(user_id);

-- Enable RLS (Row Level Security)
ALTER TABLE public.user_oauth_tokens ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
-- Policy for service role (full access)
CREATE POLICY "Service role can manage all tokens" ON public.user_oauth_tokens
    FOR ALL USING (auth.role() = 'service_role');

-- Policy for authenticated users (can only access their own tokens)
CREATE POLICY "Users can manage their own tokens" ON public.user_oauth_tokens
    FOR ALL USING (auth.uid() = user_id);

-- Create function to get user OAuth tokens (callable by service role)
CREATE OR REPLACE FUNCTION get_user_oauth_tokens(target_user_id UUID, target_provider TEXT DEFAULT 'google')
RETURNS TABLE (
    user_id UUID,
    provider TEXT,
    access_token TEXT,
    refresh_token TEXT,
    scopes TEXT[],
    token_expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
) 
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        uot.user_id,
        uot.provider,
        uot.access_token,
        uot.refresh_token,
        uot.scopes,
        uot.token_expires_at,
        uot.created_at,
        uot.updated_at
    FROM public.user_oauth_tokens uot
    WHERE uot.user_id = target_user_id 
    AND uot.provider = target_provider
    AND (uot.token_expires_at IS NULL OR uot.token_expires_at > NOW())
    ORDER BY uot.updated_at DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- Create function to store/update OAuth tokens
CREATE OR REPLACE FUNCTION store_user_oauth_tokens(
    target_user_id UUID,
    target_provider TEXT,
    target_access_token TEXT,
    target_refresh_token TEXT DEFAULT NULL,
    target_scopes TEXT[] DEFAULT '{}',
    expires_in_seconds INTEGER DEFAULT 3600
)
RETURNS JSON
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    result JSON;
    expires_at TIMESTAMPTZ;
BEGIN
    -- Calculate expiration time
    IF expires_in_seconds > 0 THEN
        expires_at := NOW() + (expires_in_seconds || ' seconds')::INTERVAL;
    ELSE
        expires_at := NULL;
    END IF;
    
    -- Insert or update the OAuth tokens
    INSERT INTO public.user_oauth_tokens (
        user_id,
        provider,
        access_token,
        refresh_token,
        scopes,
        token_expires_at,
        updated_at
    ) VALUES (
        target_user_id,
        target_provider,
        target_access_token,
        target_refresh_token,
        target_scopes,
        expires_at,
        NOW()
    )
    ON CONFLICT (user_id, provider) 
    DO UPDATE SET
        access_token = EXCLUDED.access_token,
        refresh_token = COALESCE(EXCLUDED.refresh_token, user_oauth_tokens.refresh_token),
        scopes = EXCLUDED.scopes,
        token_expires_at = EXCLUDED.token_expires_at,
        updated_at = NOW();
    
    -- Return success result
    SELECT json_build_object(
        'success', true,
        'message', 'OAuth tokens stored successfully',
        'user_id', target_user_id,
        'provider', target_provider
    ) INTO result;
    
    RETURN result;
EXCEPTION
    WHEN OTHERS THEN
        -- Return error result
        SELECT json_build_object(
            'success', false,
            'message', 'Failed to store OAuth tokens: ' || SQLERRM,
            'user_id', target_user_id,
            'provider', target_provider
        ) INTO result;
        
        RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO service_role;
GRANT ALL ON public.user_oauth_tokens TO service_role;
GRANT EXECUTE ON FUNCTION get_user_oauth_tokens(UUID, TEXT) TO service_role;
GRANT EXECUTE ON FUNCTION store_user_oauth_tokens(UUID, TEXT, TEXT, TEXT, TEXT[], INTEGER) TO service_role;
