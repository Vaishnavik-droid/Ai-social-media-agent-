-- OmniPulse AI Social Media Agent - Database Schema
-- Migration: 002_authentication_and_credentials.sql
-- Purpose: Centralized platform credentials, authenticated encryption storage, and OAuth state tracking

-- 1. Extend platform_connections table with encrypted credential columns
ALTER TABLE public.platform_connections
    ADD COLUMN IF NOT EXISTS account_id TEXT,
    ADD COLUMN IF NOT EXISTS account_name TEXT,
    ADD COLUMN IF NOT EXISTS encrypted_access_token TEXT,
    ADD COLUMN IF NOT EXISTS encrypted_refresh_token TEXT,
    ADD COLUMN IF NOT EXISTS token_expires_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS scopes TEXT,
    ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS last_verified_at TIMESTAMPTZ;

-- 2. Create oauth_states table for secure state tracking & CSRF prevention
CREATE TABLE IF NOT EXISTS public.oauth_states (
    state_id TEXT PRIMARY KEY,
    platform TEXT NOT NULL,
    redirect_origin TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for expiring state cleanup
CREATE INDEX IF NOT EXISTS idx_oauth_states_expires_at ON public.oauth_states(expires_at);

-- 3. Fix scheduled_posts column alias (reconcile run_at vs scheduled_at)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
          AND table_name = 'scheduled_posts' 
          AND column_name = 'scheduled_at'
    ) THEN
        ALTER TABLE public.scheduled_posts ADD COLUMN scheduled_at TIMESTAMPTZ;
        UPDATE public.scheduled_posts SET scheduled_at = run_at WHERE scheduled_at IS NULL;
    END IF;
END $$;

-- 4. Row Level Security on oauth_states
ALTER TABLE public.oauth_states ENABLE ROW LEVEL SECURITY;

-- Allow server-side service role or authenticated/anonymous access for oauth state handling
DROP POLICY IF EXISTS "Allow public oauth state verification" ON public.oauth_states;
CREATE POLICY "Allow public oauth state verification" ON public.oauth_states
    FOR ALL USING (true);

