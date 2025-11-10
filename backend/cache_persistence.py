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
from dataclasses import dataclass, asdict
from datetime import datetime

CACHE_DIR = "cache_data"
CACHE_FILE = os.path.join(CACHE_DIR, "cache.pkl")
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
        index_data = None
        if tenant_state.index is not None:
            # Get vectors from FAISS index
            num_vectors = tenant_state.index.ntotal
            if num_vectors > 0:
                # Extract vectors (this is a simplified approach)
                # For production, consider using faiss.write_index
                index_data = {
                    "num_vectors": num_vectors,
                    "dim": tenant_state.dim,
                    "vectors": None  # Will be handled separately
                }
        
        # Serialize cache entries
        entries_data = []
        for entry in tenant_state.rows:
            entry_dict = {
                "prompt_norm": entry.prompt_norm,
                "response_text": entry.response_text,
                "embedding": entry.embedding.tolist(),  # Convert numpy array to list
                "model": entry.model,
                "ttl_seconds": entry.ttl_seconds,
                "created_at": entry.created_at,
                "last_used_at": entry.last_used_at,
                "use_count": entry.use_count,
                "domain": entry.domain,
                "strategy": entry.strategy,
            }
            entries_data.append(entry_dict)
        
        # Serialize exact cache
        exact_cache_data = {}
        for key, entry in tenant_state.exact.items():
            exact_cache_data[key] = {
                "prompt_norm": entry.prompt_norm,
                "response_text": entry.response_text,
                "embedding": entry.embedding.tolist(),
                "model": entry.model,
                "ttl_seconds": entry.ttl_seconds,
                "created_at": entry.created_at,
                "last_used_at": entry.last_used_at,
                "use_count": entry.use_count,
                "domain": entry.domain,
                "strategy": entry.strategy,
            }
        
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
                }
                for e in tenant_state.events
            ]
        }
    
    # Save to file
    with open(filepath, 'wb') as f:
        pickle.dump(cache_data, f)
    
    print(f"Cache saved to {filepath}")

def load_cache(filepath: str = CACHE_FILE):
    """
    Load cache data from disk.
    
    Returns:
        Dictionary of tenant states or None if file doesn't exist
    """
    if not os.path.exists(filepath):
        return None
    
    try:
        with open(filepath, 'rb') as f:
            cache_data = pickle.load(f)
        
        # Reconstruct tenant states
        from semantic_cache_server import TenantState, CacheEntry, CacheEvent
        
        tenants = {}
        for tenant_id, tenant_data in cache_data.get("tenants", {}).items():
            # Reconstruct exact cache
            exact_cache = {}
            for key, entry_data in tenant_data.get("exact", {}).items():
                entry = CacheEntry(
                    prompt_norm=entry_data["prompt_norm"],
                    response_text=entry_data["response_text"],
                    embedding=np.array(entry_data["embedding"]),
                    model=entry_data["model"],
                    ttl_seconds=entry_data["ttl_seconds"],
                    created_at=entry_data["created_at"],
                    last_used_at=entry_data.get("last_used_at", time.time()),
                    use_count=entry_data.get("use_count", 0),
                    domain=entry_data.get("domain", "general"),
                    strategy=entry_data.get("strategy", "miss"),
                )
                exact_cache[key] = entry
            
            # Reconstruct rows
            rows = []
            for entry_data in tenant_data.get("rows", []):
                entry = CacheEntry(
                    prompt_norm=entry_data["prompt_norm"],
                    response_text=entry_data["response_text"],
                    embedding=np.array(entry_data["embedding"]),
                    model=entry_data["model"],
                    ttl_seconds=entry_data["ttl_seconds"],
                    created_at=entry_data["created_at"],
                    last_used_at=entry_data.get("last_used_at", time.time()),
                    use_count=entry_data.get("use_count", 0),
                    domain=entry_data.get("domain", "general"),
                    strategy=entry_data.get("strategy", "miss"),
                )
                rows.append(entry)
            
            # Reconstruct FAISS index
            index = None
            dim = tenant_data.get("dim")
            if dim and len(rows) > 0:
                # Create FAISS index
                index = faiss.IndexFlatIP(dim)
                # Add embeddings to index (must match order of rows)
                embeddings_list = []
                for entry in rows:
                    if entry.embedding is not None:
                        embeddings_list.append(entry.embedding)
                
                if embeddings_list:
                    embeddings = np.array(embeddings_list).astype('float32')
                    # Ensure embeddings are normalized
                    faiss.normalize_L2(embeddings)
                    # Add to index
                    index.add(embeddings)
                    print(f"Reconstructed FAISS index with {len(embeddings_list)} vectors for tenant {tenant_id}")
            
            # Reconstruct events
            events = []
            for event_data in tenant_data.get("events", []):
                event = CacheEvent(
                    timestamp=event_data["timestamp"],
                    tenant_id=event_data["tenant_id"],
                    prompt_hash=event_data["prompt_hash"],
                    decision=event_data["decision"],
                    similarity=event_data["similarity"],
                    latency_ms=event_data["latency_ms"],
                )
                events.append(event)
            
            # Create tenant state
            tenant_state = TenantState(
                exact=exact_cache,
                index=index,
                rows=rows,
                dim=dim,
                hits=tenant_data.get("hits", 0),
                misses=tenant_data.get("misses", 0),
                semantic_hits=tenant_data.get("semantic_hits", 0),
                latencies_ms=tenant_data.get("latencies_ms", []),
                sim_threshold=tenant_data.get("sim_threshold", 0.83),
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

