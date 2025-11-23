"""
Script to list all registered users and their details from the database.
"""
import sys
import os
from database import get_db_connection

def list_all_users():
    """List all users with their details."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get all users with their API keys and usage stats
            cursor.execute("""
                SELECT 
                    u.id,
                    u.email,
                    u.name,
                    u.email_verified,
                    u.is_admin,
                    u.last_login_at,
                    u.created_at,
                    u.updated_at,
                    COUNT(DISTINCT ak.id) as api_key_count,
                    GROUP_CONCAT(DISTINCT ak.tenant_id) as tenant_ids,
                    SUM(ak.usage_count) as total_usage,
                    MAX(ak.last_used_at) as last_used_at,
                    GROUP_CONCAT(DISTINCT ak.plan) as plans
                FROM users u
                LEFT JOIN api_keys ak ON u.id = ak.user_id
                GROUP BY u.id
                ORDER BY u.created_at DESC
            """)
            
            users = cursor.fetchall()
            
            if not users:
                print("No users found in the database.")
                return
            
            print("=" * 100)
            print(f"TOTAL REGISTERED USERS: {len(users)}")
            print("=" * 100)
            print()
            
            for idx, user in enumerate(users, 1):
                user_dict = dict(user)
                print(f"User #{idx}")
                print("-" * 100)
                print(f"  ID:              {user_dict['id']}")
                print(f"  Email:           {user_dict['email']}")
                print(f"  Name:            {user_dict['name'] or 'N/A'}")
                print(f"  Email Verified:  {'Yes' if user_dict['email_verified'] else 'No'}")
                print(f"  Is Admin:        {'Yes' if user_dict['is_admin'] else 'No'}")
                print(f"  Created At:      {user_dict['created_at']}")
                print(f"  Updated At:      {user_dict['updated_at']}")
                print(f"  Last Login:      {user_dict['last_login_at'] or 'Never'}")
                print(f"  API Keys:        {user_dict['api_key_count'] or 0}")
                print(f"  Tenant IDs:      {user_dict['tenant_ids'] or 'None'}")
                print(f"  Total Usage:     {user_dict['total_usage'] or 0} requests")
                print(f"  Last Used:       {user_dict['last_used_at'] or 'Never'}")
                print(f"  Plans:           {user_dict['plans'] or 'None'}")
                
                # Get API keys for this user
                if user_dict['api_key_count'] > 0:
                    cursor.execute("""
                        SELECT api_key, tenant_id, plan, is_active, created_at, last_used_at, usage_count
                        FROM api_keys
                        WHERE user_id = ?
                        ORDER BY created_at DESC
                    """, (user_dict['id'],))
                    
                    api_keys = cursor.fetchall()
                    print(f"  API Key Details:")
                    for ak in api_keys:
                        ak_dict = dict(ak)
                        status = "Active" if ak_dict['is_active'] else "Inactive"
                        print(f"    - Key: {ak_dict['api_key'][:50]}...")
                        print(f"      Tenant: {ak_dict['tenant_id']}")
                        print(f"      Plan: {ak_dict['plan']}")
                        print(f"      Status: {status}")
                        print(f"      Usage: {ak_dict['usage_count']} requests")
                        print(f"      Created: {ak_dict['created_at']}")
                        print(f"      Last Used: {ak_dict['last_used_at'] or 'Never'}")
                
                # Get usage statistics
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_requests,
                        SUM(cache_hits) as total_hits,
                        SUM(cache_misses) as total_misses,
                        SUM(tokens_used) as total_tokens,
                        SUM(cost_estimate) as total_cost
                    FROM usage_logs
                    WHERE user_id = ?
                """, (user_dict['id'],))
                
                usage = cursor.fetchone()
                if usage and usage['total_requests']:
                    usage_dict = dict(usage)
                    print(f"  Usage Statistics:")
                    print(f"    - Total Requests: {usage_dict['total_requests']}")
                    print(f"    - Cache Hits: {usage_dict['total_hits'] or 0}")
                    print(f"    - Cache Misses: {usage_dict['total_misses'] or 0}")
                    print(f"    - Tokens Used: {usage_dict['total_tokens'] or 0}")
                    print(f"    - Estimated Cost: ${usage_dict['total_cost'] or 0:.2f}")
                
                print()
            
            # Summary statistics
            print("=" * 100)
            print("SUMMARY STATISTICS")
            print("=" * 100)
            
            cursor.execute("SELECT COUNT(*) as total FROM users")
            total_users = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as total FROM users WHERE is_admin = 1")
            admin_count = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as total FROM users WHERE email_verified = 1")
            verified_count = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(DISTINCT user_id) as total FROM api_keys WHERE user_id IS NOT NULL")
            users_with_keys = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as total FROM api_keys")
            total_api_keys = cursor.fetchone()['total']
            
            cursor.execute("SELECT SUM(usage_count) as total FROM api_keys")
            total_usage = cursor.fetchone()['total'] or 0
            
            print(f"Total Users:           {total_users}")
            print(f"Admin Users:           {admin_count}")
            print(f"Verified Users:        {verified_count}")
            print(f"Users with API Keys:   {users_with_keys}")
            print(f"Total API Keys:        {total_api_keys}")
            print(f"Total Usage:           {total_usage} requests")
            print("=" * 100)
            
    except Exception as e:
        print(f"Error listing users: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    print("\nFetching all registered users from database...\n")
    list_all_users()


