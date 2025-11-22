"""
Script to create an admin user.
Usage: python create_admin.py <email> <password> [name]
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auth import get_password_hash, validate_email, validate_password_strength
from database import get_user_by_email, create_user_with_password, set_user_admin

def create_admin(email: str, password: str, name: str = None):
    """Create an admin user."""
    # Validate email
    email_valid, email_error = validate_email(email)
    if not email_valid:
        print(f"❌ Email validation failed: {email_error}")
        return False

    # Validate password strength
    password_valid, password_error = validate_password_strength(password)
    if not password_valid:
        print(f"❌ Password validation failed: {password_error}")
        return False

    # Check if user already exists
    existing_user = get_user_by_email(email)
    if existing_user:
        # User exists, make them admin
        user_id = existing_user['id']
        if existing_user.get('is_admin'):
            print(f"✅ User {email} is already an admin")
            return True
        
        # Set admin status
        if set_user_admin(user_id, True):
            print(f"✅ User {email} (ID: {user_id}) is now an admin")
            return True
        else:
            print(f"❌ Failed to set admin status for {email}")
            return False
    
    # Create new admin user
    password_hash = get_password_hash(password)
    user_id = create_user_with_password(email, password_hash, name, is_admin=True)
    
    if user_id:
        print(f"✅ Admin user created successfully!")
        print(f"   Email: {email}")
        print(f"   User ID: {user_id}")
        if name:
            print(f"   Name: {name}")
        return True
    else:
        print(f"❌ Failed to create admin user")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python create_admin.py <email> <password> [name]")
        print("\nExample:")
        print("  python create_admin.py admin@example.com SecurePass123 Admin User")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    name = sys.argv[3] if len(sys.argv) > 3 else None
    
    success = create_admin(email, password, name)
    sys.exit(0 if success else 1)



