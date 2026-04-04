# Semantys AI — Architecture & System Overview

## What is Semantys AI?

Semantys AI is a production-ready SaaS **semantic caching gateway** that sits between applications and the OpenAI API. It intercepts LLM requests, checks if a semantically similar question has been asked before, and returns the cached response — saving both cost and latency.

**Core value proposition:** Reduce LLM API costs by 50–70% and cut latency from 2–5 seconds (live LLM calls) to sub-millisecond (cache hits), with zero code changes required — just swap one import line.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT APPLICATION                        │
│  (Python / TypeScript / Any HTTP client)                         │
│                                                                   │
│  from semantys_cache import ChatCompletion  ← drop-in replace    │
│  ChatCompletion.create(model="gpt-4o-mini", messages=[...])      │
└──────────────────────────┬───────────────────────────────────────┘
                           │ POST /v1/chat/completions
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                     SEMANTYS AI GATEWAY                           │
│                                                                   │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐  │
│  │ Auth Layer   │→│ Rate Limiter  │→│  Input Validation      │  │
│  │ (API Key /   │  │ (slowapi,     │  │  (role, length,       │  │
│  │  Supabase    │  │  per-tenant)  │  │   message count)      │  │
│  │  JWT)        │  │              │  │                        │  │
│  └─────────────┘  └──────────────┘  └───────────┬────────────┘  │
│                                                   │               │
│  ┌────────────────────────────────────────────────▼────────────┐ │
│  │              5-TIER CACHE ENGINE                             │ │
│  │                                                              │ │
│  │  Tier 1: Exact Match (dict lookup, <0.02ms)                 │ │
│  │  Tier 2: Normalized Hash (contractions/filler stripped)      │ │
│  │  Tier 3: Local Embedding Pre-filter (MiniLM, ~5ms)         │ │
│  │  Tier 4: OpenAI Semantic Search (FAISS/Pinecone, ~50ms)    │ │
│  │  Tier 5: Cache Miss → LLM call (1–18 seconds)              │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌────────────────────── STORAGE TIERS ───────────────────────┐  │
│  │ L1: In-Memory (dict + FAISS)                               │  │
│  │ L2: Redis (exact match + embeddings with TTL)              │  │
│  │ L3: PostgreSQL/Supabase (encrypted, persistent)            │  │
│  │ L4: Pinecone (cross-worker vector search)                  │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                           │
                           │ Cache Miss only
                           ▼
                    ┌──────────────┐
                    │  OpenAI API  │
                    │  (or BYOK    │
                    │   user key)  │
                    └──────────────┘
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.10+, FastAPI, Uvicorn |
| **Frontend** | React 19, TypeScript, Vite 7, Tailwind CSS |
| **Database** | PostgreSQL (Supabase) |
| **Vector Search** | FAISS (in-memory) + optional Pinecone |
| **Embeddings** | OpenAI `text-embedding-3-small` (1024 dims) + local `all-MiniLM-L6-v2` |
| **Cache Layer** | Redis (L2 cache) |
| **Auth** | Supabase Auth (PKCE flow, JWT) |
| **Payments** | Stripe (subscriptions + credits) |
| **SDKs** | Python (`semantys-cache` on PyPI), TypeScript (`semantys-cache` on npm) |
| **Monitoring** | Prometheus metrics, Sentry error tracking, PostHog analytics |
| **Deployment** | Docker Compose, Kubernetes (with Ingress, Fluent Bit, Prometheus) |
| **Domains** | `api.semantys.ai` (backend), `app.semantys.ai` (frontend) |

---

## Multi-Tenancy Model

Every user gets full isolation:

- **Tenant ID**: derived from API key format `sc-{tenant}-{random}` → tenant slug = second segment
- **Internal tenant**: `usr_{user_id}` (Supabase user UUID)
- **Isolation scope**: separate FAISS index, separate metrics counters, separate event logs, separate DB rows (all filtered by `org_id` or `tenant_id`)
- **Organizations**: users can create orgs, add members, share API keys within an org
- **RLS**: Row Level Security enabled on all Supabase tables (backend uses `service_role` to bypass)

---

## Database Schema (8 Core Tables)

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `profiles` | User accounts (linked to Supabase auth) | `id` (UUID), `email`, `name`, `is_admin`, `openai_api_key_encrypted` |
| `organizations` | Tenant grouping | `id`, `slug` (unique), `plan`, `settings` (JSONB), `credits_balance` |
| `org_members` | User ↔ Org membership | `org_id`, `user_id`, `role` (owner/admin/member) |
| `api_keys` | API key registry | `api_key` (unique), `tenant_id`, `user_id`, `org_id`, `plan`, `scope`, `usage_count` |
| `usage_logs` | Per-request telemetry | `cache_hits`, `cache_misses`, `tokens_used`, `cost_estimate`, `decision`, `similarity`, `latency_ms`, `tokens_saved` |
| `audit_logs` | Security audit trail | `action`, `resource_type`, `details` (JSONB), `ip_address` |
| `cache_entries` | Cached prompt-response pairs | `org_id`, `prompt_hash`, `prompt_norm`, `response_text`, `embedding` (BYTEA), `model`, `ttl_expires_at`, `is_encrypted` |
| `credits_ledger` | Prepaid credits transactions | `org_id`, `amount` (+credit/-debit), `balance_after`, `reason` |

**Auto-signup trigger**: When a new user registers via Supabase Auth, a PostgreSQL trigger automatically creates their `profiles` row, an `organizations` row, grants `$1.00` starting credits, and adds them as `owner`.

---

## Billing & Pricing Model

### Plans

| Plan | Price | Requests/month | Cache Entries | Starting Credits |
|------|-------|----------------|---------------|-----------------|
| **Free** | $0 | 1,000 | 1,000 | $1.00 |
| **Pro** | $49/mo | 100,000 | 100,000 | $5.00 |
| **Team** | Custom | Unlimited | Unlimited | Custom |

### How Credits Work

- **Cache hits are always free** — no credits deducted
- **Cache misses (non-BYOK)**: charged per token at Semantys rates:
  - Prompt tokens: $0.20 / 1M tokens
  - Completion tokens: $0.80 / 1M tokens
- **BYOK users pay $0** to Semantys — they pay OpenAI directly with their own key
- If `credits_balance <= 0` for a non-BYOK user → HTTP 402 (payment required)

### BYOK (Bring Your Own Key)

Users can store their own OpenAI API key (encrypted with Fernet/PBKDF2HMAC at rest). When set:
- LLM calls use the user's key directly
- No token charges from Semantys
- Semantys never stores the plaintext key

---

## Encryption

Two independent encryption systems:

1. **BYOK Key Storage** (Fernet symmetric)
   - Key derivation: PBKDF2HMAC(SHA256, 100K iterations, `ENCRYPTION_SALT`) on `ENCRYPTION_KEY`
   - Stored in `profiles.openai_api_key_encrypted`

2. **Cache Entry Encryption** (AES-256-GCM per-tenant)
   - Master key: `CACHE_ENCRYPTION_KEY` (32 bytes)
   - Per-tenant key: HKDF(SHA256, salt=`"semantys-cache-v1"`, info=`tenant_id`)
   - Format: `"ENC:" + base64(nonce[12] + ciphertext + tag[16])`
   - Optional — only activates if master key is set

---

## Authentication

### Two Auth Paths

1. **API Key Bearer** (`Authorization: Bearer sc-{tenant}-{random}`)
   - Used by: SDK clients, direct API calls
   - Validated against `api_keys` table with 300s LRU cache (10K entries)

2. **Supabase JWT** (`Authorization: Bearer {jwt}`)
   - Used by: frontend dashboard, account/billing endpoints
   - Verified via JWKS discovery at Supabase URL, with HS256 fallback
   - 10-minute key cache

### Admin Auth
- Admin endpoints require JWT with `is_admin = true` on the user's profile
- Admin dashboard at `/admin` with separate login flow

---

## File Map

```
Semantys_AI/
├── backend/
│   ├── semantic_cache_server.py   # Main app: FastAPI, all endpoints, cache engine
│   ├── database.py                # All DB access, connection pool, credits, audit
│   ├── billing.py                 # Plans, token pricing, Stripe integration
│   ├── encryption.py              # Fernet (BYOK) + AES-256-GCM (cache)
│   ├── auth.py                    # Supabase JWT verification
│   ├── admin_api.py               # Admin router (user mgmt, analytics)
│   ├── vector_store.py            # Pinecone abstraction
│   ├── cache_persistence.py       # Pickle-based L1 disk persistence
│   ├── redis_cache.py             # Redis L2 cache
│   ├── input_guard.py             # Request validation/sanitization
│   ├── webhooks.py                # Org webhook notifications
│   ├── prometheus_metrics.py      # Prometheus metric collection
│   └── supabase_schema.sql        # Full DB schema + RLS + triggers
├── frontend/
│   ├── src/
│   │   ├── App.tsx                # Routes and layout
│   │   ├── pages/                 # All page components
│   │   ├── components/            # Reusable UI components
│   │   ├── api/                   # semanticAPI.ts + adminAPI.ts
│   │   ├── contexts/              # AuthContext (Supabase)
│   │   ├── hooks/                 # useSemanticCache, useMetrics, etc.
│   │   └── lib/                   # Supabase client init
│   └── .env                       # Frontend env vars (VITE_*)
├── sdk/
│   ├── python-wrapper/            # PyPI package: semantys-cache
│   ├── typescript/                # npm package: semantys-cache
│   └── integrations/              # LangChain, FastAPI, Django, Express, etc.
├── k8s/                           # Kubernetes manifests
├── docker-compose.yml             # Local/production Docker setup
├── documentation/                 # Project documentation (you are here)
└── README.md                      # Public-facing overview
```
