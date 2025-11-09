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

import os, time, re, logging
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
    # adaptive similarity threshold
    sim_threshold: float = 0.83

# -----------------------------
# Core semantic cache service
# -----------------------------
class SemanticCacheService:
    def __init__(self):
        self.tenants: Dict[str, TenantState] = {}

    def tenant(self, tenant_id: str) -> TenantState:
        if tenant_id not in self.tenants:
            self.tenants[tenant_id] = TenantState()
        return self.tenants[tenant_id]

    @staticmethod
    def norm_text(s: str) -> str:
        return " ".join(s.strip().split()).lower()

    def _faiss_add(self, T: TenantState, emb: np.ndarray):
        v = emb.astype("float32").reshape(1, -1)
        faiss.normalize_L2(v)
        if T.index is None:
            T.dim = v.shape[1]
            T.index = faiss.IndexFlatIP(T.dim)
        T.index.add(v)

    def _faiss_search(self, T: TenantState, emb: np.ndarray, k: int = 1) -> Tuple[int, float]:
        q = emb.astype("float32").reshape(1, -1)
        faiss.normalize_L2(q)
        sims, idxs = T.index.search(q, k)
        return int(idxs[0][0]), float(sims[0][0])

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
                return entry.response_text, meta

        # 2) semantic
        if T.index is not None and len(T.rows) > 0:
            user_text = " ".join([m["content"] for m in messages if m.get("role") == "user"]) or prompt_norm
            emb = get_embedding(user_text)
            best_idx, best_sim = self._faiss_search(T, emb, k=1)
            if best_sim >= T.sim_threshold and T.rows[best_idx].fresh():
                entry = T.rows[best_idx]
                entry.use_count += 1
                entry.last_used_at = time.time()
                T.hits += 1
                T.semantic_hits += 1
                latency = round((time.time() - t0) * 1000, 2)
                T.latencies_ms.append(latency)
                meta = {"hit": "semantic", "similarity": round(best_sim, 4), "latency_ms": latency, "strategy": "hybrid"}
                semantic_log.info(f"{tenant_id} | semantic | sim={best_sim:.3f} | key={prompt_norm[:80]}")
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
        return response_text, meta

    def metrics(self, tenant_id: str) -> dict:
        T = self.tenant(tenant_id)
        total = T.hits + T.misses
        p50 = np.percentile(T.latencies_ms, 50) if T.latencies_ms else 0
        p95 = np.percentile(T.latencies_ms, 95) if T.latencies_ms else 0
        return {
            "tenant": tenant_id,
            "requests": total,
            "hits": T.hits,
            "semantic_hits": T.semantic_hits,
            "misses": T.misses,
            "hit_ratio": round((T.hits / total) if total else 0.0, 3),
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
