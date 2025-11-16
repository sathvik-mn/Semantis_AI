# Semantic Cache Algorithm Enhancement Plan

## Overview
Enhance the semantic caching algorithm to increase hit rate, improve response quality, and reduce false positives through better matching accuracy, response quality ranking, and context awareness.

## Current State Analysis

**Current Algorithm Flow:**
1. Exact match check (normalized text)
2. Semantic match (FAISS top-5, cosine similarity ≥ 0.72)
3. Typo tolerance (accepts 0.65+ similarity)
4. LLM call on miss

**Limitations Identified:**
- Only uses last user message (ignores conversation context)
- Simple similarity threshold (no confidence scoring)
- No reranking of top matches
- No domain-specific matching
- No response quality scoring
- No query expansion or normalization improvements

## Implementation Plan

### Phase 1: Enhanced Matching Accuracy

#### 1.1 Context-Aware Embeddings
**File:** `backend/semantic_cache_server.py`
**Location:** `query()` method, line ~339

**Changes:**
- Create `_get_context_aware_embedding()` method that:
  - Embeds last user message (current)
  - Embeds conversation context (last 2-3 messages combined)
  - Embeds full conversation summary (if >3 messages)
  - Returns weighted combination or best match from multiple embeddings

**Implementation:**
```python
# After line 338, replace single embedding with context-aware
def _get_context_aware_embedding(self, messages: List[dict], prompt_norm: str) -> Tuple[np.ndarray, str]:
    """Generate context-aware embedding considering conversation history."""
    user_messages = [m["content"] for m in messages if m.get("role") == "user"]
    
    # Primary: Last user message (most important)
    primary_text = user_messages[-1] if user_messages else prompt_norm
    primary_emb = get_embedding(primary_text)
    
    # Context: Last 2-3 messages for context
    if len(user_messages) > 1:
        context_text = " ".join(user_messages[-3:])
        context_emb = get_embedding(context_text)
        # Weighted combination: 70% primary, 30% context
        combined_emb = 0.7 * primary_emb + 0.3 * context_emb
        combined_emb /= (np.linalg.norm(combined_emb) + 1e-12)
        return combined_emb, primary_text
    return primary_emb, primary_text
```

#### 1.2 Query Expansion & Normalization
**File:** `backend/semantic_cache_server.py`
**Location:** New method `_expand_query()`

**Changes:**
- Add query expansion for common variations:
  - Handle contractions ("what's" → "what is")
  - Handle question variations ("what is" vs "tell me about" vs "explain")
  - Handle plural/singular variations
  - Normalize common synonyms

**Implementation:**
```python
# Add after norm_text() method (line ~260)
@staticmethod
def _expand_query(text: str) -> List[str]:
    """Expand query with variations for better matching."""
    variations = [text.lower().strip()]
    
    # Handle contractions
    contractions = {
        "what's": "what is", "who's": "who is", "where's": "where is",
        "it's": "it is", "that's": "that is"
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
```

#### 1.3 Hybrid Similarity Signals
**File:** `backend/semantic_cache_server.py`
**Location:** `query()` method, semantic matching section (~337-400)

**Changes:**
- Combine multiple similarity signals:
  - Embedding cosine similarity (current)
  - Text-based similarity (Jaccard, word overlap)
  - Domain matching (same domain = boost)
  - Recency score (fresher = slight boost)
  - Usage score (more used = slight boost)

**Implementation:**
```python
# Replace best match selection (line ~347-350) with hybrid scoring
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
    domain_boost = 0.1 if entry.domain == domain_hint(query_text) else 0
    
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
```

### Phase 2: Response Quality & Reranking

#### 2.1 Multi-Stage Reranking
**File:** `backend/semantic_cache_server.py`
**Location:** `query()` method, after top-K search (~342)

**Changes:**
- Instead of taking first match above threshold:
  1. Get top-K candidates (increase K to 10-20)
  2. Calculate hybrid scores for all
  3. Filter by minimum threshold
  4. Rerank by quality score
  5. Select best match with confidence check

**Implementation:**
```python
# Replace lines 342-400 with reranking logic
# Search more candidates initially
top_matches = self._faiss_search_top_k(T, emb, k=min(20, len(T.rows)))

# Calculate hybrid scores for all candidates
candidates = []
for idx, sim in top_matches:
    if idx < len(T.rows) and T.rows[idx].fresh():
        entry = T.rows[idx]
        hybrid_score = self._calculate_hybrid_score(
            emb, user_text, entry, entry.embedding, sim
        )
        candidates.append({
            'idx': idx,
            'entry': entry,
            'base_sim': sim,
            'hybrid_score': hybrid_score,
            'confidence': self._calculate_confidence(hybrid_score, sim, entry)
        })

# Sort by hybrid score
candidates.sort(key=lambda x: x['hybrid_score'], reverse=True)

# Apply adaptive threshold with confidence check
adaptive_threshold = self._get_adaptive_threshold(T, len(candidates))
best_match = None

for candidate in candidates:
    if candidate['hybrid_score'] >= adaptive_threshold:
        # Additional confidence check to reduce false positives
        if candidate['confidence'] >= 0.7:  # 70% confidence minimum
            best_match = candidate
            break
```

#### 2.2 Confidence Scoring
**File:** `backend/semantic_cache_server.py`
**Location:** New method `_calculate_confidence()`

**Changes:**
- Calculate confidence score based on:
  - Hybrid score strength
  - Base similarity
  - Entry quality (use count, freshness)
  - Domain match
  - Text overlap percentage

**Implementation:**
```python
# Add new method after _calculate_hybrid_score()
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
```

### Phase 3: Domain-Specific Matching

#### 3.1 Domain-Aware Thresholds
**File:** `backend/semantic_cache_server.py`
**Location:** `TenantState` dataclass and `_get_adaptive_threshold()` method

**Changes:**
- Store domain-specific thresholds per tenant
- Use stricter thresholds for technical domains
- Use lenient thresholds for conversational domains

**Implementation:**
```python
# Update TenantState (line ~186)
@dataclass
class TenantState:
    # ... existing fields ...
    domain_thresholds: Dict[str, float] = field(default_factory=dict)  # domain -> threshold

# Add method to get domain-specific threshold
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
```

### Phase 4: Performance Optimizations

#### 4.1 Caching Embeddings
**File:** `backend/semantic_cache_server.py`
**Location:** New cache for embeddings

**Changes:**
- Cache embeddings for common queries
- Reuse embeddings for query expansion variations
- Store embeddings in memory with LRU eviction

**Implementation:**
```python
# Add to SemanticCacheService.__init__()
from collections import OrderedDict

class SemanticCacheService:
    def __init__(self):
        self.tenants: Dict[str, TenantState] = {}
        self._embedding_cache: OrderedDict[str, np.ndarray] = OrderedDict()
        self._embedding_cache_max_size = 1000
        # ... rest of init ...
    
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
```

### Phase 5: Enhanced Metrics & Monitoring

#### 5.1 Track Quality Metrics
**File:** `backend/semantic_cache_server.py`
**Location:** `CacheEvent` and metrics tracking

**Changes:**
- Add confidence score to CacheEvent
- Track false positive rate (user feedback or response quality)
- Add quality metrics to admin API

**Implementation:**
```python
# Update CacheEvent (line ~177)
@dataclass
class CacheEvent:
    timestamp: str
    tenant_id: str
    prompt_hash: str
    decision: str
    similarity: float
    latency_ms: float
    confidence: float = 0.0  # Add confidence field
    hybrid_score: float = 0.0  # Add hybrid score field

# Update metrics() method to include quality metrics
def metrics(self, tenant_id: str) -> dict:
    T = self.tenant(tenant_id)
    # ... existing metrics ...
    
    # Calculate average confidence for semantic hits
    semantic_events = [e for e in T.events if e.decision == "semantic"]
    avg_confidence = np.mean([e.confidence for e in semantic_events]) if semantic_events else 0.0
    
    return {
        # ... existing metrics ...
        "avg_confidence": round(avg_confidence, 3),
        "high_confidence_hits": len([e for e in semantic_events if e.confidence >= 0.8]),
    }
```

## Implementation Order

1. **Phase 1.1**: Context-aware embeddings (high impact, medium complexity)
2. **Phase 2.1**: Multi-stage reranking (high impact, high complexity)
3. **Phase 2.2**: Confidence scoring (medium impact, low complexity)
4. **Phase 1.2**: Query expansion (medium impact, low complexity)
5. **Phase 1.3**: Hybrid similarity signals (medium impact, medium complexity)
6. **Phase 3.1**: Domain-aware thresholds (low impact, low complexity)
7. **Phase 4.1**: Embedding caching (low impact, low complexity)
8. **Phase 5.1**: Quality metrics (low impact, low complexity)

## Testing Strategy

1. **Unit Tests**: Test each new method independently
2. **Integration Tests**: Test full query flow with improvements
3. **Performance Tests**: Measure latency impact of new features
4. **Quality Tests**: Compare hit rate and false positive rate before/after

## Files to Modify

1. `backend/semantic_cache_server.py` - Main algorithm improvements
2. `backend/test_api.py` - Add tests for new features
3. `backend/admin_api.py` - Add quality metrics to admin endpoints

## Expected Outcomes

- **Hit Rate**: Increase by ~15-20% (more semantic matches through better matching)
- **False Positives**: Reduce by ~30% (confidence scoring filters bad matches)
- **Response Quality**: Improve relevance by ~20% (reranking selects best matches)
- **Context Awareness**: Handle multi-turn conversations better
- **Performance**: <5% latency increase (embedding caching mitigates overhead)

## Rollout Strategy

1. Implement Phase 1.1 and 2.1 first (biggest impact)
2. Test with existing traffic
3. Gradually enable other phases
4. Monitor metrics and adjust thresholds
5. A/B test old vs new algorithm if needed

## Key Code Locations

- **Main query method**: `backend/semantic_cache_server.py` line ~298
- **Semantic matching**: `backend/semantic_cache_server.py` line ~337-400
- **TenantState dataclass**: `backend/semantic_cache_server.py` line ~186
- **CacheEntry dataclass**: `backend/semantic_cache_server.py` line ~161
- **Metrics method**: `backend/semantic_cache_server.py` line ~443


