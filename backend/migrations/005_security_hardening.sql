-- =============================================================================
-- 005: Security Hardening
--
-- Fixes Supabase database advisor warnings:
--   1. Enable RLS on public.schema_migrations (lint 0013)
--   2. Pin search_path on mutable functions (lint 0011)
--   3. Optimize RLS policies to use (select auth.uid()) pattern (lint 0003)
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. Enable RLS on schema_migrations
--    The table is exposed via PostgREST's public schema; RLS prevents
--    unauthenticated reads.  Service-role access is unaffected.
-- ---------------------------------------------------------------------------
ALTER TABLE IF EXISTS public.schema_migrations ENABLE ROW LEVEL SECURITY;

-- Allow service-role / superuser only (no user-facing policy needed)
-- No policies = deny all via RLS for anon/authenticated roles, which is correct.

-- ---------------------------------------------------------------------------
-- 2. Pin search_path on functions flagged as mutable
--    Prevents search-path hijacking for SECURITY DEFINER functions.
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION public.update_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = public
AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
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

  INSERT INTO public.organizations (name, slug, plan, credits_balance)
  VALUES (
    COALESCE(NEW.raw_user_meta_data->>'name', split_part(NEW.email, '@', 1)) || '''s Org',
    user_slug,
    'free',
    1.00
  )
  RETURNING id INTO new_org_id;

  INSERT INTO public.credits_ledger (org_id, amount, balance_after, reason)
  VALUES (new_org_id, 1.00, 1.00, 'starting_credits');

  INSERT INTO public.org_members (org_id, user_id, role)
  VALUES (new_org_id, NEW.id, 'owner');

  RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION public.cleanup_old_logs()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  DELETE FROM public.usage_logs WHERE logged_at < NOW() - INTERVAL '90 days';
  DELETE FROM public.audit_logs WHERE created_at < NOW() - INTERVAL '365 days';
END;
$$;

-- ---------------------------------------------------------------------------
-- 3. Optimize RLS policies: wrap auth.uid() in (select ...) so the planner
--    evaluates it once as an init-plan instead of per-row.
-- ---------------------------------------------------------------------------

-- profiles
DROP POLICY IF EXISTS "Users can view own profile" ON public.profiles;
DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;
CREATE POLICY "Users can view own profile" ON public.profiles
  FOR SELECT USING ((select auth.uid()) = id);
CREATE POLICY "Users can update own profile" ON public.profiles
  FOR UPDATE USING ((select auth.uid()) = id);

-- organizations
DROP POLICY IF EXISTS "Org members can view organization" ON public.organizations;
DROP POLICY IF EXISTS "Org owners can update organization" ON public.organizations;
DROP POLICY IF EXISTS "Authenticated users can create organizations" ON public.organizations;
CREATE POLICY "Org members can view organization" ON public.organizations
  FOR SELECT USING (
    id IN (SELECT org_id FROM public.org_members WHERE user_id = (select auth.uid()))
  );
CREATE POLICY "Org owners can update organization" ON public.organizations
  FOR UPDATE USING (
    id IN (SELECT org_id FROM public.org_members WHERE user_id = (select auth.uid()) AND role = 'owner')
  );
CREATE POLICY "Authenticated users can create organizations" ON public.organizations
  FOR INSERT WITH CHECK ((select auth.uid()) IS NOT NULL);

-- org_members
DROP POLICY IF EXISTS "Org members can view members" ON public.org_members;
DROP POLICY IF EXISTS "Org admins can insert members" ON public.org_members;
DROP POLICY IF EXISTS "Org admins can delete members" ON public.org_members;
CREATE POLICY "Org members can view members" ON public.org_members
  FOR SELECT USING (
    org_id IN (SELECT org_id FROM public.org_members WHERE user_id = (select auth.uid()))
  );
CREATE POLICY "Org admins can insert members" ON public.org_members
  FOR INSERT WITH CHECK (
    org_id IN (SELECT org_id FROM public.org_members WHERE user_id = (select auth.uid()) AND role IN ('owner', 'admin'))
  );
CREATE POLICY "Org admins can delete members" ON public.org_members
  FOR DELETE USING (
    org_id IN (SELECT org_id FROM public.org_members WHERE user_id = (select auth.uid()) AND role IN ('owner', 'admin'))
  );

-- api_keys
DROP POLICY IF EXISTS "Users can view own API keys" ON public.api_keys;
DROP POLICY IF EXISTS "Users can insert own API keys" ON public.api_keys;
DROP POLICY IF EXISTS "Users can update own API keys" ON public.api_keys;
CREATE POLICY "Users can view own API keys" ON public.api_keys
  FOR SELECT USING ((select auth.uid()) = user_id);
CREATE POLICY "Users can insert own API keys" ON public.api_keys
  FOR INSERT WITH CHECK ((select auth.uid()) = user_id);
CREATE POLICY "Users can update own API keys" ON public.api_keys
  FOR UPDATE USING ((select auth.uid()) = user_id);

-- usage_logs
DROP POLICY IF EXISTS "Users can view own usage" ON public.usage_logs;
CREATE POLICY "Users can view own usage" ON public.usage_logs
  FOR SELECT USING ((select auth.uid()) = user_id);

-- audit_logs
DROP POLICY IF EXISTS "Org members can view audit logs" ON public.audit_logs;
CREATE POLICY "Org members can view audit logs" ON public.audit_logs
  FOR SELECT USING (
    org_id IN (SELECT org_id FROM public.org_members WHERE user_id = (select auth.uid()))
  );

-- cache_entries
DROP POLICY IF EXISTS "Org members can view cache entries" ON public.cache_entries;
DROP POLICY IF EXISTS "Org members can insert cache entries" ON public.cache_entries;
DROP POLICY IF EXISTS "Org members can update cache entries" ON public.cache_entries;
CREATE POLICY "Org members can view cache entries" ON public.cache_entries
  FOR SELECT USING (
    org_id IN (SELECT org_id FROM public.org_members WHERE user_id = (select auth.uid()))
  );
CREATE POLICY "Org members can insert cache entries" ON public.cache_entries
  FOR INSERT WITH CHECK (
    org_id IN (SELECT org_id FROM public.org_members WHERE user_id = (select auth.uid()))
  );
CREATE POLICY "Org members can update cache entries" ON public.cache_entries
  FOR UPDATE USING (
    org_id IN (SELECT org_id FROM public.org_members WHERE user_id = (select auth.uid()))
  );

-- credits_ledger
DROP POLICY IF EXISTS "Org members can view credits" ON public.credits_ledger;
CREATE POLICY "Org members can view credits" ON public.credits_ledger
  FOR SELECT USING (
    org_id IN (SELECT org_id FROM public.org_members WHERE user_id = (select auth.uid()))
  );
