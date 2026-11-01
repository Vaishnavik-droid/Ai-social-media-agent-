-- OmniPulse AI Social Media Agent - Database Schema
-- Migration: 005_add_partially_published_status.sql
-- Purpose: 
--   1. Add 'partially_published' to public.posts status check constraint.
--   2. Add 'expired', 'reauth_required', and 'temp_unavailable' to public.platform_connections status check constraint.

DO $$
DECLARE
    r RECORD;
BEGIN
    -- 1. Update public.posts status check constraint
    FOR r IN (
        SELECT conname 
        FROM pg_constraint 
        WHERE conrelid = 'public.posts'::regclass 
          AND contype = 'c' 
          AND pg_get_constraintdef(oid) LIKE '%status%'
    ) LOOP
        EXECUTE 'ALTER TABLE public.posts DROP CONSTRAINT IF EXISTS ' || quote_ident(r.conname);
    END LOOP;

    ALTER TABLE public.posts
        ADD CONSTRAINT posts_status_check
        CHECK (status IN ('draft', 'published', 'partially_published', 'scheduled', 'failed'));

    -- 2. Update public.platform_connections status check constraint
    FOR r IN (
        SELECT conname 
        FROM pg_constraint 
        WHERE conrelid = 'public.platform_connections'::regclass 
          AND contype = 'c' 
          AND pg_get_constraintdef(oid) LIKE '%status%'
    ) LOOP
        EXECUTE 'ALTER TABLE public.platform_connections DROP CONSTRAINT IF EXISTS ' || quote_ident(r.conname);
    END LOOP;

    ALTER TABLE public.platform_connections
        ADD CONSTRAINT platform_connections_status_check
        CHECK (status IN ('connected', 'disconnected', 'error', 'expired', 'reauth_required', 'temp_unavailable'));

END $$;

