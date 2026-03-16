"""
Semantis AI - Semantic Cache API (Enterprise Edition)

Repo: Semantis_AI
Folder: backend/

FastAPI service providing:
 - Multi-tenant, org-level auth (Bearer sc-{org_slug}-{any})
 - Exact + semantic cache (FAISS cosine) with Redis L2 + PostgreSQL L3
 - Adaptive per-tenant threshold
 - Rotating logs (access/errors/semantic_ops)
 - OpenAI integration
 - OpenAI-like POST /v1/chat/completions + simple GET /query
 - Audit logging, API key scoping, per-org rate limits
"""

import os, time, re, logging, hashlib, json
from logging.handlers import RotatingFileHandler
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from collections import OrderedDict
from contextvars import ContextVar
import threading

import numpy as np
import faiss
from fastapi import FastAPI, Request, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
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
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",") if o.strip()]
if not OPENAI_API_KEY or OPENAI_API_KEY == "sk-REPLACE_ME":
    print("WARNING: OPENAI_API_KEY is not set. Set it in backend/.env or OS env.")

# openai python (responses-compatible style kept for portability)
import openai
openai.api_key = OPENAI_API_KEY

EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
EMBED_DIMENSIONS = int(os.getenv("EMBED_DIMENSIONS", "1024"))
CHAT_MODEL  = os.getenv("CHAT_MODEL", "gpt-4o-mini")

# Local model config — lazy-loaded to avoid startup cost when not needed
LOCAL_MODEL_NAME = os.getenv("LOCAL_EMBED_MODEL", "all-MiniLM-L6-v2")
LOCAL_MODEL_ENABLED = os.getenv("LOCAL_EMBED_ENABLED", "true").lower() == "true"
CROSS_ENCODER_MODEL = os.getenv("CROSS_ENCODER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
CROSS_ENCODER_ENABLED = os.getenv("CROSS_ENCODER_ENABLED", "false").lower() == "true"

# IVF threshold — switch from brute-force to IVF when tenant has more entries
IVF_UPGRADE_THRESHOLD = int(os.getenv("IVF_UPGRADE_THRESHOLD", "10000"))

# -----------------------------
# Logging setup (rotating)
# -----------------------------
os.makedirs("logs", exist_ok=True)

def make_rotating_logger(name: str, filename: str, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    handler = RotatingFileHandler(
        os.path.join("logs", filename), maxBytes=10_000_000, backupCount=5
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

# Create comprehensive loggers
access_log      = make_rotating_logger("access", "access.log", logging.INFO)
error_log       = make_rotating_logger("errors", "errors.log", logging.ERROR)
semantic_log    = make_rotating_logger("semantic", "semantic_ops.log", logging.INFO)
performance_log = make_rotating_logger("performance", "performance.log", logging.INFO)
security_log    = make_rotating_logger("security", "security.log", logging.WARNING)
system_log      = make_rotating_logger("system", "system.log", logging.INFO)
app_log         = make_rotating_logger("application", "application.log", logging.INFO)

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
# Query normalization for better matching
# -----------------------------
_CONTRACTIONS = {
    "won't": "will not", "can't": "cannot", "n't": " not",
    "'re": " are", "'ve": " have", "'ll": " will", "'d": " would",
    "'m": " am", "let's": "let us", "it's": "it is", "i'm": "i am",
    "he's": "he is", "she's": "she is", "that's": "that is",
    "what's": "what is", "there's": "there is", "here's": "here is",
    "who's": "who is", "how's": "how is", "where's": "where is",
}
_CONTRACTION_RE = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in sorted(_CONTRACTIONS, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)
_FILLER_RE = re.compile(
    r"\b(please|pls|plz|hey|hi|hello|um|uh|like|just|actually|basically|literally|ok|okay|thanks|thank you|thx)\b",
    re.IGNORECASE,
)
_MULTI_SPACE_RE = re.compile(r"\s+")
_PUNCT_NOISE_RE = re.compile(r"[.!?,;:]+$")

def normalize_query(text: str) -> str:
    """Light normalization for hash-index lookups: expand contractions, strip
    filler words, collapse whitespace. Does NOT expand abbreviations — the
    embedding model handles semantic equivalence (ML≈machine learning, typos, etc.)."""
    t = text.strip().lower()
    t = _CONTRACTION_RE.sub(lambda m: _CONTRACTIONS.get(m.group(0).lower(), m.group(0)), t)
    t = _FILLER_RE.sub("", t)
    t = _PUNCT_NOISE_RE.sub("", t)
    t = _MULTI_SPACE_RE.sub(" ", t).strip()
    return t

def _tokenize(text: str) -> set:
    """Simple word-level tokenizer for overlap scoring."""
    return set(re.findall(r"[a-z0-9]+", text.lower()))

def token_overlap_score(query: str, candidate: str) -> float:
    """Jaccard token overlap. Returns 0.0..1.0."""
    q_tokens = _tokenize(query)
    c_tokens = _tokenize(candidate)
    if not q_tokens:
        return 0.0
    union = q_tokens | c_tokens
    if not union:
        return 0.0
    return len(q_tokens & c_tokens) / len(union)

def hybrid_score(cosine_sim: float, token_sim: float) -> float:
    """Cosine-dominant scoring. Token overlap is only a minor tiebreaker
    so it never blocks valid semantic matches (typos, abbreviations,
    paraphrases all have low token overlap but high cosine similarity)."""
    return 0.97 * cosine_sim + 0.03 * token_sim

# -----------------------------
# Embeddings & LLM
# -----------------------------
def _get_user_openai_key(user_id: Optional[str]) -> Optional[str]:
    """Retrieve and decrypt the user's BYOK OpenAI key, or return None."""
    if not user_id:
        return None
    
    try:
        from database import get_user_openai_key_encrypted
        from encryption import decrypt_api_key
        
        encrypted_key = get_user_openai_key_encrypted(user_id)
        if encrypted_key:
            return decrypt_api_key(encrypted_key)
    except Exception as e:
        error_log.warning(f"Failed to get user OpenAI key | user_id={user_id} | error={str(e)}")
    
    return None

_openai_key_lock = threading.Lock()

def _resolve_openai_key(user_id: Optional[str] = None) -> str:
    """Get the effective OpenAI API key (user BYOK or server fallback)."""
    user_api_key = _get_user_openai_key(user_id)
    key = user_api_key or OPENAI_API_KEY
    if not key or key == "sk-REPLACE_ME":
        raise ValueError(
            "No OpenAI API key available. Either add your own key in Account Settings, "
            "or ask the admin to set a server-level OPENAI_API_KEY."
        )
    return key

EMBEDDING_PREFIX = "Semantic meaning: "

# Reusable OpenAI client pool
_openai_clients: Dict[str, "openai.OpenAI"] = {}
_client_lock = threading.Lock()

def _get_openai_client(api_key: str):
    """Return a cached OpenAI client for the given key."""
    from openai import OpenAI
    with _client_lock:
        if api_key not in _openai_clients:
            _openai_clients[api_key] = OpenAI(api_key=api_key, timeout=30.0, max_retries=1)
        return _openai_clients[api_key]

# ── Local model singletons (lazy-loaded) ──
_local_model = None
_local_model_lock = threading.Lock()
_cross_encoder = None
_cross_encoder_lock = threading.Lock()

def _get_local_model():
    """Lazy-load the local sentence-transformer for fast pre-filtering."""
    global _local_model
    if _local_model is not None:
        return _local_model
    with _local_model_lock:
        if _local_model is not None:
            return _local_model
        try:
            from sentence_transformers import SentenceTransformer
            _local_model = SentenceTransformer(LOCAL_MODEL_NAME)
            system_log.info(f"Local embed model loaded | model={LOCAL_MODEL_NAME}")
        except Exception as e:
            system_log.warning(f"Local embed model unavailable: {e}. Falling back to OpenAI-only.")
            _local_model = False  # sentinel: tried and failed
    return _local_model

def _get_cross_encoder():
    """Lazy-load the cross-encoder for re-ranking."""
    global _cross_encoder
    if _cross_encoder is not None:
        return _cross_encoder
    with _cross_encoder_lock:
        if _cross_encoder is not None:
            return _cross_encoder
        try:
            from sentence_transformers import CrossEncoder
            _cross_encoder = CrossEncoder(CROSS_ENCODER_MODEL)
            system_log.info(f"Cross-encoder loaded | model={CROSS_ENCODER_MODEL}")
        except Exception as e:
            system_log.warning(f"Cross-encoder unavailable: {e}. Skipping re-ranking.")
            _cross_encoder = False
    return _cross_encoder

def get_local_embedding(text: str) -> Optional[np.ndarray]:
    """Fast local embedding (~5ms). Returns None if local model unavailable."""
    if not LOCAL_MODEL_ENABLED:
        return None
    model = _get_local_model()
    if model is False or model is None:
        return None
    v = model.encode(text, normalize_embeddings=True)
    return np.array(v, dtype="float32")

def cross_encoder_score(query: str, candidates: List[str]) -> Optional[List[float]]:
    """Score query-candidate pairs with cross-encoder. Returns None if unavailable."""
    if not CROSS_ENCODER_ENABLED or not candidates:
        return None
    encoder = _get_cross_encoder()
    if encoder is False or encoder is None:
        return None
    pairs = [[query, c] for c in candidates]
    scores = encoder.predict(pairs)
    return [float(s) for s in scores]

def get_embedding(text: str, user_id: Optional[str] = None) -> np.ndarray:
    """Return L2-normalized embedding vector from OpenAI (thread-safe).
    Uses reduced dimensions (default 1024) for faster search and lower memory."""
    start_time = time.time()
    key = _resolve_openai_key(user_id)
    prefixed = f"{EMBEDDING_PREFIX}{text.strip().lower()}"

    try:
        client = _get_openai_client(key)
        resp = client.embeddings.create(
            model=EMBED_MODEL, input=prefixed, dimensions=EMBED_DIMENSIONS
        )
        v = np.array(resp.data[0].embedding, dtype="float32")
        v /= (np.linalg.norm(v) + 1e-12)
        embedding_time = round((time.time() - start_time) * 1000, 2)
        performance_log.debug(
            f"Embedding generated | model={EMBED_MODEL} | dims={EMBED_DIMENSIONS} | "
            f"user_id={user_id} | text_len={len(text)} | time={embedding_time}ms"
        )
        return v
    except Exception as e:
        embedding_time = round((time.time() - start_time) * 1000, 2)
        error_log.exception(
            f"Embedding failed | model={EMBED_MODEL} | user_id={user_id} | "
            f"text_len={len(text)} | time={embedding_time}ms | error={str(e)}"
        )
        raise

def call_llm_stream(messages: List[dict], temperature: float = 0.2, user_id: Optional[str] = None):
    """OpenAI chat call with streaming. Yields SSE chunks."""
    key = _resolve_openai_key(user_id)
    client = _get_openai_client(key)
    stream = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=1024,
        stream=True,
    )
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


def call_llm(messages: List[dict], temperature: float = 0.2, user_id: Optional[str] = None) -> str:
    """OpenAI chat call (thread-safe, uses cached client)."""
    start_time = time.time()
    prompt_tokens = sum(len(m.get("content", "").split()) for m in messages)
    key = _resolve_openai_key(user_id)
    
    try:
        client = _get_openai_client(key)
        resp = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=1024,
        )
        llm_time = round((time.time() - start_time) * 1000, 2)
        response_text = resp.choices[0].message.content.strip()
        completion_tokens = len(response_text.split())
        total_tokens = prompt_tokens + completion_tokens
        
        app_log.info(
            f"LLM call | model={CHAT_MODEL} | user_id={user_id} | temp={temperature} | "
            f"prompt_tokens~={prompt_tokens} | completion_tokens~={completion_tokens} | "
            f"total_tokens~={total_tokens} | time={llm_time}ms"
        )
        return response_text
    except Exception as e:
        llm_time = round((time.time() - start_time) * 1000, 2)
        error_log.exception(
            f"LLM call failed | model={CHAT_MODEL} | user_id={user_id} | temp={temperature} | "
            f"time={llm_time}ms | error={str(e)}"
        )
        raise

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
    response_embedding: Optional[np.ndarray] = None  # Tier 2: response validation
    local_embedding: Optional[np.ndarray] = None      # Tier 2: fast local pre-filter
    cluster_id: int = -1                               # Tier 3: cluster routing

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
    confidence: float = 0.0
    hybrid_score: float = 0.0

@dataclass
class TenantState:
    exact: Dict[str, CacheEntry] = field(default_factory=dict)
    index: Optional[faiss.IndexFlatIP] = None
    rows: List[CacheEntry] = field(default_factory=list)
    dim: Optional[int] = None
    # Tier 1: normalized-text hash index for O(1) deep-norm lookups
    norm_hash_index: Dict[str, CacheEntry] = field(default_factory=dict)
    # Tier 2: local model FAISS index for fast pre-filtering
    local_index: Optional[faiss.IndexFlatIP] = None
    local_dim: Optional[int] = None
    # Tier 3: cluster centroids for routing
    cluster_centroids: Optional[np.ndarray] = None
    n_clusters: int = 0
    # metrics
    hits: int = 0
    misses: int = 0
    semantic_hits: int = 0
    latencies_ms: List[float] = field(default_factory=list)
    sim_threshold: float = 0.55
    domain_thresholds: Dict[str, float] = field(default_factory=dict)
    events: List[CacheEvent] = field(default_factory=list)

# -----------------------------
# Core semantic cache service
# -----------------------------
class SemanticCacheService:
    def __init__(self):
        self.tenants: Dict[str, TenantState] = {}
        self._embedding_cache: OrderedDict[str, np.ndarray] = OrderedDict()
        self._embedding_cache_max_size = 1000
        self._cache_lock = threading.Lock()
        self._load_cache()
    
    def _load_cache(self):
        """Load cache from pickle then warm from Redis. Handles dimension migration."""
        try:
            from cache_persistence import load_cache
            start_time = time.time()
            loaded_tenants = load_cache()
            load_time = round((time.time() - start_time) * 1000, 2)
            if loaded_tenants:
                total_entries = 0
                migrated = 0
                for tid, tstate in loaded_tenants.items():
                    # Dimension migration: if existing embeddings don't match
                    # EMBED_DIMENSIONS, invalidate the FAISS index and old embeddings
                    # so they get re-computed lazily on next hit.
                    needs_rebuild = False
                    for row in tstate.rows:
                        if row.embedding is not None and row.embedding.shape[0] != EMBED_DIMENSIONS:
                            needs_rebuild = True
                            break

                    if needs_rebuild:
                        system_log.info(
                            f"Dimension migration needed for tenant={tid} | "
                            f"old_dim={tstate.rows[0].embedding.shape[0] if tstate.rows else '?'} | "
                            f"new_dim={EMBED_DIMENSIONS} | clearing FAISS index and embeddings"
                        )
                        tstate.index = None
                        tstate.dim = None
                        tstate.local_index = None
                        tstate.local_dim = None
                        for row in tstate.rows:
                            row.embedding = None
                            row.response_embedding = None
                            row.local_embedding = None
                        migrated += len(tstate.rows)

                    # Rebuild norm_hash_index from loaded entries
                    if not hasattr(tstate, 'norm_hash_index') or not tstate.norm_hash_index:
                        tstate.norm_hash_index = {}
                    for key, entry in tstate.exact.items():
                        norm_key = normalize_query(key)
                        if norm_key:
                            tstate.norm_hash_index[norm_key] = entry

                    total_entries += len(tstate.rows)

                self.tenants.update(loaded_tenants)
                system_log.info(
                    f"Cache loaded from disk | tenants={len(loaded_tenants)} | "
                    f"entries={total_entries} | migrated={migrated} | time={load_time}ms"
                )
            else:
                system_log.info(f"Cache load | no local cache found | time={load_time}ms")
        except Exception as e:
            error_log.exception(f"Cache load failed | error={str(e)}")

        # Check Redis availability
        try:
            from redis_cache import is_available
            if is_available():
                system_log.info("Redis L2 cache connected")
            else:
                system_log.info("Redis not available, using in-memory only")
        except Exception:
            pass
    
    def _save_cache(self):
        """Save cache to disk periodically."""
        try:
            from cache_persistence import save_cache
            start_time = time.time()
            total_entries = sum(len(t.rows) for t in self.tenants.values())
            save_cache(self.tenants)
            save_time = round((time.time() - start_time) * 1000, 2)
            system_log.info(
                f"Cache saved | tenants={len(self.tenants)} | "
                f"entries={total_entries} | time={save_time}ms"
            )
        except Exception as e:
            error_log.exception(f"Cache save failed | error={str(e)}")
            system_log.error(f"Could not save cache to disk: {e}")

    def tenant(self, tenant_id: str) -> TenantState:
        if tenant_id not in self.tenants:
            self.tenants[tenant_id] = TenantState()
        return self.tenants[tenant_id]

    @staticmethod
    def norm_text(s: str) -> str:
        """Lightweight normalization for exact-match lookup only (whitespace + lowercase)."""
        return " ".join(s.strip().split()).lower()

    def _get_embedding_for_query(self, messages: List[dict], user_id: Optional[str] = None) -> Tuple[np.ndarray, str]:
        """Get embedding for the user's raw query text. We embed the original
        text (lowercased) rather than the normalized version so the embedding
        model can leverage its own understanding of abbreviations, typos, and
        paraphrases — it's far better at this than hand-coded normalization."""
        user_messages = [m["content"] for m in messages if m.get("role") == "user"]
        raw_text = user_messages[-1] if user_messages else ""
        raw_text = raw_text.strip()
        if not raw_text:
            raise ValueError("Empty query")

        text_for_embed = raw_text.lower()

        if text_for_embed in self._embedding_cache:
            self._embedding_cache.move_to_end(text_for_embed)
            return self._embedding_cache[text_for_embed], raw_text

        emb = get_embedding(text_for_embed, user_id=user_id)
        self._embedding_cache[text_for_embed] = emb
        if len(self._embedding_cache) > self._embedding_cache_max_size:
            self._embedding_cache.popitem(last=False)

        return emb, raw_text

    def _append_event(self, T: TenantState, tenant_id: str, prompt_hash: str, decision: str, similarity: float, latency_ms: float):
        T.events.append(CacheEvent(
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
            tenant_id=tenant_id,
            prompt_hash=prompt_hash,
            decision=decision,
            similarity=similarity,
            latency_ms=latency_ms,
        ))
        if len(T.events) > 1000:
            T.events = T.events[-1000:]

    def _faiss_add(self, T: TenantState, emb: np.ndarray):
        v = emb.astype("float32").reshape(1, -1)
        faiss.normalize_L2(v)
        if T.index is None:
            T.dim = v.shape[1]
            T.index = faiss.IndexFlatIP(T.dim)
        T.index.add(v)
        # Tier 2b: auto-upgrade to IVF when cache grows large
        if len(T.rows) == IVF_UPGRADE_THRESHOLD and T.dim is not None:
            self._upgrade_to_ivf(T)

    def _local_faiss_add(self, T: TenantState, local_emb: np.ndarray):
        """Add to the local-model FAISS index for fast pre-filtering."""
        v = local_emb.astype("float32").reshape(1, -1)
        faiss.normalize_L2(v)
        if T.local_index is None:
            T.local_dim = v.shape[1]
            T.local_index = faiss.IndexFlatIP(T.local_dim)
        T.local_index.add(v)

    def _upgrade_to_ivf(self, T: TenantState):
        """Upgrade from IndexFlatIP to IndexIVFFlat for O(sqrt(n)) search."""
        try:
            n = len(T.rows)
            nlist = max(4, int(np.sqrt(n)))
            quantizer = faiss.IndexFlatIP(T.dim)
            ivf_index = faiss.IndexIVFFlat(quantizer, T.dim, nlist, faiss.METRIC_INNER_PRODUCT)
            all_vecs = np.vstack([
                r.embedding.astype("float32").reshape(1, -1) for r in T.rows
            ])
            faiss.normalize_L2(all_vecs)
            ivf_index.train(all_vecs)
            ivf_index.add(all_vecs)
            ivf_index.nprobe = max(1, nlist // 4)
            T.index = ivf_index
            semantic_log.info(
                f"FAISS upgraded to IVFFlat | entries={n} | nlist={nlist} | nprobe={ivf_index.nprobe}"
            )
        except Exception as e:
            error_log.warning(f"IVF upgrade failed, keeping flat index: {e}")

    def _rebuild_clusters(self, T: TenantState, n_clusters: int = 0):
        """Tier 3: build cluster centroids from cached embeddings for routing."""
        if len(T.rows) < 50:
            return
        if n_clusters == 0:
            n_clusters = max(4, int(np.sqrt(len(T.rows)) / 2))
        all_vecs = np.vstack([
            r.embedding.astype("float32").reshape(1, -1) for r in T.rows
        ])
        faiss.normalize_L2(all_vecs)
        d = all_vecs.shape[1]
        kmeans = faiss.Kmeans(d, n_clusters, niter=20, verbose=False, gpu=False)
        kmeans.train(all_vecs)
        T.cluster_centroids = kmeans.centroids.copy()
        T.n_clusters = n_clusters
        # Assign cluster IDs to entries
        _, assignments = kmeans.index.search(all_vecs, 1)
        for i, row in enumerate(T.rows):
            row.cluster_id = int(assignments[i][0])

    def _resolve_threshold(self, T: TenantState, domain: str) -> float:
        """Per-domain threshold if configured, else tenant default."""
        return T.domain_thresholds.get(domain, T.sim_threshold)

    def query(
        self,
        tenant_id: str,
        prompt_norm: str,
        messages: List[dict],
        model: str,
        ttl_seconds: int = 7 * 24 * 3600,
        temperature: float = 0.2,
        user_id: Optional[str] = None,
    ) -> Tuple[str, dict]:
        """
        Multi-tier cache lookup pipeline:
          1. Exact match on original text (sub-ms).
          2. Normalized-hash O(1) lookup (sub-ms).
          3. Local model pre-filter gate — skip expensive OpenAI call if
             local similarity < 0.5 (Tier 2c).
          4. OpenAI semantic search: FAISS cosine top-k → cross-encoder
             re-rank (Tier 3a) → hybrid scoring → confidence tiers.
        On miss: LLM call + async embed/store.
        """
        T = self.tenant(tenant_id)
        t0 = time.time()
        prompt_hash = hashlib.md5(prompt_norm.encode()).hexdigest()

        # ── 1) Exact match on original normalized text (sub-ms) ──
        if prompt_norm in T.exact:
            entry = T.exact[prompt_norm]
            if entry.fresh() and entry.model == model:
                entry.use_count += 1
                entry.last_used_at = time.time()
                T.hits += 1
                latency = round((time.time() - t0) * 1000, 2)
                T.latencies_ms.append(latency)
                meta = {"hit": "exact", "similarity": 1.0, "latency_ms": latency, "strategy": "exact"}
                semantic_log.info(f"{tenant_id} | exact | sim=1.000 | key={prompt_norm[:80]}")
                self._append_event(T, tenant_id, prompt_hash, "exact", 1.0, latency)
                return entry.response_text, meta

        # ── 2) Normalized-hash O(1) lookup (Tier 1b) ──
        deep_norm = normalize_query(prompt_norm)
        if deep_norm and deep_norm in T.norm_hash_index:
            entry = T.norm_hash_index[deep_norm]
            if entry.fresh() and entry.model == model:
                entry.use_count += 1
                entry.last_used_at = time.time()
                T.hits += 1
                latency = round((time.time() - t0) * 1000, 2)
                T.latencies_ms.append(latency)
                meta = {"hit": "exact", "similarity": 1.0, "latency_ms": latency, "strategy": "normalized_hash"}
                semantic_log.info(f"{tenant_id} | normalized_hash | key={prompt_norm[:80]}")
                self._append_event(T, tenant_id, prompt_hash, "exact", 1.0, latency)
                return entry.response_text, meta

        # ── 3) Local model pre-filter gate (Tier 2c) ──
        # Use normalized text (with abbreviation expansion) for the local gate
        # so "Explain ML" gets expanded to "Explain machine learning" before
        # comparing to cached embeddings.
        local_gate_passed = True
        if T.local_index is not None and len(T.rows) > 0 and LOCAL_MODEL_ENABLED:
            try:
                local_emb = get_local_embedding(prompt_norm)
                if local_emb is not None:
                    lq = local_emb.astype("float32").reshape(1, -1)
                    faiss.normalize_L2(lq)
                    local_k = min(3, T.local_index.ntotal)
                    if local_k > 0:
                        local_sims, _ = T.local_index.search(lq, local_k)
                        best_local_sim = float(local_sims[0][0])
                        if best_local_sim < 0.25:
                            local_gate_passed = False
                            semantic_log.debug(
                                f"{tenant_id} | local_gate_reject | best_local_sim={best_local_sim:.3f} | "
                                f"key={prompt_norm[:80]}"
                            )
            except Exception as e:
                error_log.debug(f"Local pre-filter error (non-fatal): {e}")

        # ── 4) Semantic search with hybrid re-ranking + cross-encoder ──
        query_emb = None
        query_text = prompt_norm

        if local_gate_passed and T.index is not None and len(T.rows) > 0:
            query_emb, query_text = self._get_embedding_for_query(messages, user_id=user_id)
            query_domain = domain_hint(query_text)

            # Tier 3b: cluster routing — narrow search to nearest clusters
            search_rows_mask = None
            if T.cluster_centroids is not None and T.n_clusters >= 4:
                cq = query_emb.astype("float32").reshape(1, -1)
                faiss.normalize_L2(cq)
                centroid_index = faiss.IndexFlatIP(T.cluster_centroids.shape[1])
                centroid_index.add(T.cluster_centroids)
                n_probe_clusters = max(1, T.n_clusters // 3)
                _, cluster_ids = centroid_index.search(cq, n_probe_clusters)
                target_clusters = set(int(c) for c in cluster_ids[0] if c >= 0)
                search_rows_mask = set(
                    i for i, r in enumerate(T.rows) if r.cluster_id in target_clusters
                )

            k = min(10, len(T.rows))
            q = query_emb.astype("float32").reshape(1, -1)
            faiss.normalize_L2(q)
            sims, idxs = T.index.search(q, k)

            candidates = []
            for i in range(k):
                idx = int(idxs[0][i])
                cosine_sim = float(sims[0][i])
                if idx < 0 or idx >= len(T.rows):
                    continue
                if search_rows_mask is not None and idx not in search_rows_mask:
                    continue
                entry = T.rows[idx]
                if not entry.fresh() or entry.model != model:
                    continue

                tok_sim = token_overlap_score(query_text, entry.prompt_norm)
                h_score = hybrid_score(cosine_sim, tok_sim)
                candidates.append((entry, cosine_sim, tok_sim, h_score, idx))

            # Tier 3a: cross-encoder re-ranking on top candidates
            if len(candidates) >= 2 and CROSS_ENCODER_ENABLED:
                try:
                    cand_texts = [c[0].prompt_norm for c in candidates[:5]]
                    ce_scores = cross_encoder_score(query_text, cand_texts)
                    if ce_scores is not None:
                        for j, score in enumerate(ce_scores):
                            entry, cosine_sim, tok_sim, h_score, idx = candidates[j]
                            # Blend: 60% hybrid, 40% cross-encoder (CE is more accurate)
                            ce_norm = max(0.0, min(1.0, (score + 5) / 10))  # normalize ~[-5,5] to [0,1]
                            blended = 0.60 * h_score + 0.40 * ce_norm
                            candidates[j] = (entry, cosine_sim, tok_sim, blended, idx)
                except Exception as e:
                    error_log.debug(f"Cross-encoder error (non-fatal): {e}")

            candidates.sort(key=lambda c: c[3], reverse=True)

            if candidates:
                best_entry, best_cosine, best_tok, best_hybrid, _ = candidates[0]
                threshold = self._resolve_threshold(T, query_domain)

                is_match = False
                confidence_tier = "none"

                # Primary decision: trust the cosine similarity from the
                # embedding model. It already understands abbreviations (ML),
                # typos ("artifical inteligence"), and paraphrases.
                if best_cosine >= threshold + 0.10:
                    is_match = True
                    confidence_tier = "high"
                elif best_cosine >= threshold:
                    is_match = True
                    confidence_tier = "medium"
                elif best_cosine >= threshold - 0.08:
                    is_match = True
                    confidence_tier = "low"

                # Response embedding sanity check — only reject if the
                # response is truly unrelated (very low threshold).
                if is_match and best_entry.response_embedding is not None and query_emb is not None:
                    resp_sim = float(np.dot(
                        query_emb / (np.linalg.norm(query_emb) + 1e-12),
                        best_entry.response_embedding / (np.linalg.norm(best_entry.response_embedding) + 1e-12),
                    ))
                    if resp_sim < 0.10:
                        is_match = False
                        confidence_tier = "response_mismatch"
                        semantic_log.info(
                            f"{tenant_id} | response_mismatch | query_resp_sim={resp_sim:.3f} | "
                            f"key={prompt_norm[:80]}"
                        )

                if is_match:
                    best_entry.use_count += 1
                    best_entry.last_used_at = time.time()
                    T.hits += 1
                    T.semantic_hits += 1
                    latency = round((time.time() - t0) * 1000, 2)
                    T.latencies_ms.append(latency)
                    meta = {
                        "hit": "semantic",
                        "similarity": round(best_cosine, 4),
                        "hybrid_score": round(best_hybrid, 4),
                        "token_overlap": round(best_tok, 4),
                        "confidence": confidence_tier,
                        "latency_ms": latency,
                        "strategy": "hybrid_semantic",
                        "threshold_used": round(threshold, 3),
                        "domain": query_domain,
                    }
                    semantic_log.info(
                        f"{tenant_id} | semantic | cosine={best_cosine:.3f} | "
                        f"hybrid={best_hybrid:.3f} | token_overlap={best_tok:.3f} | "
                        f"confidence={confidence_tier} | threshold={threshold:.3f} | "
                        f"domain={query_domain} | key={prompt_norm[:80]}"
                    )
                    self._append_event(T, tenant_id, prompt_hash, "semantic",
                                       round(best_cosine, 4), latency)
                    if T.events:
                        T.events[-1].confidence = best_hybrid
                        T.events[-1].hybrid_score = best_hybrid
                    return best_entry.response_text, meta

                semantic_log.info(
                    f"{tenant_id} | near-miss | cosine={best_cosine:.3f} | "
                    f"hybrid={best_hybrid:.3f} | token_overlap={best_tok:.3f} | "
                    f"threshold={threshold:.3f} | domain={query_domain} | "
                    f"key={prompt_norm[:80]}"
                )
                if not hasattr(T, '_near_misses'):
                    T._near_misses = []
                T._near_misses.append(best_hybrid)
                if len(T._near_misses) > 100:
                    T._near_misses = T._near_misses[-100:]

        # ── 5) Cache miss — LLM call + async storage ──
        T.misses += 1
        response_text = call_llm(messages, temperature, user_id)

        latency = round((time.time() - t0) * 1000, 2)
        T.latencies_ms.append(latency)
        semantic_log.debug(f"{tenant_id} | miss | total={latency}ms | key={prompt_norm[:80]}")

        meta = {"hit": "miss", "similarity": 0.0, "latency_ms": latency, "strategy": "miss"}
        self._append_event(T, tenant_id, prompt_hash, "miss", 0.0, latency)

        # Store immediately with query embedding (fast path)
        _cached_emb = query_emb
        def _store_fast():
            """Store entry in cache ASAP with just the query embedding."""
            try:
                emb = _cached_emb
                if emb is None:
                    emb, _ = self._get_embedding_for_query(messages, user_id=user_id)
                user_text = " ".join(m["content"] for m in messages if m.get("role") == "user") or prompt_norm
                entry_domain = domain_hint(user_text)

                entry = CacheEntry(
                    prompt_norm=prompt_norm,
                    response_text=response_text,
                    embedding=emb,
                    model=model,
                    ttl_seconds=ttl_seconds,
                    domain=entry_domain,
                    strategy="miss",
                )
                with self._cache_lock:
                    T.exact[prompt_norm] = entry
                    norm_key = normalize_query(prompt_norm)
                    if norm_key:
                        T.norm_hash_index[norm_key] = entry
                    T.rows.append(entry)
                    self._faiss_add(T, emb)
                    if len(T.rows) % 10 == 0:
                        threading.Thread(target=self._save_cache, daemon=True).start()
                try:
                    from redis_cache import store_exact_match, store_embedding
                    store_exact_match(tenant_id, prompt_hash, response_text, model, ttl_seconds)
                    store_embedding(tenant_id, prompt_hash, emb, ttl_seconds)
                except Exception:
                    pass

                # Enrich asynchronously: response embedding, local embedding, clusters
                def _enrich():
                    try:
                        resp_emb = None
                        try:
                            resp_emb = get_embedding(response_text[:500], user_id=user_id)
                        except Exception:
                            pass
                        local_emb = get_local_embedding(prompt_norm) if LOCAL_MODEL_ENABLED else None

                        with self._cache_lock:
                            entry.response_embedding = resp_emb
                            entry.local_embedding = local_emb
                            if local_emb is not None:
                                self._local_faiss_add(T, local_emb)
                            if len(T.rows) % 100 == 0 and len(T.rows) >= 50:
                                self._rebuild_clusters(T)
                    except Exception as e:
                        error_log.debug(f"Enrich failed (non-fatal) | tenant={tenant_id} | {e}")
                threading.Thread(target=_enrich, daemon=True).start()

            except Exception as e:
                error_log.warning(f"Cache store failed | tenant={tenant_id} | {e}")
        threading.Thread(target=_store_fast, daemon=True).start()

        return response_text, meta

    def metrics(self, tenant_id: str) -> dict:
        T = self.tenant(tenant_id)
        total = T.hits + T.misses
        p50 = np.percentile(T.latencies_ms, 50) if T.latencies_ms else 0
        p95 = np.percentile(T.latencies_ms, 95) if T.latencies_ms else 0
        avg_latency = np.mean(T.latencies_ms) if T.latencies_ms else 0
        semantic_hit_ratio = (T.semantic_hits / total) if total > 0 else 0.0

        semantic_events = [e for e in T.events if e.decision == "semantic"]
        avg_cosine = np.mean([e.similarity for e in semantic_events]) if semantic_events else 0.0
        avg_hybrid = np.mean([e.hybrid_score for e in semantic_events if e.hybrid_score > 0]) if semantic_events else 0.0
        high_confidence_hits = len([e for e in semantic_events if e.hybrid_score >= 0.85])

        near_misses = getattr(T, '_near_misses', [])
        tokens_saved_est = T.hits * 100
        entries_with_resp_emb = sum(1 for r in T.rows if r.response_embedding is not None)
        entries_with_local_emb = sum(1 for r in T.rows if r.local_embedding is not None)
        index_type = type(T.index).__name__ if T.index else "none"

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
            "avg_confidence": round(avg_cosine, 3),
            "avg_hybrid_score": round(avg_hybrid, 3),
            "high_confidence_hits": high_confidence_hits,
            "high_confidence_ratio": round((high_confidence_hits / len(semantic_events)) if semantic_events else 0.0, 3),
            "near_miss_count": len(near_misses),
            "domain_thresholds": {k: round(v, 3) for k, v in T.domain_thresholds.items()},
            # Engine info
            "embed_model": EMBED_MODEL,
            "embed_dimensions": EMBED_DIMENSIONS,
            "index_type": index_type,
            "local_model": LOCAL_MODEL_NAME if LOCAL_MODEL_ENABLED else "disabled",
            "cross_encoder": CROSS_ENCODER_MODEL if CROSS_ENCODER_ENABLED else "disabled",
            "entries_with_response_embedding": entries_with_resp_emb,
            "entries_with_local_embedding": entries_with_local_emb,
            "norm_hash_index_size": len(T.norm_hash_index),
            "n_clusters": T.n_clusters,
        }

    def adapt_threshold(self, tenant_id: str):
        """Adapt threshold using both hit ratio and near-miss distribution.

        Strategy:
        - If many near-misses cluster just below threshold → lower threshold
          to capture them (they're likely valid matches).
        - If hit ratio is very high → raise threshold to improve precision.
        - Near-miss data provides a direct signal the old approach lacked.
        """
        T = self.tenant(tenant_id)
        total = T.hits + T.misses
        if total < 10:
            return

        hit_ratio = T.hits / total
        near_misses = getattr(T, '_near_misses', [])

        # Near-miss pull: if many near-misses are within 0.05 of threshold,
        # there's a cluster of queries being needlessly rejected.
        if len(near_misses) >= 5:
            close_misses = [s for s in near_misses if s >= T.sim_threshold - 0.05]
            close_ratio = len(close_misses) / len(near_misses)
            if close_ratio > 0.5:
                T.sim_threshold = max(0.40, T.sim_threshold - 0.02)
                semantic_log.info(
                    f"{tenant_id} | threshold_adapted_down | "
                    f"close_miss_ratio={close_ratio:.2f} | new={T.sim_threshold:.3f}"
                )
                return

        if hit_ratio < 0.25:
            T.sim_threshold = max(0.40, T.sim_threshold - 0.015)
        elif hit_ratio > 0.80:
            T.sim_threshold = min(0.75, T.sim_threshold + 0.01)

    def warmup(
        self,
        tenant_id: str,
        entries: List[dict],
        user_id: Optional[str] = None,
        ttl_seconds: int = 7 * 24 * 3600,
        skip_duplicates: bool = True,
    ) -> dict:
        """
        Pre-populate cache with historical (prompt, response) pairs.
        Each entry: {"prompt": str, "response": str, "model": str (optional)}
        Returns: {"added": int, "skipped": int, "errors": int}
        """
        T = self.tenant(tenant_id)
        added, skipped, errors = 0, 0, 0
        for i, item in enumerate(entries):
            try:
                prompt = (item.get("prompt") or item.get("query") or "").strip()
                response_text = (item.get("response") or item.get("answer") or item.get("content") or "").strip()
                model = item.get("model") or CHAT_MODEL
                if not prompt or not response_text:
                    skipped += 1
                    continue
                prompt_norm = self.norm_text(prompt)
                if skip_duplicates and prompt_norm in T.exact:
                    skipped += 1
                    continue
                emb = get_embedding(prompt, user_id=user_id)
                user_text = prompt
                resp_emb = None
                try:
                    resp_emb = get_embedding(response_text[:500], user_id=user_id)
                except Exception:
                    pass
                local_emb = get_local_embedding(prompt_norm) if LOCAL_MODEL_ENABLED else None

                entry = CacheEntry(
                    prompt_norm=prompt_norm,
                    response_text=response_text,
                    embedding=emb,
                    model=model,
                    ttl_seconds=ttl_seconds,
                    domain=domain_hint(user_text),
                    strategy="warmup",
                    response_embedding=resp_emb,
                    local_embedding=local_emb,
                )
                with self._cache_lock:
                    T.exact[prompt_norm] = entry
                    norm_key = normalize_query(prompt_norm)
                    if norm_key:
                        T.norm_hash_index[norm_key] = entry
                    T.rows.append(entry)
                    self._faiss_add(T, emb)
                    if local_emb is not None:
                        self._local_faiss_add(T, local_emb)
                added += 1
                try:
                    from redis_cache import store_exact_match, store_embedding
                    prompt_hash = hashlib.md5(prompt_norm.encode()).hexdigest()
                    store_exact_match(tenant_id, prompt_hash, response_text, model, ttl_seconds)
                    store_embedding(tenant_id, prompt_hash, emb, ttl_seconds)
                except Exception:
                    pass
                if (i + 1) % 5 == 0:
                    time.sleep(0.05)
            except Exception as e:
                errors += 1
                error_log.warning(f"Warmup entry failed | tenant={tenant_id} | idx={i} | error={e}")
        if added > 0:
            threading.Thread(target=self._save_cache, daemon=True).start()
        return {"added": added, "skipped": skipped, "errors": errors}

svc = SemanticCacheService()

# Save cache on shutdown
import atexit

def _save_cache_on_exit():
    """Save cache on normal exit."""
    try:
        svc._save_cache()
        system_log.info("Shutdown | cache saved")
    except Exception as e:
        print(f"Failed to save cache on exit: {e}")

atexit.register(_save_cache_on_exit)

# -----------------------------
# FastAPI app + middleware + rate limiting
# -----------------------------
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Semantis AI - Semantic Cache API", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with detailed information."""
    import uuid
    start_time = time.time()
    request_id = str(uuid.uuid4())[:8]
    
    # Get client IP
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Log request
    access_log.info(
        f"{request_id} | REQ | {request.method} {request.url.path} | "
        f"tenant=extracting | ip={client_ip} | ua={user_agent[:100]}"
    )
    
    try:
        response = await call_next(request)
        process_time = round((time.time() - start_time) * 1000, 2)
        response_size = 0
        if hasattr(response, 'body'):
            try:
                response_size = len(response.body) if response.body else 0
            except:
                pass
        
        access_log.info(
            f"{request_id} | RESP | {request.method} {request.url.path} | "
            f"status={response.status_code} | time={process_time}ms | size={response_size}B"
        )
        
        # Log slow requests
        if process_time > 5000:  # > 5 seconds
            performance_log.warning(
                f"{request_id} | SLOW_REQUEST | {request.method} {request.url.path} | "
                f"time={process_time}ms | ip={client_ip}"
            )
        
        return response
    except Exception as e:
        process_time = round((time.time() - start_time) * 1000, 2)
        error_log.exception(
            f"{request_id} | REQ_ERROR | {request.method} {request.url.path} | "
            f"ip={client_ip} | time={process_time}ms | error={str(e)}"
        )
        raise

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
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

# Include admin router (after app is created)
def setup_admin_routes():
    """Setup admin routes after all dependencies are loaded."""
    try:
        from admin_api import admin_router
        app.include_router(admin_router)
        system_log.info("Admin routes registered")
    except Exception as e:
        error_log.warning(f"Could not register admin routes: {e}")

# Setup admin routes
setup_admin_routes()

# Simple API-key format: Bearer sc-{tenant}-{anything}
API_KEY_REGEX = re.compile(r"^Bearer\s+(sc-[A-Za-z0-9_-]+)$")
_api_key_cache: Dict[str, dict] = {}  # token -> {"user_id": ..., "ts": epoch}

# Request-scoped API key context (safe for concurrent async requests)
_current_api_key_var: ContextVar[dict] = ContextVar('_current_api_key', default={"key": None, "user_id": None})

def get_tenant_from_key(request: Request) -> str:
    client_ip = request.client.host if request.client else "unknown"
    auth = request.headers.get("Authorization", "")
    m = API_KEY_REGEX.match(auth)
    if not m:
        security_log.warning(
            f"Auth failed | ip={client_ip} | reason=invalid_format | "
            f"header_length={len(auth)} | path={request.url.path}"
        )
        error_log.error(f"Unauthorized access | ip={client_ip} | Header length: {len(auth)}")
        raise HTTPException(status_code=401, detail="Missing or invalid API key")
    token = m.group(1)
    parts = token.split("-")
    if len(parts) < 3:
        security_log.warning(
            f"Auth failed | ip={client_ip} | reason=malformed_key | "
            f"token_prefix={token[:10]} | path={request.url.path}"
        )
        raise HTTPException(status_code=401, detail="Malformed API key")
    tenant = parts[1]
    
    ctx = {"key": token, "user_id": None, "org_id": None, "scope": "read-write"}
    _current_api_key_var.set(ctx)
    
    # Fast in-memory API key cache (avoids DB round-trip on every request)
    cached = _api_key_cache.get(token)
    if cached and (time.time() - cached["ts"]) < 300:
        ctx["user_id"] = cached.get("user_id")
        ctx["org_id"] = cached.get("org_id")
        ctx["scope"] = cached.get("scope", "read-write")
        _current_api_key_var.set(ctx)
        # Check expiration
        if cached.get("expires_at") and time.time() > cached["expires_at"]:
            raise HTTPException(status_code=401, detail="API key expired")
        # Check IP allowlist
        allowed = cached.get("allowed_ips")
        if allowed and client_ip not in allowed:
            security_log.warning(f"IP denied | tenant={tenant} | ip={client_ip}")
            raise HTTPException(status_code=403, detail="IP not allowed for this key")
        def _bg_usage():
            try:
                from database import update_api_key_usage
                update_api_key_usage(token, tenant)
            except Exception:
                pass
        threading.Thread(target=_bg_usage, daemon=True).start()
        return tenant

    try:
        from database import get_api_key_info, update_api_key_usage
        key_info = get_api_key_info(token)
        if key_info:
            # Check expiration
            exp = key_info.get("expires_at")
            if exp and str(exp) < time.strftime("%Y-%m-%d %H:%M:%S"):
                raise HTTPException(status_code=401, detail="API key expired")
            # Check IP allowlist
            allowed = key_info.get("allowed_ips")
            if allowed and client_ip not in allowed:
                security_log.warning(f"IP denied | tenant={tenant} | ip={client_ip}")
                raise HTTPException(status_code=403, detail="IP not allowed for this key")
            
            update_api_key_usage(token, tenant)
            ctx["user_id"] = key_info.get('user_id')
            ctx["org_id"] = str(key_info.get('org_id', '')) or None
            ctx["scope"] = key_info.get('scope', 'read-write')
            _current_api_key_var.set(ctx)
            _api_key_cache[token] = {
                "user_id": ctx["user_id"],
                "org_id": ctx["org_id"],
                "scope": ctx["scope"],
                "allowed_ips": allowed,
                "expires_at": None,
                "ts": time.time(),
            }
            security_log.debug(
                f"Auth success | tenant={tenant} | ip={client_ip} | "
                f"plan={key_info.get('plan', 'unknown')} | scope={ctx['scope']} | "
                f"org_id={ctx['org_id']}"
            )
        else:
            security_log.warning(
                f"API key not found | tenant={tenant} | ip={client_ip} | "
                f"key_prefix={token[:20]}"
            )
    except HTTPException:
        raise
    except Exception as e:
        error_log.warning(f"Database operation failed | tenant={tenant} | error={str(e)}")
    
    return tenant


def _require_scope(request: Request, required: str):
    """Check that the current API key has the required scope."""
    ctx = _current_api_key_var.get()
    scope = ctx.get("scope", "read-write")
    scope_levels = {"read-only": 0, "read-write": 1, "admin": 2}
    if scope_levels.get(scope, 0) < scope_levels.get(required, 0):
        raise HTTPException(
            status_code=403,
            detail=f"Insufficient permissions. Required: {required}, got: {scope}"
        )

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
    stream: bool = False

# -----------------------------
# Endpoints
# -----------------------------
@app.get("/health")
def health():
    """Health check endpoint with system status."""
    import sys
    
    try:
        try:
            import psutil
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=0)
            has_system_metrics = True
        except ImportError:
            has_system_metrics = False
        
        total_tenants = len(svc.tenants)
        total_entries = sum(len(t.rows) for t in svc.tenants.values())
        
        # Redis health
        try:
            from redis_cache import health_check as redis_health
            redis_status = redis_health()
        except Exception:
            redis_status = {"status": "unavailable"}
        
        health_status = {
            "status": "ok",
            "service": "semantic-cache",
            "version": "3.0.0",
            "engine": {
                "embed_model": EMBED_MODEL,
                "embed_dimensions": EMBED_DIMENSIONS,
                "local_model": LOCAL_MODEL_NAME if LOCAL_MODEL_ENABLED else "disabled",
                "cross_encoder": CROSS_ENCODER_MODEL if CROSS_ENCODER_ENABLED else "disabled",
            },
            "cache": {
                "tenants": total_tenants,
                "total_entries": total_entries,
            },
            "redis": redis_status,
        }
        
        if has_system_metrics:
            health_status["system"] = {
                "memory_percent": round(memory.percent, 2),
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "cpu_percent": round(cpu_percent, 2),
            }
        
        return health_status
    except Exception as e:
        error_log.exception(f"Health check failed | error={str(e)}")
        return {"status": "error", "service": "semantic-cache", "version": "2.0.0"}

@app.get("/metrics")
def get_metrics(tenant: str = Depends(get_tenant_from_key)):
    """Get cache performance metrics for the tenant."""
    svc.adapt_threshold(tenant)
    m = svc.metrics(tenant)
    access_log.info(f"{tenant} | /metrics | hit_ratio={m['hit_ratio']}")
    return m

@app.get("/prometheus/metrics")
def prometheus_metrics():
    """Prometheus metrics endpoint."""
    try:
        from prometheus_metrics import get_metrics_response
        return get_metrics_response()
    except ImportError:
        # Prometheus not available, return basic metrics
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(
            "# Prometheus metrics not available. Install prometheus-client for full metrics.\n"
            "# Basic metrics:\n"
            f"cache_entries_total {sum(len(t.rows) for t in svc.tenants.values())}\n"
            f"cache_tenants_total {len(svc.tenants)}\n",
            media_type="text/plain"
        )
    except Exception as e:
        error_log.exception(f"Prometheus metrics endpoint failed | error={str(e)}")
        raise HTTPException(status_code=500, detail="Metrics endpoint failed")

@app.get("/query")
@limiter.limit("60/minute")
def simple_query(request: Request, prompt: str = Query(...), model: str = CHAT_MODEL, tenant: str = Depends(get_tenant_from_key)):
    messages = [{"role": "user", "content": prompt}]
    prompt_norm = SemanticCacheService.norm_text(prompt)
    prompt_hash = hashlib.md5(prompt_norm.encode()).hexdigest()[:8]
    
    endpoint_start = time.time()
    try:
        # Get user_id from current API key context
        _ctx = _current_api_key_var.get()
        user_id = _ctx.get("user_id")
        ans, meta = svc.query(tenant, prompt_norm, messages, model, user_id=user_id)
        query_time = round((time.time() - endpoint_start) * 1000, 2)
        
        # Get metrics (fast - just reading from memory)
        metrics_start = time.time()
        metrics = svc.metrics(tenant)
        metrics_time = round((time.time() - metrics_start) * 1000, 2)
        
        # Enhanced logging (fast - just file write)
        log_start = time.time()
        access_log.info(
            f"{tenant} | /query | {meta['hit']} | sim={meta['similarity']:.3f} | "
            f"latency={meta['latency_ms']}ms | prompt_hash={prompt_hash} | "
            f"model={model} | prompt_len={len(prompt)}"
        )
        log_time = round((time.time() - log_start) * 1000, 2)
        
        # Capture context for async logging (ContextVar is not inherited by threads)
        _log_api_key = _ctx.get("key", "unknown")
        _log_user_id = user_id
        
        # Log usage to database asynchronously (non-blocking - database can be slow)
        def log_usage_async():
            try:
                from database import log_usage
                api_key = _log_api_key
                user_id = _log_user_id
                log_usage(
                    api_key=api_key,
                    tenant_id=tenant,
                    endpoint="/query",
                    request_count=1,
                    cache_hits=1 if meta.get('hit') != 'miss' else 0,
                    cache_misses=1 if meta.get('hit') == 'miss' else 0,
                    tokens_used=0,
                    cost_estimate=0,
                    user_id=user_id
                )
            except Exception as e:
                error_log.warning(f"Could not log usage to database | tenant={tenant} | error={str(e)}")
        
        # Run database logging in background thread (non-blocking)
        threading.Thread(target=log_usage_async, daemon=True).start()
        
        # Log timing breakdown
        before_return = time.time()
        endpoint_total = round((before_return - endpoint_start) * 1000, 2)
        access_log.debug(
            f"{tenant} | /query-timing | query={query_time}ms | metrics={metrics_time}ms | "
            f"log={log_time}ms | total={endpoint_total}ms | response_len={len(ans)}"
        )
        
        # Return immediately with metrics (database logging happens async)
        return {"answer": ans, "meta": meta, "metrics": metrics}
    except Exception as e:
        error_log.exception(
            f"{tenant} | /query | error: {e} | prompt_hash={prompt_hash} | "
            f"prompt_len={len(prompt)} | model={model}"
        )
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

class SettingsUpdate(BaseModel):
    sim_threshold: Optional[float] = None
    ttl_days: Optional[int] = None
    domain_thresholds: Optional[Dict[str, float]] = None

@app.get("/settings")
def get_settings(tenant: str = Depends(get_tenant_from_key)):
    """Get current cache settings for the tenant."""
    T = svc.tenant(tenant)
    return {
        "sim_threshold": round(T.sim_threshold, 3),
        "ttl_days": 7,
        "entries": len(T.rows),
        "domain_thresholds": {k: round(v, 3) for k, v in T.domain_thresholds.items()},
        "available_domains": list(DOMAIN_MAP.keys()),
        "embed_model": EMBED_MODEL,
        "embed_dimensions": EMBED_DIMENSIONS,
        "local_model": LOCAL_MODEL_NAME if LOCAL_MODEL_ENABLED else "disabled",
        "cross_encoder": CROSS_ENCODER_MODEL if CROSS_ENCODER_ENABLED else "disabled",
        "ivf_upgrade_threshold": IVF_UPGRADE_THRESHOLD,
        "index_type": type(T.index).__name__ if T.index else "none",
        "norm_hash_index_size": len(T.norm_hash_index),
        "n_clusters": T.n_clusters,
    }

class WarmupEntry(BaseModel):
    prompt: str = ""
    response: str = ""
    model: Optional[str] = None


class WarmupRequest(BaseModel):
    entries: List[WarmupEntry]
    tenant: Optional[str] = None
    skip_duplicates: bool = True


@app.post("/api/cache/warmup")
@limiter.limit("10/hour")
def cache_warmup(body: WarmupRequest, request: Request):
    """
    Pre-populate cache with historical (prompt, response) pairs.
    Use your previous application queries to warm the cache for immediate semantic hits.
    Requires Supabase JWT. Entries: [{"prompt": "...", "response": "...", "model": "gpt-4o-mini"}]
    """
    try:
        user = _get_user_from_supabase_token(request)
        from database import get_user_orgs, get_api_key_info, list_api_keys
        orgs = get_user_orgs(user["id"])
        tenant = body.tenant
        if not tenant and orgs:
            tenant = orgs[0].get("slug")
        if not tenant:
            keys = list_api_keys(user_id=user["id"])
            if keys:
                tenant = keys[0].get("tenant_id", f"usr_{user['id'][:8]}")
        if not tenant:
            tenant = f"usr_{user['id'][:8]}"
        entries = [
            {"prompt": e.prompt, "response": e.response, "model": e.model}
            for e in body.entries
        ]
        if len(entries) > 500:
            raise HTTPException(status_code=400, detail="Maximum 500 entries per request")
        result = svc.warmup(
            tenant,
            entries,
            user_id=user["id"],
            skip_duplicates=body.skip_duplicates,
        )
        app_log.info(f"Cache warmup | tenant={tenant} | added={result['added']} | skipped={result['skipped']} | errors={result['errors']}")
        return {"message": "Warmup complete", **result}
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"Cache warmup failed | error={e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/cache/warmup")
@limiter.limit("10/hour")
def cache_warmup_api_key(body: WarmupRequest, request: Request, tenant: str = Depends(get_tenant_from_key)):
    """
    Pre-populate cache with historical (prompt, response) pairs. Uses API key auth.
    Entries: [{"prompt": "...", "response": "...", "model": "gpt-4o-mini"}]
    """
    try:
        _ctx = _current_api_key_var.get()
        user_id = _ctx.get("user_id")
        entries = [
            {"prompt": e.prompt, "response": e.response, "model": e.model}
            for e in body.entries
        ]
        if len(entries) > 500:
            raise HTTPException(status_code=400, detail="Maximum 500 entries per request")
        result = svc.warmup(
            tenant,
            entries,
            user_id=user_id,
            skip_duplicates=body.skip_duplicates,
        )
        return {"message": "Warmup complete", **result}
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"Cache warmup failed | error={e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/settings")
def update_settings(body: SettingsUpdate, tenant: str = Depends(get_tenant_from_key)):
    """Update cache settings for the tenant."""
    T = svc.tenant(tenant)
    changed = {}
    if body.sim_threshold is not None:
        clamped = max(0.40, min(0.99, body.sim_threshold))
        T.sim_threshold = clamped
        changed["sim_threshold"] = round(clamped, 3)
    if body.ttl_days is not None:
        changed["ttl_days"] = max(1, min(90, body.ttl_days))
    if body.domain_thresholds is not None:
        valid_domains = set(DOMAIN_MAP.keys()) | {"general"}
        for domain, thresh in body.domain_thresholds.items():
            if domain in valid_domains:
                T.domain_thresholds[domain] = max(0.40, min(0.99, thresh))
        changed["domain_thresholds"] = {k: round(v, 3) for k, v in T.domain_thresholds.items()}
    access_log.info(f"{tenant} | /settings | updated={changed}")
    return {"status": "ok", "settings": {
        **changed,
        "sim_threshold": round(T.sim_threshold, 3),
        "domain_thresholds": {k: round(v, 3) for k, v in T.domain_thresholds.items()},
    }}

def _get_user_from_supabase_token(request: Request) -> dict:
    """Extract and verify Supabase JWT from Authorization header. Returns user profile dict."""
    from auth import verify_token
    from database import get_user_by_id

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")

    token = auth_header.split(" ")[1]
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    user["id"] = str(user["id"])
    return user


@app.get("/api/keys/current")
def get_current_api_key(request: Request):
    """Get the current user's API key (requires Supabase JWT)."""
    try:
        user = _get_user_from_supabase_token(request)
        from database import list_api_keys

        api_keys = list_api_keys(user_id=user["id"])
        if api_keys:
            active_keys = [k for k in api_keys if k.get('is_active')]
            if active_keys:
                key = active_keys[0]
                return {
                    "api_key": key.get('api_key'),
                    "tenant_id": key.get('tenant_id'),
                    "plan": key.get('plan', 'free'),
                    "created_at": str(key.get('created_at', '')),
                    "exists": True
                }

        return {"exists": False, "message": "No API key found. Generate one in Settings."}
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"Get API key failed | error={str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get API key")

@app.post("/api/keys/generate")
@limiter.limit("5/hour")
def generate_api_key_endpoint(
    request: Request,
    tenant: Optional[str] = Query(None),
    length: int = Query(32, ge=16, le=64),
    plan: str = Query("free"),
    label: Optional[str] = Query(None),
    scope: str = Query("read-write"),
):
    """Generate a new API key for the authenticated user (requires Supabase JWT)."""
    try:
        user = _get_user_from_supabase_token(request)
        user_id = user["id"]
        from api_key_generator import generate_api_key
        from database import create_api_key, list_api_keys, get_api_key_info, get_user_orgs

        existing_keys = list_api_keys(user_id=user_id)
        if existing_keys and tenant is None:
            existing_key = existing_keys[0]
            return {
                "api_key": existing_key.get('api_key'),
                "tenant_id": existing_key.get('tenant_id'),
                "plan": existing_key.get('plan', plan),
                "created_at": str(existing_key.get('created_at', '')),
                "format": f"Bearer {existing_key.get('api_key')}",
                "message": "Using existing API key."
            }

        # Resolve org for user
        org_id = None
        try:
            orgs = get_user_orgs(user_id)
            if orgs:
                org = orgs[0]
                org_id = str(org["id"])
                if tenant is None:
                    tenant = org["slug"]
        except Exception:
            pass

        if tenant is None:
            tenant = f"usr_{user_id[:8]}"

        api_key, tenant_id = generate_api_key(tenant=tenant, length=length, auto_tenant=False)
        result = create_api_key(
            api_key, tenant_id, user_id=user_id, plan=plan,
            org_id=org_id, scope=scope, label=label,
        )
        if not result:
            raise HTTPException(status_code=500, detail="Failed to save API key to database")

        saved_key = get_api_key_info(api_key)
        if not saved_key:
            raise HTTPException(status_code=500, detail="API key was not saved properly")

        # Audit log
        try:
            from database import log_audit
            log_audit(
                org_id=org_id, user_id=user_id, action="api_key.created",
                resource_type="api_key", resource_id=api_key[:20],
                details={"scope": scope, "label": label},
                ip_address=request.client.host if request.client else None,
            )
        except Exception:
            pass

        app_log.info(f"API key generated | tenant={tenant_id} | user_id={user_id} | org={org_id}")

        return {
            "api_key": api_key,
            "tenant_id": tenant_id,
            "org_id": org_id,
            "plan": plan,
            "scope": scope,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "format": f"Bearer {api_key}",
            "message": "API key generated successfully. Save this key securely."
        }
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"API key generation failed | error={str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate API key: {str(e)}")

# -----------------------------
# Authentication endpoints (Supabase JWT)
# Signup / login / password-reset are handled entirely by the
# frontend via @supabase/supabase-js. The backend only verifies tokens.
# -----------------------------

@app.get("/api/auth/me")
def get_current_user(request: Request):
    """Get current authenticated user info from Supabase JWT."""
    try:
        user = _get_user_from_supabase_token(request)
        orgs = []
        try:
            from database import get_user_orgs
            orgs = get_user_orgs(user["id"])
        except Exception:
            pass
        return {
            "id": user['id'],
            "email": user['email'],
            "name": user['name'],
            "is_admin": user.get('is_admin', False),
            "created_at": str(user.get('created_at', '')),
            "orgs": [{
                "id": str(o["id"]),
                "name": o["name"],
                "slug": o["slug"],
                "plan": o.get("plan", "free"),
                "role": o.get("role", "member"),
            } for o in orgs],
        }
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"Get current user failed | error={str(e)}")
        raise HTTPException(status_code=401, detail="Authentication failed")

class OpenAIKeyRequest(BaseModel):
    api_key: str

@app.post("/api/users/openai-key")
def set_user_openai_key_endpoint(request: OpenAIKeyRequest, auth_request: Request):
    """Set user's OpenAI API key (requires Supabase JWT)."""
    try:
        user = _get_user_from_supabase_token(auth_request)
        from database import set_user_openai_key
        from encryption import encrypt_api_key

        try:
            encrypted_key = encrypt_api_key(request.api_key)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        success = set_user_openai_key(user["id"], encrypted_key)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save OpenAI API key")

        app_log.info(f"OpenAI API key set | user_id={user['id']}")
        return {"message": "OpenAI API key saved successfully", "key_set": True}
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"Set OpenAI key failed | error={str(e)}")
        raise HTTPException(status_code=500, detail="Failed to set OpenAI API key")

@app.get("/api/users/openai-key")
def get_user_openai_key_status(auth_request: Request):
    """Check if user has OpenAI API key set (requires Supabase JWT)."""
    try:
        user = _get_user_from_supabase_token(auth_request)
        from database import get_user_openai_key_encrypted

        encrypted_key = get_user_openai_key_encrypted(user["id"])
        if encrypted_key:
            return {"key_set": True, "key_preview": "sk-..." + encrypted_key[-4:] if len(encrypted_key) > 4 else "sk-***"}
        return {"key_set": False, "message": "No OpenAI API key configured"}
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"Get OpenAI key status failed | error={str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get OpenAI API key status")

@app.delete("/api/users/openai-key")
def remove_user_openai_key(auth_request: Request):
    """Remove user's OpenAI API key (requires Supabase JWT)."""
    try:
        user = _get_user_from_supabase_token(auth_request)
        from database import clear_user_openai_key

        success = clear_user_openai_key(user["id"])
        if not success:
            raise HTTPException(status_code=500, detail="Failed to remove OpenAI API key")

        app_log.info(f"OpenAI API key removed | user_id={user['id']}")
        return {"message": "OpenAI API key removed successfully", "key_set": False}
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"Remove OpenAI key failed | error={str(e)}")
        raise HTTPException(status_code=500, detail="Failed to remove OpenAI API key")

@app.post("/api/auth/logout")
def logout():
    """Logout (client clears Supabase session)."""
    return {"message": "Logged out successfully"}

# ── Organization endpoints ──

class CreateOrgRequest(BaseModel):
    name: str
    slug: str

@app.post("/api/orgs")
def create_org(body: CreateOrgRequest, request: Request):
    """Create a new organization (requires Supabase JWT)."""
    try:
        user = _get_user_from_supabase_token(request)
        from database import create_organization, log_audit
        org = create_organization(body.name, body.slug, user["id"])
        if not org:
            raise HTTPException(status_code=400, detail="Could not create organization")
        log_audit(
            org_id=str(org["id"]), user_id=user["id"], action="org.created",
            resource_type="organization", resource_id=str(org["id"]),
            ip_address=request.client.host if request.client else None,
        )
        return {"org": {k: str(v) for k, v in org.items()}}
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"Create org failed | error={e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/orgs")
def list_user_orgs(request: Request):
    """List organizations for the current user."""
    try:
        user = _get_user_from_supabase_token(request)
        from database import get_user_orgs
        orgs = get_user_orgs(user["id"])
        return {"orgs": [{k: str(v) for k, v in o.items()} for o in orgs]}
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"List orgs failed | error={e}")
        raise HTTPException(status_code=500, detail=str(e))

class InviteMemberRequest(BaseModel):
    email: str
    role: str = "member"

@app.post("/api/orgs/{org_id}/members")
def invite_member(org_id: str, body: InviteMemberRequest, request: Request):
    """Add a member to an organization."""
    try:
        user = _get_user_from_supabase_token(request)
        from database import add_org_member, get_user_by_email, log_audit
        target = get_user_by_email(body.email)
        if not target:
            raise HTTPException(status_code=404, detail="User not found")
        ok = add_org_member(org_id, str(target["id"]), body.role)
        if not ok:
            raise HTTPException(status_code=400, detail="Already a member")
        log_audit(
            org_id=org_id, user_id=user["id"], action="member.added",
            resource_type="org_member", resource_id=str(target["id"]),
            details={"role": body.role, "email": body.email},
            ip_address=request.client.host if request.client else None,
        )
        return {"message": f"Added {body.email} as {body.role}"}
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"Invite member failed | error={e}")
        raise HTTPException(status_code=500, detail=str(e))

class OrgSettingsUpdate(BaseModel):
    webhook_url: Optional[str] = None

@app.patch("/api/orgs/{org_id}/settings")
def update_org_settings_endpoint(org_id: str, body: OrgSettingsUpdate, request: Request):
    """Update organization settings (e.g. webhook URL for cache events)."""
    try:
        user = _get_user_from_supabase_token(request)
        from database import update_org_settings, get_user_orgs
        orgs = get_user_orgs(user["id"])
        if not any(str(o["id"]) == org_id for o in orgs):
            raise HTTPException(status_code=403, detail="Not a member of this organization")
        updates = {}
        if body.webhook_url is not None:
            updates["webhook_url"] = body.webhook_url.strip() or None
        if updates:
            update_org_settings(org_id, updates)
        return {"message": "Settings updated"}
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"Update org settings failed | error={e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/orgs/{org_id}/audit")
def get_audit_logs(org_id: str, request: Request, limit: int = Query(50, ge=1, le=500)):
    """Get audit logs for an organization."""
    try:
        _get_user_from_supabase_token(request)
        from database import get_db_connection
        from psycopg2.extras import RealDictCursor
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(
                """SELECT id, org_id, user_id, action, resource_type, resource_id,
                          details, ip_address, created_at
                   FROM audit_logs WHERE org_id = %s
                   ORDER BY created_at DESC LIMIT %s""",
                (org_id, limit)
            )
            logs = [dict(r) for r in cur.fetchall()]
        return {"audit_logs": [{k: str(v) for k, v in l.items()} for l in logs]}
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"Audit logs failed | error={e}")
        raise HTTPException(status_code=500, detail=str(e))

def _sse_chunk(content: str, chunk_id: str) -> str:
    """Format a content delta as OpenAI SSE chunk."""
    obj = {
        "id": chunk_id,
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": CHAT_MODEL,
        "choices": [{"index": 0, "delta": {"content": content}, "finish_reason": None}],
    }
    return f"data: {json.dumps(obj)}\n\n"


@app.post("/v1/chat/completions")
@limiter.limit("60/minute")
def openai_compatible(request: Request, body: ChatRequest, tenant: str = Depends(get_tenant_from_key)):
    """OpenAI-compatible endpoint for zero-code integration.
    
    Point your OpenAI client at this server:
        client = openai.OpenAI(base_url="https://api.semantis.ai/v1", api_key="sc-...")
    Supports stream=True for streaming responses.
    """
    _ctx = _current_api_key_var.get()
    _require_scope(request, "read-write")
    
    prompt_norm = SemanticCacheService.norm_text(
        " ".join([m.content for m in body.messages if m.role == "user"]) or ""
    )
    try:
        user_id = _ctx.get("user_id")
        messages = [m.model_dump() for m in body.messages]
        chunk_id = f"chatcmpl-{hashlib.md5(str(time.time()).encode()).hexdigest()[:24]}"

        if body.stream:
            def stream_generator():
                ans, meta = svc.query(
                    tenant,
                    prompt_norm,
                    messages,
                    body.model,
                    ttl_seconds=body.ttl_seconds,
                    temperature=body.temperature,
                    user_id=user_id,
                )
                _log_key = _ctx.get("key", "unknown")
                _log_uid = _ctx.get("user_id")
                _log_org = _ctx.get("org_id")
                _log_hit = meta.get("hit")
                def _bg_log():
                    try:
                        from database import log_usage
                        log_usage(
                            api_key=_log_key, tenant_id=tenant,
                            endpoint="/v1/chat/completions", request_count=1,
                            cache_hits=1 if _log_hit != "miss" else 0,
                            cache_misses=1 if _log_hit == "miss" else 0,
                            tokens_used=0, cost_estimate=0,
                            user_id=_log_uid, org_id=_log_org,
                        )
                    except Exception:
                        pass
                threading.Thread(target=_bg_log, daemon=True).start()
                access_log.info(f"{tenant} | /v1/chat/completions | stream | {meta['hit']} | {meta['latency_ms']}ms")
                try:
                    from webhooks import fire_cache_event
                    fire_cache_event(
                        _ctx.get("org_id"),
                        tenant,
                        "cache.decision",
                        {"hit": meta["hit"], "similarity": meta["similarity"], "latency_ms": meta["latency_ms"]},
                    )
                except Exception:
                    pass
                for i in range(0, len(ans), 4):
                    chunk = ans[i : i + 4]
                    if chunk:
                        yield _sse_chunk(chunk, chunk_id)
                yield f"data: {json.dumps({'id': chunk_id, 'object': 'chat.completion.chunk', 'choices': [{'index': 0, 'delta': {}, 'finish_reason': 'stop'}]})}\n\n"

            return StreamingResponse(
                stream_generator(),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
            )

        ans, meta = svc.query(
            tenant,
            prompt_norm,
            messages,
            body.model,
            ttl_seconds=body.ttl_seconds,
            temperature=body.temperature,
            user_id=user_id,
        )
        _log_key = _ctx.get("key", "unknown")
        _log_uid = _ctx.get("user_id")
        _log_org = _ctx.get("org_id")
        _log_hit = meta.get("hit")
        def _bg_log():
            try:
                from database import log_usage
                log_usage(
                    api_key=_log_key, tenant_id=tenant,
                    endpoint="/v1/chat/completions", request_count=1,
                    cache_hits=1 if _log_hit != "miss" else 0,
                    cache_misses=1 if _log_hit == "miss" else 0,
                    tokens_used=0, cost_estimate=0,
                    user_id=_log_uid, org_id=_log_org,
                )
            except Exception:
                pass
        threading.Thread(target=_bg_log, daemon=True).start()
        
        prompt_tokens = sum(len(m.content.split()) * 4 // 3 for m in body.messages)
        completion_tokens = len(ans.split()) * 4 // 3
        
        access_log.info(f"{tenant} | /v1/chat/completions | {meta['hit']} | sim={meta['similarity']:.3f} | {meta['latency_ms']}ms")
        try:
            from webhooks import fire_cache_event
            fire_cache_event(
                _ctx.get("org_id"),
                tenant,
                "cache.decision",
                {"hit": meta["hit"], "similarity": meta["similarity"], "latency_ms": meta["latency_ms"]},
            )
        except Exception:
            pass
        return {
            "id": chunk_id,
            "object": "chat.completion",
            "created": int(time.time()),
            "model": body.model,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": ans},
                "finish_reason": "stop",
                "logprobs": None,
            }],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
            "system_fingerprint": f"semantis-{meta.get('hit', 'miss')}",
            "meta": meta,
        }
    except Exception as e:
        error_log.exception(f"{tenant} | /v1/chat/completions | error: {e}")
        raise HTTPException(status_code=500, detail="Internal error")


@app.get("/v1/models")
def list_models(tenant: str = Depends(get_tenant_from_key)):
    """OpenAI-compatible models listing for proxy compatibility."""
    return {
        "object": "list",
        "data": [
            {"id": "gpt-4o-mini", "object": "model", "created": 1700000000, "owned_by": "semantis-cache"},
            {"id": "gpt-4o", "object": "model", "created": 1700000000, "owned_by": "semantis-cache"},
            {"id": "gpt-4", "object": "model", "created": 1700000000, "owned_by": "semantis-cache"},
            {"id": "gpt-3.5-turbo", "object": "model", "created": 1700000000, "owned_by": "semantis-cache"},
        ],
    }


# ── Billing endpoints ──

@app.get("/api/billing/plans")
def get_billing_plans():
    """Get available billing plans and their limits."""
    from billing import PLANS, is_enabled
    return {"plans": PLANS, "stripe_enabled": is_enabled()}


@app.get("/api/billing/status")
def get_billing_status(request: Request):
    """Get billing status for the current user's org."""
    try:
        user = _get_user_from_supabase_token(request)
        from database import get_user_orgs, get_usage_stats_by_org
        from billing import get_plan_limits
        orgs = get_user_orgs(user["id"])
        if not orgs:
            return {"plan": "free", "limits": get_plan_limits("free")}
        org = orgs[0]
        plan = org.get("plan", "free")
        
        # Get current usage by org_id (not slug)
        usage = {}
        try:
            usage = get_usage_stats_by_org(str(org["id"]), days=30)
        except Exception:
            pass
        
        total_hits = int(usage.get("total_hits", 0))
        total_requests = int(usage.get("total_requests", 0))
        total_misses = int(usage.get("total_misses", 0))
        total_cost = float(usage.get("total_cost", 0))
        # Estimate savings: avg cost per miss * hits (cost we avoided)
        if total_misses > 0 and total_cost > 0:
            avg_cost_per_request = total_cost / total_misses
            estimated_savings_usd = round(total_hits * avg_cost_per_request, 2)
        else:
            estimated_savings_usd = round(total_hits * 0.002, 2)  # fallback $0.002/hit
        
        limits = get_plan_limits(plan)
        return {
            "org_id": str(org["id"]),
            "org_name": org["name"],
            "plan": plan,
            "limits": limits,
            "usage_30d": usage,
            "savings_estimate": {
                "cached_requests": total_hits,
                "total_requests": total_requests,
                "estimated_savings_usd": estimated_savings_usd,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"Billing status failed | error={e}")
        raise HTTPException(status_code=500, detail=str(e))


class UpgradePlanRequest(BaseModel):
    plan: str
    success_url: str = "http://localhost:3000/settings?billing=success"
    cancel_url: str = "http://localhost:3000/settings?billing=cancel"

@app.post("/api/billing/upgrade")
def upgrade_plan(body: UpgradePlanRequest, request: Request):
    """Start a plan upgrade via Stripe Checkout."""
    try:
        user = _get_user_from_supabase_token(request)
        from billing import is_enabled, create_customer, create_checkout_session, STRIPE_PRICE_PRO, STRIPE_PRICE_TEAM
        
        if not is_enabled():
            # If Stripe is not configured, just update the plan directly
            from database import get_user_orgs, update_org_settings
            orgs = get_user_orgs(user["id"])
            if orgs:
                from database import get_db_connection
                with get_db_connection() as conn:
                    cur = conn.cursor()
                    cur.execute(
                        "UPDATE organizations SET plan = %s WHERE id = %s",
                        (body.plan, orgs[0]["id"])
                    )
                return {"message": f"Plan updated to {body.plan}", "redirect_url": None}
            raise HTTPException(status_code=400, detail="No organization found")
        
        price_map = {
            "pro": STRIPE_PRICE_PRO,
            "team": STRIPE_PRICE_TEAM,
        }
        price_id = price_map.get(body.plan)
        if not price_id:
            raise HTTPException(status_code=400, detail=f"Invalid plan: {body.plan}")
        
        from database import get_user_orgs, get_organization, update_org_settings
        orgs = get_user_orgs(user["id"])
        if not orgs:
            raise HTTPException(status_code=400, detail="No organization found")
        org = orgs[0]
        org_id = str(org["id"])
        org_name = org.get("name", "Semantis")
        user_email = user.get("email", "")
        
        org_full = get_organization(org_id)
        settings = org_full.get("settings") or {}
        customer_id = settings.get("stripe_customer_id")
        
        if not customer_id:
            customer_id = create_customer(org_id, org_name, user_email)
            if customer_id:
                update_org_settings(org_id, {"stripe_customer_id": customer_id})
        
        if not customer_id:
            raise HTTPException(status_code=500, detail="Failed to create Stripe customer")
        
        base_url = request.base_url
        success_url = body.success_url or str(base_url) + "settings?billing=success"
        cancel_url = body.cancel_url or str(base_url) + "settings?billing=cancel"
        
        redirect_url = create_checkout_session(
            customer_id, price_id, success_url, cancel_url, org_id, body.plan
        )
        return {"message": f"Redirect to Stripe checkout for {body.plan}", "redirect_url": redirect_url}
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"Plan upgrade failed | error={e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/billing/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events."""
    try:
        from billing import handle_webhook
        payload = await request.body()
        sig = request.headers.get("stripe-signature", "")
        event = handle_webhook(payload, sig)
        if not event:
            raise HTTPException(status_code=400, detail="Invalid webhook")
        
        event_type = event.get("type")
        app_log.info(f"Stripe webhook | type={event_type}")
        
        if event_type == "checkout.session.completed":
            obj = event.get("data") or {}
            metadata = obj.get("metadata", {}) if isinstance(obj, dict) else getattr(obj, "metadata", None) or {}
            org_id = metadata.get("org_id") if isinstance(metadata, dict) else None
            plan = metadata.get("plan", "pro") if isinstance(metadata, dict) else "pro"
            if org_id:
                try:
                    from database import get_db_connection
                    with get_db_connection() as conn:
                        cur = conn.cursor()
                        cur.execute(
                            "UPDATE organizations SET plan = %s WHERE id = %s",
                            (plan, org_id)
                        )
                except Exception as e:
                    error_log.error(f"Webhook plan update failed | org={org_id} | error={e}")
        
        return {"received": True}
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"Webhook failed | error={e}")
        raise HTTPException(status_code=500, detail=str(e))

# -----------------------------
# Entry point
# -----------------------------
if __name__ == "__main__":
    import uvicorn
    import sys
    port = int(os.getenv("PORT", 8000))
    
    # Log startup
    system_log.info(
        f"Server starting | port={port} | version=0.1.0 | "
        f"python={sys.version.split()[0]}"
    )
    
    print(f"Semantis AI Semantic Cache API running on http://0.0.0.0:{port}")
    print(f"Logs directory: {os.path.abspath('logs')}")
    print(f"Access logs: logs/access.log")
    print(f"Error logs: logs/errors.log")
    print(f"Semantic logs: logs/semantic_ops.log")
    print(f"Performance logs: logs/performance.log")
    print(f"Security logs: logs/security.log")
    print(f"System logs: logs/system.log")
    print(f"Application logs: logs/application.log")
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=port)
    except KeyboardInterrupt:
        system_log.info("Server stopped by user")
    except Exception as e:
        error_log.exception(f"Server startup failed | error={str(e)}")
        raise
