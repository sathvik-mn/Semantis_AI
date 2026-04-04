"""
Simple SQL migration runner for Semantys AI.

Uses a `schema_migrations` table to track which migrations have been applied.
Migrations are numbered SQL files in the migrations/ directory.

Usage:
    python migrations/migrate.py          # Apply pending migrations
    python migrations/migrate.py status   # Show migration status
"""
import os
import sys
import glob
import logging

# Add parent dir so we can import database module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from database import get_db_connection
from psycopg2.extras import RealDictCursor

logger = logging.getLogger("migrations")
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

MIGRATIONS_DIR = os.path.dirname(os.path.abspath(__file__))


def ensure_migration_table():
    """Create the schema_migrations tracking table if it doesn't exist."""
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(255) PRIMARY KEY,
                applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                filename VARCHAR(500)
            )
        """)


def get_applied_migrations():
    """Get list of already-applied migration versions."""
    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT version, applied_at FROM schema_migrations ORDER BY version")
        return {row["version"]: row["applied_at"] for row in cur.fetchall()}


def get_pending_migrations():
    """Find SQL files that haven't been applied yet."""
    applied = get_applied_migrations()
    sql_files = sorted(glob.glob(os.path.join(MIGRATIONS_DIR, "*.sql")))
    pending = []
    for filepath in sql_files:
        filename = os.path.basename(filepath)
        # Extract version number (e.g., "001" from "001_initial_schema.sql")
        version = filename.split("_")[0]
        if version not in applied:
            pending.append((version, filename, filepath))
    return pending


def apply_migration(version: str, filename: str, filepath: str):
    """Apply a single migration file."""
    with open(filepath, "r") as f:
        sql = f.read()

    if not sql.strip():
        logger.warning(f"Skipping empty migration: {filename}")
        return

    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            # Execute the migration SQL
            cur.execute(sql)
            # Record it as applied
            cur.execute(
                "INSERT INTO schema_migrations (version, filename) VALUES (%s, %s)",
                (version, filename)
            )
            logger.info(f"Applied: {filename}")
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed: {filename} — {e}")
            raise


def migrate():
    """Apply all pending migrations."""
    ensure_migration_table()
    pending = get_pending_migrations()

    if not pending:
        logger.info("No pending migrations.")
        return

    logger.info(f"Found {len(pending)} pending migration(s)")
    for version, filename, filepath in pending:
        apply_migration(version, filename, filepath)

    logger.info("All migrations applied successfully.")


def status():
    """Show migration status."""
    ensure_migration_table()
    applied = get_applied_migrations()
    pending = get_pending_migrations()

    print("\n=== Applied Migrations ===")
    if applied:
        for version, applied_at in applied.items():
            print(f"  {version} — applied at {applied_at}")
    else:
        print("  (none)")

    print("\n=== Pending Migrations ===")
    if pending:
        for version, filename, _ in pending:
            print(f"  {version} — {filename}")
    else:
        print("  (none)")
    print()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        status()
    else:
        migrate()
