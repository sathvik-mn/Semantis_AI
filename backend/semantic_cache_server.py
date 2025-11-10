"""
Semantis AI - Semantic Cache API (Plug & Play)

Repo: Semantis_AI
Folder: backend/

FastAPI service providing:
 - Multi-tenant API-key auth (Bearer sc-{tenant}-{any})
 - Exact + semantic cache (FAISS cosine)
 - Adaptive per-tenant threshold
 - Rotating logs (access/errors/semantic_ops)
 - OpenAI integration
 - OpenAI-like POST /v1/chat/completions + simple GET /query
"""

import os, time, re, logging, hashlib
from logging.handlers import RotatingFileHandler
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
import faiss
from fastapi import FastAPI, Request, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel
from dotenv import load_dotenv

# -----------------------------
# Environment & OpenAI client
# -----------------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-REPLACE_ME")
if not OPENAI_API_KEY or OPENAI_API_KEY == "sk-REPLACE_ME":
    print("⚠️  OPENAI_API_KEY is not set. Set it in backend/.env or OS env.")

# openai python (responses-compatible style kept for portability)
import openai
openai.api_key = OPENAI_API_KEY

EMBED_MODEL = "text-embedding-3-large"
CHAT_MODEL  = "gpt-4o-mini"

# -----------------------------
# Logging setup (rotating)
# -----------------------------
os.makedirs("logs", exist_ok=True)

def make_rotating_logger(name: str, filename: str, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    handler = RotatingFileHandler(
        os.path.join("logs", filename), maxBytes=5_000_000, backupCount=3
    )
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(message)s", datefmt="%Y-%m-%dT%H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    # Also stream to stdout for dev visibility
    stream = logging.StreamHandler()
    stream.setFormatter(formatter)
    logger.addHandler(stream)
    return logger

access_log   = make_rotating_logger("access", "access.log", logging.INFO)
error_log    = make_rotating_logger("errors", "errors.log", logging.ERROR)
semantic_log = make_rotating_logger("semantic", "semantic_ops.log", logging.INFO)

# -----------------------------
# Domain heuristics (optional)
# -----------------------------
DOMAIN_MAP = {
    "finance":   ["stock", "market", "inflation", "interest", "portfolio"],
    "legal":     ["contract", "clause", "law", "liability", "nda"],
    "tech":      ["api", "python", "vector", "fastapi", "kubernetes", "embedding"],
    "geography": ["capital", "country", "city", "border"],
}

def domain_hint(text: str) -> str:
    t = text.lower()
    best, hits = "general", 0
    for d, kws in DOMAIN_MAP.items():
        score = sum(1 for k in kws if k in t)
        if score > hits:
            best, hits = d, score
    return best

# -----------------------------
# Embeddings & LLM
# -----------------------------
def get_embedding(text: str) -> np.ndarray:
    """Return L2-normalized embedding vector."""
    resp = openai.embeddings.create(model=EMBED_MODEL, input=text)
    v = np.array(resp.data[0].embedding, dtype="float32")
    v /= (np.linalg.norm(v) + 1e-12)
    return v

def call_llm(messages: List[dict], temperature: float = 0.2) -> str:
    """Minimal OpenAI chat call wrapper."""
    resp = openai.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        temperature=temperature,
    )
    return resp.choices[0].message.content.strip()

# -----------------------------
# Cache data models
# -----------------------------
@dataclass
class CacheEntry:
    prompt_norm: str
    response_text: str
    embedding: np.ndarray
    model: str
    ttl_seconds: int
    created_at: float = field(default_factory=time.time)
    last_used_at: float = field(default_factory=time.time)
    use_count: int = 0
    domain: str = "general"
    strategy: str = "miss"  # exact | semantic | miss

    def fresh(self) -> bool:
        return (time.time() - self.created_at) < self.ttl_seconds

@dataclass
class CacheEvent:
    timestamp: str
    tenant_id: str
    prompt_hash: str
    decision: str  # "exact", "semantic", "miss"
    similarity: float
    latency_ms: float

@dataclass
class TenantState:
    exact: Dict[str, CacheEntry] = field(default_factory=dict)
    index: Optional[faiss.IndexFlatIP] = None
    rows: List[CacheEntry] = field(default_factory=list)
    dim: Optional[int] = None
    # metrics
    hits: int = 0
    misses: int = 0
    semantic_hits: int = 0
    latencies_ms: List[float] = field(default_factory=list)
    # adaptive similarity threshold (lowered default for better semantic matching and typo tolerance)
    sim_threshold: float = 0.72  # Lowered from 0.78 to 0.72 for better matching of similar queries and typos
    # events log
    events: List[CacheEvent] = field(default_factory=list)

# -----------------------------
# Core semantic cache service
# -----------------------------
class SemanticCacheService:
    def __init__(self):
        self.tenants: Dict[str, TenantState] = {}
        # Load cache from disk if available
        self._load_cache()
    
    def _load_cache(self):
        """Load cache from disk on startup."""
        try:
            from cache_persistence import load_cache
            loaded_tenants = load_cache()
            if loaded_tenants:
                self.tenants.update(loaded_tenants)
                print(f"Loaded cache for {len(loaded_tenants)} tenant(s) from disk")
        except Exception as e:
            print(f"Could not load cache from disk: {e}")
    
    def _save_cache(self):
        """Save cache to disk periodically."""
        try:
            from cache_persistence import save_cache
            save_cache(self.tenants)
        except Exception as e:
            print(f"Could not save cache to disk: {e}")

    def tenant(self, tenant_id: str) -> TenantState:
        if tenant_id not in self.tenants:
            self.tenants[tenant_id] = TenantState()
        return self.tenants[tenant_id]

    @staticmethod
    def norm_text(s: str) -> str:
        """Normalize text for exact matching. Preserves semantic meaning better."""
        # Remove extra whitespace and convert to lowercase
        s = " ".join(s.strip().split()).lower()
        # Remove common articles and prepositions for better matching
        # But keep them for semantic matching (handled separately)
        return s

    def _faiss_add(self, T: TenantState, emb: np.ndarray):
        v = emb.astype("float32").reshape(1, -1)
        faiss.normalize_L2(v)
        if T.index is None:
            T.dim = v.shape[1]
            T.index = faiss.IndexFlatIP(T.dim)
        T.index.add(v)

    def _faiss_search(self, T: TenantState, emb: np.ndarray, k: int = 1) -> Tuple[int, float]:
        """Search FAISS index. Returns (index, similarity)."""
        q = emb.astype("float32").reshape(1, -1)
        faiss.normalize_L2(q)
        k = min(k, len(T.rows))  # Don't search more than available
        sims, idxs = T.index.search(q, k)
        if k == 1:
            return int(idxs[0][0]), float(sims[0][0])
        # Return best match
        best_idx = int(idxs[0][0])
        best_sim = float(sims[0][0])
        return best_idx, best_sim
    
    def _faiss_search_top_k(self, T: TenantState, emb: np.ndarray, k: int = 3) -> List[Tuple[int, float]]:
        """Search FAISS index and return top k matches. Returns list of (index, similarity)."""
        q = emb.astype("float32").reshape(1, -1)
        faiss.normalize_L2(q)
        search_k = min(k, len(T.rows))
        if search_k == 0:
            return []
        sims, idxs = T.index.search(q, search_k)
        results = []
        for i in range(search_k):
            idx_val = int(idxs[0][i])
            sim_val = float(sims[0][i])
            if idx_val >= 0 and idx_val < len(T.rows):  # Valid index
                results.append((idx_val, sim_val))
        return results

    def query(
        self,
        tenant_id: str,
        prompt_norm: str,
        messages: List[dict],
        model: str,
        ttl_seconds: int = 7 * 24 * 3600,
        temperature: float = 0.2,
    ) -> Tuple[str, dict]:

        T = self.tenant(tenant_id)
        t0 = time.time()
        prompt_hash = hashlib.md5(prompt_norm.encode()).hexdigest()

        # 1) exact
        if prompt_norm in T.exact:
            entry = T.exact[prompt_norm]
            if entry.fresh() and entry.model == model:
                entry.use_count += 1
                entry.last_used_at = time.time()
                T.hits += 1
                latency = round((time.time() - t0) * 1000, 2)
                T.latencies_ms.append(latency)
                meta = {"hit": "exact", "similarity": 1.0, "latency_ms": latency, "strategy": "hybrid"}
                semantic_log.info(f"{tenant_id} | exact | sim=1.000 | key={prompt_norm[:80]}")
                # Store event
                T.events.append(CacheEvent(
                    timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
                    tenant_id=tenant_id,
                    prompt_hash=prompt_hash,
                    decision="exact",
                    similarity=1.0,
                    latency_ms=latency
                ))
                # Keep only last 1000 events
                if len(T.events) > 1000:
                    T.events = T.events[-1000:]
                return entry.response_text, meta

        # 2) semantic - improved matching with top-k search and typo tolerance
        if T.index is not None and len(T.rows) > 0:
            user_text = " ".join([m["content"] for m in messages if m.get("role") == "user"]) or prompt_norm
            emb = get_embedding(user_text)
            # Search top 5 matches and use the best one that meets threshold
            top_matches = self._faiss_search_top_k(T, emb, k=min(5, len(T.rows)))
            best_idx = None
            best_sim = 0.0
            
            # Find best match from top-K results
            for idx, sim in top_matches:
                if idx < len(T.rows) and T.rows[idx].fresh() and sim > best_sim:
                    best_sim = sim
                    best_idx = idx
            
            # Use adaptive threshold with typo tolerance
            # Base threshold: lower for small caches to catch typos better
            if len(T.rows) < 10:
                base_threshold = max(0.70, T.sim_threshold)  # Very lenient for small cache
            elif len(T.rows) < 20:
                base_threshold = max(0.72, T.sim_threshold)  # Lenient for medium cache
            else:
                base_threshold = T.sim_threshold  # Standard for larger cache
            
            adaptive_threshold = base_threshold
            
            # Typo tolerance: be more lenient for very similar queries
            if best_idx is not None and best_sim > 0:
                if best_sim >= adaptive_threshold:
                    # Normal match - above threshold
                    pass
                elif best_sim >= 0.65:  # Very lenient for typos
                    # Typo tolerance: accept if similarity is 0.65+ (very similar)
                    # This handles typos like "comptr" vs "computer", "iz" vs "is"
                    adaptive_threshold = max(0.65, best_sim - 0.02)  # Lower threshold to just below similarity
                    semantic_log.info(f"{tenant_id} | typo-tolerance | sim={best_sim:.3f} | threshold-adjusted-to={adaptive_threshold:.3f}")
                else:
                    # Too low similarity, skip semantic match
                    best_idx = None
                    best_sim = 0.0
            
            if best_idx is not None and best_sim >= adaptive_threshold:
                entry = T.rows[best_idx]
                entry.use_count += 1
                entry.last_used_at = time.time()
                T.hits += 1
                T.semantic_hits += 1
                latency = round((time.time() - t0) * 1000, 2)
                T.latencies_ms.append(latency)
                meta = {"hit": "semantic", "similarity": round(best_sim, 4), "latency_ms": latency, "strategy": "hybrid", "threshold_used": round(adaptive_threshold, 3)}
                semantic_log.info(f"{tenant_id} | semantic | sim={best_sim:.3f} | threshold={adaptive_threshold:.3f} | key={prompt_norm[:80]}")
                # Store event
                T.events.append(CacheEvent(
                    timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
                    tenant_id=tenant_id,
                    prompt_hash=prompt_hash,
                    decision="semantic",
                    similarity=round(best_sim, 4),
                    latency_ms=latency
                ))
                # Keep only last 1000 events
                if len(T.events) > 1000:
                    T.events = T.events[-1000:]
                return entry.response_text, meta

        # 3) miss → call LLM & insert
        T.misses += 1
        response_text = call_llm(messages, temperature=temperature)
        user_text = " ".join([m["content"] for m in messages if m.get("role") == "user"]) or prompt_norm
        emb = get_embedding(user_text)
        entry = CacheEntry(
            prompt_norm=prompt_norm,
            response_text=response_text,
            embedding=emb,
            model=model,
            ttl_seconds=ttl_seconds,
            domain=domain_hint(user_text),
            strategy="miss",
        )
        T.exact[prompt_norm] = entry
        T.rows.append(entry)
        self._faiss_add(T, emb)

        latency = round((time.time() - t0) * 1000, 2)
        T.latencies_ms.append(latency)
        semantic_log.info(f"{tenant_id} | miss | sim=0.000 | key={prompt_norm[:80]}")
        meta = {"hit": "miss", "similarity": 0.0, "latency_ms": latency, "strategy": "hybrid"}
        # Store event
        T.events.append(CacheEvent(
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
            tenant_id=tenant_id,
            prompt_hash=prompt_hash,
            decision="miss",
            similarity=0.0,
            latency_ms=latency
        ))
        # Keep only last 1000 events
        if len(T.events) > 1000:
            T.events = T.events[-1000:]
        
        # Periodically save cache to disk (every 10 new entries)
        if len(T.rows) % 10 == 0:
            self._save_cache()
        
        return response_text, meta

    def metrics(self, tenant_id: str) -> dict:
        T = self.tenant(tenant_id)
        total = T.hits + T.misses
        p50 = np.percentile(T.latencies_ms, 50) if T.latencies_ms else 0
        p95 = np.percentile(T.latencies_ms, 95) if T.latencies_ms else 0
        avg_latency = np.mean(T.latencies_ms) if T.latencies_ms else 0
        semantic_hit_ratio = (T.semantic_hits / total) if total > 0 else 0.0
        # Estimate tokens saved (rough estimate: 100 tokens per miss saved)
        tokens_saved_est = T.hits * 100  # Rough estimate
        return {
            "tenant": tenant_id,
            "requests": total,
            "hits": T.hits,
            "semantic_hits": T.semantic_hits,
            "misses": T.misses,
            "hit_ratio": round((T.hits / total) if total else 0.0, 3),
            "semantic_hit_ratio": round(semantic_hit_ratio, 3),
            "total_requests": total,
            "avg_latency_ms": round(float(avg_latency), 2),
            "tokens_saved_est": tokens_saved_est,
            "sim_threshold": round(T.sim_threshold, 3),
            "entries": len(T.rows),
            "p50_latency_ms": round(float(p50), 2),
            "p95_latency_ms": round(float(p95), 2),
        }

    def adapt_threshold(self, tenant_id: str):
        """Gently adjust sim threshold based on hit ratio when traffic is non-trivial."""
        T = self.tenant(tenant_id)
        total = T.hits + T.misses
        if total < 20:
            return
        hit_ratio = T.hits / total
        if hit_ratio < 0.55:
            T.sim_threshold = max(0.70, T.sim_threshold - 0.01)
        elif hit_ratio > 0.85:
            T.sim_threshold = min(0.92, T.sim_threshold + 0.01)

svc = SemanticCacheService()

# Save cache on shutdown
import atexit
atexit.register(lambda: svc._save_cache())

# -----------------------------
# FastAPI app + middleware
# -----------------------------
app = FastAPI(title="Semantis AI - Semantic Cache API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define API Key Header
api_key_header = APIKeyHeader(
    name="Authorization",
    scheme_name="BearerAuth",
    description="Use format: Bearer sc-{tenant}-{anything}",
    auto_error=False,
)

# Custom OpenAPI schema with explicit auth
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Semantis AI Semantic Cache API",
        version="0.1.0",
        description=(
            "A semantic caching service for LLM apps. "
            "Authentication via Bearer API keys formatted as `Bearer sc-{tenant}-{anything}`."
        ),
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "sc-{tenant}-{anything}",
            "description": "Use tenant-based auth keys (e.g., Bearer sc-test-local)"
        }
    }
    openapi_schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Simple API-key format: Bearer sc-{tenant}-{anything}
API_KEY_REGEX = re.compile(r"^Bearer\s+(sc-[A-Za-z0-9_-]+)$")

# Store current request API key for usage logging (thread-local would be better for production)
_current_api_key = {"key": None}

def get_tenant_from_key(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    m = API_KEY_REGEX.match(auth)
    if not m:
        error_log.error(f"Unauthorized access. Header: {auth}")
        raise HTTPException(status_code=401, detail="Missing or invalid API key")
    token = m.group(1)
    # sc-devA-foo -> tenant = 'devA'
    parts = token.split("-")
    if len(parts) < 3:
        raise HTTPException(status_code=401, detail="Malformed API key")
    tenant = parts[1]
    
    # Store API key for usage logging
    _current_api_key["key"] = token
    
    # Verify API key in database and track usage
    try:
        from database import get_api_key_info, update_api_key_usage, create_api_key
        key_info = get_api_key_info(token)
        if key_info:
            # Key exists and is active
            update_api_key_usage(token, tenant)
        else:
            # Auto-create key in database if it doesn't exist (for backward compatibility)
            create_api_key(token, tenant, plan='free')
            update_api_key_usage(token, tenant)
    except Exception as e:
        # Don't fail if database is not available, but log it
        error_log.warning(f"Database operation failed: {e}")
    
    return tenant

# -----------------------------
# Request/Response models (OpenAI-like)
# -----------------------------
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str = CHAT_MODEL
    messages: List[ChatMessage]
    temperature: float = 0.2
    ttl_seconds: int = 7 * 24 * 3600

# -----------------------------
# Endpoints
# -----------------------------
@app.get("/health")
def health():
    return {"status": "ok", "service": "semantic-cache", "version": "0.1.0"}

@app.get("/metrics")
def get_metrics(tenant: str = Depends(get_tenant_from_key)):
    svc.adapt_threshold(tenant)
    m = svc.metrics(tenant)
    access_log.info(f"{tenant} | /metrics | hit_ratio={m['hit_ratio']}")
    return m

@app.get("/query")
def simple_query(prompt: str = Query(...), model: str = CHAT_MODEL, tenant: str = Depends(get_tenant_from_key)):
    messages = [{"role": "user", "content": prompt}]
    prompt_norm = SemanticCacheService.norm_text(prompt)
    try:
        ans, meta = svc.query(tenant, prompt_norm, messages, model)
        access_log.info(f"{tenant} | /query | {meta['hit']} | sim={meta['similarity']:.3f} | {meta['latency_ms']}ms")
        return {"answer": ans, "meta": meta, "metrics": svc.metrics(tenant)}
    except Exception as e:
        error_log.exception(f"{tenant} | /query | error: {e}")
        raise HTTPException(status_code=500, detail="Internal error")

@app.get("/events")
def get_events(limit: int = Query(100, ge=1, le=1000), tenant: str = Depends(get_tenant_from_key)):
    """Get recent cache events for the tenant."""
    T = svc.tenant(tenant)
    events = T.events[-limit:] if len(T.events) > limit else T.events
    return [
        {
            "timestamp": e.timestamp,
            "tenant_id": e.tenant_id,
            "prompt_hash": e.prompt_hash,
            "decision": e.decision,
            "similarity": e.similarity,
            "latency_ms": e.latency_ms,
        }
        for e in reversed(events)  # Most recent first
    ]

@app.post("/v1/chat/completions")
def openai_compatible(body: ChatRequest, tenant: str = Depends(get_tenant_from_key)):
    prompt_norm = SemanticCacheService.norm_text(
        " ".join([m.content for m in body.messages if m.role == "user"]) or ""
    )
    try:
        ans, meta = svc.query(
            tenant,
            prompt_norm,
            [m.dict() for m in body.messages],
            body.model,
            ttl_seconds=body.ttl_seconds,
            temperature=body.temperature,
        )
        # Log usage to database
        try:
            from database import log_usage
            api_key = _current_api_key.get("key", "unknown")
            log_usage(
                api_key=api_key,
                tenant_id=tenant,
                endpoint="/v1/chat/completions",
                request_count=1,
                cache_hits=1 if meta.get('hit') != 'miss' else 0,
                cache_misses=1 if meta.get('hit') == 'miss' else 0,
                tokens_used=0,  # Can be calculated from response if needed
                cost_estimate=0  # Can be calculated based on tokens
            )
        except Exception as e:
            # Don't fail if database logging fails
            error_log.warning(f"Could not log usage to database: {e}")
        
        access_log.info(f"{tenant} | /v1/chat/completions | {meta['hit']} | sim={meta['similarity']:.3f} | {meta['latency_ms']}ms")
        return {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": body.model,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": ans}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": None, "completion_tokens": None, "total_tokens": None},
            "meta": meta,
        }
    except Exception as e:
        error_log.exception(f"{tenant} | /v1/chat/completions | error: {e}")
        raise HTTPException(status_code=500, detail="Internal error")

# -----------------------------
# Entry point
# -----------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"Semantis AI Semantic Cache API running on http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
