import requests

BASE_URL = "http://localhost:8000"
API_KEY = "sc-test-local"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}
TIMEOUT = 30

def test_simple_query_endpoint_returns_semantic_cache_response():
    prompt = "What is Python?"
    params = {"prompt": prompt, "model": "gpt-4o-mini"}

    try:
        response = requests.get(f"{BASE_URL}/query", headers=HEADERS, params=params, timeout=TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as e:
        assert False, f"Request to /query failed: {e}"

    json_data = response.json()
    # Validate top-level keys
    assert "answer" in json_data, "Response missing 'answer'"
    assert "meta" in json_data, "Response missing 'meta'"
    meta = json_data["meta"]
    # Validate meta contents
    assert isinstance(meta, dict), "'meta' should be an object"
    assert "hit" in meta, "'meta' missing 'hit'"
    assert meta["hit"] in ("exact", "semantic", "miss"), "'hit' must be 'exact', 'semantic', or 'miss'"
    assert "similarity" in meta, "'meta' missing 'similarity'"
    assert isinstance(meta["similarity"], (float, int)), "'similarity' must be a number"
    assert "latency_ms" in meta, "'meta' missing 'latency_ms'"
    assert isinstance(meta["latency_ms"], (float, int)), "'latency_ms' must be a number"
    assert "strategy" in meta, "'meta' missing 'strategy'"
    assert isinstance(meta["strategy"], str), "'strategy' must be a string"

    # Optional: Check metrics key presence (type object) if present
    if "metrics" in json_data:
        assert isinstance(json_data["metrics"], dict), "'metrics' should be an object if present"

test_simple_query_endpoint_returns_semantic_cache_response()