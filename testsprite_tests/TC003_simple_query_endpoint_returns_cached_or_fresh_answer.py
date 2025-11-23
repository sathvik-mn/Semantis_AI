import requests
import time

BASE_URL = "http://localhost:8000"
AUTH_TOKEN = "sc-test-abc123 "
HEADERS = {"Authorization": f"Bearer {AUTH_TOKEN.strip()}"}
TIMEOUT = 30

def test_simple_query_endpoint_returns_cached_or_fresh_answer():
    prompt = "What is Python?"
    model = "gpt-4o-mini"
    params = {"prompt": prompt, "model": model}

    try:
        # First request: Expect a miss or cached answer (if existing)
        start_ts = time.time()
        response1 = requests.get(f"{BASE_URL}/query", headers=HEADERS, params=params, timeout=TIMEOUT)
        latency_ms_1 = (time.time() - start_ts) * 1000

        assert response1.status_code == 200, f"Expected 200, got {response1.status_code}"
        body1 = response1.json()
        assert "answer" in body1, "Response missing 'answer'"
        assert "meta" in body1, "Response missing 'meta'"
        meta1 = body1["meta"]

        # Validate meta keys and their types
        assert meta1.get("hit") in ["exact", "semantic", "miss"], f"Unexpected hit type: {meta1.get('hit')}"
        assert isinstance(meta1.get("similarity"), (float, int)), "meta.similarity must be a number"
        assert isinstance(meta1.get("latency_ms"), (float, int)), "meta.latency_ms must be a number"
        assert isinstance(meta1.get("strategy"), str), "meta.strategy must be a string"

        # The latency reported by server should be a positive number and roughly match actual client latency
        assert meta1["latency_ms"] >= 0, "meta.latency_ms should be >= 0"
        assert abs(meta1["latency_ms"] - latency_ms_1) < 5000, "meta.latency_ms very different from measured latency"

        # Save the answer to test caching hits semantic or exact on second request
        cached_answer = body1["answer"]

        # Second request: Identical prompt should result in exact or semantic hit with same answer
        start_ts = time.time()
        response2 = requests.get(f"{BASE_URL}/query", headers=HEADERS, params=params, timeout=TIMEOUT)
        latency_ms_2 = (time.time() - start_ts) * 1000

        assert response2.status_code == 200, f"Expected 200, got {response2.status_code}"
        body2 = response2.json()
        assert "answer" in body2, "Response missing 'answer'"
        assert "meta" in body2, "Response missing 'meta'"
        meta2 = body2["meta"]

        # On second call we expect hit to be either "exact" or "semantic" (not miss)
        assert meta2.get("hit") in ["exact", "semantic"], f"Unexpected hit type on second request: {meta2.get('hit')}"
        assert body2["answer"] == cached_answer, "Cached answer differs from first response"

        # Validate meta fields on second call
        assert isinstance(meta2.get("similarity"), (float, int)), "meta.similarity must be a number"
        assert isinstance(meta2.get("latency_ms"), (float, int)), "meta.latency_ms must be a number"
        assert isinstance(meta2.get("strategy"), str), "meta.strategy must be a string"
        assert meta2["latency_ms"] >= 0, "meta.latency_ms should be >= 0"
        assert abs(meta2["latency_ms"] - latency_ms_2) < 5000, "meta.latency_ms very different from measured latency"

        # Also test a semantic query (paraphrased) to try to trigger semantic cache hit
        semantic_prompt = "Can you explain what Python is?"
        params_semantic = {"prompt": semantic_prompt, "model": model}
        start_ts = time.time()
        response3 = requests.get(f"{BASE_URL}/query", headers=HEADERS, params=params_semantic, timeout=TIMEOUT)
        latency_ms_3 = (time.time() - start_ts) * 1000

        assert response3.status_code == 200, f"Expected 200, got {response3.status_code}"
        body3 = response3.json()
        assert "answer" in body3, "Response missing 'answer'"
        assert "meta" in body3, "Response missing 'meta'"
        meta3 = body3["meta"]

        assert meta3.get("hit") in ["exact", "semantic", "miss"], f"Unexpected hit type on semantic query: {meta3.get('hit')}"
        assert isinstance(meta3.get("similarity"), (float, int)), "meta.similarity must be a number"
        assert meta3["similarity"] >= 0.0, "meta.similarity should be >= 0"
        assert meta3.get("latency_ms") >= 0, "meta.latency_ms should be >= 0"
        assert isinstance(meta3.get("strategy"), str), "meta.strategy must be a string"

    except requests.RequestException as e:
        assert False, f"Request failed: {e}"
    except AssertionError:
        raise

test_simple_query_endpoint_returns_cached_or_fresh_answer()