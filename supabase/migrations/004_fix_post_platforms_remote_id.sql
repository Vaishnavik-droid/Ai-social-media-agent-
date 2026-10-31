-- OmniPulse AI Social Media Agent - Database Schema
-- Migration: 004_fix_post_platforms_remote_id.sql
-- Purpose: Add remote_post_id and remote_post_url to public.post_platforms if not present

DO $$
BEGIN
    -- 1. Add remote_post_id column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
          AND table_name = 'post_platforms' 
          AND column_name = 'remote_post_id'
    ) THEN
        ALTER TABLE public.post_platforms ADD COLUMN remote_post_id TEXT;
    END IF;

    -- 2. Add remote_post_url column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
          AND table_name = 'post_platforms' 
          AND column_name = 'remote_post_url'
    ) THEN
        ALTER TABLE public.post_platforms ADD COLUMN remote_post_url TEXT;
    END IF;

    -- 3. Synchronize existing published_url into remote_post_url if available
    UPDATE public.post_platforms
    SET remote_post_url = published_url
    WHERE remote_post_url IS NULL AND published_url IS NOT NULL;

END $$;

