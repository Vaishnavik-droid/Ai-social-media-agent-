-- OmniPulse AI Social Media Agent - Database Schema
-- Migration: 003_add_pinterest_youtube_platforms.sql
-- Purpose: Update platform check constraints to include Pinterest and YouTube

DO $$
DECLARE
    r RECORD;
BEGIN
    -- 1. Drop existing CHECK constraints on platform column in post_platforms
    FOR r IN (
        SELECT conname 
        FROM pg_constraint 
        WHERE conrelid = 'public.post_platforms'::regclass 
          AND contype = 'c' 
          AND pg_get_constraintdef(oid) LIKE '%platform%'
    ) LOOP
        EXECUTE 'ALTER TABLE public.post_platforms DROP CONSTRAINT IF EXISTS ' || quote_ident(r.conname);
    END LOOP;

    -- Add updated CHECK constraint on post_platforms
    ALTER TABLE public.post_platforms
        ADD CONSTRAINT post_platforms_platform_check
        CHECK (platform IN ('linkedin', 'instagram', 'facebook', 'bluesky', 'twitter', 'pinterest', 'youtube'));

    -- 2. Drop existing CHECK constraints on platform column in platform_connections
    FOR r IN (
        SELECT conname 
        FROM pg_constraint 
        WHERE conrelid = 'public.platform_connections'::regclass 
          AND contype = 'c' 
          AND pg_get_constraintdef(oid) LIKE '%platform%'
    ) LOOP
        EXECUTE 'ALTER TABLE public.platform_connections DROP CONSTRAINT IF EXISTS ' || quote_ident(r.conname);
    END LOOP;

    -- Add updated CHECK constraint on platform_connections
    ALTER TABLE public.platform_connections
        ADD CONSTRAINT platform_connections_platform_check
        CHECK (platform IN ('linkedin', 'instagram', 'facebook', 'bluesky', 'twitter', 'pinterest', 'youtube'));

END $$;

