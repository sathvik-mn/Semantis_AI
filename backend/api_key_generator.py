"""
API Key Generator for Semantis AI
Generates API keys in the format: sc-{tenant}-{random}
"""
import secrets
import string
import argparse
import json
from typing import List, Dict
from datetime import datetime

def generate_api_key(tenant: str, length: int = 16) -> str:
    """
    Generate an API key for a tenant.
    
    Format: sc-{tenant}-{random_string}
    
    Args:
        tenant: Tenant identifier (e.g., 'user123', 'company-abc')
        length: Length of random string (default: 16)
    
    Returns:
        API key string (e.g., 'sc-user123-a1b2c3d4e5f6g7h8')
    """
    # Validate tenant name (alphanumeric, dash, underscore only)
    if not all(c.isalnum() or c in ['-', '_'] for c in tenant):
        raise ValueError("Tenant name can only contain alphanumeric characters, dashes, and underscores")
    
    # Generate random string
    alphabet = string.ascii_letters + string.digits
    random_part = ''.join(secrets.choice(alphabet) for _ in range(length))
    
    # Format: sc-{tenant}-{random}
    api_key = f"sc-{tenant}-{random_part}"
    
    return api_key

def generate_multiple_keys(tenant: str, count: int = 1, length: int = 16) -> List[str]:
    """
    Generate multiple API keys for a tenant.
    
    Args:
        tenant: Tenant identifier
        count: Number of keys to generate
        length: Length of random string
    
    Returns:
        List of API keys
    """
    keys = []
    for _ in range(count):
        key = generate_api_key(tenant, length)
        keys.append(key)
    return keys

def save_keys(keys: List[Dict[str, str]], filename: str = "api_keys.json"):
    """
    Save generated API keys to a JSON file.
    
    Args:
        keys: List of key dictionaries with 'tenant', 'api_key', 'created_at'
        filename: Output filename
    """
    try:
        # Load existing keys if file exists
        try:
            with open(filename, 'r') as f:
                existing_keys = json.load(f)
        except FileNotFoundError:
            existing_keys = []
        
        # Append new keys
        existing_keys.extend(keys)
        
        # Save all keys
        with open(filename, 'w') as f:
            json.dump(existing_keys, f, indent=2)
        
        print(f"\nKeys saved to: {filename}")
        print(f"Total keys in file: {len(existing_keys)}")
    except Exception as e:
        print(f"Error saving keys: {e}")

def list_keys(filename: str = "api_keys.json"):
    """
    List all API keys from the file.
    
    Args:
        filename: Keys file
    """
    try:
        with open(filename, 'r') as f:
            keys = json.load(f)
        
        if not keys:
            print("No API keys found.")
            return
        
        print(f"\n{'Tenant':<20} {'API Key':<40} {'Created At'}")
        print("-" * 80)
        for key_data in keys:
            tenant = key_data.get('tenant', 'N/A')
            api_key = key_data.get('api_key', 'N/A')
            created_at = key_data.get('created_at', 'N/A')
            print(f"{tenant:<20} {api_key:<40} {created_at}")
        
        print(f"\nTotal keys: {len(keys)}")
    except FileNotFoundError:
        print(f"File not found: {filename}")
    except Exception as e:
        print(f"Error reading keys: {e}")

def validate_api_key(api_key: str) -> bool:
    """
    Validate API key format.
    
    Format: sc-{tenant}-{anything}
    
    Args:
        api_key: API key to validate
    
    Returns:
        True if valid, False otherwise
    """
    if not api_key.startswith("sc-"):
        return False
    
    parts = api_key.split("-")
    if len(parts) < 3:
        return False
    
    # Check tenant part (second part)
    tenant = parts[1]
    if not tenant or not all(c.isalnum() or c in ['-', '_'] for c in tenant):
        return False
    
    return True

def extract_tenant(api_key: str) -> str:
    """
    Extract tenant ID from API key.
    
    Format: sc-{tenant}-{anything}
    
    Args:
        api_key: API key
    
    Returns:
        Tenant ID
    """
    if not validate_api_key(api_key):
        raise ValueError("Invalid API key format")
    
    parts = api_key.split("-")
    return parts[1]

def main():
    """Main function for CLI."""
    parser = argparse.ArgumentParser(description="Generate API keys for Semantis AI")
    parser.add_argument("--tenant", type=str, help="Tenant identifier (e.g., 'user123', 'company-abc')")
    parser.add_argument("--count", type=int, default=1, help="Number of keys to generate (default: 1)")
    parser.add_argument("--length", type=int, default=16, help="Length of random string (default: 16)")
    parser.add_argument("--save", action="store_true", help="Save keys to database and api_keys.json")
    parser.add_argument("--list", action="store_true", help="List all saved keys from database")
    parser.add_argument("--validate", type=str, help="Validate an API key")
    parser.add_argument("--extract-tenant", type=str, help="Extract tenant from API key")
    parser.add_argument("--user-email", type=str, help="User email for database storage")
    parser.add_argument("--user-name", type=str, help="User name for database storage")
    parser.add_argument("--plan", type=str, default="free", help="Plan type (default: free)")
    
    args = parser.parse_args()
    
    # List keys
    if args.list:
        try:
            from database import list_api_keys
            keys = list_api_keys()
            if keys:
                print(f"\n{'Tenant':<20} {'API Key':<40} {'Plan':<10} {'Created At'}")
                print("-" * 90)
                for key in keys:
                    print(f"{key.get('tenant_id', 'N/A'):<20} {key.get('api_key', 'N/A'):<40} {key.get('plan', 'N/A'):<10} {key.get('created_at', 'N/A')}")
                print(f"\nTotal keys: {len(keys)}")
            else:
                print("No API keys found in database.")
                # Fallback to JSON file
                list_keys()
        except Exception as e:
            print(f"Database error: {e}. Falling back to JSON file.")
            list_keys()
        return
    
    # Validate key
    if args.validate:
        is_valid = validate_api_key(args.validate)
        if is_valid:
            tenant = extract_tenant(args.validate)
            print(f"[VALID] API key is valid")
            print(f"Tenant: {tenant}")
        else:
            print(f"[INVALID] API key format is invalid")
            print("Expected format: sc-{tenant}-{random}")
        return
    
    # Extract tenant
    if args.extract_tenant:
        try:
            tenant = extract_tenant(args.extract_tenant)
            print(f"Tenant: {tenant}")
        except ValueError as e:
            print(f"Error: {e}")
        return
    
    # Generate keys
    if not args.tenant:
        print("Error: --tenant is required for key generation")
        return
    
    try:
        keys = generate_multiple_keys(args.tenant, args.count, args.length)
        
        print(f"\nGenerated {len(keys)} API key(s) for tenant '{args.tenant}':")
        print("=" * 80)
        
        key_records = []
        user_id = None
        
        # Create user in database if email provided
        if args.save and args.user_email:
            try:
                from database import create_user
                user_id = create_user(args.user_email, args.user_name)
                print(f"User created/updated in database: {args.user_email} (ID: {user_id})")
            except Exception as e:
                print(f"Warning: Could not create user in database: {e}")
        
        for i, key in enumerate(keys, 1):
            print(f"\n{i}. {key}")
            print(f"   Format: Bearer {key}")
            print(f"   Tenant: {args.tenant}")
            
            key_records.append({
                "tenant": args.tenant,
                "api_key": key,
                "created_at": datetime.now().isoformat(),
                "length": args.length
            })
            
            # Save to database if requested
            if args.save:
                try:
                    from database import create_api_key
                    create_api_key(key, args.tenant, user_id=user_id, plan=args.plan)
                    print(f"   Saved to database (plan: {args.plan})")
                except Exception as e:
                    print(f"   Warning: Could not save to database: {e}")
        
        # Also save to JSON file for backup
        if args.save:
            save_keys(key_records)
        else:
            print("\n[NOTE] Use --save to save keys to database and api_keys.json")
        
        print("\n" + "=" * 80)
        print("Usage in API calls:")
        print(f"  Authorization: Bearer {keys[0]}")
        print("\nUsage in frontend:")
        print(f"  API Key: {keys[0]}")
        
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Error generating keys: {e}")

if __name__ == "__main__":
    main()

