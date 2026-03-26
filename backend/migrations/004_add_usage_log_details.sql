-- Add decision details to usage_logs for persistent event logs
ALTER TABLE public.usage_logs
  ADD COLUMN IF NOT EXISTS decision TEXT DEFAULT 'miss',
  ADD COLUMN IF NOT EXISTS similarity REAL DEFAULT 0.0,
  ADD COLUMN IF NOT EXISTS latency_ms REAL DEFAULT 0.0,
  ADD COLUMN IF NOT EXISTS prompt_hash TEXT;
