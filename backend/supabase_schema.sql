-- =============================================================================
-- Semantis AI - Supabase Database Schema (Phase 1.1: Organization Tenancy)
-- Run this in your Supabase SQL Editor (Dashboard > SQL Editor > New Query)
-- =============================================================================

-- =============================================================================
-- 1. Utility Functions
-- =============================================================================

CREATE OR REPLACE FUNCTION public.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 2. Profiles table (extends auth.users with app-specific data)
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT,
  name TEXT,
  company TEXT,
  is_admin BOOLEAN DEFAULT FALSE,
  openai_api_key_encrypted TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

DROP TRIGGER IF EXISTS profiles_updated_at ON public.profiles;
CREATE TRIGGER profiles_updated_at
  BEFORE UPDATE ON public.profiles
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

-- =============================================================================
-- 3. Organizations table
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.organizations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  plan TEXT DEFAULT 'free',
  settings JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

DROP TRIGGER IF EXISTS organizations_updated_at ON public.organizations;
CREATE TRIGGER organizations_updated_at
  BEFORE UPDATE ON public.organizations
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

-- =============================================================================
-- 4. Organization Members (join table)
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.org_members (
  id SERIAL PRIMARY KEY,
  org_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  role TEXT DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'member')),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(org_id, user_id)
);

-- =============================================================================
-- 5. API Keys table (updated with org tenancy)
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.api_keys (
  id SERIAL PRIMARY KEY,
  api_key TEXT UNIQUE NOT NULL,
  tenant_id TEXT NOT NULL,
  user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  org_id UUID REFERENCES public.organizations(id),
  plan TEXT DEFAULT 'free',
  plan_expires_at TIMESTAMPTZ,
  is_active BOOLEAN DEFAULT TRUE,
  scope TEXT DEFAULT 'read-write' CHECK (scope IN ('read-only', 'read-write', 'admin')),
  allowed_ips TEXT[],
  expires_at TIMESTAMPTZ,
  label TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  last_used_at TIMESTAMPTZ,
  usage_count INTEGER DEFAULT 0
);

DROP TRIGGER IF EXISTS api_keys_updated_at ON public.api_keys;
CREATE TRIGGER api_keys_updated_at
  BEFORE UPDATE ON public.api_keys
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

-- =============================================================================
-- 6. Usage Logs table (updated with org_id)
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.usage_logs (
  id SERIAL PRIMARY KEY,
  api_key TEXT NOT NULL,
  tenant_id TEXT NOT NULL,
  user_id UUID,
  org_id UUID REFERENCES public.organizations(id),
  endpoint TEXT,
  request_count INTEGER DEFAULT 1,
  cache_hits INTEGER DEFAULT 0,
  cache_misses INTEGER DEFAULT 0,
  tokens_used INTEGER DEFAULT 0,
  cost_estimate REAL DEFAULT 0,
  logged_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- 7. Audit Logs table
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.audit_logs (
  id SERIAL PRIMARY KEY,
  org_id UUID REFERENCES public.organizations(id),
  user_id UUID,
  action TEXT NOT NULL,
  resource_type TEXT,
  resource_id TEXT,
  details JSONB DEFAULT '{}',
  ip_address TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- 8. Cache Entries table
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.cache_entries (
  id SERIAL PRIMARY KEY,
  org_id UUID REFERENCES public.organizations(id) ON DELETE CASCADE,
  prompt_hash TEXT NOT NULL,
  prompt_norm TEXT NOT NULL,
  response_text TEXT NOT NULL,
  embedding BYTEA,
  model TEXT DEFAULT 'gpt-4o-mini',
  ttl_expires_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  last_used_at TIMESTAMPTZ DEFAULT NOW(),
  use_count INTEGER DEFAULT 0,
  domain TEXT DEFAULT 'general'
);

-- =============================================================================
-- 8b. Migration: Add new columns to existing tables (for upgrades from old schema)
-- =============================================================================

-- api_keys: add org_id, scope, allowed_ips, expires_at, label if missing
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'api_keys' AND column_name = 'org_id') THEN
    ALTER TABLE public.api_keys ADD COLUMN org_id UUID REFERENCES public.organizations(id);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'api_keys' AND column_name = 'scope') THEN
    ALTER TABLE public.api_keys ADD COLUMN scope TEXT DEFAULT 'read-write' CHECK (scope IN ('read-only', 'read-write', 'admin'));
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'api_keys' AND column_name = 'allowed_ips') THEN
    ALTER TABLE public.api_keys ADD COLUMN allowed_ips TEXT[];
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'api_keys' AND column_name = 'expires_at') THEN
    ALTER TABLE public.api_keys ADD COLUMN expires_at TIMESTAMPTZ;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'api_keys' AND column_name = 'label') THEN
    ALTER TABLE public.api_keys ADD COLUMN label TEXT;
  END IF;
END $$;

-- usage_logs: add org_id if missing
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'usage_logs' AND column_name = 'org_id') THEN
    ALTER TABLE public.usage_logs ADD COLUMN org_id UUID REFERENCES public.organizations(id);
  END IF;
END $$;

-- =============================================================================
-- 9. Indexes
-- =============================================================================

-- Profiles
CREATE INDEX IF NOT EXISTS idx_profiles_email ON public.profiles(email);

-- Organizations
CREATE INDEX IF NOT EXISTS idx_organizations_slug ON public.organizations(slug);
CREATE INDEX IF NOT EXISTS idx_organizations_plan ON public.organizations(plan);

-- Org Members
CREATE INDEX IF NOT EXISTS idx_org_members_org_id ON public.org_members(org_id);
CREATE INDEX IF NOT EXISTS idx_org_members_user_id ON public.org_members(user_id);

-- API Keys
CREATE INDEX IF NOT EXISTS idx_api_key ON public.api_keys(api_key);
CREATE INDEX IF NOT EXISTS idx_tenant_id ON public.api_keys(tenant_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON public.api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_org_id ON public.api_keys(org_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_expires_at ON public.api_keys(expires_at);

-- Usage Logs
CREATE INDEX IF NOT EXISTS idx_usage_api_key ON public.usage_logs(api_key);
CREATE INDEX IF NOT EXISTS idx_usage_user_id ON public.usage_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_tenant ON public.usage_logs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_usage_org_id ON public.usage_logs(org_id);
CREATE INDEX IF NOT EXISTS idx_usage_logged_at ON public.usage_logs(logged_at);

-- Audit Logs
CREATE INDEX IF NOT EXISTS idx_audit_org_id ON public.audit_logs(org_id);
CREATE INDEX IF NOT EXISTS idx_audit_user_id ON public.audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON public.audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_created_at ON public.audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_resource ON public.audit_logs(resource_type, resource_id);

-- Cache Entries
CREATE INDEX IF NOT EXISTS idx_cache_org_id ON public.cache_entries(org_id);
CREATE INDEX IF NOT EXISTS idx_cache_prompt_hash ON public.cache_entries(prompt_hash);
CREATE INDEX IF NOT EXISTS idx_cache_org_hash ON public.cache_entries(org_id, prompt_hash);
CREATE INDEX IF NOT EXISTS idx_cache_ttl ON public.cache_entries(ttl_expires_at);
CREATE INDEX IF NOT EXISTS idx_cache_domain ON public.cache_entries(domain);
CREATE INDEX IF NOT EXISTS idx_cache_last_used ON public.cache_entries(last_used_at);

-- =============================================================================
-- 10. Row Level Security
-- =============================================================================

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.org_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.usage_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cache_entries ENABLE ROW LEVEL SECURITY;

-- Profiles: users can read/update their own profile
DROP POLICY IF EXISTS "Users can view own profile" ON public.profiles;
DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;
CREATE POLICY "Users can view own profile" ON public.profiles
  FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON public.profiles
  FOR UPDATE USING (auth.uid() = id);

-- Organizations: members can see their org
DROP POLICY IF EXISTS "Org members can view organization" ON public.organizations;
DROP POLICY IF EXISTS "Org owners can update organization" ON public.organizations;
DROP POLICY IF EXISTS "Authenticated users can create organizations" ON public.organizations;
CREATE POLICY "Org members can view organization" ON public.organizations
  FOR SELECT USING (
    id IN (SELECT org_id FROM public.org_members WHERE user_id = auth.uid())
  );
CREATE POLICY "Org owners can update organization" ON public.organizations
  FOR UPDATE USING (
    id IN (SELECT org_id FROM public.org_members WHERE user_id = auth.uid() AND role = 'owner')
  );
CREATE POLICY "Authenticated users can create organizations" ON public.organizations
  FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);

-- Org Members: members can see fellow members; owners/admins can manage
DROP POLICY IF EXISTS "Org members can view members" ON public.org_members;
DROP POLICY IF EXISTS "Org admins can insert members" ON public.org_members;
DROP POLICY IF EXISTS "Org admins can delete members" ON public.org_members;
CREATE POLICY "Org members can view members" ON public.org_members
  FOR SELECT USING (
    org_id IN (SELECT org_id FROM public.org_members WHERE user_id = auth.uid())
  );
CREATE POLICY "Org admins can insert members" ON public.org_members
  FOR INSERT WITH CHECK (
    org_id IN (SELECT org_id FROM public.org_members WHERE user_id = auth.uid() AND role IN ('owner', 'admin'))
  );
CREATE POLICY "Org admins can delete members" ON public.org_members
  FOR DELETE USING (
    org_id IN (SELECT org_id FROM public.org_members WHERE user_id = auth.uid() AND role IN ('owner', 'admin'))
  );

-- API Keys: users can manage their own keys
DROP POLICY IF EXISTS "Users can view own API keys" ON public.api_keys;
DROP POLICY IF EXISTS "Users can insert own API keys" ON public.api_keys;
DROP POLICY IF EXISTS "Users can update own API keys" ON public.api_keys;
CREATE POLICY "Users can view own API keys" ON public.api_keys
  FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own API keys" ON public.api_keys
  FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own API keys" ON public.api_keys
  FOR UPDATE USING (auth.uid() = user_id);

-- Usage Logs: users can view their own logs
DROP POLICY IF EXISTS "Users can view own usage" ON public.usage_logs;
CREATE POLICY "Users can view own usage" ON public.usage_logs
  FOR SELECT USING (auth.uid() = user_id);

-- Audit Logs: org members can view their org audit logs
DROP POLICY IF EXISTS "Org members can view audit logs" ON public.audit_logs;
CREATE POLICY "Org members can view audit logs" ON public.audit_logs
  FOR SELECT USING (
    org_id IN (SELECT org_id FROM public.org_members WHERE user_id = auth.uid())
  );

-- Cache Entries: org members can view/manage their org cache
DROP POLICY IF EXISTS "Org members can view cache entries" ON public.cache_entries;
DROP POLICY IF EXISTS "Org members can insert cache entries" ON public.cache_entries;
DROP POLICY IF EXISTS "Org members can update cache entries" ON public.cache_entries;
CREATE POLICY "Org members can view cache entries" ON public.cache_entries
  FOR SELECT USING (
    org_id IN (SELECT org_id FROM public.org_members WHERE user_id = auth.uid())
  );
CREATE POLICY "Org members can insert cache entries" ON public.cache_entries
  FOR INSERT WITH CHECK (
    org_id IN (SELECT org_id FROM public.org_members WHERE user_id = auth.uid())
  );
CREATE POLICY "Org members can update cache entries" ON public.cache_entries
  FOR UPDATE USING (
    org_id IN (SELECT org_id FROM public.org_members WHERE user_id = auth.uid())
  );

-- =============================================================================
-- 11. Triggers: Auto-create profile + default org on signup
-- =============================================================================

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
DECLARE
  new_org_id UUID;
  user_slug TEXT;
BEGIN
  INSERT INTO public.profiles (id, email, name)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'name', split_part(NEW.email, '@', 1))
  );

  user_slug := lower(replace(split_part(NEW.email, '@', 1), '.', '-')) || '-' || substr(NEW.id::text, 1, 8);

  INSERT INTO public.organizations (name, slug, plan)
  VALUES (
    COALESCE(NEW.raw_user_meta_data->>'name', split_part(NEW.email, '@', 1)) || '''s Org',
    user_slug,
    'free'
  )
  RETURNING id INTO new_org_id;

  INSERT INTO public.org_members (org_id, user_id, role)
  VALUES (new_org_id, NEW.id, 'owner');

  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- NOTE: The backend uses the service_role key which bypasses RLS,
-- so all admin and logging operations work without policy restrictions.
