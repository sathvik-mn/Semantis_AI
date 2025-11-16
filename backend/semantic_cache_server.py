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
from collections import OrderedDict

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
# Embeddings & LLM
# -----------------------------
def get_embedding(text: str) -> np.ndarray:
    """Return L2-normalized embedding vector."""
    start_time = time.time()
    try:
        resp = openai.embeddings.create(model=EMBED_MODEL, input=text)
        v = np.array(resp.data[0].embedding, dtype="float32")
        v /= (np.linalg.norm(v) + 1e-12)
        embedding_time = round((time.time() - start_time) * 1000, 2)
        performance_log.debug(
            f"Embedding generated | model={EMBED_MODEL} | "
            f"text_len={len(text)} | time={embedding_time}ms"
        )
        return v
    except Exception as e:
        embedding_time = round((time.time() - start_time) * 1000, 2)
        error_log.exception(
            f"Embedding failed | model={EMBED_MODEL} | "
            f"text_len={len(text)} | time={embedding_time}ms | error={str(e)}"
        )
        raise

def call_llm(messages: List[dict], temperature: float = 0.2) -> str:
    """Minimal OpenAI chat call wrapper."""
    start_time = time.time()
    prompt_tokens = sum(len(m.get("content", "").split()) for m in messages)  # Rough estimate
    try:
        resp = openai.chat.completions.create(
            model=CHAT_MODEL,
            messages=messages,
            temperature=temperature,
        )
        llm_time = round((time.time() - start_time) * 1000, 2)
        response_text = resp.choices[0].message.content.strip()
        completion_tokens = len(response_text.split())  # Rough estimate
        total_tokens = prompt_tokens + completion_tokens
        
        # Log LLM call
        app_log.info(
            f"LLM call | model={CHAT_MODEL} | temp={temperature} | "
            f"prompt_tokens~={prompt_tokens} | completion_tokens~={completion_tokens} | "
            f"total_tokens~={total_tokens} | time={llm_time}ms"
        )
        
        performance_log.debug(
            f"LLM performance | model={CHAT_MODEL} | time={llm_time}ms | "
            f"tokens~={total_tokens}"
        )
        
        return response_text
    except Exception as e:
        llm_time = round((time.time() - start_time) * 1000, 2)
        error_log.exception(
            f"LLM call failed | model={CHAT_MODEL} | temp={temperature} | "
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
    confidence: float = 0.0  # Confidence score for semantic matches
    hybrid_score: float = 0.0  # Hybrid similarity score

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
    # domain-specific thresholds
    domain_thresholds: Dict[str, float] = field(default_factory=dict)  # domain -> threshold
    # events log
    events: List[CacheEvent] = field(default_factory=list)

# -----------------------------
# Core semantic cache service
# -----------------------------
class SemanticCacheService:
    def __init__(self):
        self.tenants: Dict[str, TenantState] = {}
        # Embedding cache with LRU eviction
        self._embedding_cache: OrderedDict[str, np.ndarray] = OrderedDict()
        self._embedding_cache_max_size = 1000
        # Load cache from disk if available
        self._load_cache()
    
    def _load_cache(self):
        """Load cache from disk on startup."""
        try:
            from cache_persistence import load_cache
            start_time = time.time()
            loaded_tenants = load_cache()
            load_time = round((time.time() - start_time) * 1000, 2)
            if loaded_tenants:
                total_entries = sum(len(t.rows) for t in loaded_tenants.values())
                self.tenants.update(loaded_tenants)
                system_log.info(
                    f"Cache loaded | tenants={len(loaded_tenants)} | "
                    f"entries={total_entries} | time={load_time}ms"
                )
            else:
                system_log.info(f"Cache load | no cache found | time={load_time}ms")
        except Exception as e:
            error_log.exception(f"Cache load failed | error={str(e)}")
            system_log.error(f"Could not load cache from disk: {e}")
    
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
        """Normalize text for exact matching. Preserves semantic meaning better."""
        # Remove extra whitespace and convert to lowercase
        s = " ".join(s.strip().split()).lower()
        # Remove common articles and prepositions for better matching
        # But keep them for semantic matching (handled separately)
        return s
    
    @staticmethod
    def _expand_query(text: str) -> List[str]:
        """Expand query with variations for better matching."""
        variations = [text.lower().strip()]
        
        # Handle contractions
        contractions = {
            "what's": "what is", "who's": "who is", "where's": "where is",
            "it's": "it is", "that's": "that is", "how's": "how is",
            "when's": "when is", "why's": "why is", "there's": "there is"
        }
        for cont, exp in contractions.items():
            if cont in text.lower():
                variations.append(text.lower().replace(cont, exp))
        
        # Handle question variations
        question_starters = ["what is", "tell me about", "explain", "describe", "define"]
        for starter in question_starters:
            if text.lower().startswith(starter):
                for alt in question_starters:
                    if alt != starter:
                        variations.append(text.lower().replace(starter, alt, 1))
        
        return list(set(variations))  # Remove duplicates
    
    def _get_cached_embedding(self, text: str) -> Optional[np.ndarray]:
        """Get cached embedding or None."""
        text_key = text.lower().strip()
        if text_key in self._embedding_cache:
            # Move to end (LRU)
            self._embedding_cache.move_to_end(text_key)
            return self._embedding_cache[text_key]
        return None
    
    def _cache_embedding(self, text: str, emb: np.ndarray):
        """Cache embedding with LRU eviction."""
        text_key = text.lower().strip()
        if text_key in self._embedding_cache:
            self._embedding_cache.move_to_end(text_key)
        else:
            self._embedding_cache[text_key] = emb
            # Evict oldest if cache full
            if len(self._embedding_cache) > self._embedding_cache_max_size:
                self._embedding_cache.popitem(last=False)
    
    def _get_context_aware_embedding(self, messages: List[dict], prompt_norm: str) -> Tuple[np.ndarray, str]:
        """Generate context-aware embedding considering conversation history."""
        user_messages = [m["content"] for m in messages if m.get("role") == "user"]
        
        # Primary: Last user message (most important)
        primary_text = user_messages[-1] if user_messages else prompt_norm
        
        # Check cache first
        cached_emb = self._get_cached_embedding(primary_text)
        if cached_emb is not None:
            return cached_emb, primary_text
        
        # Generate embedding
        primary_emb = get_embedding(primary_text)
        self._cache_embedding(primary_text, primary_emb)
        
        # Context: Last 2-3 messages for context (if multiple messages)
        if len(user_messages) > 1:
            context_text = " ".join(user_messages[-3:])
            cached_context = self._get_cached_embedding(context_text)
            if cached_context is not None:
                context_emb = cached_context
            else:
                context_emb = get_embedding(context_text)
                self._cache_embedding(context_text, context_emb)
            
            # Weighted combination: 70% primary, 30% context
            combined_emb = 0.7 * primary_emb + 0.3 * context_emb
            combined_emb /= (np.linalg.norm(combined_emb) + 1e-12)
            return combined_emb, primary_text
        
        return primary_emb, primary_text
    
    def _calculate_hybrid_score(
        self, 
        query_emb: np.ndarray, 
        query_text: str,
        entry: CacheEntry, 
        entry_emb: np.ndarray,
        base_sim: float
    ) -> float:
        """Calculate hybrid similarity score combining multiple signals."""
        # 1. Embedding similarity (primary, 60% weight)
        emb_score = base_sim
        
        # 2. Text overlap (20% weight)
        query_words = set(query_text.lower().split())
        entry_words = set(entry.prompt_norm.lower().split())
        jaccard = len(query_words & entry_words) / len(query_words | entry_words) if (query_words | entry_words) else 0
        text_score = jaccard
        
        # 3. Domain match (10% weight) - boost if same domain
        query_domain = domain_hint(query_text)
        domain_boost = 0.1 if entry.domain == query_domain else 0
        
        # 4. Recency score (5% weight) - fresher entries slightly preferred
        age_days = (time.time() - entry.created_at) / 86400
        recency_score = max(0, 1 - (age_days / 30))  # Decay over 30 days
        
        # 5. Usage score (5% weight) - more used = more reliable
        usage_score = min(1.0, entry.use_count / 10)  # Cap at 10 uses
        
        # Weighted combination
        hybrid_score = (
            0.60 * emb_score +
            0.20 * text_score +
            0.10 * domain_boost +
            0.05 * recency_score +
            0.05 * usage_score
        )
        return min(1.0, hybrid_score)  # Cap at 1.0
    
    def _calculate_confidence(
        self, 
        hybrid_score: float, 
        base_sim: float, 
        entry: CacheEntry
    ) -> float:
        """Calculate confidence score for a match (0.0-1.0)."""
        # Base confidence from hybrid score
        confidence = hybrid_score
        
        # Boost if base similarity is high (strong embedding match)
        if base_sim > 0.85:
            confidence += 0.1
        elif base_sim > 0.80:
            confidence += 0.05
        
        # Boost if entry is well-used (proven reliable)
        if entry.use_count > 5:
            confidence += 0.05
        
        # Boost if entry is fresh
        age_days = (time.time() - entry.created_at) / 86400
        if age_days < 7:
            confidence += 0.05
        
        # Penalize if similarity is borderline
        if base_sim < 0.75:
            confidence -= 0.1
        
        return max(0.0, min(1.0, confidence))  # Clamp to [0, 1]
    
    def _get_adaptive_threshold(self, T: TenantState, num_candidates: int, domain: str = None) -> float:
        """Get adaptive threshold considering domain and cache size."""
        # Base threshold from cache size
        if len(T.rows) < 10:
            base = max(0.70, T.sim_threshold)
        elif len(T.rows) < 20:
            base = max(0.72, T.sim_threshold)
        else:
            base = T.sim_threshold
        
        # Domain-specific adjustment
        if domain and domain in T.domain_thresholds:
            domain_thresh = T.domain_thresholds[domain]
            # Use stricter of base or domain threshold
            base = max(base, domain_thresh)
        
        # Adjust based on number of candidates (more candidates = can be stricter)
        if num_candidates > 10:
            base += 0.02  # Slightly stricter with more options
        
        return base

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

        # 2) semantic - enhanced matching with context-aware embeddings, hybrid scoring, and reranking
        if T.index is not None and len(T.rows) > 0:
            user_text = " ".join([m["content"] for m in messages if m.get("role") == "user"]) or prompt_norm
            
            # Use context-aware embedding (considers conversation history)
            emb, primary_text = self._get_context_aware_embedding(messages, prompt_norm)
            
            # Search more candidates initially (top 20 for better reranking)
            top_matches = self._faiss_search_top_k(T, emb, k=min(20, len(T.rows)))
            
            # Calculate hybrid scores for all candidates
            candidates = []
            for idx, sim in top_matches:
                if idx < len(T.rows) and T.rows[idx].fresh():
                    entry = T.rows[idx]
                    hybrid_score = self._calculate_hybrid_score(
                        emb, primary_text, entry, entry.embedding, sim
                    )
                    confidence = self._calculate_confidence(hybrid_score, sim, entry)
                    candidates.append({
                        'idx': idx,
                        'entry': entry,
                        'base_sim': sim,
                        'hybrid_score': hybrid_score,
                        'confidence': confidence
                    })
            
            # Sort by hybrid score (best matches first)
            candidates.sort(key=lambda x: x['hybrid_score'], reverse=True)
            
            # Get domain for domain-aware threshold
            query_domain = domain_hint(primary_text)
            
            # Apply adaptive threshold with confidence check
            adaptive_threshold = self._get_adaptive_threshold(T, len(candidates), query_domain)
            
            # Typo tolerance: be more lenient for very similar queries
            best_match = None
            for candidate in candidates:
                hybrid_score = candidate['hybrid_score']
                base_sim = candidate['base_sim']
                confidence = candidate['confidence']
                
                # Normal match - above threshold with good confidence
                if hybrid_score >= adaptive_threshold and confidence >= 0.7:
                    best_match = candidate
                    break
                # Typo tolerance: accept if similarity is 0.65+ with decent confidence
                elif base_sim >= 0.65 and confidence >= 0.65:
                    # Lower threshold to just below similarity for typo tolerance
                    if hybrid_score >= max(0.65, base_sim - 0.02):
                        best_match = candidate
                        semantic_log.info(f"{tenant_id} | typo-tolerance | sim={base_sim:.3f} | hybrid={hybrid_score:.3f} | conf={confidence:.3f}")
                        break
            
            if best_match is not None:
                entry = best_match['entry']
                entry.use_count += 1
                entry.last_used_at = time.time()
                T.hits += 1
                T.semantic_hits += 1
                latency = round((time.time() - t0) * 1000, 2)
                T.latencies_ms.append(latency)
                
                hybrid_score = best_match['hybrid_score']
                base_sim = best_match['base_sim']
                confidence = best_match['confidence']
                
                meta = {
                    "hit": "semantic", 
                    "similarity": round(base_sim, 4), 
                    "hybrid_score": round(hybrid_score, 4),
                    "confidence": round(confidence, 4),
                    "latency_ms": latency, 
                    "strategy": "hybrid-enhanced", 
                    "threshold_used": round(adaptive_threshold, 3)
                }
                semantic_log.info(
                    f"{tenant_id} | semantic | sim={base_sim:.3f} | hybrid={hybrid_score:.3f} | "
                    f"conf={confidence:.3f} | threshold={adaptive_threshold:.3f} | key={prompt_norm[:80]}"
                )
                # Store event with enhanced metrics
                T.events.append(CacheEvent(
                    timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
                    tenant_id=tenant_id,
                    prompt_hash=prompt_hash,
                    decision="semantic",
                    similarity=round(base_sim, 4),
                    latency_ms=latency,
                    confidence=round(confidence, 4),
                    hybrid_score=round(hybrid_score, 4)
                ))
                # Keep only last 1000 events
                if len(T.events) > 1000:
                    T.events = T.events[-1000:]
                return entry.response_text, meta

        # 3) miss → call LLM & insert
        T.misses += 1
        response_text = call_llm(messages, temperature=temperature)
        user_text = " ".join([m["content"] for m in messages if m.get("role") == "user"]) or prompt_norm
        
        # Use context-aware embedding for storing (consistent with query)
        emb, _ = self._get_context_aware_embedding(messages, prompt_norm)
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
        
        # Calculate quality metrics for semantic hits
        semantic_events = [e for e in T.events if e.decision == "semantic"]
        avg_confidence = np.mean([e.confidence for e in semantic_events]) if semantic_events else 0.0
        avg_hybrid_score = np.mean([e.hybrid_score for e in semantic_events]) if semantic_events else 0.0
        high_confidence_hits = len([e for e in semantic_events if e.confidence >= 0.8])
        
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
            # Enhanced quality metrics
            "avg_confidence": round(avg_confidence, 3),
            "avg_hybrid_score": round(avg_hybrid_score, 3),
            "high_confidence_hits": high_confidence_hits,
            "high_confidence_ratio": round((high_confidence_hits / len(semantic_events)) if semantic_events else 0.0, 3),
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
import signal

def shutdown_handler(signum=None, frame=None):
    """Handle graceful shutdown."""
    system_log.info("Shutdown signal received | saving cache...")
    try:
        svc._save_cache()
        system_log.info("Shutdown complete | cache saved")
    except Exception as e:
        error_log.exception(f"Shutdown error | {str(e)}")
    finally:
        import sys
        sys.exit(0)

atexit.register(lambda: svc._save_cache())
signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

# -----------------------------
# FastAPI app + middleware
# -----------------------------
app = FastAPI(title="Semantis AI - Semantic Cache API", version="0.1.0")

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

# Store current request API key for usage logging (thread-local would be better for production)
_current_api_key = {"key": None}

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
    # sc-devA-foo -> tenant = 'devA'
    parts = token.split("-")
    if len(parts) < 3:
        security_log.warning(
            f"Auth failed | ip={client_ip} | reason=malformed_key | "
            f"token_prefix={token[:10]} | path={request.url.path}"
        )
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
            security_log.debug(
                f"Auth success | tenant={tenant} | ip={client_ip} | "
                f"plan={key_info.get('plan', 'unknown')}"
            )
        else:
            # Auto-create key in database if it doesn't exist (for backward compatibility)
            create_api_key(token, tenant, plan='free')
            update_api_key_usage(token, tenant)
            app_log.info(
                f"API key auto-created | tenant={tenant} | ip={client_ip} | plan=free"
            )
            security_log.info(
                f"New API key | tenant={tenant} | ip={client_ip}"
            )
    except Exception as e:
        # Don't fail if database is not available, but log it
        error_log.warning(f"Database operation failed | tenant={tenant} | error={str(e)}")
    
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
    """Health check endpoint with system status."""
    import sys
    
    try:
        try:
            import psutil
            # Get system metrics
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=0.1)
            has_system_metrics = True
        except ImportError:
            # psutil not available, skip system metrics
            has_system_metrics = False
        
        # Cache statistics
        total_tenants = len(svc.tenants)
        total_entries = sum(len(t.rows) for t in svc.tenants.values())
        
        health_status = {
            "status": "ok",
            "service": "semantic-cache",
            "version": "0.1.0",
            "cache": {
                "tenants": total_tenants,
                "total_entries": total_entries,
            }
        }
        
        if has_system_metrics:
            health_status["system"] = {
                "memory_percent": round(memory.percent, 2),
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "cpu_percent": round(cpu_percent, 2),
            }
            system_log.debug(
                f"Health check | memory={memory.percent:.1f}% | "
                f"cpu={cpu_percent:.1f}% | tenants={total_tenants} | entries={total_entries}"
            )
        else:
            system_log.debug(
                f"Health check | psutil not available | "
                f"tenants={total_tenants} | entries={total_entries}"
            )
        
        return health_status
    except Exception as e:
        error_log.exception(f"Health check failed | error={str(e)}")
        return {"status": "error", "service": "semantic-cache", "version": "0.1.0"}

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
def simple_query(prompt: str = Query(...), model: str = CHAT_MODEL, tenant: str = Depends(get_tenant_from_key)):
    messages = [{"role": "user", "content": prompt}]
    prompt_norm = SemanticCacheService.norm_text(prompt)
    prompt_hash = hashlib.md5(prompt_norm.encode()).hexdigest()[:8]
    
    try:
        ans, meta = svc.query(tenant, prompt_norm, messages, model)
        
        # Enhanced logging
        access_log.info(
            f"{tenant} | /query | {meta['hit']} | sim={meta['similarity']:.3f} | "
            f"latency={meta['latency_ms']}ms | prompt_hash={prompt_hash} | "
            f"model={model} | prompt_len={len(prompt)}"
        )
        
        # Log usage to database
        try:
            from database import log_usage
            api_key = _current_api_key.get("key", "unknown")
            log_usage(
                api_key=api_key,
                tenant_id=tenant,
                endpoint="/query",
                request_count=1,
                cache_hits=1 if meta.get('hit') != 'miss' else 0,
                cache_misses=1 if meta.get('hit') == 'miss' else 0,
                tokens_used=0,
                cost_estimate=0
            )
        except Exception as e:
            error_log.warning(f"Could not log usage to database | tenant={tenant} | error={str(e)}")
        
        return {"answer": ans, "meta": meta, "metrics": svc.metrics(tenant)}
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

@app.post("/api/keys/generate")
def generate_api_key_endpoint(
    tenant: Optional[str] = Query(None, description="Optional tenant ID. If not provided, a unique tenant ID will be generated"),
    length: int = Query(32, ge=16, le=64, description="Length of random string (16-64, default: 32)"),
    email: Optional[str] = Query(None, description="Optional email for user creation"),
    name: Optional[str] = Query(None, description="Optional name for user creation"),
    plan: str = Query("free", description="Plan type (default: free)")
):
    """
    Generate a new API key.
    
    Returns a new API key with a unique tenant ID.
    The key is automatically saved to the database.
    """
    try:
        from api_key_generator import generate_api_key
        from database import create_user, create_api_key
        
        # Generate API key
        auto_tenant = tenant is None
        api_key, tenant_id = generate_api_key(tenant=tenant, length=length, auto_tenant=auto_tenant)
        
        # Create user if email provided
        user_id = None
        if email:
            try:
                user_id = create_user(email, name)
                app_log.info(f"User created | email={email} | user_id={user_id}")
            except Exception as e:
                error_log.warning(f"Could not create user | email={email} | error={str(e)}")
        
        # Save API key to database
        try:
            create_api_key(api_key, tenant_id, user_id=user_id, plan=plan)
            app_log.info(f"API key generated | tenant={tenant_id} | plan={plan}")
        except Exception as e:
            error_log.error(f"Could not save API key to database | tenant={tenant_id} | error={str(e)}")
            # Still return the key even if database save fails
        
        return {
            "api_key": api_key,
            "tenant_id": tenant_id,
            "plan": plan,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "format": f"Bearer {api_key}",
            "message": "API key generated successfully. Save this key securely - it won't be shown again."
        }
    except Exception as e:
        error_log.exception(f"API key generation failed | error={str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate API key: {str(e)}")

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
