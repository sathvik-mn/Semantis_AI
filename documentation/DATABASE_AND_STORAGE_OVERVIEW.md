# Database and Storage Overview

## Current Database System

### Primary Database: **SQLite**

**Location:** `backend/cache_data/api_keys.db`

**Tables:**

1. **`users`** - User accounts
   - `id` (PRIMARY KEY)
   - `email` (UNIQUE)
   - `name`
   - `created_at` (TIMESTAMP)
   - `updated_at` (TIMESTAMP)

2. **`api_keys`** - API key management
   - `id` (PRIMARY KEY)
   - `api_key` (UNIQUE, NOT NULL)
   - `tenant_id` (NOT NULL)
   - `user_id` (FOREIGN KEY → users.id)
   - `plan` (DEFAULT: 'free')
   - `plan_expires_at` (TIMESTAMP)
   - `is_active` (BOOLEAN, DEFAULT: 1)
   - `created_at` (TIMESTAMP)
   - `updated_at` (TIMESTAMP)
   - `last_used_at` (TIMESTAMP)
   - `usage_count` (INTEGER, DEFAULT: 0)

3. **`usage_logs`** - Usage tracking and billing
   - `id` (PRIMARY KEY)
   - `api_key` (FOREIGN KEY → api_keys.api_key)
   - `tenant_id` (NOT NULL)
   - `endpoint` (TEXT)
   - `request_count` (INTEGER, DEFAULT: 1)
   - `cache_hits` (INTEGER, DEFAULT: 0)
   - `cache_misses` (INTEGER, DEFAULT: 0)
   - `tokens_used` (INTEGER, DEFAULT: 0)
   - `cost_estimate` (REAL, DEFAULT: 0)
   - `logged_at` (TIMESTAMP, DEFAULT: CURRENT_TIMESTAMP)

---

## Cache Layer Storage

### In-Memory Cache (Primary)

**Type:** Python dictionaries + FAISS vector index

**Structure:**
- **Exact Cache:** `Dict[str, CacheEntry]` - O(1) lookup by normalized prompt
- **Semantic Cache:** `faiss.IndexFlatIP` - Vector similarity search
- **Rows List:** `List[CacheEntry]` - All cache entries for a tenant
- **Events List:** `List[CacheEvent]` - Last 1000 events per tenant

**Per-Tenant State (`TenantState`):**
```python
{
    "exact": Dict[str, CacheEntry],      # Exact match cache
    "index": faiss.IndexFlatIP,          # FAISS vector index
    "rows": List[CacheEntry],            # All entries
    "events": List[CacheEvent],          # Last 1000 events
    "hits": int,                         # Cache hit counter
    "misses": int,                       # Cache miss counter
    "semantic_hits": int,                # Semantic hit counter
    "latencies_ms": List[float],         # Response latencies
    "sim_threshold": float,              # Similarity threshold (default: 0.72)
    "domain_thresholds": Dict[str, float] # Domain-specific thresholds
}
```

**CacheEntry Structure:**
```python
{
    "prompt_norm": str,          # Normalized prompt text
    "response_text": str,        # LLM response
    "embedding": np.ndarray,     # 3072-dim embedding vector
    "model": str,                # Model used (e.g., "gpt-4o-mini")
    "ttl_seconds": int,          # Time-to-live (default: 604800 = 7 days)
    "created_at": float,         # Unix timestamp
    "last_used_at": float,       # Unix timestamp
    "use_count": int,            # Usage counter
    "domain": str,               # Domain classification
    "strategy": str              # "exact" | "semantic" | "miss"
}
```

### Persistent Storage: **Pickle File**

**Location:** `backend/cache_data/cache.pkl`

**What's Saved:**
- All cache entries (exact + semantic)
- FAISS index vectors
- Events (last 1000 per tenant)
- Metrics (hits, misses, latencies)
- Thresholds (per-tenant and domain-specific)

**When Saved:**
- Every 10 new cache entries
- On server shutdown (graceful)
- Manually via `/save` endpoint

**When Loaded:**
- On server startup (automatic)

---

## What Gets Stored Where?

### Database (SQLite) - `api_keys.db`

✅ **Stored:**
- User accounts (email, name)
- API keys and tenant IDs
- User plans and subscriptions
- Usage logs (for billing/analytics)

❌ **NOT Stored:**
- Cache entries (prompts/responses)
- Embeddings
- Event details

### Cache Layer (Memory + Pickle) - `cache.pkl`

✅ **Stored:**
- **All cache entries:**
  - Prompt text (normalized)
  - LLM responses
  - Embeddings (3072-dim vectors)
  - Metadata (model, TTL, domain, strategy)
- **Events:** Last 1000 per tenant
  - Timestamp
  - Decision (exact/semantic/miss)
  - Similarity score
  - Latency
  - Confidence/hybrid scores
- **Metrics:**
  - Hit/miss counts
  - Response latencies
  - Similarity thresholds

### Log Files (Rotating) - `backend/logs/`

✅ **Stored:**
- **`access.log`** - All HTTP requests/responses
- **`errors.log`** - Error traces
- **`semantic_ops.log`** - Cache operations (hits/misses)
- **`performance.log`** - Slow requests (>5s)
- **`security.log`** - Security events
- **`system.log`** - System operations
- **`application.log`** - Application events

**Retention:** 5 backup files, 10MB each (~60MB total)

---

## Data Retention Policies

### 1. Cache Entries (TTL-Based Expiration)

**Default TTL:** `7 days` (604800 seconds)

**Expiration:**
- Entries expire after `ttl_seconds` from `created_at`
- Expired entries are **not automatically deleted** from memory
- Expired entries are **filtered during query** (not returned)
- Production storage has `delete_expired_entries()` method (manual cleanup)

**Configuration:**
```python
# Default in semantic_cache_server.py
ttl_seconds: int = 7 * 24 * 3600  # 7 days
```

**Per-Request TTL:**
- Can be customized per request via API
- Default: 7 days

### 2. Events (Rolling Window)

**Retention:** Last **1000 events** per tenant

**Storage:**
- In-memory: `List[CacheEvent]` (max 1000)
- Persisted to pickle file
- Automatically trimmed: `T.events = T.events[-1000:]`

**When Trimmed:**
- After each cache query (exact/semantic/miss)

### 3. Usage Logs (Permanent)

**Retention:** **Indefinite** (no automatic deletion)

**Storage:**
- SQLite database (`usage_logs` table)
- Stored permanently for billing/analytics

**Manual Cleanup:**
- Can be deleted manually via SQL
- No automatic cleanup implemented

### 4. Log Files (Rotating)

**Retention:** 
- 5 backup files per log type
- 10MB per file
- **Total:** ~60MB per log type

**Rotation:**
- New file when current file exceeds 10MB
- Oldest backup deleted when > 5 backups

### 5. Cache Pickle File (Permanent)

**Retention:** **Indefinite** (until manually deleted)

**Size:** Grows with cache entries (no size limit in current implementation)

**Note:** For production, consider implementing cache size limits or periodic cleanup.

---

## Customer Interaction Storage

### ✅ What's Stored

1. **All Cache Queries:**
   - Prompt text (normalized)
   - LLM responses
   - Embeddings
   - Metadata (model, domain, strategy)

2. **Usage Logs (Database):**
   - Request counts
   - Cache hits/misses
   - Tokens used
   - Cost estimates
   - Timestamps

3. **Events (Last 1000 per tenant):**
   - Query decisions
   - Similarity scores
   - Response latencies
   - Confidence scores

4. **Request Logs (Files):**
   - All HTTP requests/responses
   - Client IP, user-agent
   - Response times
   - Error traces

### ❌ What's NOT Stored (Currently)

1. **Raw prompt text** (only normalized version)
2. **Full conversation history** (only individual queries)
3. **User input before normalization**
4. **Session IDs or user sessions**

---

## Production Storage Options (Available but Not Active)

### PostgreSQL (Available)

**Location:** `backend/production_storage.py`

**When Enabled:**
- Set `DB_BACKEND=postgresql` in environment
- Configure PostgreSQL connection string

**Features:**
- Persistent cache entries in database
- TTL-based expiration
- Better for high-volume production

### Redis (Available)

**Location:** `backend/production_storage.py`

**When Enabled:**
- Set `REDIS_ENABLED=true` in environment
- Configure Redis connection

**Features:**
- Fast in-memory cache
- TTL-based expiration (native)
- Good for high-throughput caching

### S3 (Available)

**Location:** `backend/production_storage.py`

**When Enabled:**
- Set `S3_ENABLED=true` in environment
- Configure AWS credentials

**Features:**
- Backup cache to S3
- Long-term storage
- Disaster recovery

---

## Summary

| Data Type | Storage | Retention | Size Limit |
|-----------|---------|-----------|------------|
| **Cache Entries** | Memory + Pickle | TTL: 7 days (default) | No limit (current) |
| **Events** | Memory + Pickle | Last 1000 per tenant | 1000 events |
| **Usage Logs** | SQLite | Permanent | No limit |
| **Users/API Keys** | SQLite | Permanent | No limit |
| **Request Logs** | Rotating Files | ~60MB per type | 60MB (5 files × 10MB) |

---

## Recommendations for Production

### 1. Implement Cache Size Limits

```python
# Add to TenantState
MAX_ENTRIES_PER_TENANT = 100000  # Configurable
```

### 2. Implement Automatic Cleanup

```python
# Delete expired entries periodically
def cleanup_expired_entries():
    # Remove expired entries from memory
    # Update pickle file
    pass
```

### 3. Archive Old Usage Logs

```python
# Move old logs to archive table or S3
# Keep only last 90 days in active table
```

### 4. Monitor Cache File Size

```python
# Alert if cache.pkl exceeds threshold (e.g., 1GB)
# Implement LRU eviction for oldest entries
```

### 5. Use Production Storage

- Switch to PostgreSQL for cache persistence
- Use Redis for hot cache layer
- Enable S3 backups for disaster recovery

---

## Current Storage Locations

```
backend/
├── cache_data/
│   ├── api_keys.db          # SQLite database (users, keys, usage logs)
│   └── cache.pkl            # Pickle file (cache entries, events)
├── logs/
│   ├── access.log           # Request logs
│   ├── errors.log           # Error logs
│   ├── semantic_ops.log     # Cache operations
│   ├── performance.log      # Slow requests
│   ├── security.log         # Security events
│   ├── system.log           # System logs
│   └── application.log      # Application logs
```

---

## Quick Reference

**Database:** SQLite (`cache_data/api_keys.db`)  
**Cache Storage:** Memory + Pickle (`cache_data/cache.pkl`)  
**Logs:** Rotating files (`backend/logs/`)  

**Cache TTL:** 7 days (default)  
**Event Retention:** Last 1000 per tenant  
**Usage Logs:** Permanent  
**Log Files:** ~60MB per type (5 backups × 10MB)  

**Production Options:** PostgreSQL, Redis, S3 (available but not active)

