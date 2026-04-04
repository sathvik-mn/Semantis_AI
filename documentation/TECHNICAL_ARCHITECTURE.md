# Semantys AI - Technical Architecture Document

## System Overview

Semantys AI is a multi-tenant semantic caching platform for LLM applications. It intercepts API calls between client applications and LLM providers, detects semantically similar queries that have been answered before, and returns cached responses with sub-50ms latency.

```
                        +------------------+
                        |   Client Apps    |
                        | (OpenAI SDK,     |
                        |  Python/TS SDK,  |
                        |  REST API)       |
                        +--------+---------+
                                 |
                         HTTPS / SSE Stream
                                 |
                        +--------v---------+
                        |   Vercel CDN     |
                        |   (Frontend)     |
                        +--------+---------+
                                 |
                        +--------v---------+
                        |  Railway Server  |
                        |  (FastAPI)       |
                        |                  |
                        | +==============+ |
                        | | Cache Engine | |
                        | | 5-Tier       | |
                        | | Pipeline     | |
                        | +==============+ |
                        +--+----+----+---+-+
                           |    |    |   |
              +------------+    |    |   +-----------+
              |                 |    |               |
     +--------v--+    +--------v-+  +--v--------+  +v-----------+
     |   FAISS   |    | Supabase |  |   Redis   |  |  Pinecone  |
     | (In-Memory|    | Postgres |  |  (Upstash)|  | (Optional) |
     |  Vectors) |    |   (L3)   |  |   (L2)    |  |    (L4)    |
     +-----------+    +----------+  +-----------+  +------------+
              |
     +--------v----------+
     |   OpenAI API      |
     | (Embeddings +     |
     |  Chat Completions)|
     +--------------------+
```

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | React 19, TypeScript 5.9, Vite 7.2, Tailwind CSS | Dashboard, Playground, Analytics |
| Backend | Python 3.13, FastAPI, Uvicorn | API server, cache engine |
| Database | Supabase (PostgreSQL 15) | User data, cache persistence, audit logs |
| Vector Search | FAISS (IndexFlatIP / IndexIVFFlat) | In-memory cosine similarity search |
| Distributed Cache | Redis (Upstash) | L2 exact-match + embedding cache |
| External Vectors | Pinecone (optional) | Cross-worker vector consistency |
| Embeddings | OpenAI text-embedding-3-small (1024d) | Primary semantic embeddings |
| Local Embeddings | all-MiniLM-L6-v2 (384d) | Fast pre-filter gate |
| Re-ranking | cross-encoder/ms-marco-MiniLM-L-6-v2 | Optional candidate re-ranking |
| Auth | Supabase Auth (JWT, PKCE) | User authentication |
| Payments | Stripe | Subscriptions, credits, webhooks |
| Hosting | Railway (backend), Vercel (frontend) | Production deployment |
| Monitoring | Sentry, PostHog, Prometheus | Errors, analytics, metrics |
| Encryption | AES-256-GCM, Fernet, HKDF-SHA256 | Data at rest encryption |

---

## Core Engine: The 5-Tier Cache Pipeline

When a query arrives at `/v1/chat/completions`, it passes through 5 tiers sequentially. The first match wins.

### Tier 1: Exact Match (~0.02ms)

```
Input: "What is machine learning?"
        |
        v
   T.exact[prompt_norm] --> dict lookup O(1)
        |
   Found? -> Check TTL + model compatibility -> RETURN cached response
```

- **Data structure**: Python dict (`TenantState.exact`)
- **Key**: Normalized prompt text (lowercased, trimmed)
- **Complexity**: O(1) hash table lookup
- **Latency**: <0.02ms

### Tier 2: Deep-Normalized Hash Match (~0.02ms)

```
Input: "What's ML?"
        |
   normalize_query() --> "what is ml"
        |
   Not found in hash index?
        |
   deep_normalize() --> "what is machine learning"
        |
   T.norm_hash_index["what is machine learning"] --> O(1) lookup
        |
   Found? -> RETURN cached response
```

**Normalization pipeline:**

```
Step 1: Lowercase
  "What's ML?" --> "what's ml?"

Step 2: Expand contractions (30+ rules)
  "what's ml?" --> "what is ml?"

Step 3: Strip filler words (25 words: please, hey, um, just, basically, etc.)
  "please what is ml?" --> "what is ml?"

Step 4: Remove trailing punctuation
  "what is ml?" --> "what is ml"

Step 5 (deep): Expand abbreviations (55+ mappings)
  "what is ml" --> "what is machine learning"

Step 6 (deep): Synonym normalization (30 groups)
  "what is the cost" --> "what is the charge"
```

**Abbreviation map includes**: ML, AI, NLP, DL, CV, RL, DB, API, UI, UX, CI, CD, K8s, JS, TS, SQL, AWS, GCP, LLM, RAG, ETL, ORM, SDK, CLI, HTTP, TCP, GPU, CPU, RAM, SSD, IoT, SaaS, ROI, KPI, HR, CEO, CTO, MVP, OOP, FP, TDD, DDD, DNS, SSL, SSH, VPN

**Synonym groups include**: cost/price/fee/charge, buy/purchase/acquire, create/make/build/generate, delete/remove/erase, error/bug/issue/problem, fix/repair/resolve/patch, start/begin/launch, and 23 more groups

### Tier 3: Local Model Pre-Filter Gate (~5ms)

```
Input: deep_normalize(query)
        |
   get_local_embedding(text)  --> all-MiniLM-L6-v2 (384-dim vector)
        |
   T.local_index.search(embedding, top_k=3)  --> FAISS cosine search
        |
   best_local_sim < 0.35? --> SKIP to Tier 5 (saves expensive OpenAI call)
   best_local_sim >= 0.35? --> PROCEED to Tier 4
```

- **Model**: `all-MiniLM-L6-v2` (22M params, runs locally)
- **Dimensions**: 384
- **Purpose**: Fast, cheap gate to avoid unnecessary OpenAI API calls
- **Threshold**: 0.35 (lowered from 0.40 for better recall)
- **Key optimization**: Uses deep-normalized text so "ML" is embedded as "machine learning"

### Tier 4: OpenAI Semantic Search (~50ms)

This is the main matching tier with the most sophisticated logic.

#### Step 4a: Embedding Generation

```
Input: "What is machine learning?"
        |
   Prefix: "Semantic meaning: what is machine learning?"
        |
   OpenAI text-embedding-3-small API call
        |
   Output: 1024-dimensional float32 vector, L2-normalized
```

- **Model**: `text-embedding-3-small`
- **Dimensions**: 1024 (configurable via EMBED_DIMENSIONS)
- **Prefix**: `"Semantic meaning: "` prepended to all text
- **Normalization**: L2-normalized for cosine similarity via inner product
- **Caching**: In-memory LRU cache (1000 entries) to avoid duplicate API calls

#### Step 4b: FAISS Vector Search

```
Query embedding (1024d)
        |
   T.index.search(query, top_k=10)
        |
   +-- IndexFlatIP (brute-force): O(n), used when entries < 10,000
   +-- IndexIVFFlat (clustered):  O(sqrt(n)), auto-upgrade at 10,000 entries
        |
   Returns: top-10 candidates with cosine similarity scores
```

**Auto-upgrade to IVF**:
- Triggered when tenant reaches 10,000 entries
- Creates `nlist = sqrt(n)` clusters via k-means
- Sets `nprobe = nlist/4` for search
- Reduces search from O(n) to O(sqrt(n))

**Cluster routing** (when clusters exist):
- Query is compared against cluster centroids
- Only entries in the top `n_clusters/3` closest clusters are searched
- Further reduces candidate set

#### Step 4c: Multi-Signal Text Similarity

For each FAISS candidate, compute 8 text-based similarity signals:

```python
signals = compute_text_similarity(query, candidate)

# Returns:
{
    "token_overlap":      0.43,   # Jaccard overlap on word tokens
    "char_ngram":         0.85,   # Dice coefficient on character trigrams
    "stemmed_overlap":    0.50,   # Jaccard on stemmed tokens
    "idf_weighted":       0.39,   # Stopword-downweighted overlap
    "synonym_expanded":   0.80,   # Overlap after synonym normalization
    "entity_overlap":     0.67,   # Non-stopword overlap (Overlap coefficient)
    "question_type":      1.0,    # Intent match (define/howto/why/when/where/compare/list/ability)
    "sorted_token":       0.50,   # Word-order-invariant overlap
    "text_sim":           0.58,   # Weighted composite of all signals
}
```

**Composite text_sim weights:**
```
text_sim = 0.25 * entity_overlap      (topic correctness)
         + 0.20 * synonym_expanded    (paraphrase detection)
         + 0.15 * idf_weighted        (meaningful word overlap)
         + 0.15 * char_ngram          (typo/morphology tolerance)
         + 0.10 * stemmed_overlap     (word form normalization)
         + 0.10 * question_type       (intent agreement)
         + 0.05 * sorted_token        (word reordering tolerance)
```

#### Step 4d: Hybrid Score Computation

```python
hybrid_score = 0.88 * cosine_similarity + 0.12 * text_sim
```

- **88% cosine**: Embedding model captures deep semantic meaning
- **12% text_sim**: Surface-level signals as safety net and tiebreaker

#### Step 4e: Query-to-Response Matching (Tier 3.5)

```
Query embedding
        |
   T.response_index.search(query, top_k=5)  --> Search RESPONSE embeddings
        |
   High similarity? --> The cached RESPONSE answers this question
        |
   Already a candidate? --> Boost its hybrid score by up to 0.15
   New candidate? --> Add to pool (if response_sim >= 0.45)
```

**Why this matters**: If "What is ML?" was cached, its *response* explains machine learning. When "What is machine learning?" comes in, the query-to-query similarity might be moderate, but the query-to-response similarity is very high. This catches cases where completely different questions need the same answer.

#### Step 4f: Cross-Encoder Re-ranking (Optional)

```
Top-5 candidates
        |
   cross-encoder/ms-marco-MiniLM-L-6-v2
        |
   Score each (query, candidate) pair
        |
   Blend: 55% hybrid_score + 45% cross_encoder_normalized
```

- **Model**: `ms-marco-MiniLM-L-6-v2`
- **Purpose**: More accurate pairwise relevance scoring
- **Enabled via**: `CROSS_ENCODER_ENABLED=true` environment variable

#### Step 4g: Multi-Signal Confidence Decision

```python
threshold = tenant.sim_threshold  # default 0.72, per-tenant configurable

# Signal agreement: both cosine and text signals look good
signals_agree = (cosine >= threshold - 0.03) and (text_sim >= 0.35)

if cosine >= threshold + 0.10:
    MATCH (high confidence)

elif cosine >= threshold:
    MATCH (medium confidence)

elif cosine >= threshold - 0.05 and text_sim >= 0.30:
    MATCH (low confidence - text signals confirm)

elif cosine >= threshold - 0.08 and synonym_expanded >= 0.50:
    MATCH (low confidence - synonym rescue)
    # Catches: "What's the cost?" vs "What is the price?"

elif cosine >= threshold - 0.08 and char_ngram >= 0.60:
    MATCH (low confidence - typo rescue)
    # Catches: "artifical inteligence" vs "artificial intelligence"

elif signals_agree and entity_overlap >= 0.60:
    MATCH (low confidence - entity + signal agreement)
    # Catches: "How to sort an array in JS" vs "JavaScript array sorting"

else:
    NO MATCH --> proceed to Tier 5
```

**Safety guards (post-match):**

1. **Entity mismatch guard**: If confidence is not high AND entity_overlap < 0.15 AND text_sim < 0.20 --> REJECT
   - Prevents: "capital of France" matching "capital of Germany"

2. **Intent mismatch guard**: If confidence is low AND question_type == 0.0 (different intent) --> REJECT
   - Prevents: "How to use Python" matching "What is Python"

3. **Response sanity check**: If query_embedding dot response_embedding < 0.20 --> REJECT
   - Prevents: returning a cached response that is completely unrelated to the query

### Tier 5: Cache Miss --> LLM Call (1-18 seconds)

```
Cache miss
        |
   call_llm(messages, temperature, model)
        |
   OpenAI chat completions API
        |
   Return response to user
        |
   Background async tasks:
     1. Store in T.exact, T.norm_hash_index (+ deep_normalize key), T.rows
     2. Add embedding to T.index (FAISS)
     3. Store in Redis L2 (exact match + embedding)
     4. Persist to PostgreSQL L3 (encrypted if configured)
     5. Upsert to Pinecone L4 (if configured)
     6. Compute response_embedding --> add to T.response_index
     7. Compute local_embedding (deep-normalized text) --> add to T.local_index
     8. Rebuild clusters if needed (every 100 entries)
```

---

## Storage Architecture

### L1: In-Memory (Primary, ~0.02-50ms)

```
TenantState {
    exact:              Dict[str, CacheEntry]      # O(1) exact lookup
    norm_hash_index:    Dict[str, CacheEntry]      # O(1) normalized lookup
    index:              FAISS IndexFlatIP/IVFFlat   # Cosine similarity search
    local_index:        FAISS IndexFlatIP           # Local model pre-filter
    response_index:     FAISS IndexFlatIP           # Query-to-response matching
    response_index_map: List[int]                   # Maps response_index pos -> rows index
    rows:               List[CacheEntry]            # All entries in insertion order
    cluster_centroids:  np.ndarray                  # K-means cluster centers
}
```

### L2: Redis / Upstash (~1-5ms)

- Exact match cache: `{tenant_id}:{prompt_hash}` -> response text
- Embedding cache: `{tenant_id}:emb:{prompt_hash}` -> embedding bytes
- Monthly usage counters: `{tenant_id}:usage:{month}`
- TTL-based expiration matching cache entry TTL

### L3: PostgreSQL / Supabase (~10-50ms)

```sql
cache_entries (
    id              SERIAL PRIMARY KEY,
    org_id          UUID REFERENCES organizations(id),
    prompt_hash     TEXT NOT NULL,
    prompt_norm     TEXT NOT NULL,       -- encrypted with AES-256-GCM
    response_text   TEXT NOT NULL,       -- encrypted with AES-256-GCM
    embedding       BYTEA,              -- raw float32 bytes
    model           TEXT DEFAULT 'gpt-4o-mini',
    domain          TEXT DEFAULT 'general',
    ttl_expires_at  TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT now(),
    last_used_at    TIMESTAMPTZ DEFAULT now(),
    use_count       INTEGER DEFAULT 0
)
-- Indexes: (org_id, prompt_hash), (ttl_expires_at)
```

### L4: Pinecone (Optional, ~20-100ms)

- Namespace-per-tenant isolation
- Full embedding vectors with metadata
- Provides cross-worker consistency for multi-replica deployments

---

## Data Model

### CacheEntry

```python
@dataclass
class CacheEntry:
    prompt_norm:        str              # Normalized query text
    response_text:      str              # LLM response
    embedding:          np.ndarray       # OpenAI embedding (1024-dim float32)
    model:              str              # e.g., "gpt-4o-mini"
    ttl_seconds:        int              # Time-to-live (default 7 days)
    created_at:         float            # Unix timestamp
    last_used_at:       float            # Unix timestamp
    use_count:          int              # Hit counter
    domain:             str              # "general" | "finance" | "legal" | "tech" | ...
    strategy:           str              # "exact" | "semantic" | "miss" | "warmup"
    response_embedding: Optional[np.ndarray]  # For query-to-response matching
    local_embedding:    Optional[np.ndarray]  # For local pre-filter
    cluster_id:         int              # K-means cluster assignment (-1 = unassigned)
```

### Model Compatibility

Models are grouped into families for cache matching. A response cached from `gpt-4o-mini` is returned for `gpt-4o` queries:

```python
def models_compatible(requested, cached):
    # gpt-4o-mini, gpt-4o -> family "gpt-4o"
    # gpt-4, gpt-4-turbo -> family "gpt-4"
    # gpt-3.5-turbo variants -> family "gpt-3.5"
    # claude variants -> family "claude"
```

---

## Multi-Tenant Architecture

```
Organization (Supabase)
    |
    +-- org_members (user <-> org mapping with roles)
    |
    +-- api_keys (sc-{tenant}-{random32})
    |       |
    |       +-- scope: read-only | read-write | admin
    |       +-- allowed_ips: ["1.2.3.4", ...]
    |       +-- expires_at: optional expiration
    |
    +-- TenantState (in-memory, per-tenant)
            |
            +-- Own FAISS index (query embeddings)
            +-- Own response FAISS index
            +-- Own local FAISS index
            +-- Own exact + hash dictionaries
            +-- Own similarity threshold
            +-- Own domain-specific thresholds
            +-- Own metrics (hits, misses, latencies)
```

**Tenant isolation**: Every tenant has a completely separate `TenantState` object. There is zero data leakage between tenants. API keys encode the tenant ID, which is validated on every request.

---

## Security Architecture

### Encryption Layers

```
Layer 1: Transport
    TLS 1.3 (HTTPS) for all API traffic

Layer 2: API Key Storage
    Fernet symmetric encryption (128-bit AES-CBC + HMAC-SHA256)
    User's OpenAI keys encrypted before database storage

Layer 3: Cache at Rest
    AES-256-GCM authenticated encryption
    Per-tenant key derivation via HKDF-SHA256
    Master key from environment variable
    Encrypted fields prefixed with "ENC:" for backward compatibility

Layer 4: Database
    Supabase Row Level Security (RLS) on all 8 tables
    Service role key for backend (bypasses RLS)
    User tokens scoped to their own data
```

### Authentication Flow

```
Client Request
    |
    +-- API Key path: Authorization: Bearer sc-{tenant}-{suffix}
    |       |
    |       +-- Extract tenant from key format
    |       +-- Validate against api_keys table (cached 5 min)
    |       +-- Check expiration, IP allowlist, scope
    |       +-- Set context: user_id, org_id, scope
    |
    +-- JWT path: Authorization: Bearer {supabase_jwt}
            |
            +-- Verify JWT signature (ES256/RS256 via JWKS)
            +-- JWKS cached with 10-min TTL
            +-- Extract user_id from token
            +-- Lookup org membership
```

---

## Adaptive Threshold Tuning

The system automatically adjusts similarity thresholds per-tenant:

```python
def adapt_threshold(T):
    # If >50% of near-misses are within 0.05 of threshold --> lower by 0.02
    # If hit ratio < 25% --> lower by 0.015
    # If hit ratio > 80% --> raise by 0.01
    # Clamped to [0.50, 0.99]
```

Per-domain thresholds are also configurable:
```json
{
    "finance": 0.78,    // Higher threshold for financial queries (precision matters)
    "tech": 0.70,       // Lower threshold for tech queries (more paraphrasing)
    "general": 0.72     // Default
}
```

---

## Domain Detection

Queries are automatically classified into domains for domain-specific threshold tuning:

```python
DOMAIN_MAP = {
    "finance":   ["stock", "market", "inflation", "interest", "portfolio", "revenue", ...],
    "legal":     ["contract", "clause", "law", "liability", "nda", "compliance", ...],
    "tech":      ["api", "python", "vector", "fastapi", "kubernetes", "embedding", ...],
    "geography": ["capital", "country", "city", "border", "continent", ...],
    "medical":   ["symptom", "diagnosis", "treatment", "patient", "clinical", ...],
    "education": ["course", "curriculum", "student", "exam", "grade", ...],
}
```

---

## Monitoring & Observability

### Logging (8 Rotating Log Files)

| Log | File | Content |
|-----|------|---------|
| Access | access.log | Every API request/response |
| Errors | errors.log | Exceptions and failures |
| Semantic | semantic_ops.log | Cache decisions with similarity scores |
| Performance | performance.log | Embedding/LLM timing |
| Security | security.log | Auth failures, IP blocks |
| System | system.log | Startup, shutdown, cache operations |
| Application | application.log | App-level events |

Each log: 10MB max, 5 backup rotations, JSON or text format configurable.

### Prometheus Metrics

```
# Cache metrics
cache_requests_total{tenant, hit_type}
cache_hits_total{tenant}
cache_misses_total{tenant}
cache_latency_seconds{tenant}          # histogram: 0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10
cache_entries_total{tenant}
cache_hit_ratio{tenant}

# API metrics
api_requests_total{endpoint, method, status}
api_latency_seconds{endpoint}

# Token metrics
tokens_used_total{type}                # prompt, completion, total
tokens_saved_total{tenant}
cost_estimate_total{tenant}
```

### Custom Metrics Endpoint (`GET /metrics`)

```json
{
    "requests": 15420,
    "hits": 10794,
    "misses": 4626,
    "hit_ratio": 0.70,
    "semantic_hit_ratio": 0.45,
    "avg_latency_ms": 42.3,
    "p50_latency_ms": 12.1,
    "p95_latency_ms": 156.8,
    "entries": 3847,
    "tokens_saved_est": 2840000,
    "sim_threshold": 0.72,
    "domain_thresholds": {"finance": 0.78, "tech": 0.70},
    "index_type": "IndexFlatIP"
}
```

---

## API Reference

### Primary Endpoint: POST /v1/chat/completions

**Request** (OpenAI-compatible):
```json
{
    "model": "gpt-4o-mini",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is machine learning?"}
    ],
    "temperature": 0.2,
    "stream": true
}
```

**Response** (with cache metadata):
```json
{
    "id": "chatcmpl-abc123",
    "object": "chat.completion",
    "model": "gpt-4o-mini",
    "choices": [{
        "index": 0,
        "message": {"role": "assistant", "content": "Machine learning is..."},
        "finish_reason": "stop"
    }],
    "meta": {
        "hit": "semantic",
        "similarity": 0.8742,
        "hybrid_score": 0.8519,
        "text_sim": 0.6458,
        "entity_overlap": 1.0,
        "synonym_overlap": 0.8,
        "char_ngram_sim": 0.75,
        "token_overlap": 0.43,
        "confidence": "high",
        "latency_ms": 38.42,
        "strategy": "multi_signal_semantic",
        "threshold_used": 0.72,
        "domain": "tech"
    }
}
```

---

## Database Schema

```
profiles            organizations       org_members
+-------------+    +---------------+   +-------------+
| id (UUID)   |    | id (UUID)     |   | org_id      |
| email       |    | name          |   | user_id     |
| name        |    | slug (unique) |   | role        |
| company     |    | plan          |   +-------------+
| is_admin    |    | settings JSON |
| openai_key* |    | credits       |
+-------------+    +---------------+

api_keys             cache_entries         usage_logs
+---------------+   +----------------+   +---------------+
| api_key (uniq)|   | id             |   | id            |
| tenant_id     |   | org_id         |   | tenant_id     |
| user_id       |   | prompt_hash    |   | org_id        |
| org_id        |   | prompt_norm*   |   | endpoint      |
| plan          |   | response_text* |   | cache_hits    |
| scope         |   | embedding      |   | cache_misses  |
| allowed_ips   |   | model          |   | tokens_used   |
| expires_at    |   | domain         |   | cost_estimate |
+---------------+   | ttl_expires_at |   | is_byok       |
                     +----------------+   +---------------+

audit_logs           credits_ledger
+---------------+   +---------------+
| org_id        |   | org_id        |
| user_id       |   | reason        |
| action        |   | amount_usd    |
| resource_type |   | balance_after |
| details JSON  |   | created_at    |
| ip_address    |   +---------------+
+---------------+

* = encrypted with AES-256-GCM when CACHE_ENCRYPTION_KEY is set
```

---

## Deployment Architecture

### Production (Current)

```
GitHub (main branch)
    |
    +-- Railway (auto-deploy on push)
    |       |
    |       +-- FastAPI backend (1 replica, us-west2)
    |       +-- Environment variables for secrets
    |       +-- Auto-restart on crash
    |
    +-- Vercel (auto-deploy on push)
            |
            +-- React frontend (CDN-distributed)
            +-- SPA routing via vercel.json rewrites
```

### Production-Ready (Kubernetes)

```yaml
# Included in repo: docker-compose.yml + k8s manifests
Backend:  2 replicas, resource limits, health checks
Frontend: 2 replicas, Nginx serving static files
Ingress:  Path-based routing (/api -> backend, / -> frontend)
```

---

## Performance Characteristics

| Operation | Latency | Notes |
|-----------|---------|-------|
| Exact hash match | <0.02ms | Dict lookup |
| Deep-normalized hash | <0.02ms | Dict lookup after normalization |
| Local model embedding | ~5ms | all-MiniLM-L6-v2, runs on CPU |
| Local FAISS search | <1ms | Pre-filter gate |
| OpenAI embedding | 30-100ms | Network-bound, LRU cached |
| FAISS search (brute) | <5ms | Up to 10K entries |
| FAISS search (IVF) | <2ms | 10K+ entries, O(sqrt(n)) |
| Text similarity (8 signals) | <1ms | Pure CPU, no I/O |
| Cross-encoder re-rank | ~20ms | Optional, top-5 candidates |
| Full semantic hit | ~50ms | End-to-end with embedding |
| Full cache miss | 1-18s | LLM API call (cached for next time) |

---

## Algorithms Reference

| Algorithm | Implementation | Use Case |
|-----------|---------------|----------|
| Cosine Similarity | FAISS IndexFlatIP (inner product on L2-normalized vectors) | Primary semantic matching |
| Jaccard Index | `\|A intersection B\| / \|A union B\|` on word tokens | Basic token overlap |
| Dice Coefficient | `2 * \|A intersection B\| / (\|A\| + \|B\|)` on character trigrams | Typo/misspelling tolerance |
| Overlap Coefficient | `\|A intersection B\| / min(\|A\|, \|B\|)` on entity tokens | Key entity matching |
| IDF Weighting | Stopwords=0.1, content words=1.0 in weighted Jaccard | Meaningful word emphasis |
| Suffix Stemming | Custom rule-based (28 suffix rules) | Morphological normalization |
| K-Means Clustering | FAISS cluster centroids, rebuilt every 100 entries | Search space reduction |
| IVF Indexing | Inverted file with k-means, nlist=sqrt(n), nprobe=nlist/4 | Sublinear vector search |
| HKDF-SHA256 | Key derivation from master key + tenant salt | Per-tenant encryption keys |
| AES-256-GCM | Authenticated encryption with 96-bit nonce | Cache encryption at rest |
