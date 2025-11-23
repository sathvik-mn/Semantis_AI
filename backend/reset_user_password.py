"""
Reset password for a user.
"""
import sys
from database import get_user_by_email, get_db_connection
from auth import get_password_hash

if len(sys.argv) < 3:
    print("Usage: python reset_user_password.py <email> <new_password>")
    print("\nExample:")
    print("  python reset_user_password.py new@gmail.com newpassword123")
    sys.exit(1)

email = sys.argv[1]
new_password = sys.argv[2]

print(f"\n{'='*80}")
print(f"Resetting password for: {email}")
print(f"{'='*80}\n")

user = get_user_by_email(email)
if not user:
    print(f"[ERROR] User '{email}' NOT found in database!")
    sys.exit(1)

print(f"[OK] User found:")
print(f"  ID: {user['id']}")
print(f"  Email: {user['email']}")
print(f"  Name: {user.get('name', 'N/A')}")

# Hash new password
password_hash = get_password_hash(new_password)

# Update password in database
with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
        (password_hash, user['id'])
    )
    conn.commit()

if cursor.rowcount > 0:
    print(f"\n[SUCCESS] Password reset successfully!")
    print(f"  New password: {new_password}")
    print(f"  You can now login with this password.")
else:
    print(f"\n[ERROR] Failed to update password!")

print(f"\n{'='*80}\n")

