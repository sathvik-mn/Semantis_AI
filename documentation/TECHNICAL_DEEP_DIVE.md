# Semantys AI — Technical Deep Dive

A comprehensive guide to the internal architecture, algorithms, and implementation of the Semantys AI semantic caching platform. Written for engineers, technical reviewers, and anyone who wants to understand exactly how the system works under the hood.

---

## Table of Contents

1. [Why This Exists](#1-why-this-exists)
2. [System Architecture Overview](#2-system-architecture-overview)
3. [Technology Stack](#3-technology-stack)
4. [The 5-Tier Cache Engine (Core Algorithm)](#4-the-5-tier-cache-engine)
5. [The 8-Signal Matching Engine](#5-the-8-signal-matching-engine)
6. [Storage Architecture (4 Layers)](#6-storage-architecture)
7. [Query Normalization Pipeline](#7-query-normalization-pipeline)
8. [Adaptive Threshold Tuning](#8-adaptive-threshold-tuning)
9. [Multi-Tenancy & Isolation](#9-multi-tenancy--isolation)
10. [Authentication & Authorization](#10-authentication--authorization)
11. [Encryption Architecture](#11-encryption-architecture)
12. [Billing & Credits System](#12-billing--credits-system)
13. [Frontend Architecture](#13-frontend-architecture)
14. [SDK Documentation](#14-sdk-documentation)
15. [Framework Integrations](#15-framework-integrations)
16. [Monitoring & Observability](#16-monitoring--observability)
17. [Database Schema](#17-database-schema)
18. [Deployment Architecture](#18-deployment-architecture)
19. [Request Lifecycle (End-to-End)](#19-request-lifecycle)
20. [Performance Characteristics](#20-performance-characteristics)

---

## 1. Why This Exists

### The Problem

Large Language Models (LLMs) like GPT-4o are powerful but have two fundamental issues in production:

1. **Cost**: Every API call costs money ($0.15–$60 per 1M tokens depending on model). In production, 40–70% of queries are semantically identical to previous ones — "What is ML?" and "What is machine learning?" both need the same answer, but both trigger full LLM calls.

2. **Latency**: LLM API calls take 1–18 seconds. For user-facing applications, this is unacceptable. Users expect sub-second responses.

### The Approach

Semantys AI solves both problems by intercepting API calls and checking if a semantically similar question has already been answered. If yes, return the cached response in <50ms. If no, forward to the LLM and cache the response for next time.

The key insight is that **semantic similarity is not a single metric** — it requires multiple complementary signals to avoid false positives (returning wrong cached answers) and false negatives (missing valid cache hits). Our 8-signal matching engine with false-positive guards achieves both high precision and high recall.

### Why Build This as a Gateway?

The gateway pattern (sit between client and LLM) was chosen over a library/SDK-only approach because:

- **Zero code changes**: Clients just change the base URL
- **Language agnostic**: Works with any HTTP client, any language
- **Centralized caching**: All instances share the same cache
- **Observable**: Metrics, logs, and decision audit trail in one place
- **Upgradeable**: Algorithm improvements benefit all users instantly

---

## 2. System Architecture Overview

```
                     ┌──────────────────────────────────────────┐
                     │           CLIENT APPLICATIONS            │
                     │                                          │
                     │  ┌──────────┐ ┌──────────┐ ┌─────────┐ │
                     │  │ OpenAI   │ │ Python   │ │ TypeScript│ │
                     │  │ SDK      │ │ SDK      │ │ SDK      │ │
                     │  │ (base_url│ │(semantys)│ │(semantys-│ │
                     │  │  swap)   │ │          │ │ cache)   │ │
                     │  └────┬─────┘ └────┬─────┘ └────┬─────┘ │
                     └───────┼────────────┼────────────┼────────┘
                             │            │            │
                        HTTPS (TLS 1.3) + SSE Streaming
                             │            │            │
                     ┌───────▼────────────▼────────────▼────────┐
                     │         SEMANTYS AI GATEWAY               │
                     │         (FastAPI + Uvicorn)               │
                     │                                           │
                     │  ┌─────────────────────────────────────┐ │
                     │  │         MIDDLEWARE STACK             │ │
                     │  │                                     │ │
                     │  │  1. MaxBodySizeMiddleware (2MB)     │ │
                     │  │  2. Request Logger (UUID, timing)   │ │
                     │  │  3. CORS (configurable origins)     │ │
                     │  │  4. Rate Limiter (slowapi)          │ │
                     │  └──────────────┬──────────────────────┘ │
                     │                 │                         │
                     │  ┌──────────────▼──────────────────────┐ │
                     │  │      AUTHENTICATION LAYER           │ │
                     │  │                                     │ │
                     │  │  Path A: API Key Bearer             │ │
                     │  │    sc-{tenant}-{random32}           │ │
                     │  │    → LRU cache (10K entries, 300s)  │ │
                     │  │                                     │ │
                     │  │  Path B: Supabase JWT               │ │
                     │  │    → JWKS verification (ES256/RS256)│ │
                     │  │    → Key cache (10 min TTL)         │ │
                     │  └──────────────┬──────────────────────┘ │
                     │                 │                         │
                     │  ┌──────────────▼──────────────────────┐ │
                     │  │      INPUT VALIDATION               │ │
                     │  │                                     │ │
                     │  │  • Message format validation        │ │
                     │  │  • Role validation (system/user/    │ │
                     │  │    assistant)                        │ │
                     │  │  • Length limits                     │ │
                     │  │  • Prompt injection detection        │ │
                     │  └──────────────┬──────────────────────┘ │
                     │                 │                         │
                     │  ┌══════════════▼══════════════════════┐ │
                     │  ║      5-TIER CACHE ENGINE            ║ │
                     │  ║                                     ║ │
                     │  ║  Tier 1: Exact Match     (<0.02ms) ║ │
                     │  ║  Tier 2: Normalized Hash (<0.02ms) ║ │
                     │  ║  Tier 3: Local Pre-filter   (~5ms) ║ │
                     │  ║  Tier 4: Semantic Search   (~50ms) ║ │
                     │  ║  Tier 5: LLM Call        (1-18s)   ║ │
                     │  ╚══════════════╤══════════════════════╝ │
                     │                 │                         │
                     │  ┌──────────────▼──────────────────────┐ │
                     │  │      BACKGROUND WORKERS             │ │
                     │  │      ThreadPoolExecutor(32)         │ │
                     │  │                                     │ │
                     │  │  • Cache storage (all 4 layers)     │ │
                     │  │  • Usage logging (PostgreSQL)       │ │
                     │  │  • Credit deduction                 │ │
                     │  │  • Webhook notifications            │ │
                     │  │  • Embedding computation            │ │
                     │  └──────────────────────────────────────┘ │
                     └────────┬───────┬───────┬───────┬─────────┘
                              │       │       │       │
                   ┌──────────▼──┐ ┌──▼────┐ ┌▼─────┐ ┌▼────────┐
                   │ FAISS       │ │Supa-  │ │Redis │ │Pinecone │
                   │ (In-Memory) │ │base   │ │(Up-  │ │(Optional│
                   │             │ │Postgres│ │stash)│ │ L4)     │
                   │ • Query idx │ │(L3)   │ │(L2)  │ │         │
                   │ • Local idx │ │       │ │      │ │         │
                   │ • Resp idx  │ │       │ │      │ │         │
                   └─────────────┘ └───────┘ └──────┘ └─────────┘
                              │
                   ┌──────────▼──────────┐
                   │    OpenAI API       │
                   │    (or BYOK key)    │
                   │                     │
                   │  • text-embedding-  │
                   │    3-small (1024d)  │
                   │  • gpt-4o-mini     │
                   │  • gpt-4o          │
                   └─────────────────────┘
```

---

## 3. Technology Stack

### Backend

| Component | Technology | Version | Why This Choice |
|-----------|-----------|---------|-----------------|
| **Language** | Python | 3.10+ | Rich ML/NLP ecosystem, FAISS bindings, OpenAI SDK |
| **Framework** | FastAPI | Latest | Async support, automatic OpenAPI docs, Pydantic validation, high performance |
| **Server** | Uvicorn | Latest | ASGI server, supports HTTP/2 and WebSocket |
| **Production Server** | Gunicorn + Uvicorn workers | Latest | Multi-process for production scaling |
| **Vector Search** | FAISS (faiss-cpu) | Latest | Facebook's billion-scale similarity search; O(1) to O(√n) |
| **Embeddings (Primary)** | OpenAI text-embedding-3-small | 1024 dims | Best quality-to-cost ratio for semantic understanding |
| **Embeddings (Local)** | sentence-transformers (all-MiniLM-L6-v2) | 384 dims | 22M params, runs on CPU in ~5ms, free pre-filter gate |
| **Re-ranking** | cross-encoder/ms-marco-MiniLM-L-6-v2 | - | Optional pairwise relevance scoring |
| **Array Operations** | NumPy | Latest | Fast vectorized math for similarity computations |
| **Data Validation** | Pydantic | v2 | Request/response validation, type safety |
| **Rate Limiting** | slowapi | Latest | Per-tenant, per-endpoint rate limiting |
| **HTTP Client** | httpx | Latest | Async HTTP for OpenAI API calls |
| **Database Driver** | psycopg2 | Latest | PostgreSQL connection pooling |
| **Redis Client** | redis-py | Latest | L2 cache operations |
| **Vector DB Client** | pinecone-client | Latest | Optional L4 distributed vector search |
| **Spelling** | symspellpy | Latest | Typo correction in queries |
| **Encryption** | cryptography | Latest | Fernet + AES-256-GCM |
| **JWT** | python-jose | Latest | JWT verification (ES256, RS256, HS256) |
| **Payments** | stripe | Latest | Subscriptions, webhooks, customer portal |
| **Monitoring** | prometheus-client | Latest | Metrics collection |
| **Error Tracking** | sentry-sdk | Latest | Exception tracking + performance profiling |
| **Email** | resend | Latest | Transactional emails |
| **Process Info** | psutil | Latest | System health monitoring |

### Frontend

| Component | Technology | Version | Why This Choice |
|-----------|-----------|---------|-----------------|
| **Framework** | React | 19 | Latest concurrent features, Suspense |
| **Language** | TypeScript | 5.9 | Type safety for complex state |
| **Build Tool** | Vite | 7 | Fast HMR, ESBuild-based |
| **Styling** | Tailwind CSS | 3 | Utility-first, rapid UI development |
| **Routing** | React Router DOM | v7 | File-based routing, loaders |
| **Auth** | Supabase JS | 2.97 | PKCE flow, session management |
| **Charts** | Recharts | 3.4 | Admin analytics dashboards |
| **3D Graphics** | Three.js | 0.183 | Animated landing page background |
| **Animations** | Framer Motion | 12.35 | Component transitions |
| **Icons** | Lucide React | 0.553 | Consistent icon set |
| **Markdown** | react-markdown + remark-gfm | 10.1 | Chat response rendering |
| **Syntax Highlighting** | react-syntax-highlighter (Prism) | 16.1 | Code blocks in chat |
| **HTTP Client** | Axios | 1.13 | Admin API (interceptors for JWT) |
| **Analytics** | PostHog | 1.363 | Product analytics |
| **Error Tracking** | Sentry React | 10.45 | Frontend error monitoring |

### Infrastructure

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Database** | Supabase (PostgreSQL 15) | User data, cache persistence, auth, RLS |
| **Cache** | Redis / Upstash | L2 caching layer |
| **Vector Store** | Pinecone (optional) | Distributed vector search for multi-replica |
| **Backend Hosting** | Railway | Auto-deploy, environment management |
| **Frontend Hosting** | Vercel | CDN-distributed SPA |
| **Containers** | Docker + docker-compose | Local development + production |
| **Orchestration** | Kubernetes | Production-scale deployment |
| **CI/CD** | GitHub Actions | Automated testing + deployment |
| **TLS** | Let's Encrypt (cert-manager) | HTTPS termination |
| **Log Aggregation** | Fluent Bit | K8s log collection |
| **Metrics** | Prometheus + Grafana | Infrastructure monitoring |

---

## 4. The 5-Tier Cache Engine

The core of Semantys AI. When a query arrives at `POST /v1/chat/completions`, it passes through 5 tiers sequentially. **The first match wins** — this means most queries are resolved at the cheapest, fastest tier.

### Tier 1: Exact Match

```
Input: "What is machine learning?"
         │
         ▼
  lowercase + strip whitespace
         │
         ▼
  TenantState.exact[normalized_prompt]  ──→  O(1) dict lookup
         │
    Found? ──→ Check TTL expiration
         │         │
         │    Not expired? ──→ Check model compatibility
         │                        │
         │                   Compatible? ──→ RETURN cached response
         │
    Not found ──→ Proceed to Tier 2
```

**Data Structure**: Python `dict` (hash table)
**Key**: Lowercased, whitespace-stripped prompt text
**Complexity**: O(1) amortized
**Latency**: <0.02ms
**What it catches**: Repeated identical queries (common in production — users retry, multiple instances)

### Tier 2: Deep-Normalized Hash Match

```
Input: "What's ML? Please help"
         │
         ▼
  normalize_query()
    1. Lowercase:           "what's ml? please help"
    2. Expand contractions:  "what is ml? please help"
    3. Strip filler words:   "what is ml?"
    4. Remove punctuation:   "what is ml"
         │
         ▼
  deep_normalize()
    5. Expand abbreviations: "what is machine learning"
    6. Synonym normalization: (no change here)
         │
         ▼
  TenantState.norm_hash_index[deep_normalized]  ──→  O(1) dict lookup
         │
    Found? ──→ RETURN cached response
    Not found ──→ Proceed to Tier 3
```

**Data Structure**: Python `dict`
**Key**: Deep-normalized prompt text
**Complexity**: O(1) after normalization (~0.01ms for normalization)
**Latency**: <0.02ms total
**What it catches**: Contractions ("what's" → "what is"), filler words ("please", "hey", "um"), abbreviations ("ML" → "machine learning"), synonyms ("cost" → "price")

### Tier 3: Local Model Pre-Filter Gate

```
Input: deep_normalized query text
         │
         ▼
  all-MiniLM-L6-v2 encode(text)  ──→  384-dim vector (~5ms)
         │
         ▼
  TenantState.local_index.search(vector, k=3)  ──→  FAISS cosine search
         │
  best_similarity < 0.35?
         │
    Yes ──→ SKIP Tier 4, go directly to Tier 5
             (saves ~$0.00002 OpenAI embedding call)
         │
    No  ──→ Proceed to Tier 4 (worth the OpenAI call)
```

**Model**: `all-MiniLM-L6-v2` (22M parameters, runs locally on CPU)
**Dimensions**: 384
**Gate Threshold**: 0.35 cosine similarity
**Purpose**: Cheap, fast filter that prevents unnecessary OpenAI embedding API calls. If the local model says "nothing even remotely similar exists", we skip the expensive Tier 4 entirely.
**Cost savings**: Avoids 60–70% of OpenAI embedding calls in practice

**Why a separate local model?** OpenAI's text-embedding-3-small is more accurate but costs money and has network latency. The local model costs nothing and runs in 5ms. Using it as a gate gives us the best of both worlds — cheap pre-filtering with expensive precision only when needed.

### Tier 4: Multi-Signal Semantic Search

This is the main matching tier with the most sophisticated logic. It has 7 substeps:

#### Step 4a: OpenAI Embedding Generation

```
Input: "What is machine learning?"
         │
         ▼
  Prefix: "Semantic meaning: what is machine learning?"
         │
         ▼
  OpenAI API: text-embedding-3-small (dimensions=1024)
         │
         ▼
  Output: 1024-dim float32 vector, L2-normalized
         │
  LRU Cache: Store embedding (1000 entries max)
```

- **Model**: `text-embedding-3-small`
- **Dimensions**: 1024 (configurable via `EMBED_DIMENSIONS`)
- **Prefix**: `"Semantic meaning: "` prepended to improve embedding quality
- **Normalization**: L2-normalized so inner product = cosine similarity
- **Caching**: In-memory LRU (1000 entries) to avoid duplicate API calls

#### Step 4b: FAISS Vector Search

```
Query embedding (1024-dim)
         │
         ▼
  TenantState.index.search(query_vector, k=10)
         │
  ┌──────┴──────────────────────────────────┐
  │  Entries < 10,000?                       │
  │  → IndexFlatIP (brute force)             │
  │    O(n), exhaustive, exact results       │
  │                                          │
  │  Entries >= 10,000?                      │
  │  → IndexIVFFlat (clustered)              │
  │    nlist = √n clusters (k-means)         │
  │    nprobe = nlist/4 searched             │
  │    O(√n), approximate, fast              │
  └──────┬──────────────────────────────────┘
         │
         ▼
  Top-10 candidates with cosine similarity scores
```

**Auto-upgrade mechanism**: When a tenant accumulates 10,000 cache entries, the system automatically:
1. Trains an IVF index with `nlist = √n` clusters via k-means
2. Sets `nprobe = nlist/4` for search (balances speed vs recall)
3. Migrates all vectors to the new index
4. Rebuilds clusters every 100 new entries

**Cluster routing**: When clusters exist, queries are first compared against cluster centroids, then only entries in the top `n_clusters/3` closest clusters are searched.

#### Step 4c: Multi-Signal Text Similarity

For each of the top-10 FAISS candidates, compute 8 text-based similarity signals. See [Section 5](#5-the-8-signal-matching-engine) for full details.

#### Step 4d: Hybrid Score Computation

```python
hybrid_score = 0.88 * cosine_similarity + 0.12 * text_sim_composite
```

- **88% cosine**: The embedding model captures deep semantic meaning
- **12% text_sim**: Surface-level signals serve as safety net and tiebreaker

**Why not 100% cosine?** Embeddings can be deceived by superficial similarity (e.g., "Capital of France" vs "Capital of Germany" have very high cosine similarity). The text signals catch these cases.

#### Step 4e: Query-to-Response Matching

```
Query embedding
         │
         ▼
  TenantState.response_index.search(query, k=5)
         │
  Search against RESPONSE embeddings (not query embeddings)
         │
  For each response match:
    response_sim >= 0.45?
         │
    Already in candidate pool? → Boost hybrid_score by up to 0.15
    New candidate? → Add to pool
```

**Why this exists**: Sometimes completely different questions need the same answer. "Explain backpropagation" and "How do neural networks learn weights?" are very different queries, but the cached response for one answers the other. By matching the incoming query against response embeddings, we catch these cross-question cache hits.

#### Step 4f: Cross-Encoder Re-ranking (Optional)

```
Top-5 candidates from above
         │
         ▼
  cross-encoder/ms-marco-MiniLM-L-6-v2
         │
  Score each (query, candidate) pair independently
         │
  Blend: 55% hybrid_score + 45% cross_encoder_normalized
         │
  Re-sort candidates
```

- **Model**: `ms-marco-MiniLM-L-6-v2`
- **Enable**: Set `CROSS_ENCODER_ENABLED=true`
- **Purpose**: More accurate pairwise relevance scoring than bi-encoder similarity
- **Latency**: ~20ms for 5 candidates

#### Step 4g: Multi-Signal Confidence Decision

```python
threshold = tenant.sim_threshold  # default 0.72, per-tenant configurable (0.50–0.99)

# High confidence — cosine alone is very strong
if cosine >= threshold + 0.10:
    → MATCH (high confidence)

# Medium confidence — cosine meets threshold
elif cosine >= threshold:
    → MATCH (medium confidence)

# Low confidence — cosine is close, text signals confirm
elif cosine >= threshold - 0.05 and text_sim >= 0.30:
    → MATCH (low confidence, text-confirmed)

# Synonym rescue — cosine is borderline, but synonyms match well
elif cosine >= threshold - 0.08 and synonym_expanded >= 0.50:
    → MATCH (low confidence, synonym rescue)
    # Catches: "What's the cost?" vs "What is the price?"

# Typo rescue — cosine is borderline, but character overlap is high
elif cosine >= threshold - 0.08 and char_ngram >= 0.60:
    → MATCH (low confidence, typo rescue)
    # Catches: "artifical inteligence" vs "artificial intelligence"

# Entity + agreement rescue — signals agree broadly
elif signals_agree and entity_overlap >= 0.60:
    → MATCH (low confidence, entity + signal agreement)
    # Catches: "How to sort array in JS" vs "JavaScript array sorting"

else:
    → NO MATCH → proceed to Tier 5
```

**Post-match safety guards:**

```python
# Guard 1: Entity mismatch
if confidence != "high" and entity_overlap < 0.15 and text_sim < 0.20:
    → REJECT (different topics entirely)
    # Prevents: "capital of France" matching "capital of Germany"

# Guard 2: Intent mismatch
if confidence == "low" and question_type_sim == 0.0:
    → REJECT (different question intent)
    # Prevents: "How to use Python" matching "What is Python"

# Guard 3: Response sanity check
if dot(query_embedding, response_embedding) < 0.20:
    → REJECT (response doesn't answer this query)
    # Final safety net against semantic drift
```

### Tier 5: Cache Miss → LLM Call

```
No match found in any tier
         │
         ▼
  Determine API key:
    BYOK user? → Use their encrypted OpenAI key (decrypted at runtime)
    Semantys key? → Use platform OpenAI key
         │
         ▼
  OpenAI chat.completions.create(
      model=requested_model,
      messages=messages,
      temperature=temperature,
      stream=stream
  )
         │
         ▼
  Return response to client (streaming or complete)
         │
         ▼
  Background async tasks (ThreadPoolExecutor, 32 workers):
    1. Store in TenantState.exact[prompt_norm]
    2. Store in TenantState.norm_hash_index[deep_normalized]
    3. Add OpenAI embedding to TenantState.index (FAISS)
    4. Compute response_embedding → add to TenantState.response_index
    5. Compute local_embedding (MiniLM) → add to TenantState.local_index
    6. Store in Redis L2 (exact key + embedding bytes)
    7. Persist to PostgreSQL L3 (encrypted if configured)
    8. Upsert to Pinecone L4 (if configured)
    9. Log usage to PostgreSQL (tokens, cost, decision)
    10. Deduct credits (non-BYOK users)
    11. Send webhook notification (if org has webhooks)
    12. Rebuild FAISS clusters if needed (every 100 entries)
```

---

## 5. The 8-Signal Matching Engine

Each signal captures a different dimension of similarity. Together, they provide robust matching with false-positive protection.

### Signal 1: Token Overlap (Jaccard Index)

```
Measure: |A ∩ B| / |A ∪ B|   where A, B = sets of word tokens

Example:
  A = {"what", "is", "machine", "learning"}
  B = {"what", "is", "deep", "learning"}
  Intersection = {"what", "is", "learning"} = 3
  Union = {"what", "is", "machine", "deep", "learning"} = 5
  Score = 3/5 = 0.60
```

**Strength**: Simple, fast, intuitive baseline
**Weakness**: Doesn't handle synonyms or morphological variants

### Signal 2: Character N-gram Similarity (Dice Coefficient)

```
Measure: 2 * |A ∩ B| / (|A| + |B|)   where A, B = sets of character trigrams

Example:
  "artificial" → {"art", "rti", "tif", "ifi", "fic", "ici", "cia", "ial"}
  "artifical"  → {"art", "rti", "tif", "ifi", "fic", "ica", "cal"}
  High overlap despite the typo!
  Score ≈ 0.85
```

**Strength**: Catches typos, misspellings, and morphological variants
**Weakness**: Can give high scores for unrelated short words

### Signal 3: Stemmed Token Overlap

```
Measure: Jaccard index on stemmed tokens (custom suffix-based stemmer)

Stemming rules (28 suffix rules):
  "running"    → "run"
  "databases"  → "databas"
  "learning"   → "learn"
  "implementation" → "implement"

Example:
  "implementing databases" → {"implement", "databas"}
  "database implementation" → {"databas", "implement"}
  Score = 1.0 (perfect match after stemming)
```

**Strength**: Handles verb tenses, plurals, gerunds
**Weakness**: Aggressive stemming can merge unrelated words

### Signal 4: IDF-Weighted Token Overlap

```
Measure: Weighted Jaccard where stopwords get weight 0.1, content words get 1.0

Example:
  "What is the capital of France" → weights: what=0.1, is=0.1, the=0.1,
                                              capital=1.0, of=0.1, france=1.0
  "What is the capital of Germany" → same weights
  
  Unweighted overlap: 5/7 = 0.71 (misleadingly high)
  IDF-weighted overlap: (0.1+0.1+0.1+1.0+0.1) / (0.1+0.1+0.1+1.0+0.1+1.0+1.0) = 0.43
  (correctly shows that "France" vs "Germany" matters a lot)
```

**Strength**: Downweights common/meaningless words, emphasizes important content
**Weakness**: Doesn't know domain-specific term importance

### Signal 5: Synonym-Expanded Overlap

```
Measure: Jaccard after replacing all words with canonical synonyms

Synonym groups (292 groups):
  cost, price, fee, charge, expense → "cost"
  create, make, build, generate, construct → "create"
  delete, remove, erase, destroy → "delete"
  error, bug, issue, problem, fault → "error"
  fix, repair, resolve, patch, mend → "fix"
  start, begin, launch, initiate → "start"
  ... (292 groups total)

Example:
  "What is the cost of this?" → {"what", "is", "the", "cost", "of", "this"}
  "What is the price of this?" → {"what", "is", "the", "cost", "of", "this"}
                                                         ↑ price → cost
  Score = 1.0 (perfect match after synonym expansion)
```

**Strength**: Catches paraphrases that use different words for the same concept
**Weakness**: Limited to predefined synonym groups

### Signal 6: Entity Overlap (Overlap Coefficient)

```
Measure: |A ∩ B| / min(|A|, |B|)   on non-stopword tokens only

Example:
  "Capital of France" → entities: {"capital", "france"}
  "Capital of Germany" → entities: {"capital", "germany"}
  Intersection = {"capital"} = 1
  min(2, 2) = 2
  Score = 1/2 = 0.50

  "Capital of France" → entities: {"capital", "france"}
  "What is France's capital" → entities: {"france", "capital"}
  Intersection = {"capital", "france"} = 2
  Score = 2/2 = 1.0
```

**Strength**: Focuses on key entities/nouns; critical for false-positive prevention
**Weakness**: Purely lexical — doesn't catch entity synonyms

### Signal 7: Question Type Match

```
9 question type categories:
  "how to ..."     → howto
  "what is ..."    → define
  "why ..."        → why
  "when ..."       → when
  "where ..."      → where
  "who ..."        → who
  "how many ..."   → count
  "compare ..."    → compare
  "list ..."       → list

Score: 1.0 if same type, 0.0 if different

Example:
  "How to use Python" → howto
  "What is Python"    → define
  Score = 0.0 (different intent — prevents false match)
```

**Strength**: Prevents matching queries with the same topic but different intent
**Weakness**: Some queries don't fit neatly into categories

### Signal 8: Sorted Token Overlap

```
Measure: Jaccard on alphabetically sorted, deduplicated word sets

Example:
  "sorting arrays in Python" → {"arrays", "in", "python", "sorting"}
  "Python array sorting"     → {"array", "python", "sorting"}
  Score: moderate overlap (word order doesn't matter)
```

**Strength**: Handles word reordering ("Python sorting" ≈ "sorting in Python")
**Weakness**: Loses word order information that may be meaningful

### Composite Text Similarity Score

```python
text_sim = (
    0.25 * entity_overlap      +  # Topic correctness (highest weight — most critical)
    0.20 * synonym_expanded     +  # Paraphrase detection
    0.15 * idf_weighted         +  # Meaningful word overlap
    0.15 * char_ngram           +  # Typo/morphology tolerance
    0.10 * stemmed_overlap      +  # Word form normalization
    0.10 * question_type        +  # Intent agreement
    0.05 * sorted_token            # Word reordering tolerance
)
```

---

## 6. Storage Architecture

### Layer 1: In-Memory (L1)

The primary storage layer. All active cache data lives in Python process memory for maximum speed.

```python
class TenantState:
    tenant_id: str
    
    # Tier 1 & 2 - Hash lookups
    exact: Dict[str, CacheEntry]           # prompt_norm → entry
    norm_hash_index: Dict[str, CacheEntry] # deep_norm → entry
    
    # Tier 3 - Local pre-filter
    local_index: faiss.IndexFlatIP         # MiniLM 384-dim vectors
    
    # Tier 4 - Semantic search
    index: faiss.IndexFlatIP | IndexIVFFlat  # OpenAI 1024-dim vectors
    response_index: faiss.IndexFlatIP        # Response 1024-dim vectors
    response_index_map: List[int]            # Maps response pos → rows index
    
    # Entry storage
    rows: List[CacheEntry]                 # All entries in insertion order
    
    # Clustering (for large tenants)
    cluster_centroids: Optional[np.ndarray]  # K-means cluster centers
    
    # Metrics
    hits: int
    misses: int
    semantic_hits: int
    latencies: List[float]
    
    # Config
    sim_threshold: float                   # Default 0.72, range [0.50, 0.99]
    domain_thresholds: Dict[str, float]    # Per-domain overrides
```

### Layer 2: Redis (L2)

Secondary cache for fast cross-restart persistence and exact-match lookups.

```
Key patterns:
  {tenant_id}:{prompt_hash}           → response text (string)
  {tenant_id}:emb:{prompt_hash}       → embedding bytes (binary)
  {tenant_id}:usage:{YYYY-MM}         → monthly request count (integer)

TTL: Matches cache entry TTL (default 7 days)
Connection: Upstash Redis (serverless) or self-hosted
Fallback: In-memory dict if Redis is unavailable
```

### Layer 3: PostgreSQL / Supabase (L3)

Persistent storage for durability and cross-deploy consistency.

```sql
cache_entries (
    id              SERIAL PRIMARY KEY,
    org_id          UUID REFERENCES organizations(id),
    prompt_hash     TEXT NOT NULL,
    prompt_norm     TEXT NOT NULL,           -- encrypted with AES-256-GCM if key set
    response_text   TEXT NOT NULL,           -- encrypted with AES-256-GCM if key set
    embedding       BYTEA,                  -- raw float32 bytes (1024 × 4 = 4096 bytes)
    model           TEXT DEFAULT 'gpt-4o-mini',
    domain          TEXT DEFAULT 'general',
    ttl_expires_at  TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT now(),
    last_used_at    TIMESTAMPTZ DEFAULT now(),
    use_count       INTEGER DEFAULT 0,
    is_encrypted    BOOLEAN DEFAULT false
)

-- Indexes for fast lookups:
CREATE INDEX idx_cache_org_hash ON cache_entries(org_id, prompt_hash);
CREATE INDEX idx_cache_ttl ON cache_entries(ttl_expires_at);
```

### Layer 4: Pinecone (L4, Optional)

Distributed vector search for multi-replica deployments.

```
Namespace: per-tenant (e.g., "tenant-myorg")
Vectors: 1024-dim float32
Metadata: prompt_norm, response_text, model, domain, created_at
Purpose: Cross-worker consistency when running multiple backend replicas
```

### Startup Hydration Flow

```
Server starts
    │
    ▼
Load from PostgreSQL L3 (all non-expired cache_entries per org)
    │
    ▼
For each entry:
  1. Decrypt prompt_norm and response_text (if encrypted)
  2. Deserialize embedding from BYTEA
  3. Add to TenantState.exact and norm_hash_index
  4. Add embedding to TenantState.index (FAISS)
  5. Compute local embedding → add to TenantState.local_index
  6. Compute response embedding → add to TenantState.response_index
    │
    ▼
Server ready (cache pre-warmed from persistent storage)
```

---

## 7. Query Normalization Pipeline

The normalization pipeline transforms queries before matching, significantly increasing hit rates without any ML model.

### Step 1: Basic Normalization (`normalize_query`)

```python
def normalize_query(text: str) -> str:
    text = text.lower()                          # "What's ML?" → "what's ml?"
    text = expand_contractions(text)              # "what's ml?" → "what is ml?"
    text = strip_filler_words(text)               # "hey um what is ml?" → "what is ml?"
    text = text.strip().rstrip("?!.,;:")          # "what is ml?" → "what is ml"
    return text
```

**Contraction rules** (30+ mappings):
```
what's → what is,  it's → it is,  don't → do not,  won't → will not,
can't → cannot,  i'm → i am,  they're → they are,  we've → we have,
shouldn't → should not,  couldn't → could not,  wouldn't → would not, ...
```

**Filler words** (25 words stripped):
```
please, hey, um, uh, like, basically, actually, just, so, well,
okay, ok, right, you know, i mean, kind of, sort of, ...
```

### Step 2: Deep Normalization (`deep_normalize`)

```python
def deep_normalize(text: str) -> str:
    text = normalize_query(text)                  # Basic normalization first
    text = expand_abbreviations(text)             # "ml" → "machine learning"
    text = apply_synonym_normalization(text)       # "cost" → "price" (canonical form)
    text = apply_suffix_stemming(text)             # "running" → "run"
    return text
```

**Abbreviation mappings** (52 expansions):
```
ml → machine learning,  ai → artificial intelligence,  nlp → natural language processing,
dl → deep learning,  cv → computer vision,  rl → reinforcement learning,
db → database,  api → application programming interface,  k8s → kubernetes,
js → javascript,  ts → typescript,  sql → structured query language,
aws → amazon web services,  gcp → google cloud platform,  llm → large language model,
rag → retrieval augmented generation,  etl → extract transform load,  orm → object relational mapping,
sdk → software development kit,  cli → command line interface,  gpu → graphics processing unit,
cpu → central processing unit,  ram → random access memory,  dns → domain name system,
ssl → secure sockets layer,  ssh → secure shell,  vpn → virtual private network,
saas → software as a service,  roi → return on investment,  kpi → key performance indicator,
mvp → minimum viable product,  oop → object oriented programming,  tdd → test driven development,
... (52 total)
```

**Synonym groups** (292 groups, canonical form is the first word):
```
cost/price/fee/charge/expense,  buy/purchase/acquire,  create/make/build/generate/construct,
delete/remove/erase/destroy/eliminate,  error/bug/issue/problem/fault/defect,
fix/repair/resolve/patch/mend,  start/begin/launch/initiate/commence,
stop/end/halt/terminate/cease,  fast/quick/rapid/speedy/swift,
big/large/huge/enormous/massive,  small/tiny/little/miniature/minute,
... (292 total)
```

**Suffix stemming rules** (28 rules):
```
-ing → (remove),  -tion → (remove),  -sion → (remove),  -ment → (remove),
-ness → (remove),  -able → (remove),  -ible → (remove),  -ful → (remove),
-less → (remove),  -ous → (remove),  -ive → (remove),  -al → (remove),
-ly → (remove),  -er → (remove),  -est → (remove),  -ed → (remove),
-es → (remove),  -s → (remove if word > 3 chars), ...
```

---

## 8. Adaptive Threshold Tuning

The system automatically adjusts the similarity threshold per-tenant based on their usage patterns.

```python
def adapt_threshold(tenant_state: TenantState):
    """Called periodically after cache decisions."""
    
    current = tenant_state.sim_threshold  # default 0.72
    
    # If many near-misses cluster just below threshold → lower it
    # (queries that almost matched but were rejected)
    near_misses = count_scores_in_range(current - 0.05, current)
    if near_misses / total_queries > 0.50:
        current -= 0.02  # Let more through
    
    # If hit ratio is very low → lower threshold to catch more
    if hit_ratio < 0.25:
        current -= 0.015
    
    # If hit ratio is very high → raise threshold for precision
    if hit_ratio > 0.80:
        current += 0.01
    
    # Clamp to safe range
    tenant_state.sim_threshold = clamp(current, 0.50, 0.99)
```

### Per-Domain Thresholds

Different content domains have different precision requirements:

```python
domain_thresholds = {
    "finance":   0.78,  # Higher — "buy AAPL" vs "buy GOOG" must not match
    "legal":     0.78,  # Higher — contract terms require exact matching
    "medical":   0.78,  # Higher — medical advice must be precise
    "tech":      0.70,  # Lower — tech queries have more paraphrasing
    "education": 0.70,  # Lower — students ask the same thing many ways
    "general":   0.72,  # Default
}
```

### Domain Detection

Queries are auto-classified using keyword matching:

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

## 9. Multi-Tenancy & Isolation

### Tenant Identification

```
API Key format: sc-{tenant_slug}-{random_32_chars}

Example: sc-mycompany-a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6

Tenant slug extracted: "mycompany"
Internal tenant ID: "usr_{supabase_user_uuid}" (for users without org)
```

### Isolation Guarantees

| Layer | Isolation Method |
|-------|-----------------|
| **In-Memory** | Separate `TenantState` object per tenant (separate FAISS indexes, dicts, metrics) |
| **Redis** | Key prefix: `{tenant_id}:...` |
| **PostgreSQL** | `org_id` column on all tables + Row-Level Security (RLS) |
| **Pinecone** | Separate namespace per tenant |
| **FAISS** | Separate `IndexFlatIP`/`IndexIVFFlat` per tenant |
| **Metrics** | Separate counters per tenant |
| **Encryption** | Per-tenant derived encryption key (HKDF from master + tenant_id) |

### Organization Model

```
Organization
  ├── name, slug (unique identifier)
  ├── plan (free / pro / team)
  ├── settings (JSONB: threshold, TTL, domain overrides)
  ├── credits_balance (prepaid credit amount)
  │
  ├── Members
  │   ├── Owner (1, full control)
  │   ├── Admin (N, manage keys and settings)
  │   └── Member (N, use API keys)
  │
  └── API Keys
      ├── Key 1 (scope: read-write, no IP restriction)
      ├── Key 2 (scope: read-only, allowed_ips: ["1.2.3.4"])
      └── Key 3 (scope: admin, expires: 2025-12-31)
```

---

## 10. Authentication & Authorization

### Path A: API Key Bearer

```
Request: Authorization: Bearer sc-myorg-abc123def456...

Flow:
  1. Extract key from Authorization header
  2. Check LRU cache (10,000 entries, 300s TTL)
  3. Cache miss → query api_keys table in PostgreSQL
  4. Validate:
     - Key exists and is not revoked
     - Key has not expired (expires_at)
     - IP is in allowed_ips (if set)
     - Scope permits this operation
  5. Set request context: user_id, org_id, tenant_id, scope, plan
```

### Path B: Supabase JWT Bearer

```
Request: Authorization: Bearer eyJhbGciOiJFUzI1NiIs...

Flow:
  1. Extract JWT from Authorization header
  2. Fetch JWKS from Supabase URL (cached 10 minutes)
  3. Verify signature:
     - Try ES256/RS256 keys from JWKS first
     - Fallback to HS256 with SUPABASE_JWT_SECRET
  4. Check token expiration
  5. Extract user_id (sub claim)
  6. Lookup user profile and org membership in PostgreSQL
  7. Set request context: user_id, org_id, is_admin, email
```

### Admin Authorization

```
Admin endpoints require:
  1. Valid Supabase JWT (Path B)
  2. profiles.is_admin = true for the authenticated user
  
Admin capabilities:
  - View all users and organizations
  - Modify user plans and credits
  - View platform-wide analytics
  - System health monitoring
```

---

## 11. Encryption Architecture

### Layer 1: BYOK Key Storage (Fernet)

Users can store their own OpenAI API key. It's encrypted before database storage.

```
User submits: "sk-abc123..."
                │
                ▼
Key Derivation:
  PBKDF2HMAC(
    algorithm = SHA256,
    length = 32 bytes,
    salt = ENCRYPTION_SALT (env var),
    iterations = 100,000
  ) applied to ENCRYPTION_KEY (env var)
                │
                ▼
Fernet.encrypt(plaintext_key)
                │
                ▼
Stored in: profiles.openai_api_key_encrypted
```

**Fernet** provides:
- AES-128-CBC encryption
- HMAC-SHA256 authentication
- Timestamp-based token versioning

### Layer 2: Cache Entry Encryption (AES-256-GCM)

Cache entries (prompt text + response text) can be encrypted at rest.

```
Master Key: CACHE_ENCRYPTION_KEY (32 bytes, env var)
                │
                ▼
Per-Tenant Key Derivation:
  HKDF(
    algorithm = SHA256,
    length = 32 bytes,
    salt = b"semantys-cache-v1",
    info = tenant_id.encode()
  ) applied to Master Key
                │
                ▼
For each cache entry:
  nonce = os.urandom(12)            # 96-bit random nonce
  ciphertext, tag = AES-256-GCM.encrypt(plaintext, key, nonce)
  stored = "ENC:" + base64(nonce + ciphertext + tag)
```

**Format**: `"ENC:" + base64(nonce[12 bytes] + ciphertext[variable] + tag[16 bytes])`

**Per-tenant key derivation** ensures:
- Different tenants have different encryption keys
- Compromising one tenant's data doesn't affect others
- The master key never directly encrypts any data

---

## 12. Billing & Credits System

### Subscription Plans

| Plan | Price | Monthly Requests | Cache Entries | Starting Credits |
|------|-------|-----------------|---------------|-----------------|
| **Free** | $0/mo | 1,000 | 1,000 | $1.00 |
| **Pro** | $49/mo | 100,000 | 100,000 | $5.00 |
| **Team** | Custom | Unlimited | Unlimited | Custom |

### Credit Flow

```
New user signs up via Supabase Auth
        │
        ▼
PostgreSQL trigger fires:
  1. Create profiles row
  2. Create organizations row (slug = user UUID prefix)
  3. Insert $1.00 into credits_ledger
  4. Set credits_balance = $1.00
  5. Add user as org owner

User makes API call:
        │
        ▼
Cache HIT? → $0.00 charged (always free)
        │
Cache MISS? → Is BYOK? → $0.00 charged (user pays OpenAI directly)
        │
Not BYOK? → Calculate token cost:
  prompt_tokens × $0.20 / 1,000,000
  + completion_tokens × $0.80 / 1,000,000
  = cost_estimate
        │
        ▼
Deduct from credits_balance
  If balance ≤ 0 → HTTP 402 Payment Required
```

### Stripe Integration

```
Upgrade flow:
  User clicks "Upgrade to Pro"
        │
        ▼
  POST /api/billing/upgrade
        │
        ▼
  Backend creates Stripe Checkout Session
  (price_id, customer_email, success_url, cancel_url)
        │
        ▼
  User redirected to Stripe Checkout
        │
        ▼
  Payment succeeds → Stripe sends webhook
        │
        ▼
  POST /api/billing/webhook (signature-verified)
        │
        ▼
  Backend updates:
    - organizations.plan = "pro"
    - api_keys.plan = "pro"
    - credits_ledger += $5.00
    - organizations.credits_balance += $5.00
```

---

## 13. Frontend Architecture

### Application Structure

```
frontend/src/
├── App.tsx                    # Root: routing, auth provider, layout
├── contexts/
│   └── AuthContext.tsx         # Supabase auth state, login/signup/logout
├── api/
│   ├── semanticAPI.ts         # Cache/metrics/settings (fetch + Bearer token)
│   └── adminAPI.ts            # Admin endpoints (Axios + JWT interceptor)
├── pages/
│   ├── LandingPage.tsx        # Hero + Three.js animated background
│   ├── SignInPage.tsx          # Email/password login
│   ├── SignUpPage.tsx          # Registration + password strength
│   ├── PlaygroundPage.tsx      # Main chat UI (wrapper)
│   ├── MetricsPage.tsx         # KPI cards + savings dashboard
│   ├── LogsPage.tsx            # Event log table
│   ├── SettingsPage.tsx        # Billing + cache settings
│   ├── PricingPage.tsx         # Three-tier pricing cards
│   └── admin/
│       ├── AdminDashboard.tsx  # KPI cards, growth charts
│       ├── AdminUsers.tsx      # User management table
│       ├── AdminTopUsers.tsx   # Top users by usage
│       ├── AdminAnalytics.tsx  # Platform analytics
│       └── AdminSettings.tsx   # System health
├── components/
│   ├── QueryPlayground.tsx     # Chat UI: streaming, cache badges, history
│   ├── MarkdownRenderer.tsx    # Memoized markdown + syntax highlighting
│   ├── SettingsPanel.tsx       # API key, BYOK, threshold slider, TTL
│   ├── BillingSection.tsx      # Plan display, credits, upgrade buttons
│   ├── CacheWarmup.tsx         # Upload JSONL/JSON for cache seeding
│   ├── KpiCards.tsx            # 5 metric cards with auto-refresh
│   ├── SavingsDashboard.tsx    # 30-day savings summary
│   ├── LogsTable.tsx           # Sortable log table with CSV export
│   ├── Layout.tsx              # Sticky nav + health indicator + footer
│   ├── AdminLayout.tsx         # Admin sidebar + dark mode
│   ├── AccountMenu.tsx         # User dropdown: org switcher, API key, logout
│   ├── OnboardingWizard.tsx    # First-time user tutorial
│   ├── FloatingAssistant.tsx   # Help widget
│   ├── TubesBackground.tsx     # Three.js animated tubes (landing page)
│   └── DocsPage.tsx            # Full documentation page
└── lib/
    └── supabase.ts             # Supabase client initialization
```

### Authentication Flow

```
                   ┌─────────────────┐
                   │   App.tsx        │
                   │                  │
                   │  <AuthProvider>  │
                   │    <Router>      │
                   │      <Routes>    │
                   │    </Router>     │
                   │  </AuthProvider>  │
                   └────────┬─────────┘
                            │
              ┌─────────────▼─────────────┐
              │     AuthContext.tsx         │
              │                            │
              │  On mount:                 │
              │    supabase.auth           │
              │      .getSession()         │
              │      (3s timeout)          │
              │                            │
              │  Subscription:             │
              │    onAuthStateChange()     │
              │    → refresh tokens        │
              │    → update user state     │
              │                            │
              │  After login:              │
              │    GET /api/auth/me         │
              │    → user profile + orgs   │
              │                            │
              │    GET /api/keys/current    │
              │    → API key → localStorage│
              └───────────────────────────┘
```

### Key UI Components

**QueryPlayground** — Full chat interface:
- Streaming responses via SSE (`EventSource` pattern over fetch)
- Cache decision badges: `EXACT HIT` (green), `SEMANTIC HIT` (blue with similarity %), `MISS` (gray)
- Per-response metadata: latency, token count, confidence level
- Multi-turn conversation history (sent to backend for context)
- Model selector (gpt-4o-mini, gpt-4o, gpt-4-turbo)
- Temperature slider (0.0–1.0)
- Chat history persistence (50 conversations in localStorage)

**MetricsPage** — Real-time dashboard:
- 5 KPI cards: Hit Ratio, Semantic Hit Ratio, Avg Latency, Total Requests, Tokens Saved
- 30-day savings: cached requests, hit rate, estimated $ saved
- Auto-refresh every 15 seconds

**SettingsPanel** — Cache configuration:
- API key generate/copy
- BYOK key save/remove (encrypted)
- Similarity threshold slider (0.50–0.99)
- TTL input (1–90 days)
- Cache warmup upload (JSONL/JSON)

---

## 14. SDK Documentation

### Python SDK

**Package**: `semantys` on PyPI
**Install**: `pip install semantys`
**Source**: `sdk/python/`

#### Quick Start

```python
from semantys import SemantysCache

# Initialize with your API key
cache = SemantysCache(api_key="sc-myorg-xxxxxxxx")

# OpenAI-compatible interface (drop-in replacement)
response = cache.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "What is machine learning?"}],
    temperature=0.2,
)

print(response.choices[0].message.content)
print(f"Cache: {response.meta.hit}")          # "exact", "semantic", or "miss"
print(f"Similarity: {response.meta.similarity}")  # 0.0 to 1.0
print(f"Latency: {response.meta.latency_ms}ms")   # End-to-end latency
```

#### Streaming

```python
stream = cache.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Explain neural networks"}],
    stream=True,
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

#### Zero-Code Proxy Mode

```python
# No SDK needed! Use the standard OpenAI client with a different base_url
import openai

client = openai.OpenAI(
    base_url="https://api.semantys.ai/v1",
    api_key="sc-myorg-xxxxxxxx",
)

# All existing code works unchanged
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "What is ML?"}],
)
```

#### Convenience Methods

```python
# Simple query (non-OpenAI format)
result = cache.query("What is caching?", model="gpt-4o-mini")

# Health check
status = cache.health()

# Metrics
metrics = cache.metrics()  # Returns hit ratio, latency stats, etc.
```

#### Self-Hosted

```python
cache = SemantysCache(
    api_key="sc-myorg-xxxxxxxx",
    base_url="http://localhost:8000",  # Your own server
    timeout=30.0,                       # Custom timeout
    max_retries=5,                      # Custom retry count
)
```

#### OpenAI Fallback

If Semantys is unreachable, the SDK automatically falls back to direct OpenAI calls:

```python
# Install with fallback support
# pip install semantys[openai]

cache = SemantysCache(api_key="sc-myorg-xxxxxxxx")
# If api.semantys.ai is down → automatically calls OpenAI directly
# Response includes meta.strategy = "openai_fallback"
```

#### Class Reference

```python
class SemantysCache:
    """Main SDK client. Drop-in OpenAI replacement."""
    
    def __init__(
        self,
        api_key: str,                           # Required: sc-{tenant}-{...}
        base_url: str = "https://api.semantys.ai",  # Override for self-hosted
        timeout: float = 60.0,                   # Request timeout in seconds
        max_retries: int = 3,                    # Retry count for 429/5xx
    ): ...
    
    chat: _Chat
        completions: _Completions
            def create(
                *,
                model: str = "gpt-4o-mini",
                messages: List[Dict[str, str]],
                temperature: float = 0.2,
                stream: bool = False,
                ttl_seconds: int = 604800,       # 7 days default
                **kwargs,                         # Any OpenAI parameter
            ) -> ChatCompletion | Iterator[ChatCompletionChunk]: ...
    
    def query(prompt: str, model: str = "gpt-4o-mini") -> dict: ...
    def health() -> dict: ...
    def metrics() -> dict: ...
    def close() -> None: ...

class ChatCompletion:
    id: str
    object: str             # "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Optional[Usage]
    meta: Optional[CacheMeta]

class CacheMeta:
    hit: str                # "exact", "semantic", "miss", "fallback"
    similarity: float       # 0.0 to 1.0
    latency_ms: float       # End-to-end latency
    strategy: str           # "exact_match", "multi_signal_semantic", "miss", "openai_fallback"
```

### TypeScript SDK

**Package**: `semantys-cache` on npm
**Install**: `npm install semantys-cache`
**Source**: `sdk/typescript/`

#### Quick Start

```typescript
import { SemanticCache } from 'semantys-cache';

const cache = new SemanticCache({
    apiKey: 'sc-myorg-xxxxxxxx',
    baseUrl: 'https://api.semantys.ai',  // optional
});

// Query
const result = await cache.query('What is caching?');
console.log(result.answer, result.cacheHit, result.similarity);

// Health
const health = await cache.health();

// Metrics
const metrics = await cache.metrics();
```

#### OpenAI Proxy

```typescript
import { SemantysOpenAI } from 'semantys-cache/openai-proxy';

const client = new SemantysOpenAI({
    apiKey: 'sc-myorg-xxxxxxxx',
});

// Same interface as OpenAI SDK
const response = await client.chat.completions.create({
    model: 'gpt-4o-mini',
    messages: [{ role: 'user', content: 'What is ML?' }],
});
```

#### Features

- **Automatic retry**: Exponential backoff on 429/5xx (3 retries, 8s cap)
- **Typed errors**: `SemanticsError` class with status code and message
- **TypeScript types**: Full type definitions for all responses

---

## 15. Framework Integrations

### LangChain

```python
from semantys_integrations.langchain import SemantysLLM

llm = SemantysLLM(api_key="sc-myorg-xxx", model="gpt-4o-mini")

# Use as any LangChain LLM
response = llm.invoke("What is semantic caching?")

# Works with chains
from langchain.chains import LLMChain
chain = LLMChain(llm=llm, prompt=my_prompt)
result = chain.run("explain caching")
```

### LlamaIndex

```python
from semantys_integrations.llamaindex import SemantysLLM

llm = SemantysLLM(api_key="sc-myorg-xxx")

# Use as any LlamaIndex LLM
from llama_index.core import VectorStoreIndex
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine(llm=llm)
response = query_engine.query("What is caching?")
```

### FastAPI Middleware

```python
from fastapi import FastAPI
from semantys_integrations.fastapi import SemantysMiddleware

app = FastAPI()
app.add_middleware(SemantysMiddleware, api_key="sc-myorg-xxx")

# All /v1/chat/completions calls now go through Semantys cache
```

### Django Middleware

```python
# settings.py
MIDDLEWARE = [
    ...
    'semantys_integrations.django.SemantysMiddleware',
]

SEMANTYS_API_KEY = "sc-myorg-xxx"
SEMANTYS_BASE_URL = "https://api.semantys.ai"
```

### Express.js Middleware

```javascript
const { semantysCache } = require('semantys-cache/express');

app.use('/api/chat', semantysCache({
    apiKey: 'sc-myorg-xxx',
    baseUrl: 'https://api.semantys.ai',
}));
```

### AWS Lambda

```python
from semantys_integrations.lambda_handler import semantys_handler

@semantys_handler(api_key="sc-myorg-xxx")
def lambda_handler(event, context):
    # Queries are automatically cached
    return {"statusCode": 200, "body": "..."}
```

### RAG (Retrieval-Augmented Generation)

```python
from semantys_integrations.rag import SemantysRAG

rag = SemantysRAG(
    api_key="sc-myorg-xxx",
    context_weight=0.3,  # How much to weight context in cache key
)

# Context-aware caching: same question + different context = different cache entry
response = rag.query(
    question="What are the benefits?",
    context="Retrieved document about machine learning...",
)
```

### SQL / BI (Natural Language to SQL)

```python
from semantys_integrations.sql import SemantysSQLCache

sql_cache = SemantysSQLCache(
    api_key="sc-myorg-xxx",
    schema_hash="abc123",  # Include schema version in cache key
)

# Cache natural-language-to-SQL translations
result = sql_cache.query("Show me top 10 customers by revenue")
```

---

## 16. Monitoring & Observability

### Logging System

7 rotating log files, each 10MB max with 5 backup rotations:

| Logger | File | Content |
|--------|------|---------|
| `access` | access.log | Every HTTP request/response (method, path, status, timing) |
| `errors` | errors.log | Exceptions and stack traces |
| `semantic_ops` | semantic_ops.log | Cache decisions with full similarity scores |
| `performance` | performance.log | Embedding and LLM call timing |
| `security` | security.log | Auth failures, rate limit hits, IP blocks |
| `system` | system.log | Startup, shutdown, cache operations |
| `application` | application.log | Application-level events |

**Log format** (configurable via `LOG_FORMAT` env var):
- `"text"` — Human-readable: `2025-01-15 10:30:45 | INFO | cache hit for tenant myorg | similarity=0.87`
- `"json"` — Structured: `{"timestamp": "...", "level": "INFO", "message": "...", "tenant": "myorg", "similarity": 0.87}`

### Prometheus Metrics

```
# Cache performance
cache_requests_total{tenant, hit_type}          counter
cache_hits_total{tenant}                         counter
cache_misses_total{tenant}                       counter
cache_latency_seconds{tenant}                    histogram [0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
cache_entries_total{tenant}                      gauge
cache_hit_ratio{tenant}                          gauge

# API performance
api_requests_total{endpoint, method, status}     counter
api_latency_seconds{endpoint}                    histogram

# Token tracking
tokens_used_total{type}                          counter  (prompt, completion, total)
tokens_saved_total{tenant}                       counter
cost_estimate_total{tenant}                      counter
```

**Scrape endpoint**: `GET /prometheus/metrics`

### Custom Metrics Endpoint

`GET /metrics` (API key authenticated) returns:

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

### Kubernetes Monitoring Alerts

```yaml
# Alert: High 5xx error rate
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
  for: 5m
  
# Alert: High latency
- alert: HighLatency
  expr: histogram_quantile(0.95, rate(api_latency_seconds_bucket[5m])) > 2
  for: 5m

# Alert: Low cache hit ratio
- alert: LowCacheHitRatio
  expr: cache_hit_ratio < 0.3
  for: 15m

# Alert: High memory usage
- alert: HighMemoryUsage
  expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.9
  for: 5m

# Alert: Backend down
- alert: BackendDown
  expr: up{job="semantys-backend"} == 0
  for: 1m
```

---

## 17. Database Schema

### Entity Relationship Diagram

```
┌─────────────┐     ┌────────────────┐     ┌──────────────┐
│  profiles    │     │ organizations  │     │  org_members  │
│             │     │                │     │              │
│ id (PK,UUID)├──┐  │ id (PK, UUID)  │◄─┬──┤ org_id (FK)  │
│ email       │  │  │ name           │  │  │ user_id (FK) │
│ name        │  │  │ slug (unique)  │  │  │ role         │
│ company     │  └──┤                │  │  │  (owner/     │
│ is_admin    │     │ plan           │  │  │   admin/     │
│ openai_key* │     │ settings(JSON) │  │  │   member)    │
│ created_at  │     │ credits_balance│  │  └──────────────┘
└──────┬──────┘     └───────┬────────┘  │
       │                    │           │
       │     ┌──────────────┤           │
       │     │              │           │
┌──────▼─────▼──┐  ┌───────▼────────┐  │
│   api_keys    │  │ cache_entries   │  │
│               │  │                 │  │
│ api_key(uniq) │  │ id (PK)        │  │
│ tenant_id     │  │ org_id (FK)    ├──┘
│ user_id (FK)  │  │ prompt_hash    │
│ org_id (FK)   │  │ prompt_norm*   │
│ plan          │  │ response_text* │
│ scope         │  │ embedding      │
│ allowed_ips   │  │ model          │
│ expires_at    │  │ domain         │
│ usage_count   │  │ ttl_expires_at │
│ is_active     │  │ use_count      │
└───────────────┘  └────────────────┘

┌────────────────┐  ┌─────────────────┐
│  usage_logs    │  │  audit_logs     │
│                │  │                 │
│ id (PK)        │  │ id (PK)         │
│ tenant_id      │  │ org_id (FK)     │
│ org_id (FK)    │  │ user_id (FK)    │
│ endpoint       │  │ action          │
│ cache_hits     │  │ resource_type   │
│ cache_misses   │  │ details (JSON)  │
│ tokens_used    │  │ ip_address      │
│ cost_estimate  │  │ created_at      │
│ decision       │  └─────────────────┘
│ similarity     │
│ latency_ms     │  ┌─────────────────┐
│ tokens_saved   │  │ credits_ledger  │
│ is_byok        │  │                 │
│ created_at     │  │ id (PK)         │
└────────────────┘  │ org_id (FK)     │
                    │ amount (+/-)    │
                    │ balance_after   │
                    │ reason          │
                    │ created_at      │
                    └─────────────────┘

* = Encrypted with AES-256-GCM when CACHE_ENCRYPTION_KEY is set
```

### Row-Level Security (RLS)

All 8 tables have RLS enabled. Example policies:

```sql
-- profiles: users can only read/update their own profile
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view own profile"
  ON profiles FOR SELECT
  USING (auth.uid() = id);

-- organizations: members can view their org
CREATE POLICY "Members can view org"
  ON organizations FOR SELECT
  USING (id IN (SELECT org_id FROM org_members WHERE user_id = auth.uid()));

-- cache_entries: org-scoped access
CREATE POLICY "Org members can view cache"
  ON cache_entries FOR SELECT
  USING (org_id IN (SELECT org_id FROM org_members WHERE user_id = auth.uid()));
```

### Auto-Signup Trigger

```sql
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  -- 1. Create profile
  INSERT INTO profiles (id, email, name)
  VALUES (NEW.id, NEW.email, NEW.raw_user_meta_data->>'name');
  
  -- 2. Create organization
  INSERT INTO organizations (id, name, slug, plan, credits_balance)
  VALUES (gen_random_uuid(), NEW.email, substr(NEW.id::text, 1, 8), 'free', 1.00);
  
  -- 3. Add as owner
  INSERT INTO org_members (org_id, user_id, role)
  VALUES (org_id_from_above, NEW.id, 'owner');
  
  -- 4. Credit $1.00
  INSERT INTO credits_ledger (org_id, amount, balance_after, reason)
  VALUES (org_id_from_above, 1.00, 1.00, 'signup_bonus');
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION handle_new_user();
```

---

## 18. Deployment Architecture

### Current Production

```
GitHub (main branch)
       │
       ├──── Railway (auto-deploy on push)
       │       │
       │       └── FastAPI backend
       │           • 1 replica
       │           • us-west2
       │           • Environment variables for all secrets
       │           • Auto-restart on crash
       │
       └──── Vercel (auto-deploy on push)
               │
               └── React frontend
                   • CDN-distributed globally
                   • SPA routing via vercel.json
                   • Edge caching for static assets
```

### Docker Compose (Local/Production)

```yaml
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    env_file: backend/.env
    volumes:
      - cache_data:/app/cache_data
      - logs_data:/app/logs
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports: ["3000:80"]
    depends_on: [backend]
    restart: unless-stopped

volumes:
  cache_data:    # Persistent cache data
  logs_data:     # Persistent log files
```

### Kubernetes (Production-Scale)

```
┌─────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                     │
│                    Namespace: semantys                    │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │              Nginx Ingress Controller             │   │
│  │                                                   │   │
│  │  api.semantys.ai → backend service (port 8000)   │   │
│  │  app.semantys.ai → frontend service (port 80)    │   │
│  │                                                   │   │
│  │  TLS: Let's Encrypt (cert-manager)               │   │
│  └─────────────┬───────────────────┬─────────────────┘   │
│                │                   │                      │
│  ┌─────────────▼──────┐  ┌───────▼──────────────┐      │
│  │  Backend Deployment │  │ Frontend Deployment  │      │
│  │  2 replicas         │  │ 2 replicas           │      │
│  │                     │  │                      │      │
│  │  Resources:         │  │ Nginx serving        │      │
│  │   req: 250m CPU     │  │ static React build   │      │
│  │        512Mi RAM    │  │                      │      │
│  │   lim: 1 CPU       │  └──────────────────────┘      │
│  │        2Gi RAM      │                                 │
│  │                     │                                 │
│  │  Health checks:     │                                 │
│  │   readiness: /health│                                 │
│  │   (10s delay, 15s)  │                                 │
│  │   liveness: /health │                                 │
│  │   (30s delay, 30s)  │                                 │
│  │                     │                                 │
│  │  PVC: 5Gi cache_data│                                 │
│  └─────────────────────┘                                 │
│                                                          │
│  ┌──────────────────┐  ┌─────────────────────────┐      │
│  │  Redis Service   │  │  Monitoring Stack       │      │
│  │  (cache L2)      │  │                         │      │
│  │                  │  │  Prometheus              │      │
│  │                  │  │    ServiceMonitor        │      │
│  │                  │  │    AlertManager rules    │      │
│  │                  │  │                         │      │
│  └──────────────────┘  │  Fluent Bit             │      │
│                         │    DaemonSet            │      │
│                         │    Log aggregation      │      │
│                         └─────────────────────────┘      │
└──────────────────────────────────────────────────────────┘
```

---

## 19. Request Lifecycle (End-to-End)

A complete trace of a single `POST /v1/chat/completions` request:

```
1. CLIENT sends HTTPS request
   POST https://api.semantys.ai/v1/chat/completions
   Authorization: Bearer sc-myorg-abc123...
   Content-Type: application/json
   {"model": "gpt-4o-mini", "messages": [...], "temperature": 0.2}

2. MIDDLEWARE STACK
   2a. MaxBodySizeMiddleware checks body < 2MB                     [<1ms]
   2b. log_requests assigns UUID, starts timer                     [<1ms]
   2c. CORSMiddleware checks origin                                [<1ms]
   2d. slowapi rate limiter checks tenant limit (200/min)          [<1ms]

3. AUTHENTICATION
   3a. Extract "sc-myorg-abc123..." from Authorization header      [<1ms]
   3b. LRU cache lookup (10K entries, 300s TTL)                    [<1ms]
   3c. Cache hit → tenant_id="myorg", org_id=UUID, scope=rw       [<1ms]
   3d. Cache miss → PostgreSQL query → populate LRU cache          [5-20ms]

4. INPUT VALIDATION
   4a. Validate messages array (role, content, length)             [<1ms]
   4b. Extract last user message as query                          [<1ms]

5. CACHE ENGINE - TIER 1: Exact Match
   5a. normalize: lowercase, strip whitespace                      [<0.01ms]
   5b. TenantState.exact[prompt_norm] dict lookup                  [<0.01ms]
   5c. Not found → proceed to Tier 2

6. CACHE ENGINE - TIER 2: Normalized Hash
   6a. deep_normalize: contractions, abbreviations, synonyms       [<0.1ms]
   6b. TenantState.norm_hash_index[deep_norm] dict lookup          [<0.01ms]
   6c. Not found → proceed to Tier 3

7. CACHE ENGINE - TIER 3: Local Pre-Filter
   7a. all-MiniLM-L6-v2 encode(deep_normalized_text)              [~5ms]
   7b. FAISS local_index.search(embedding, k=3)                    [<1ms]
   7c. best_sim=0.62 >= 0.35 threshold → proceed to Tier 4

8. CACHE ENGINE - TIER 4: Semantic Search
   8a. Generate OpenAI embedding
       "Semantic meaning: {query}" → API call                      [30-100ms]
       → 1024-dim vector, L2-normalized
   8b. FAISS index.search(embedding, k=10)                         [<5ms]
       → 10 candidates with cosine similarities
   8c. For each candidate, compute 8 text similarity signals       [<1ms]
   8d. Hybrid score: 0.88 × cosine + 0.12 × text_sim             [<0.1ms]
   8e. Response index search for query-to-response boost           [<5ms]
   8f. Best candidate: cosine=0.87, hybrid=0.85, text_sim=0.72
   8g. Decision: cosine(0.87) >= threshold(0.72) + 0.10 → HIGH CONFIDENCE MATCH
   8h. Safety guards: entity_overlap=1.0 ✓, intent=same ✓, resp_sanity=0.65 ✓

9. CACHE HIT RESPONSE
   9a. Return cached response with metadata                        [<1ms]
   9b. Update last_used_at, increment use_count                    [async]
   9c. Log usage (decision="semantic", similarity=0.87)            [async]

10. TOTAL LATENCY: ~50ms (vs 1-18s for cache miss)
    COST: $0.00 (vs $0.01+ for LLM call)
```

---

## 20. Performance Characteristics

### Latency Breakdown

| Operation | Latency | Notes |
|-----------|---------|-------|
| Middleware stack | <1ms | Body size, CORS, rate limit |
| API key auth (cached) | <1ms | LRU cache hit |
| API key auth (miss) | 5–20ms | PostgreSQL query |
| Input validation | <1ms | Message format check |
| Exact hash match | <0.02ms | Python dict O(1) |
| Deep normalization | <0.1ms | String operations |
| Normalized hash match | <0.02ms | Python dict O(1) |
| Local embedding (MiniLM) | ~5ms | 22M params, CPU |
| Local FAISS search | <1ms | 384-dim, small index |
| OpenAI embedding API | 30–100ms | Network-bound |
| FAISS search (brute, <10K) | <5ms | 1024-dim, exhaustive |
| FAISS search (IVF, >10K) | <2ms | Clustered, O(√n) |
| 8-signal text similarity | <1ms | Pure CPU, no I/O |
| Cross-encoder re-rank | ~20ms | Optional, top-5 candidates |
| **Full semantic hit** | **~50ms** | **End-to-end** |
| **Full cache miss** | **1–18s** | **LLM API call** |

### Scaling Characteristics

| Metric | Value | Scaling Behavior |
|--------|-------|-----------------|
| Entries per tenant (brute force) | Up to 10,000 | O(n) search |
| Entries per tenant (IVF) | 10,000+ | O(√n) search, auto-upgrade |
| Concurrent requests | Limited by Uvicorn workers | Scale horizontally with K8s replicas |
| Background workers | 32 (ThreadPoolExecutor) | Handles async storage/logging |
| API key cache | 10,000 entries, 300s TTL | Avoids DB queries |
| Embedding cache | 1,000 entries (LRU) | Avoids duplicate OpenAI calls |
| JWKS cache | 10 min TTL | Avoids repeated JWKS fetches |

### Memory Footprint (per tenant)

| Data | Size per entry | 10K entries |
|------|---------------|-------------|
| OpenAI embedding (1024 × float32) | 4 KB | 40 MB |
| Local embedding (384 × float32) | 1.5 KB | 15 MB |
| Response embedding (1024 × float32) | 4 KB | 40 MB |
| CacheEntry metadata | ~2 KB | 20 MB |
| Dict keys (exact + normalized) | ~0.5 KB | 5 MB |
| **Total per tenant (10K entries)** | | **~120 MB** |

---

## Appendix: Environment Variables

### Required

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | Platform OpenAI key (fallback for non-BYOK users) |
| `DATABASE_URL` | Supabase PostgreSQL connection string |
| `ENCRYPTION_KEY` | Master key for Fernet encryption |
| `ENCRYPTION_SALT` | Salt for PBKDF2 key derivation |

### Optional

| Variable | Purpose | Default |
|----------|---------|---------|
| `REDIS_URL` | Redis connection for L2 cache | None (in-memory fallback) |
| `PINECONE_API_KEY` | Pinecone for L4 vector search | None (FAISS-only) |
| `PINECONE_INDEX_NAME` | Pinecone index name | None |
| `STRIPE_SECRET_KEY` | Stripe billing | None (billing disabled) |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook verification | None |
| `ADMIN_API_KEY` | Admin endpoint authentication | None |
| `SUPABASE_URL` | Supabase project URL | None |
| `SUPABASE_JWT_SECRET` | JWT verification fallback | None |
| `CACHE_ENCRYPTION_KEY` | AES-256-GCM master key (32 bytes) | None (no cache encryption) |
| `SENTRY_DSN` | Sentry error tracking | None |
| `RESEND_API_KEY` | Transactional emails | None |
| `LOG_FORMAT` | "text" or "json" | "text" |
| `PORT` | Server port | 8000 |
| `CROSS_ENCODER_ENABLED` | Enable cross-encoder re-ranking | false |
| `EMBED_DIMENSIONS` | OpenAI embedding dimensions | 1024 |
| `DB_MAX_CONNECTIONS` | PostgreSQL pool size | 10 |

---

*Semantys AI — Built for engineers who care about both performance and correctness.*
