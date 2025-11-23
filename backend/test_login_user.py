"""
Test login for a specific user.
"""
import sys
from database import get_user_by_email
from auth import verify_password

email = 'new@gmail.com'
print(f"\n{'='*80}")
print(f"Testing login for: {email}")
print(f"{'='*80}\n")

user = get_user_by_email(email)
if not user:
    print(f"[ERROR] User '{email}' NOT found in database!")
    print("\nPossible reasons:")
    print("  1. User was never created")
    print("  2. Email is misspelled")
    print("  3. Database connection issue")
    sys.exit(1)

print(f"[OK] User found:")
print(f"  ID: {user['id']}")
print(f"  Email: {user['email']}")
print(f"  Name: {user.get('name', 'N/A')}")
print(f"  Created: {user.get('created_at', 'N/A')}")

password_hash = user.get('password_hash')
if not password_hash:
    print(f"\n[ERROR] User has NO password hash!")
    print("  This means the user was created without a password.")
    print("  You need to reset the password or create a new account.")
    sys.exit(1)

print(f"\n  Password Hash: {password_hash[:50]}...")
print(f"  Hash Length: {len(password_hash)}")

# Test common passwords
print(f"\nTesting common passwords:")
test_passwords = [
    'password123',
    'test123',
    'new123',
    'Password123',
    '12345678',
    email.split('@')[0] + '123',  # username + 123
]

found_match = False
for pwd in test_passwords:
    result = verify_password(pwd, password_hash)
    status = "[MATCH]" if result else "[NO MATCH]"
    print(f"  {status} '{pwd}'")
    if result:
        print(f"    -> This password works!")
        found_match = True

if not found_match:
    print(f"\n[WARNING] None of the test passwords matched!")
    print(f"  The password might be different from common patterns.")
    print(f"  Try resetting your password or creating a new account.")

print(f"\n{'='*80}\n")

