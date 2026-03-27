# API Key Generation Guide

## Overview

The system now supports automatic API key generation with complex, secure keys similar to real API services (like OpenAI, Stripe, etc.).

## How API Keys Are Generated

### Key Format

**Format:** `sc-{tenant}-{random_string}`

**Examples:**
- `sc-usr_a1b2c3d4-AbC5DeF6-GhI7JkL8-MnO9PqR0`
- `sc-usr_x9y8z7w6-Vu5Ts4R3-Qw2Er1Ty-Ui0OpAsD`
- `sc-user123-AbC5DeF6GhI7JkL8MnO9PqR0`

### Key Features

1. **Complex Random String:**
   - Default length: **32 characters** (was 16)
   - Uses mixed case letters + digits for high entropy
   - Formatted with hyphens every 8 characters for readability (if > 24 chars)

2. **Automatic Tenant ID Generation:**
   - If no tenant ID provided, generates unique tenant ID: `usr_{8 random chars}`
   - Format: `usr_xxxxxxxx` (where x = lowercase letters + digits)

3. **Cryptographically Secure:**
   - Uses Python's `secrets.choice()` for secure random generation
   - Not predictable or guessable

## Where Keys Are Created

### 1. **Frontend Website (New! ✅)**

**Location:** Landing page (`/`)

**How to Use:**
1. Navigate to http://localhost:3000
2. Click **"🔑 Generate API Key"** button
3. Key is automatically generated and displayed
4. Key is auto-filled in the input field
5. Click "Copy" to copy to clipboard
6. Click "Access Dashboard" to use the key

**Features:**
- One-click generation
- Automatic copy functionality
- Auto-fills input field
- Secure warning message

### 2. **Backend API Endpoint**

**Endpoint:** `POST /api/keys/generate`

**Query Parameters:**
- `tenant` (optional): Custom tenant ID (if not provided, auto-generates)
- `length` (optional): Length of random string (16-64, default: 32)
- `email` (optional): User email for database storage
- `name` (optional): User name for database storage
- `plan` (optional): Plan type (default: "free")

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/keys/generate?length=32"
```

**Example Response:**
```json
{
  "api_key": "sc-usr_a1b2c3d4-AbC5DeF6-GhI7JkL8-MnO9PqR0",
  "tenant_id": "usr_a1b2c3d4",
  "plan": "free",
  "created_at": "2024-01-15T10:30:00",
  "format": "Bearer sc-usr_a1b2c3d4-AbC5DeF6-GhI7JkL8-MnO9PqR0",
  "message": "API key generated successfully. Save this key securely - it won't be shown again."
}
```

### 3. **Python CLI Script (Still Available)**

**Location:** `backend/api_key_generator.py`

**Usage:**
```bash
cd backend
python api_key_generator.py --count 1 --length 32 --save
```

**Auto-generate tenant:**
```bash
python api_key_generator.py --count 1 --length 32 --save --user-email user@example.com
```

**With custom tenant:**
```bash
python api_key_generator.py --tenant mycompany --count 1 --length 32 --save
```

## Key Generation Algorithm

### Before (Old):
- Length: 16 characters
- Format: Simple alphanumeric
- Example: `sc-user123-a1b2c3d4e5f6g7h8`

### After (New):
- Length: **32 characters** (default, configurable 16-64)
- Format: Complex alphanumeric with hyphens for readability
- Example: `sc-usr_a1b2c3d4-AbC5DeF6-GhI7JkL8-MnO9PqR0`

**Improvements:**
1. **Longer keys** - 32 chars vs 16 chars (double the entropy)
2. **Better formatting** - Hyphens every 8 characters for readability
3. **Auto tenant generation** - Unique tenant IDs if not provided
4. **Cryptographically secure** - Uses `secrets.choice()` for randomness

## Storage

### Database Storage

When a key is generated:
1. **Automatically saved to database** (`api_keys` table)
2. **Tenant ID created** (if auto-generated)
3. **User record created** (if email provided)

### Key Information Stored:

- `api_key`: The full API key string
- `tenant_id`: Tenant identifier
- `plan`: Subscription plan (default: "free")
- `created_at`: Creation timestamp
- `is_active`: Active status (default: true)
- `usage_count`: Usage counter (default: 0)

## Security Notes

1. **Keys are not shown again after generation** - Save securely!
2. **Keys are cryptographically secure** - Not guessable
3. **Unique tenant IDs** - Each key gets isolated cache space
4. **Database storage** - Keys are stored securely in SQLite database

## Usage Examples

### Frontend (Recommended)

1. Go to landing page
2. Click "Generate API Key"
3. Copy the key
4. Use in your application

### Backend API

```python
import requests

response = requests.post(
    "http://localhost:8000/api/keys/generate",
    params={"length": 32}
)
data = response.json()
api_key = data["api_key"]
print(f"Your API key: {api_key}")
```

### CLI

```bash
python backend/api_key_generator.py --save
```

## Key Characteristics

| Feature | Value |
|---------|-------|
| **Min Length** | 16 characters |
| **Default Length** | 32 characters |
| **Max Length** | 64 characters |
| **Format** | `sc-{tenant}-{random}` |
| **Random Characters** | Letters (a-z, A-Z) + Digits (0-9) |
| **Entropy** | ~190 bits (for 32 chars) |
| **Security** | Cryptographically secure |
| **Readability** | Hyphens every 8 chars (if > 24) |

## Examples of Generated Keys

```
sc-usr_a1b2c3d4-AbC5DeF6-GhI7JkL8-MnO9PqR0
sc-usr_x9y8z7w6-Vu5Ts4R3-Qw2Er1Ty-Ui0OpAsD
sc-usr_m5n6o7p8-Qr9St0Uv-Wx1Yz2Ab-Cd3Ef4Gh
sc-company-abc-XyZ1AbC2-DeF3GhI4-JkL5MnO6
sc-user123-AbC5DeF6GhI7JkL8MnO9PqR0StUvWxYz
```

---

**Note:** Always save your API keys securely. They provide full access to your cache and usage data.

