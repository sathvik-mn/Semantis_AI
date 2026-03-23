"""
Cache Persistence Module
Saves and loads cache data to/from disk for persistence across restarts.
"""
import os
import pickle
import json
import time
from typing import Dict, List
import numpy as np
import faiss
from datetime import datetime

CACHE_DIR = "cache_data"
CACHE_FILE = os.path.join(CACHE_DIR, "cache.json")
CACHE_FILE_LEGACY = os.path.join(CACHE_DIR, "cache.pkl")
KEYS_FILE = os.path.join(CACHE_DIR, "api_keys.json")

def ensure_cache_dir():
    """Ensure cache directory exists."""
    os.makedirs(CACHE_DIR, exist_ok=True)

def save_cache(tenants: Dict, filepath: str = CACHE_FILE):
    """
    Save cache data to disk.
    
    Args:
        tenants: Dictionary of tenant states
        filepath: Path to save cache file
    """
    ensure_cache_dir()
    
    # Prepare data for serialization
    cache_data = {
        "tenants": {},
        "saved_at": datetime.now().isoformat()
    }
    
    for tenant_id, tenant_state in tenants.items():
        # Convert FAISS index to numpy array if it exists
        _index_data = None
        if tenant_state.index is not None:
            # Get vectors from FAISS index
            num_vectors = tenant_state.index.ntotal
            if num_vectors > 0:
                # Extract vectors (this is a simplified approach)
                # For production, consider using faiss.write_index
                _index_data = {
                    "num_vectors": num_vectors,
                    "dim": tenant_state.dim,
                    "vectors": None  # Will be handled separately
                }
        
        def _serialize_entry(entry):
            d = {
                "prompt_norm": entry.prompt_norm,
                "response_text": entry.response_text,
                "embedding": entry.embedding.tolist() if entry.embedding is not None else None,
                "model": entry.model,
                "ttl_seconds": entry.ttl_seconds,
                "created_at": entry.created_at,
                "last_used_at": entry.last_used_at,
                "use_count": entry.use_count,
                "domain": entry.domain,
                "strategy": entry.strategy,
                "cluster_id": getattr(entry, 'cluster_id', -1),
            }
            resp_emb = getattr(entry, 'response_embedding', None)
            d["response_embedding"] = resp_emb.tolist() if resp_emb is not None else None
            local_emb = getattr(entry, 'local_embedding', None)
            d["local_embedding"] = local_emb.tolist() if local_emb is not None else None
            return d

        entries_data = [_serialize_entry(e) for e in tenant_state.rows]
        exact_cache_data = {key: _serialize_entry(e) for key, e in tenant_state.exact.items()}
        
        cache_data["tenants"][tenant_id] = {
            "exact": exact_cache_data,
            "rows": entries_data,
            "dim": tenant_state.dim,
            "hits": tenant_state.hits,
            "misses": tenant_state.misses,
            "semantic_hits": tenant_state.semantic_hits,
            "latencies_ms": tenant_state.latencies_ms,
            "sim_threshold": tenant_state.sim_threshold,
            "events": [
                {
                    "timestamp": e.timestamp,
                    "tenant_id": e.tenant_id,
                    "prompt_hash": e.prompt_hash,
                    "decision": e.decision,
                    "similarity": e.similarity,
                    "latency_ms": e.latency_ms,
                    "confidence": getattr(e, 'confidence', 0.0),  # Backward compatible
                    "hybrid_score": getattr(e, 'hybrid_score', 0.0),  # Backward compatible
                }
                for e in tenant_state.events
            ],
            "domain_thresholds": getattr(tenant_state, 'domain_thresholds', {}),  # Backward compatible
        }
    
    # Save to file as JSON (safe serialization, no arbitrary code execution on load)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f)

    print(f"Cache saved to {filepath}")

def load_cache(filepath: str = CACHE_FILE):
    """
    Load cache data from disk (JSON format, with legacy pickle fallback).

    Returns:
        Dictionary of tenant states or None if file doesn't exist
    """
    # Try JSON first, fall back to legacy pickle
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Not JSON — might be legacy pickle, try that
            with open(filepath, 'rb') as f:
                cache_data = pickle.load(f)
            print("Migrated legacy pickle cache to JSON")
    elif os.path.exists(CACHE_FILE_LEGACY):
        # Legacy pickle file exists but no JSON yet
        with open(CACHE_FILE_LEGACY, 'rb') as f:
            cache_data = pickle.load(f)
        print("Loaded legacy pickle cache (will save as JSON next time)")
    else:
        return None

    try:
        
        # Reconstruct tenant states
        from semantic_cache_server import TenantState, CacheEntry, CacheEvent
        
        def _deserialize_entry(entry_data):
            emb_data = entry_data.get("embedding")
            emb = np.array(emb_data, dtype="float32") if emb_data is not None else None
            resp_emb_data = entry_data.get("response_embedding")
            resp_emb = np.array(resp_emb_data, dtype="float32") if resp_emb_data is not None else None
            local_emb_data = entry_data.get("local_embedding")
            local_emb = np.array(local_emb_data, dtype="float32") if local_emb_data is not None else None
            return CacheEntry(
                prompt_norm=entry_data["prompt_norm"],
                response_text=entry_data["response_text"],
                embedding=emb,
                model=entry_data["model"],
                ttl_seconds=entry_data["ttl_seconds"],
                created_at=entry_data["created_at"],
                last_used_at=entry_data.get("last_used_at", time.time()),
                use_count=entry_data.get("use_count", 0),
                domain=entry_data.get("domain", "general"),
                strategy=entry_data.get("strategy", "miss"),
                response_embedding=resp_emb,
                local_embedding=local_emb,
                cluster_id=entry_data.get("cluster_id", -1),
            )

        tenants = {}
        for tenant_id, tenant_data in cache_data.get("tenants", {}).items():
            exact_cache = {
                key: _deserialize_entry(ed) for key, ed in tenant_data.get("exact", {}).items()
            }
            rows = [_deserialize_entry(ed) for ed in tenant_data.get("rows", [])]

            # Reconstruct main FAISS index
            index = None
            dim = tenant_data.get("dim")
            if dim and len(rows) > 0:
                embeddings_list = [r.embedding for r in rows if r.embedding is not None]
                if embeddings_list:
                    index = faiss.IndexFlatIP(dim)
                    embeddings = np.vstack(embeddings_list).astype('float32')
                    faiss.normalize_L2(embeddings)
                    index.add(embeddings)
                    print(f"Reconstructed FAISS index with {len(embeddings_list)} vectors for tenant {tenant_id}")

            # Reconstruct local FAISS index
            local_index = None
            local_dim = None
            local_embs = [r.local_embedding for r in rows if r.local_embedding is not None]
            if local_embs:
                local_dim = local_embs[0].shape[0]
                local_index = faiss.IndexFlatIP(local_dim)
                local_vecs = np.vstack(local_embs).astype('float32')
                faiss.normalize_L2(local_vecs)
                local_index.add(local_vecs)

            events = []
            for event_data in tenant_data.get("events", []):
                events.append(CacheEvent(
                    timestamp=event_data["timestamp"],
                    tenant_id=event_data["tenant_id"],
                    prompt_hash=event_data["prompt_hash"],
                    decision=event_data["decision"],
                    similarity=event_data["similarity"],
                    latency_ms=event_data["latency_ms"],
                    confidence=event_data.get("confidence", 0.0),
                    hybrid_score=event_data.get("hybrid_score", 0.0),
                ))

            tenant_state = TenantState(
                exact=exact_cache,
                index=index,
                rows=rows,
                dim=dim,
                norm_hash_index={},
                local_index=local_index,
                local_dim=local_dim,
                hits=tenant_data.get("hits", 0),
                misses=tenant_data.get("misses", 0),
                semantic_hits=tenant_data.get("semantic_hits", 0),
                latencies_ms=tenant_data.get("latencies_ms", []),
                sim_threshold=tenant_data.get("sim_threshold", 0.55),
                domain_thresholds=tenant_data.get("domain_thresholds", {}),
                events=events,
            )

            tenants[tenant_id] = tenant_state

        print(f"Cache loaded from {filepath}")
        return tenants
    
    except Exception as e:
        print(f"Error loading cache: {e}")
        return None

def save_api_keys(keys: List[Dict], filepath: str = KEYS_FILE):
    """
    Save API keys to JSON file.
    
    Args:
        keys: List of key dictionaries
        filepath: Path to save keys file
    """
    ensure_cache_dir()
    
    # Load existing keys
    existing_keys = []
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                existing_keys = json.load(f)
        except:
            existing_keys = []
    
    # Merge with new keys (avoid duplicates)
    existing_key_strings = {k.get("api_key") for k in existing_keys}
    for key in keys:
        if key.get("api_key") not in existing_key_strings:
            existing_keys.append(key)
            existing_key_strings.add(key.get("api_key"))
    
    # Save to file
    with open(filepath, 'w') as f:
        json.dump(existing_keys, f, indent=2)
    
    print(f"API keys saved to {filepath}")

def load_api_keys(filepath: str = KEYS_FILE):
    """
    Load API keys from JSON file.
    
    Returns:
        List of key dictionaries or empty list if file doesn't exist
    """
    if not os.path.exists(filepath):
        return []
    
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading API keys: {e}")
        return []

