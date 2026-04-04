# Semantys AI — SDK, Deployment & Configuration

## Python SDK

**Package**: `semantys-cache` on PyPI (v1.0.0)
**Install**: `pip install semantys-cache`
**Requirements**: Python 3.10+, dependencies: `httpx`, `attrs`, `python-dateutil`

### Drop-in OpenAI Replacement (Zero Code Changes)

```python
# Before (OpenAI direct)
from openai import ChatCompletion
response = ChatCompletion.create(model="gpt-4o-mini", messages=[...])

# After (Semantys — just change the import + add API key)
from semantys_cache import ChatCompletion
response = ChatCompletion.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "What is caching?"}],
    api_key="sc-myapp-abc123",
    base_url="https://api.semantys.ai"
)
# Response includes: response.answer, response.cache_hit, response.similarity
```

### Full Client Usage

```python
from semantys_cache import SemanticCache

cache = SemanticCache(api_key="sc-myapp-abc123", base_url="https://api.semantys.ai")

# Method 1: Simple query
result = cache.query("What is machine learning?", model="gpt-4o-mini")
print(result.answer, result.cache_hit, result.similarity)

# Method 2: OpenAI-compatible chat completions
result = cache.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "What is machine learning?"}]
)
```

### Architecture
- `SemanticCache` — primary client, wraps auto-generated OpenAPI HTTP client
- `ChatCompletion` — static `.create()` class mirroring old `openai.ChatCompletion.create()` signature
- `semantys_cache/integrations/` — pre-built wrappers for LangChain, LlamaIndex, FastAPI, Django, Express, Lambda, RAG, SQL

---

## TypeScript SDK

**Package**: `semantys-cache` on npm (v1.0.0)
**Install**: `npm install semantys-cache`
**Dependencies**: `axios ^1.6.0`, full TypeScript definitions included

### Usage

```typescript
import { SemanticCache } from 'semantys-cache';

const cache = new SemanticCache({
  apiKey: 'sc-myapp-abc123',
  baseUrl: 'https://api.semantys.ai'
});

// Simple query
const result = await cache.query('What is caching?');
console.log(result.answer, result.cacheHit, result.similarity);

// OpenAI-compatible (dot-path matches OpenAI SDK)
const response = await cache.chat.completions.create({
  model: 'gpt-4o-mini',
  messages: [{ role: 'user', content: 'What is caching?' }]
});
```

### OpenAI Proxy (Full Drop-in)

```typescript
import { SemantysOpenAI } from 'semantys-cache/openai-proxy';

const client = new SemantysOpenAI({
  apiKey: 'sc-myapp-abc123',
  baseUrl: 'https://api.semantys.ai'
});

// Identical interface to official openai npm package
const response = await client.chat.completions.create({
  model: 'gpt-4o-mini',
  messages: [{ role: 'user', content: 'Hello' }]
});
```

### Features
- Automatic retry with exponential backoff (3 retries, 8s cap) on 429/5xx
- Typed `SemantysError` class with `.status` and `.code`
- Health check: `cache.health()`
- Metrics: `cache.getMetrics()`

---

## Available Integrations

| Integration | Path | Description |
|-------------|------|-------------|
| **LangChain** | `sdk/integrations/langchain/` | LangChain wrapper with config options |
| **LlamaIndex** | `sdk/integrations/llamaindex/` | LlamaIndex wrapper with config options |
| **FastAPI** | `sdk/integrations/fastapi/` | FastAPI middleware (two usage patterns) |
| **Django** | `sdk/integrations/django/` | Django middleware via settings.py |
| **Express** | `sdk/integrations/express/` | Express.js middleware |
| **AWS Lambda** | `sdk/integrations/lambda/` | Lambda handler + API Gateway config |
| **RAG** | `sdk/integrations/rag/` | RAG-specific cache with context-aware queries |
| **SQL/BI** | `sdk/integrations/sql/` | Natural-language SQL cache with schema-aware queries |

---

## Docker Deployment

### docker-compose.yml

Two services:

```yaml
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    env_file: backend/.env
    volumes:
      - cache_data:/app/cache_data
      - logs_data:/app/logs

  frontend:
    build: ./frontend
    ports: ["3000:80"]  # nginx serves built React app
    depends_on: [backend]
    # VITE_* vars baked at build time via build args
```

### Running Locally

```bash
# 1. Set up environment
cp backend/.env.example backend/.env
# Edit backend/.env with your keys

cp frontend/.env.example frontend/.env
# Edit frontend/.env

# 2. Start services
docker-compose up --build

# Backend: http://localhost:8000
# Frontend: http://localhost:3000
```

---

## Kubernetes Deployment

All resources in namespace `semantys`. Images from `ghcr.io/sathvik-mn/`.

### Architecture

```
                    ┌─────────────────────────────┐
                    │    nginx Ingress Controller   │
                    │    (Let's Encrypt TLS)        │
                    ├──────────────┬────────────────┤
                    │              │                │
          api.semantys.ai    app.semantys.ai       │
                    │              │                │
                    ▼              ▼                │
              ┌──────────┐  ┌──────────┐           │
              │ backend  │  │ frontend │           │
              │ (2 pods) │  │ (2 pods) │           │
              │ port 8000│  │ port 80  │           │
              └────┬─────┘  └──────────┘           │
                   │                                │
              ┌────▼─────┐                          │
              │  Redis   │                          │
              │ (1 pod)  │                          │
              │ 256mb    │                          │
              └──────────┘                          │
                                                    │
              External: Supabase PostgreSQL          │
              External: Pinecone (optional)          │
              External: Stripe (optional)            │
              └─────────────────────────────────────┘
```

### Manifests

| File | Resources |
|------|-----------|
| `k8s/namespace.yml` | Namespace `semantys` |
| `k8s/backend.yml` | Deployment (2 replicas, 1 CPU / 2Gi), Service (ClusterIP:8000), PVC (5Gi) |
| `k8s/frontend.yml` | Deployment (2 replicas, 200m CPU / 128Mi), Service (ClusterIP:80) |
| `k8s/redis.yml` | Deployment (1 replica, 256mb, allkeys-lru), Service (redis-svc:6379), PVC (1Gi) |
| `k8s/ingress.yml` | nginx ingress, TLS (Let's Encrypt), `api.semantys.ai` → backend, `app.semantys.ai` → frontend |
| `k8s/monitoring.yml` | Prometheus ServiceMonitor, 5 alert rules (error rate, latency, hit ratio, memory, downtime) |
| `k8s/logging.yml` | Fluent Bit ConfigMap (stdout JSON, optional Elasticsearch/Loki output) |
| `k8s/secrets.yml.example` | Template for 10 base64-encoded secrets |

### Prometheus Alerts

| Alert | Condition | Severity |
|-------|-----------|----------|
| HighErrorRate | >5% 5xx for 5 min | critical |
| HighLatency | P95 > 10s for 5 min | warning |
| LowCacheHitRatio | <30% for 30 min | warning |
| HighMemoryUsage | >3GB for 10 min | warning |
| BackendDown | Unreachable for 2 min | critical |

---

## All Environment Variables

### Backend — Required

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string (Supabase) |
| `SUPABASE_URL` | Supabase project URL (for JWKS auth) |
| `SUPABASE_JWT_SECRET` | Fallback HS256 JWT secret |
| `OPENAI_API_KEY` | Server-side OpenAI key (fallback for non-BYOK users) |
| `ENCRYPTION_KEY` | Fernet key for BYOK OpenAI key encryption |
| `ENCRYPTION_SALT` | PBKDF2 salt (16-byte hex, required in production) |

### Backend — Optional

| Variable | Default | Purpose |
|----------|---------|---------|
| `PORT` | `8000` | Server listen port |
| `ALLOWED_ORIGINS` | `localhost:3000,localhost:5173` | CORS origins (comma-separated) |
| `FRONTEND_URL` | `http://localhost:3000` | Stripe redirect, email links |
| `ADMIN_API_KEY` | — | Static admin API key |
| `REDIS_URL` | — | Redis connection string (L2 cache) |
| `DB_MAX_CONNECTIONS` | `25` | PostgreSQL pool size |
| `CACHE_ENCRYPTION_KEY` | — | AES-256-GCM master key for cache at-rest encryption |

### Backend — Embedding & Model Tuning

| Variable | Default | Purpose |
|----------|---------|---------|
| `EMBED_MODEL` | `text-embedding-3-small` | OpenAI embedding model |
| `EMBED_DIMENSIONS` | `1024` | Embedding vector dimensions |
| `CHAT_MODEL` | `gpt-4o-mini` | Default LLM for cache misses |
| `LOCAL_EMBED_MODEL` | `all-MiniLM-L6-v2` | Local sentence-transformers model |
| `LOCAL_EMBED_ENABLED` | `true` | Enable local embedding pre-filter |
| `CROSS_ENCODER_MODEL` | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Cross-encoder reranking model |
| `CROSS_ENCODER_ENABLED` | `false` | Enable cross-encoder reranking |
| `IVF_UPGRADE_THRESHOLD` | `10000` | Entries threshold to upgrade FAISS from Flat to IVF |

### Backend — Stripe (optional)

| Variable | Purpose |
|----------|---------|
| `STRIPE_SECRET_KEY` | Stripe API key (billing disabled if not set) |
| `STRIPE_WEBHOOK_SECRET` | Webhook signature verification |
| `STRIPE_PRICE_PRO` | Stripe Price ID for Pro plan |

### Backend — Observability (optional)

| Variable | Default | Purpose |
|----------|---------|---------|
| `SENTRY_DSN` | — | Sentry error tracking |
| `SENTRY_TRACES_SAMPLE_RATE` | `0.1` | Performance tracing rate |
| `SENTRY_PROFILES_SAMPLE_RATE` | `0.1` | Profiling rate |
| `ENVIRONMENT` | `development` | Reported to Sentry |
| `LOG_FORMAT` | `text` | `text` or `json` for structured logging |

### Backend — Vector Store (optional)

| Variable | Purpose |
|----------|---------|
| `PINECONE_API_KEY` | Pinecone API key |
| `PINECONE_INDEX_NAME` | Pinecone index name |
| `PINECONE_HOST` | Pinecone host URL |

### Frontend (Vite build-time)

| Variable | Default | Purpose |
|----------|---------|---------|
| `VITE_BACKEND_URL` | `http://localhost:8000` | Backend API URL |
| `VITE_SUPABASE_URL` | — | Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | — | Supabase public key |
| `VITE_SENTRY_DSN` | — | Frontend Sentry DSN |
| `VITE_POSTHOG_KEY` | — | PostHog analytics key |
| `VITE_POSTHOG_HOST` | `https://us.i.posthog.com` | PostHog ingest host |

---

## Local Development Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL (Supabase account)
- OpenAI API key

### Quick Start

```bash
# 1. Clone
git clone https://github.com/sathvik-mn/Semantys-AI.git
cd Semantys-AI

# 2. Backend
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your keys
python semantic_cache_server.py
# Backend running at http://localhost:8000

# 3. Frontend (new terminal)
cd frontend
npm install
cp .env.example .env
# Edit .env
npm run dev
# Frontend running at http://localhost:5173

# 4. Run Supabase schema
# Execute supabase_schema.sql against your Supabase project
```

### First-Time Setup
1. Create a Supabase project → get URL, anon key, JWT secret, database URL
2. Run `backend/supabase_schema.sql` in Supabase SQL editor
3. Set up `.env` files for both backend and frontend
4. Start both services
5. Sign up at `/signup` → verify email → sign in
6. The auto-signup trigger creates your profile, org, and starting credits
