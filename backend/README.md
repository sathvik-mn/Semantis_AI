# Semantys AI - Semantic Cache Backend

A production-ready FastAPI service providing semantic caching for LLM applications with multi-tenant support.

## Features

- **Multi-tenant API-key authentication** (Bearer `sc-{tenant}-{any}`)
- **Hybrid caching**: Exact + semantic (FAISS cosine similarity)
- **Adaptive threshold**: Per-tenant similarity threshold adjustment
- **Rotating logs**: Access, errors, and semantic operations
- **OpenAI integration**: text-embedding-3-large embeddings + gpt-4o-mini chat
- **OpenAI-compatible API**: POST `/v1/chat/completions` + simple GET `/query`

## Quick Start

### 1. Setup Environment

```bash
# From repo root
cd backend

# Create & activate virtual environment
python -m venv .venv

# Windows:
.venv\Scripts\activate

# Mac/Linux:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Key

```bash
# Copy example file
copy .env.example .env

# Edit .env and set your OpenAI API key
# OPENAI_API_KEY=sk-your-actual-key-here
```

### 3. Run Server

```bash
python semantic_cache_server.py
```

Server will start on `http://localhost:8000` (or PORT from .env)

## API Endpoints

### Health Check
```bash
GET /health
```

### Get Cache Metrics
```bash
GET /metrics
Authorization: Bearer sc-devA-anything
```

### Simple Query
```bash
GET /query?prompt=What is Python?
Authorization: Bearer sc-devA-anything
```

### OpenAI-Compatible Chat
```bash
POST /v1/chat/completions
Authorization: Bearer sc-devA-anything
Content-Type: application/json

{
  "model": "gpt-4o-mini",
  "messages": [
    {"role": "user", "content": "What is semantic caching?"}
  ],
  "temperature": 0.2,
  "ttl_seconds": 604800
}
```

## Authentication

Use API keys in format: `Bearer sc-{tenant}-{anything}`

Example: `Bearer sc-prod-abc123`

The tenant ID is extracted from the key and used for isolated caching.

## Cache Strategy

1. **Exact match**: Normalized text lookup (fastest)
2. **Semantic match**: FAISS cosine similarity search (threshold: 0.83 default)
3. **Miss**: Call LLM, store embeddings and response

Cache entries expire based on TTL (default: 7 days).

## Logs

Rotating logs in `logs/` directory:
- `access.log`: Request/response logging
- `errors.log`: Error tracking
- `semantic_ops.log`: Cache hit/miss operations

## Testing

Run the automated test suite:

```bash
cd backend
python test_api.py
```

Expected output:
```
=== SEMANTYS AI BACKEND TEST SUITE ===
✅ /health: 200 {'status': 'ok', 'service': 'semantic-cache', 'version': '0.1.0'}
✅ /metrics: 200 {'tenant': 'test', 'hit_ratio': 0.0, ...}

🧠 Querying: What is Python in 10 words?
✅ /query => miss | sim=0.000 | latency=4523.11ms

🧠 Querying: Explain Python in 10 words.
✅ /query => semantic | sim=0.916 | latency=947.68ms

🧠 Querying: What is the capital of France?
✅ /query => miss | sim=0.000 | latency=3254.69ms
```

This verifies:
- ✅ Exact cache hits (0.02ms latency)
- ✅ Semantic cache hits (FAISS similarity)
- ✅ Cache misses (LLM fallback)
- ✅ Logging and metrics tracking

## Configuration

Environment variables (`.env`):
- `OPENAI_API_KEY`: **Required** - Your OpenAI API key
- `PORT`: Optional - Server port (default: 8000)

## OpenAPI Documentation

The API includes full OpenAPI 3.1.0 specification with:
- ✅ **Security Schemes**: Bearer authentication with `sc-{tenant}-{anything}` format
- ✅ **Auto-generated docs**: Available at `http://localhost:8000/docs`
- ✅ **OpenAPI JSON**: Available at `http://localhost:8000/openapi.json`
- ✅ **SDK Generator Ready**: Compatible with Postman, TestSprite, and other OpenAPI tools

### View Documentation
Visit `http://localhost:8000/docs` in your browser for interactive Swagger UI.

## Dependencies

- `fastapi`: Web framework
- `uvicorn`: ASGI server
- `openai`: OpenAI API client
- `faiss-cpu`: Vector similarity search
- `numpy`: Numerical operations
- `pydantic`: Data validation
- `python-dotenv`: Environment management

## License

MIT

