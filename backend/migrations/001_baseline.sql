-- Baseline migration: marks the existing schema as migrated.
-- This is a no-op — the schema already exists from supabase_schema.sql.
-- Future migrations (002+) will contain incremental changes.

-- Ensure schema_migrations table exists (handled by migrate.py, but safe to have)
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(255) PRIMARY KEY,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    filename VARCHAR(500)
);
