-- OmniPulse AI Social Media Agent - Database Schema
-- Migration: 001_initial_schema.sql
-- Targets: Supabase PostgreSQL

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Posts Table
CREATE TABLE IF NOT EXISTS public.posts (
    id TEXT PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    snippet TEXT,
    content TEXT NOT NULL,
    media_url TEXT,
    tone TEXT DEFAULT 'Professional',
    content_type TEXT DEFAULT 'General Post',
    language TEXT DEFAULT 'English',
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'scheduled', 'failed')),
    scheduled_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Platform Delivery Results (Per-platform status)
CREATE TABLE IF NOT EXISTS public.post_platforms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    post_id TEXT REFERENCES public.posts(id) ON DELETE CASCADE,
    platform TEXT NOT NULL CHECK (platform IN ('linkedin', 'instagram', 'facebook', 'bluesky', 'twitter')),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'published', 'scheduled', 'failed', 'cancelled')),
    remote_post_id TEXT,
    remote_post_url TEXT,
    error_message TEXT,
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(post_id, platform)
);

-- 3. Scheduled Posts Queue (Worker Queue)
CREATE TABLE IF NOT EXISTS public.scheduled_posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    post_id TEXT REFERENCES public.posts(id) ON DELETE CASCADE,
    run_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')),
    attempts INT DEFAULT 0,
    max_attempts INT DEFAULT 3,
    last_attempt_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Platform Connections (Metadata & safe handle references)
CREATE TABLE IF NOT EXISTS public.platform_connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    platform TEXT NOT NULL CHECK (platform IN ('linkedin', 'instagram', 'facebook', 'bluesky', 'twitter')),
    handle TEXT NOT NULL,
    connected_user TEXT,
    status TEXT NOT NULL DEFAULT 'disconnected' CHECK (status IN ('connected', 'disconnected', 'error')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, platform)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_posts_user_status ON public.posts(user_id, status);
CREATE INDEX IF NOT EXISTS idx_posts_created_at ON public.posts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_post_platforms_post ON public.post_platforms(post_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_posts_queue ON public.scheduled_posts(status, run_at);
CREATE INDEX IF NOT EXISTS idx_platform_connections_user ON public.platform_connections(user_id);

-- Row Level Security (RLS)
ALTER TABLE public.posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.post_platforms ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scheduled_posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.platform_connections ENABLE ROW LEVEL SECURITY;

-- Policies: Single user or authenticated user can manage their own records
CREATE POLICY "Users can manage own posts" ON public.posts
    FOR ALL USING (auth.uid() = user_id OR auth.uid() IS NULL);

CREATE POLICY "Users can manage own post platforms" ON public.post_platforms
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.posts p 
            WHERE p.id = post_platforms.post_id 
            AND (p.user_id = auth.uid() OR auth.uid() IS NULL)
        )
    );

CREATE POLICY "Users can manage own scheduled posts" ON public.scheduled_posts
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.posts p 
            WHERE p.id = scheduled_posts.post_id 
            AND (p.user_id = auth.uid() OR auth.uid() IS NULL)
        )
    );

CREATE POLICY "Users can manage own connections" ON public.platform_connections
    FOR ALL USING (auth.uid() = user_id OR auth.uid() IS NULL);
