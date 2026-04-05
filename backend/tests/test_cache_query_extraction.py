"""
Unit tests for cache query extraction and FAISS alignment.

These tests verify the bugs fixed in commits 847f0a0, f650435, and the
extract_cache_query refactor.  They do NOT require a running server or
OpenAI key — they test the pure logic layer.

Run with: pytest tests/test_cache_query_extraction.py -v
"""
import sys
import os
import numpy as np
import pytest

# Add backend root to path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ── extract_cache_query tests ──

class TestExtractCacheQuery:
    """Verify that cache identity always derives from the last user message,
    regardless of conversation history."""

    @pytest.fixture(autouse=True)
    def _import(self):
        from semantic_cache_server import SemanticCacheService
        self.extract = SemanticCacheService.extract_cache_query
        self.norm = SemanticCacheService.norm_text

    def test_single_user_message(self):
        msgs = [{"role": "user", "content": "What is Python?"}]
        assert self.extract(msgs) == "what is python?"

    def test_multi_turn_uses_last_user_message_only(self):
        """The bug: prompt_norm was joining ALL user messages, polluting
        the cache key with conversation history.  After fix,
        extract_cache_query must return only the last user turn."""
        msgs = [
            {"role": "user", "content": "explain how indexers work in azure"},
            {"role": "assistant", "content": "Indexers in Azure..."},
            {"role": "user", "content": "How Indexers Work in Microsoft Azure"},
        ]
        result = self.extract(msgs)
        assert result == "how indexers work in microsoft azure"
        # Must NOT contain the first user message
        assert "explain" not in result

    def test_system_messages_ignored(self):
        msgs = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello world"},
        ]
        assert self.extract(msgs) == "hello world"

    def test_assistant_messages_ignored(self):
        msgs = [
            {"role": "user", "content": "First question"},
            {"role": "assistant", "content": "First answer"},
            {"role": "user", "content": "Second question"},
            {"role": "assistant", "content": "Second answer"},
            {"role": "user", "content": "Third question"},
        ]
        assert self.extract(msgs) == "third question"

    def test_empty_messages_returns_empty(self):
        assert self.extract([]) == ""

    def test_no_user_messages_returns_empty(self):
        msgs = [{"role": "system", "content": "system prompt"}]
        assert self.extract(msgs) == ""

    def test_whitespace_normalization(self):
        msgs = [{"role": "user", "content": "  lots   of   spaces  "}]
        assert self.extract(msgs) == "lots of spaces"

    def test_matches_norm_text(self):
        """extract_cache_query must produce identical output to
        norm_text(last_user_message) — they are the same operation."""
        text = "How does RAG work?"
        msgs = [{"role": "user", "content": text}]
        assert self.extract(msgs) == self.norm(text)

    def test_paraphrase_with_prior_history_same_key(self):
        """Two different conversation contexts where the last user message
        is identical must produce the same cache key."""
        msgs_short = [
            {"role": "user", "content": "What is RAG?"},
        ]
        msgs_long = [
            {"role": "user", "content": "Tell me about LLMs"},
            {"role": "assistant", "content": "LLMs are..."},
            {"role": "user", "content": "What is RAG?"},
        ]
        assert self.extract(msgs_short) == self.extract(msgs_long)

    def test_unrelated_new_topic_in_old_chat(self):
        """A new unrelated question in an existing chat session should cache
        independently — extract only the new question."""
        msgs = [
            {"role": "user", "content": "explain quantum computing"},
            {"role": "assistant", "content": "Quantum computing uses..."},
            {"role": "user", "content": "Best pizza recipe"},
        ]
        result = self.extract(msgs)
        assert result == "best pizza recipe"
        assert "quantum" not in result


# ── FAISS alignment tests ──

class TestFAISSRowAlignment:
    """Verify that T.rows and the FAISS index stay in sync.

    The bug: when embedding failed, entry was added to T.rows but NOT FAISS,
    causing T.rows[i] != FAISS position i for all subsequent entries.
    """

    @pytest.fixture
    def service(self):
        from semantic_cache_server import SemanticCacheService
        svc = SemanticCacheService.__new__(SemanticCacheService)
        svc.tenants = {}
        svc._cache_lock = __import__("threading").Lock()
        svc._embedding_cache = {}
        svc._embedding_cache_max_size = 1000
        return svc

    @pytest.fixture
    def tenant(self, service):
        return service.tenant("test_alignment")

    def test_faiss_add_creates_index(self, service, tenant):
        """First _faiss_add should create the FAISS index."""
        assert tenant.index is None
        emb = np.random.randn(1024).astype("float32")
        emb /= np.linalg.norm(emb)
        service._faiss_add(tenant, emb, tenant_id="test", entry_id="e1")
        assert tenant.index is not None
        assert tenant.index.ntotal == 1

    def test_faiss_position_matches_rows(self, service, tenant):
        """After N inserts, FAISS position i must correspond to T.rows[i]."""
        from semantic_cache_server import CacheEntry

        for i in range(5):
            emb = np.random.randn(1024).astype("float32")
            emb /= np.linalg.norm(emb)
            entry = CacheEntry(
                prompt_norm=f"query {i}",
                response_text=f"answer {i}",
                embedding=emb,
                model="gpt-4o-mini",
                ttl_seconds=3600,
            )
            tenant.rows.append(entry)
            service._faiss_add(tenant, emb, tenant_id="test", entry_id=f"e{i}")

        assert tenant.index.ntotal == len(tenant.rows) == 5

        # Search for the 3rd entry's embedding — should return index 2
        q = tenant.rows[2].embedding.astype("float32").reshape(1, -1)
        import faiss
        faiss.normalize_L2(q)
        sims, idxs = tenant.index.search(q, 1)
        idx = int(idxs[0][0])
        assert tenant.rows[idx].prompt_norm == "query 2"

    def test_skipping_rows_when_no_embedding_keeps_alignment(self, service, tenant):
        """Entries without embeddings must NOT go into T.rows, so FAISS
        positions stay aligned with T.rows indices."""
        from semantic_cache_server import CacheEntry

        # Add entry WITH embedding
        emb1 = np.random.randn(1024).astype("float32")
        emb1 /= np.linalg.norm(emb1)
        entry1 = CacheEntry(
            prompt_norm="with embedding",
            response_text="answer 1",
            embedding=emb1,
            model="gpt-4o-mini",
            ttl_seconds=3600,
        )
        tenant.rows.append(entry1)
        service._faiss_add(tenant, emb1, tenant_id="test", entry_id="e1")

        # Simulate entry WITHOUT embedding (should NOT go into rows)
        entry_no_emb = CacheEntry(
            prompt_norm="no embedding",
            response_text="answer 2",
            embedding=None,
            model="gpt-4o-mini",
            ttl_seconds=3600,
        )
        tenant.exact["no embedding"] = entry_no_emb
        # Do NOT append to tenant.rows or FAISS

        # Add another entry WITH embedding
        emb3 = np.random.randn(1024).astype("float32")
        emb3 /= np.linalg.norm(emb3)
        entry3 = CacheEntry(
            prompt_norm="with embedding 2",
            response_text="answer 3",
            embedding=emb3,
            model="gpt-4o-mini",
            ttl_seconds=3600,
        )
        tenant.rows.append(entry3)
        service._faiss_add(tenant, emb3, tenant_id="test", entry_id="e3")

        # FAISS has 2 entries, T.rows has 2 entries — aligned
        assert tenant.index.ntotal == 2
        assert len(tenant.rows) == 2

        # Search for entry3's embedding — should find it at rows[1]
        q = emb3.astype("float32").reshape(1, -1)
        import faiss
        faiss.normalize_L2(q)
        sims, idxs = tenant.index.search(q, 1)
        idx = int(idxs[0][0])
        assert idx == 1
        assert tenant.rows[idx].prompt_norm == "with embedding 2"

        # The no-embedding entry is still reachable via exact lookup
        assert "no embedding" in tenant.exact


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
