# Semantis AI — Backend API & Cache Engine

## The 5-Tier Cache Engine

All cache logic lives in `SemanticCacheService` inside `backend/semantic_cache_server.py`. When a query arrives, it passes through 5 tiers in order — the first match wins.

### Tier 1: Exact Match (~0.02ms)
- Dict lookup on `prompt_norm` (normalized text)
- Checks TTL expiry and model match
- Stored in `TenantState.exact` dictionary

### Tier 2: Normalized Hash Match (~0.02ms)
- `normalize_query()` expands contractions, strips filler words, collapses whitespace
- Lookup on `TenantState.norm_hash_index`
- Catches rephrased-but-identical queries

### Tier 3: Local Embedding Pre-filter (~5ms)
- Uses `all-MiniLM-L6-v2` (local sentence-transformers model)
- Searches `TenantState.local_index` (FAISS IndexFlatIP) for top-3
- **Gate**: If best local cosine similarity < **0.40**, skip Tier 4 entirely (saves the expensive OpenAI embedding call)

### Tier 4: OpenAI Semantic Search (~50ms)
- Generates embedding with `text-embedding-3-small` (1024 dimensions)
- Prefix: `"Semantic meaning: "` prepended before embedding
- **Search paths**:
  - **Pinecone** (if configured): `vector_store.search()` top-10, namespace-per-tenant
  - **FAISS** (default): `IndexFlatIP` for ≤10K entries, auto-upgrades to `IndexIVFFlat` at 10K entries
- **Scoring**: `hybrid_score = 0.97 * cosine + 0.03 * token_overlap`
- **Optional cross-encoder re-ranking** (disabled by default): `0.60 * hybrid + 0.40 * cross_encoder_norm`
- **Decision thresholds** (default threshold = 0.72):
  - `cosine >= threshold + 0.10` → high-confidence match
  - `cosine >= threshold` → medium-confidence match
  - `cosine >= threshold - 0.05` AND `token_overlap >= 0.3` → low-confidence match
- **Response sanity check**: If response_embedding is stored, rejects match if `query-response cosine < 0.20`

### Tier 5: Cache Miss (1–18 seconds)
- Calls OpenAI API (using BYOK key or server key)
- Stores result asynchronously across all storage tiers
- Background enrichment: adds response_embedding and local_embedding

### Adaptive Threshold Tuning

The similarity threshold auto-adjusts per tenant (requires 10+ requests):
- **Near-miss pull**: If >50% of near-misses are within 0.05 of threshold → lower by 0.02 (min 0.55)
- **Low hit ratio** (<25%): lower by 0.015 (min 0.55)
- **High hit ratio** (>80%): raise by 0.01 (max 0.75)
- Range clamped to [0.50, 0.99]

### Domain Heuristics
- Keyword-matching detects domains: `finance`, `legal`, `tech`, `geography`
- Each domain can have an independent similarity threshold
- Configurable via `PUT /settings`

---

## Storage Tiers

| Tier | Store | Use Case | TTL |
|------|-------|----------|-----|
| **L1** | In-Memory (dict + FAISS) | Fastest access, single-worker | Persisted to pickle every 10 new entries |
| **L2** | Redis | Distributed exact-match + embeddings | Configurable per entry |
| **L3** | PostgreSQL (Supabase) | Persistent, encrypted, survives restarts | Configurable (default 7 days) |
| **L4** | Pinecone | Cross-worker vector search (optional) | Managed by Pinecone |

On boot, `_restore_from_db()` loads all cache entries from PostgreSQL back into L1 (in-memory FAISS + dicts).

---

## API Endpoints

### Cache/Query Endpoints (API Key auth)

| Method | Path | Rate Limit | Purpose |
|--------|------|------------|---------|
| `POST` | `/v1/chat/completions` | 200/min | OpenAI-compatible cache proxy (supports `stream=true`) |
| `GET` | `/v1/models` | 60/min | OpenAI-compatible model listing |
| `GET` | `/query` | 200/min | Simple GET-based cache query |
| `GET` | `/metrics` | 60/min | Per-tenant cache hit/miss stats |
| `GET` | `/events` | 60/min | Recent cache decisions |
| `GET` | `/settings` | 60/min | Read tenant cache settings |
| `PUT` | `/settings` | 30/min | Update similarity threshold, TTL, domain thresholds |

### Account Endpoints (Supabase JWT auth)

| Method | Path | Rate Limit | Purpose |
|--------|------|------------|---------|
| `GET` | `/api/auth/me` | 30/min | Current user profile + orgs |
| `POST` | `/api/auth/logout` | 10/min | Logout (client-side session clear) |
| `GET` | `/api/keys/current` | 30/min | Get user's active API key |
| `POST` | `/api/keys/generate` | 5/hour | Generate new API key |
| `POST` | `/api/users/openai-key` | 10/hour | Store BYOK OpenAI key (encrypted) |
| `GET` | `/api/users/openai-key` | 30/min | Check if BYOK key is set |
| `DELETE` | `/api/users/openai-key` | 10/hour | Remove BYOK key |

### Organization Endpoints (Supabase JWT auth)

| Method | Path | Rate Limit | Purpose |
|--------|------|------------|---------|
| `POST` | `/api/orgs` | 10/hour | Create organization |
| `GET` | `/api/orgs` | 30/min | List user's organizations |
| `POST` | `/api/orgs/{org_id}/members` | 20/hour | Add member to org |
| `PATCH` | `/api/orgs/{org_id}/settings` | 20/min | Update org settings |
| `GET` | `/api/orgs/{org_id}/audit` | 30/min | Fetch audit log |

### Billing & Credits Endpoints (Supabase JWT auth)

| Method | Path | Rate Limit | Purpose |
|--------|------|------------|---------|
| `GET` | `/api/billing/plans` | 30/min | Available plans (no auth) |
| `GET` | `/api/billing/status` | 30/min | Org usage, savings, credits balance |
| `POST` | `/api/billing/upgrade` | 5/hour | Stripe Checkout redirect |
| `POST` | `/api/billing/portal` | 10/hour | Stripe Customer Portal redirect |
| `POST` | `/api/billing/webhook` | 100/hour | Stripe event handler (no auth, Stripe signature) |
| `GET` | `/api/credits/balance` | 30/min | Current credits balance |
| `POST` | `/api/credits/add` | 3/hour | Add credits (admin only) |
| `GET` | `/api/credits/history` | 30/min | Credits ledger history |

### Cache Management Endpoints (Supabase JWT auth)

| Method | Path | Rate Limit | Purpose |
|--------|------|------------|---------|
| `POST` | `/api/cache/warmup` | 10/hour | Bulk seed cache from historical pairs |
| `POST` | `/v1/cache/warmup` | 10/hour | Same, API key auth variant |
| `GET` | `/api/cache/entries` | 30/min | List/search cached entries (paginated) |
| `DELETE` | `/api/cache/entries` | 20/min | Bulk delete entries by ID (max 100) |

### System Endpoints

| Method | Path | Auth | Rate Limit | Purpose |
|--------|------|------|------------|---------|
| `GET` | `/health` | None | 60/min | System status, Redis, engine info |
| `GET` | `/prometheus/metrics` | None | 30/min | Prometheus scrape endpoint |

---

## Request Flow: POST /v1/chat/completions

```
1. MaxBodySizeMiddleware → reject if Content-Length > 2MB
2. log_requests middleware → stamp UUID request ID, start timer
3. slowapi rate limiter → check 200/min per tenant
4. get_tenant_from_key() → extract tenant from Bearer sc-{tenant}-{...}
   └── LRU cache (300s TTL, 10K entries) or DB lookup
5. _require_scope() → check read-write permission
6. Plan limit check → Redis monthly counter (DB fallback) → 429 if over quota
7. Credits check (non-BYOK only) → 402 if credits_balance <= 0
8. input_guard.guard_request() → validate messages
9. normalize_text() → concatenate user messages, normalize
10. Cache lookup (5-tier pipeline):
    ├── HIT  → return cached response (free, no credits deducted)
    └── MISS → call OpenAI API → store result async
11. Background tasks (ThreadPoolExecutor, 32 workers):
    ├── Log to usage_logs
    ├── Deduct credits (if miss + non-BYOK)
    ├── Record tokens_saved (if hit)
    ├── Store in Redis L2
    ├── Store in PostgreSQL L3 (with optional encryption)
    ├── Upsert to Pinecone L4
    ├── Fire org webhook
    ├── Enrich: add response_embedding + local_embedding
    └── Update Prometheus metrics
12. Return OpenAI-format response + extra "meta" field:
    { hit, similarity, latency_ms, strategy, confidence, threshold_used, domain }
```

### Streaming (stream=true)

- Calls `svc.lookup()` (cache-only, no LLM)
- **Cache hit**: streams cached text word-by-word via SSE
- **Cache miss**: opens live `call_llm_stream()` → SSE → assembles full response → stores via `svc.store_miss()`

---

## Middleware Stack (outer to inner)

1. **MaxBodySizeMiddleware** — rejects requests with `Content-Length > 2MB`
2. **log_requests** — UUID request ID, timing, slow request flag (>5s), Prometheus metrics
3. **CORSMiddleware** — origins from `ALLOWED_ORIGINS` env, allows `Authorization`, `Content-Type`, `X-Request-ID`, `X-Admin-Key`
4. **slowapi Limiter** — keyed on tenant ID (`tenant:{slug}`) or client IP fallback

---

## Input Validation

- `ChatMessage.role`: must be `system`, `user`, `assistant`, `function`, or `tool` (max 50 chars)
- `ChatMessage.content`: max 30,000 characters
- `ChatRequest.messages`: 1–50 messages
- `ChatRequest.temperature`: 0.0–2.0
- `ChatRequest.ttl_seconds`: 0 to 30 days (default 7 days = 604,800 seconds)
- `input_guard.guard_request()` runs on all LLM-bound requests

---

## Background Processing

`ThreadPoolExecutor(max_workers=32)` named `bg-worker` handles all async work:
- Cache storage across tiers (Redis, PostgreSQL, Pinecone)
- Usage logging to database
- Credit deduction
- Webhook notifications
- Cache enrichment (response embedding, local embedding, cluster rebuild)

---

## Admin API

Admin endpoints are mounted via `admin_api.py` router. Authentication requires Supabase JWT with `is_admin = true`.

Key admin capabilities:
- View analytics summary (total users, requests, hit ratio, cost estimate)
- List/search users with pagination
- View per-user details and usage
- Change user plans, activate/deactivate users
- View top users by requests, hits, tokens, or savings
- User growth and usage trend charts
- Plan distribution analytics
- System health stats
- Audit log viewer

---

## Database Access (database.py)

Connection pool: `psycopg2.pool.ThreadedConnectionPool` with `minconn=2`, `maxconn=25`.

Key function groups:
- **Profile**: `get_user_by_id`, `get_user_by_email`, `set_user_admin`
- **BYOK keys**: `set_user_openai_key`, `get_user_openai_key_encrypted`, `clear_user_openai_key`
- **Organizations**: `create_organization`, `get_user_orgs`, `add_org_member`, `update_org_settings`
- **API keys**: `create_api_key` (upsert), `get_api_key_info`, `get_tenant_plan`
- **Usage**: `log_usage` (17-column insert), `get_events_from_db`, `get_usage_stats`
- **Credits**: `get_org_credits_balance`, `add_org_credits`, `deduct_org_credits` (atomic)
- **Cache**: `store_cache_entry` (upsert), `load_all_cache_entries` (boot restore)
- **Maintenance**: `cleanup_old_logs` (usage: 90 days, audit: 365 days)
