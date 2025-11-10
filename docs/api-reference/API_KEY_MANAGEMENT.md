# API Key Management Guide

## 🔐 Overview

Semantis AI uses a simple but effective API key system for multi-tenant authentication. Each API key follows the format:

```
sc-{tenant}-{random_string}
```

Where:
- `sc` = Semantic Cache prefix
- `{tenant}` = Tenant identifier (user/company ID)
- `{random_string}` = Random string for uniqueness

## 🎯 How It Works

### API Key Format

**Format:** `sc-{tenant}-{anything}`

**Examples:**
- `sc-user123-a1b2c3d4e5f6g7h8`
- `sc-company-abc-xyz789`
- `sc-test-local`
- `sc-demo-1234567890abcdef`

### Tenant Isolation

- Each tenant has isolated cache data
- Tenant ID is extracted from the API key
- Format: `sc-{tenant}-{anything}` → tenant = `{tenant}`

**Example:**
- API Key: `sc-user123-abc123`
- Tenant ID: `user123`
- All cache data is isolated to `user123`

## 🚀 Generating API Keys

### Option 1: Using the API Key Generator (Recommended)

We've created a Python script to generate API keys:

```bash
cd backend
python api_key_generator.py --tenant user123
```

**Generate multiple keys:**
```bash
python api_key_generator.py --tenant user123 --count 5
```

**Save keys to file:**
```bash
python api_key_generator.py --tenant user123 --count 3 --save
```

**List saved keys:**
```bash
python api_key_generator.py --list
```

**Validate a key:**
```bash
python api_key_generator.py --validate "sc-user123-abc123"
```

**Extract tenant from key:**
```bash
python api_key_generator.py --extract-tenant "sc-user123-abc123"
```

### Option 2: Manual Generation

You can create API keys manually by following the format:

```
sc-{tenant}-{random_string}
```

**Examples:**
- `sc-user123-abc123def456`
- `sc-company-xyz-789xyz`
- `sc-test-local`

**Rules:**
- Must start with `sc-`
- Tenant can contain: letters, numbers, dashes, underscores
- Random part can be any string (recommended: 16+ characters)

### Option 3: Programmatic Generation

```python
from backend.api_key_generator import generate_api_key

# Generate a key for a tenant
api_key = generate_api_key("user123")
print(api_key)  # sc-user123-a1b2c3d4e5f6g7h8

# Generate multiple keys
from backend.api_key_generator import generate_multiple_keys
keys = generate_multiple_keys("user123", count=5)
```

## 📋 API Key Management

### Storing Keys

**Option 1: Save to file (using generator)**
```bash
python api_key_generator.py --tenant user123 --save
```
Keys are saved to `api_keys.json`

**Option 2: Store in database**
```python
# Example: Store in database
import sqlite3

conn = sqlite3.connect('api_keys.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS api_keys (
        id INTEGER PRIMARY KEY,
        tenant TEXT NOT NULL,
        api_key TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT 1
    )
''')

# Insert key
cursor.execute('''
    INSERT INTO api_keys (tenant, api_key) VALUES (?, ?)
''', ('user123', 'sc-user123-abc123'))

conn.commit()
```

**Option 3: Environment variables**
```bash
# .env file
SEMANTIS_API_KEY=sc-user123-abc123def456
```

### Listing Keys

```bash
# List all saved keys
python api_key_generator.py --list
```

**Output:**
```
Tenant               API Key                                  Created At
--------------------------------------------------------------------------------
user123              sc-user123-a1b2c3d4e5f6g7h8             2025-11-08T20:00:00
company-abc          sc-company-abc-xyz789                   2025-11-08T20:01:00
```

### Validating Keys

```bash
# Validate a key
python api_key_generator.py --validate "sc-user123-abc123"
```

**Output:**
```
[VALID] API key is valid
Tenant: user123
```

### Extracting Tenant

```bash
# Extract tenant from key
python api_key_generator.py --extract-tenant "sc-user123-abc123"
```

**Output:**
```
Tenant: user123
```

## 🔒 Security Best Practices

### 1. Key Generation
- ✅ Use the generator script for consistent formatting
- ✅ Use cryptographically secure random strings
- ✅ Generate keys with sufficient length (16+ characters)

### 2. Key Storage
- ✅ Store keys securely (encrypted database, environment variables)
- ✅ Never commit keys to version control
- ✅ Use different keys for different environments (dev, prod)

### 3. Key Rotation
- ✅ Implement key rotation policy
- ✅ Revoke old keys when rotating
- ✅ Monitor key usage

### 4. Access Control
- ✅ One key per tenant/user
- ✅ Isolate tenant data (automatic in Semantis AI)
- ✅ Monitor API usage per tenant

## 📊 Usage Examples

### Using API Keys in API Calls

**curl:**
```bash
curl -H "Authorization: Bearer sc-user123-abc123" \
     http://localhost:8000/v1/chat/completions \
     -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"Hello"}]}'
```

**Python:**
```python
import requests

headers = {
    "Authorization": "Bearer sc-user123-abc123",
    "Content-Type": "application/json"
}

response = requests.post(
    "http://localhost:8000/v1/chat/completions",
    headers=headers,
    json={
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "Hello"}]
    }
)
```

**JavaScript:**
```javascript
fetch('http://localhost:8000/v1/chat/completions', {
    method: 'POST',
    headers: {
        'Authorization': 'Bearer sc-user123-abc123',
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        model: 'gpt-4o-mini',
        messages: [{role: 'user', content: 'Hello'}]
    })
})
```

### Using API Keys in Frontend

1. **Set API Key:**
   - Open the frontend dashboard
   - Navigate to Settings
   - Enter API key: `sc-user123-abc123`
   - Save

2. **API Key is stored in localStorage:**
   - Key: `semantic_api_key`
   - Value: `sc-user123-abc123`

## 🏗️ Multi-Tenant Architecture

### How Tenant Isolation Works

1. **API Key Format:**
   - `sc-{tenant}-{anything}`
   - Tenant ID extracted from key

2. **Cache Isolation:**
   - Each tenant has separate cache
   - No data sharing between tenants
   - Independent metrics per tenant

3. **Example:**
   ```
   Key: sc-user123-abc123 → Tenant: user123
   Key: sc-user456-xyz789 → Tenant: user456
   
   user123's cache ≠ user456's cache
   ```

### Creating Keys for Different Users

**User 1:**
```bash
python api_key_generator.py --tenant user1 --save
# Output: sc-user1-a1b2c3d4e5f6g7h8
```

**User 2:**
```bash
python api_key_generator.py --tenant user2 --save
# Output: sc-user2-x9y8z7w6v5u4t3s2
```

**Company:**
```bash
python api_key_generator.py --tenant company-abc --save
# Output: sc-company-abc-1234567890abcdef
```

## 🔧 Advanced Usage

### Key Rotation

```python
from backend.api_key_generator import generate_api_key, save_keys
from datetime import datetime

# Generate new key for tenant
new_key = generate_api_key("user123")

# Save new key
save_keys([{
    "tenant": "user123",
    "api_key": new_key,
    "created_at": datetime.now().isoformat()
}])

# Revoke old key (mark as inactive in database)
# Update application to use new key
```

### Key Validation in Application

```python
from backend.api_key_generator import validate_api_key, extract_tenant

def validate_user_key(api_key: str) -> dict:
    """Validate API key and return tenant info."""
    if not validate_api_key(api_key):
        return {"valid": False, "error": "Invalid API key format"}
    
    tenant = extract_tenant(api_key)
    return {
        "valid": True,
        "tenant": tenant,
        "api_key": api_key
    }
```

### Key Management API (Future Enhancement)

You could create an admin API for key management:

```python
# Example: Admin API endpoints
@app.post("/admin/keys/generate")
def generate_key(tenant: str):
    key = generate_api_key(tenant)
    # Save to database
    return {"api_key": key, "tenant": tenant}

@app.get("/admin/keys/{tenant}")
def list_keys(tenant: str):
    # Return all keys for tenant
    return {"keys": [...]}

@app.delete("/admin/keys/{api_key}")
def revoke_key(api_key: str):
    # Mark key as inactive
    return {"status": "revoked"}
```

## 📝 Summary

### Key Generation
- ✅ Use `api_key_generator.py` script
- ✅ Format: `sc-{tenant}-{random}`
- ✅ Save keys securely

### Key Usage
- ✅ Include in `Authorization: Bearer {key}` header
- ✅ One key per tenant/user
- ✅ Tenant data is isolated

### Key Management
- ✅ Store keys securely
- ✅ Rotate keys periodically
- ✅ Monitor key usage

### Files
- `backend/api_key_generator.py` - Key generation script
- `api_keys.json` - Saved keys (if using --save)
- `API_KEY_MANAGEMENT.md` - This guide

---

**Ready to generate keys?**
```bash
cd backend
python api_key_generator.py --tenant your-tenant-name --save
```

