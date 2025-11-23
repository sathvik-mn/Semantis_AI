"""
Test script to diagnose login and API key storage issues.
"""
import sys
import os
from database import get_db_connection, get_user_by_email
from auth import verify_password, get_password_hash

def test_login(email, password):
    """Test login for a user."""
    print(f"\n{'='*80}")
    print(f"TESTING LOGIN FOR: {email}")
    print(f"{'='*80}")
    
    user = get_user_by_email(email)
    if not user:
        print(f"[ERROR] User not found in database!")
        return False
    
    print(f"[OK] User found:")
    print(f"   ID: {user['id']}")
    print(f"   Email: {user['email']}")
    print(f"   Name: {user['name']}")
    print(f"   Password Hash: {user.get('password_hash', 'MISSING!')[:50]}...")
    
    if not user.get('password_hash'):
        print(f"[ERROR] User has no password hash!")
        return False
    
    # Test password verification
    is_valid = verify_password(password, user['password_hash'])
    if is_valid:
        print(f"[OK] Password verification: SUCCESS")
        return True
    else:
        print(f"[ERROR] Password verification: FAILED")
        print(f"   This means the password doesn't match the stored hash")
        return False

def check_api_keys():
    """Check all API keys and their user associations."""
    print(f"\n{'='*80}")
    print("CHECKING API KEYS")
    print(f"{'='*80}")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get all API keys
        cursor.execute("""
            SELECT ak.*, u.email, u.id as user_id_from_users
            FROM api_keys ak
            LEFT JOIN users u ON ak.user_id = u.id
            ORDER BY ak.created_at DESC
            LIMIT 20
        """)
        
        keys = cursor.fetchall()
        print(f"\nTotal API keys found: {len(keys)}")
        
        linked_count = 0
        unlinked_count = 0
        
        for key in keys:
            key_dict = dict(key)
            user_id = key_dict.get('user_id')
            user_email = key_dict.get('email')
            
            if user_id and user_email:
                linked_count += 1
                print(f"\n[OK] Linked API Key:")
                print(f"   Key: {key_dict['api_key'][:50]}...")
                print(f"   Tenant: {key_dict['tenant_id']}")
                print(f"   User ID: {user_id}")
                print(f"   User Email: {user_email}")
            else:
                unlinked_count += 1
                print(f"\n[WARNING] Unlinked API Key:")
                print(f"   Key: {key_dict['api_key'][:50]}...")
                print(f"   Tenant: {key_dict['tenant_id']}")
                print(f"   User ID: {key_dict.get('user_id', 'NULL')}")
        
        print(f"\n{'='*80}")
        print(f"SUMMARY:")
        print(f"  Linked API Keys: {linked_count}")
        print(f"  Unlinked API Keys: {unlinked_count}")
        print(f"{'='*80}")

def check_recent_api_key_generations():
    """Check recent API key generations."""
    print(f"\n{'='*80}")
    print("RECENT API KEY GENERATIONS")
    print(f"{'='*80}")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get API keys created in last 24 hours
        cursor.execute("""
            SELECT ak.*, u.email
            FROM api_keys ak
            LEFT JOIN users u ON ak.user_id = u.id
            WHERE ak.created_at >= datetime('now', '-1 day')
            ORDER BY ak.created_at DESC
        """)
        
        recent_keys = cursor.fetchall()
        
        if not recent_keys:
            print("No API keys created in the last 24 hours.")
        else:
            print(f"\nFound {len(recent_keys)} API keys created in last 24 hours:")
            for key in recent_keys:
                key_dict = dict(key)
                print(f"\n  Created: {key_dict['created_at']}")
                print(f"  Key: {key_dict['api_key'][:50]}...")
                print(f"  Tenant: {key_dict['tenant_id']}")
                print(f"  User ID: {key_dict.get('user_id', 'NULL')}")
                print(f"  User Email: {key_dict.get('email', 'N/A')}")
                print(f"  Is Active: {key_dict.get('is_active', False)}")

if __name__ == "__main__":
    print("\n" + "="*80)
    print("LOGIN AND API KEY DIAGNOSTICS")
    print("="*80)
    
    # Test login for known users
    test_users = [
        ("sa@gmail.com", "test123"),
        ("sathvikmn@gmail.com", "test123"),
        ("sat@gmail.com", "test123"),
        ("sathvik@gmail.com", "test123"),
    ]
    
    print("\n" + "="*80)
    print("TESTING LOGINS")
    print("="*80)
    
    for email, password in test_users:
        test_login(email, password)
    
    # Check API keys
    check_api_keys()
    
    # Check recent API key generations
    check_recent_api_key_generations()
    
    print("\n" + "="*80)
    print("DIAGNOSTICS COMPLETE")
    print("="*80)

