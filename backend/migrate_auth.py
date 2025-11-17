"""
Migration script to add authentication columns to users table.
"""
import sqlite3
import os

DB_PATH = "cache_data/api_keys.db"

def migrate():
    """Add authentication columns to users table."""
    if not os.path.exists(DB_PATH):
        print("Database doesn't exist yet. Will be created with new schema.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]

        # Add password_hash column if it doesn't exist
        if 'password_hash' not in columns:
            print("Adding password_hash column...")
            cursor.execute('ALTER TABLE users ADD COLUMN password_hash TEXT')
            print("✓ Added password_hash column")
        else:
            print("✓ password_hash column already exists")

        # Add email_verified column if it doesn't exist
        if 'email_verified' not in columns:
            print("Adding email_verified column...")
            cursor.execute('ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT 0')
            print("✓ Added email_verified column")
        else:
            print("✓ email_verified column already exists")

        # Add last_login_at column if it doesn't exist
        if 'last_login_at' not in columns:
            print("Adding last_login_at column...")
            cursor.execute('ALTER TABLE users ADD COLUMN last_login_at TIMESTAMP')
            print("✓ Added last_login_at column")
        else:
            print("✓ last_login_at column already exists")

        conn.commit()
        print("\n✅ Migration completed successfully!")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
