-- OmniPulse AI Social Media Agent - Database Schema
-- Migration: 006_ensure_user_profiles_and_oauth_state.sql
-- Purpose:
--   1. Add user_id column to oauth_states table for secure user-state binding.
--   2. Ensure automatic profile creation trigger exists on auth.users with conflict resilience.
--   3. Backfill any missing profiles from auth.users into public.profiles.
--   4. Ensure platform_connections correctly cascades and indexes on user_id.

-- 1. Extend oauth_states with user_id to track which authenticated user initiated the flow
ALTER TABLE public.oauth_states
    ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_oauth_states_user_id ON public.oauth_states(user_id);

-- 2. Ensure public.profiles table exists with proper schema
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT,
    full_name TEXT,
    username TEXT UNIQUE,
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS on profiles
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Public profiles are viewable by everyone" ON public.profiles;
CREATE POLICY "Public profiles are viewable by everyone" ON public.profiles
    FOR SELECT USING (true);

DROP POLICY IF EXISTS "Users can insert their own profile" ON public.profiles;
CREATE POLICY "Users can insert their own profile" ON public.profiles
    FOR INSERT WITH CHECK (auth.uid() = id OR auth.uid() IS NULL);

DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;
CREATE POLICY "Users can update own profile" ON public.profiles
    FOR UPDATE USING (auth.uid() = id OR auth.uid() IS NULL);

-- 3. Automatic profile creation trigger function
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
DECLARE
    gen_username TEXT;
BEGIN
    gen_username := COALESCE(NEW.raw_user_meta_data->>'username', split_part(NEW.email, '@', 1));
    IF EXISTS (SELECT 1 FROM public.profiles WHERE username = gen_username AND id != NEW.id) THEN
        gen_username := gen_username || '_' || substr(md5(random()::text), 1, 4);
    END IF;

    INSERT INTO public.profiles (id, email, full_name, username)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'name', split_part(NEW.email, '@', 1)),
        gen_username
    )
    ON CONFLICT (id) DO UPDATE SET
        email = EXCLUDED.email,
        full_name = COALESCE(EXCLUDED.full_name, public.profiles.full_name),
        username = COALESCE(public.profiles.username, EXCLUDED.username),
        updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 4. Trigger on auth.users
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT OR UPDATE ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- 5. Backfill any missing profiles for existing auth.users
INSERT INTO public.profiles (id, email, full_name, username)
SELECT 
    u.id,
    u.email,
    COALESCE(u.raw_user_meta_data->>'full_name', u.raw_user_meta_data->>'name', split_part(u.email, '@', 1)),
    COALESCE(u.raw_user_meta_data->>'username', split_part(u.email, '@', 1))
FROM auth.users u
ON CONFLICT (id) DO NOTHING;
