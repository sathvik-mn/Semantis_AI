"""
Vector Store Abstraction for Semantis AI

Supports two backends:
- Pinecone (production): External vector DB with namespace-per-tenant
- FAISS (local/fallback): In-process indexes, original behavior

Set PINECONE_API_KEY to enable Pinecone. Falls back to FAISS if not configured.
"""
import os
import logging
import time
import numpy as np
from typing import Optional, List, Tuple, Dict

logger = logging.getLogger("semantis.vector_store")

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "semantis-cache")
PINECONE_HOST = os.getenv("PINECONE_HOST", "")  # Optional: direct host URL

_pinecone_index = None
_pinecone_available: Optional[bool] = None


def _get_pinecone_index():
    """Lazy-init Pinecone index. Returns None if not configured."""
    global _pinecone_index, _pinecone_available
    if _pinecone_available is False:
        return None
    if _pinecone_index is not None:
        return _pinecone_index
    if not PINECONE_API_KEY:
        _pinecone_available = False
        logger.info("Pinecone not configured (PINECONE_API_KEY empty), using FAISS fallback")
        return None
    try:
        from pinecone import Pinecone
        pc = Pinecone(api_key=PINECONE_API_KEY)
        if PINECONE_HOST:
            _pinecone_index = pc.Index(host=PINECONE_HOST)
        else:
            _pinecone_index = pc.Index(PINECONE_INDEX_NAME)
        # Verify connectivity
        stats = _pinecone_index.describe_index_stats()
        _pinecone_available = True
        logger.info(
            f"Pinecone connected | index={PINECONE_INDEX_NAME} | "
            f"total_vectors={stats.get('total_vector_count', 0)} | "
            f"namespaces={len(stats.get('namespaces', {}))}"
        )
        return _pinecone_index
    except Exception as e:
        _pinecone_available = False
        logger.warning(f"Pinecone unavailable ({e}), using FAISS fallback")
        return None


def is_pinecone_enabled() -> bool:
    """Check if Pinecone is available and configured."""
    return _get_pinecone_index() is not None


def upsert_embedding(
    tenant_id: str,
    entry_id: str,
    embedding: np.ndarray,
    metadata: Optional[Dict] = None,
) -> bool:
    """Upsert a single embedding vector to Pinecone.

    Args:
        tenant_id: Used as Pinecone namespace for data isolation
        entry_id: Unique ID for this vector (e.g., prompt hash)
        embedding: Normalized embedding vector
        metadata: Optional metadata dict (prompt_hash, model, created_at, etc.)

    Returns:
        True if successful, False otherwise
    """
    idx = _get_pinecone_index()
    if idx is None:
        return False
    try:
        vec = embedding.astype("float32").flatten().tolist()
        meta = metadata or {}
        idx.upsert(
            vectors=[{"id": entry_id, "values": vec, "metadata": meta}],
            namespace=tenant_id,
        )
        return True
    except Exception as e:
        logger.warning(f"Pinecone upsert failed | tenant={tenant_id} | error={e}")
        return False


def upsert_batch(
    tenant_id: str,
    vectors: List[Tuple[str, np.ndarray, Optional[Dict]]],
) -> bool:
    """Batch upsert multiple embeddings.

    Args:
        tenant_id: Namespace
        vectors: List of (id, embedding, metadata) tuples
    """
    idx = _get_pinecone_index()
    if idx is None:
        return False
    try:
        records = []
        for vid, emb, meta in vectors:
            vec = emb.astype("float32").flatten().tolist()
            records.append({"id": vid, "values": vec, "metadata": meta or {}})
        # Pinecone recommends batches of 100
        batch_size = 100
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            idx.upsert(vectors=batch, namespace=tenant_id)
        return True
    except Exception as e:
        logger.warning(f"Pinecone batch upsert failed | tenant={tenant_id} | error={e}")
        return False


def search(
    tenant_id: str,
    query_embedding: np.ndarray,
    top_k: int = 10,
    filter_dict: Optional[Dict] = None,
) -> List[Dict]:
    """Search for similar vectors in Pinecone.

    Args:
        tenant_id: Namespace to search in
        query_embedding: Normalized query vector
        top_k: Number of results
        filter_dict: Optional metadata filter

    Returns:
        List of dicts with 'id', 'score', 'metadata' keys, sorted by score desc.
        Returns empty list if Pinecone unavailable.
    """
    idx = _get_pinecone_index()
    if idx is None:
        return []
    try:
        vec = query_embedding.astype("float32").flatten().tolist()
        kwargs = {
            "vector": vec,
            "top_k": top_k,
            "namespace": tenant_id,
            "include_metadata": True,
        }
        if filter_dict:
            kwargs["filter"] = filter_dict
        results = idx.query(**kwargs)
        matches = []
        for m in results.get("matches", []):
            matches.append({
                "id": m["id"],
                "score": m["score"],
                "metadata": m.get("metadata", {}),
            })
        return matches
    except Exception as e:
        logger.warning(f"Pinecone search failed | tenant={tenant_id} | error={e}")
        return []


def delete_vectors(tenant_id: str, ids: List[str]) -> bool:
    """Delete specific vectors by ID from a namespace."""
    idx = _get_pinecone_index()
    if idx is None:
        return False
    try:
        idx.delete(ids=ids, namespace=tenant_id)
        return True
    except Exception as e:
        logger.warning(f"Pinecone delete failed | tenant={tenant_id} | error={e}")
        return False


def delete_namespace(tenant_id: str) -> bool:
    """Delete all vectors in a tenant namespace."""
    idx = _get_pinecone_index()
    if idx is None:
        return False
    try:
        idx.delete(delete_all=True, namespace=tenant_id)
        return True
    except Exception as e:
        logger.warning(f"Pinecone namespace delete failed | tenant={tenant_id} | error={e}")
        return False


def get_stats(tenant_id: Optional[str] = None) -> Dict:
    """Get vector store stats (total or per namespace)."""
    idx = _get_pinecone_index()
    if idx is None:
        return {"backend": "faiss", "status": "in-memory"}
    try:
        stats = idx.describe_index_stats()
        result = {
            "backend": "pinecone",
            "status": "connected",
            "total_vectors": stats.get("total_vector_count", 0),
            "dimension": stats.get("dimension", 0),
            "namespaces": len(stats.get("namespaces", {})),
        }
        if tenant_id and "namespaces" in stats:
            ns_stats = stats["namespaces"].get(tenant_id, {})
            result["tenant_vectors"] = ns_stats.get("vector_count", 0)
        return result
    except Exception as e:
        return {"backend": "pinecone", "status": "error", "error": str(e)}


def health_check() -> Dict:
    """Health check for the vector store."""
    idx = _get_pinecone_index()
    if idx is None:
        return {"status": "faiss_fallback", "message": "Using in-memory FAISS (Pinecone not configured)"}
    try:
        start = time.time()
        stats = idx.describe_index_stats()
        latency = round((time.time() - start) * 1000, 1)
        return {
            "status": "connected",
            "backend": "pinecone",
            "index": PINECONE_INDEX_NAME,
            "latency_ms": latency,
            "total_vectors": stats.get("total_vector_count", 0),
        }
    except Exception as e:
        return {"status": "error", "backend": "pinecone", "error": str(e)}
