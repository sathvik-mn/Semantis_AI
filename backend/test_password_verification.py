"""
Test password verification for existing users.
"""
import sys
import os
from database import get_db_connection, get_user_by_email
from auth import verify_password, get_password_hash

def test_user_password(email):
    """Test if we can verify a user's password."""
    print(f"\n{'='*80}")
    print(f"Testing password for: {email}")
    print(f"{'='*80}")
    
    user = get_user_by_email(email)
    if not user:
        print(f"[ERROR] User not found!")
        return
    
    print(f"User found:")
    print(f"  ID: {user['id']}")
    print(f"  Email: {user['email']}")
    print(f"  Name: {user['name']}")
    
    password_hash = user.get('password_hash')
    if not password_hash:
        print(f"[ERROR] User has NO password hash!")
        print(f"  This means the user was created without a password.")
        return
    
    print(f"  Password Hash: {password_hash[:60]}...")
    print(f"  Hash Length: {len(password_hash)}")
    
    # Test common passwords
    test_passwords = [
        "password123",
        "test123",
        "12345678",
        "Password123",
        email.split('@')[0] + "123",  # username + 123
    ]
    
    print(f"\nTesting common passwords:")
    for pwd in test_passwords:
        result = verify_password(pwd, password_hash)
        status = "[MATCH]" if result else "[NO MATCH]"
        print(f"  {status} '{pwd}'")
        if result:
            print(f"    -> This password works!")
            return True
    
    print(f"\n[WARNING] None of the test passwords matched!")
    print(f"  The password hash might be corrupted or the password is different.")
    return False

if __name__ == "__main__":
    emails = [
        "sa@gmail.com",
        "sathvikmn@gmail.com", 
        "sat@gmail.com",
        "sathvik@gmail.com",
    ]
    
    for email in emails:
        test_user_password(email)


