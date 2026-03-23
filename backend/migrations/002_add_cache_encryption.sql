-- Add is_encrypted flag to cache_entries for at-rest encryption tracking
ALTER TABLE public.cache_entries
  ADD COLUMN IF NOT EXISTS is_encrypted BOOLEAN DEFAULT FALSE;
