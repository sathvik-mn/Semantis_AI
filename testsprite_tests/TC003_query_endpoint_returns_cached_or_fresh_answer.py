import requests
from requests.exceptions import RequestException

BASE_URL = "http://localhost:8000"
API_KEY = "sc-test-local"  # Use a valid tenant-scoped API key here
TIMEOUT = 30

def test_query_endpoint_returns_cached_or_fresh_answer():
    url = f"{BASE_URL}/query"
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    params = {
        "prompt": "What is Python?",
        "model": "gpt-4o-mini"
    }
    try:
        response = requests.get(url, headers=headers, params=params, timeout=TIMEOUT)
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        data = response.json()
        assert "answer" in data, "Response JSON missing 'answer'"
        assert isinstance(data["answer"], str) and data["answer"], "'answer' must be a non-empty string"
        assert "meta" in data, "Response JSON missing 'meta'"
        meta = data["meta"]
        # Validate hit type
        assert "hit" in meta, "'meta' missing 'hit'"
        assert meta["hit"] in ("exact", "semantic", "miss"), f"Unexpected hit value: {meta['hit']}"
        # Validate similarity score
        assert "similarity" in meta, "'meta' missing 'similarity'"
        similarity = meta["similarity"]
        assert isinstance(similarity, (int, float)), "'similarity' must be a number"
        assert 0.0 <= similarity <= 1.0, "'similarity' must be between 0 and 1"
        # Validate latency_ms
        assert "latency_ms" in meta, "'meta' missing 'latency_ms'"
        latency = meta["latency_ms"]
        assert isinstance(latency, (int, float)), "'latency_ms' must be a number"
        assert latency >= 0, "'latency_ms' must be non-negative"
        # Validate strategy
        assert "strategy" in meta, "'meta' missing 'strategy'"
        assert isinstance(meta["strategy"], str) and meta["strategy"], "'strategy' must be a non-empty string"
    except RequestException as e:
        assert False, f"Request failed: {e}"

test_query_endpoint_returns_cached_or_fresh_answer()