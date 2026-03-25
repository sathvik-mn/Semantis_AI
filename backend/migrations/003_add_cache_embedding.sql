-- Store embedding vectors alongside cache entries for fast boot restore
-- This avoids re-calling OpenAI embedding API on every server restart
ALTER TABLE public.cache_entries
  ADD COLUMN IF NOT EXISTS embedding BYTEA;

-- Add tenant_id for per-tenant cache loading
ALTER TABLE public.cache_entries
  ADD COLUMN IF NOT EXISTS tenant_id TEXT;

-- Index for faster tenant-based loading on boot
CREATE INDEX IF NOT EXISTS idx_cache_entries_tenant_id
  ON public.cache_entries (tenant_id);
