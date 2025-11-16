import requests

BASE_URL = "http://localhost:8000"
API_KEY = "sc-test-local"  # Use a valid tenant API key here

def test_simple_query_endpoint_returns_semantic_cache_response():
    url = f"{BASE_URL}/query"
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    params = {
        "prompt": "What is Python?",
        "model": "gpt-4o-mini"
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        assert response.status_code == 200, f"Expected status code 200 but got {response.status_code}"
        json_data = response.json()

        # Validate presence of main fields
        assert "answer" in json_data, "Missing 'answer' field in response"
        assert isinstance(json_data["answer"], str), "'answer' field should be a string"

        assert "meta" in json_data, "Missing 'meta' field in response"
        meta = json_data["meta"]
        assert isinstance(meta, dict), "'meta' field should be a dict"

        # Validate required meta fields
        assert "hit" in meta, "Missing 'hit' in meta"
        assert meta["hit"] in ["exact", "semantic", "miss"], f"Invalid hit type: {meta['hit']}"
        assert "similarity" in meta, "Missing 'similarity' in meta"
        assert isinstance(meta["similarity"], (int, float)), "'similarity' should be a number"
        assert "latency_ms" in meta, "Missing 'latency_ms' in meta"
        assert isinstance(meta["latency_ms"], (int, float)), "'latency_ms' should be a number"
        assert "strategy" in meta, "Missing 'strategy' in meta"
        assert isinstance(meta["strategy"], str), "'strategy' should be a string"

        # Validate metrics field presence
        assert "metrics" in json_data, "Missing 'metrics' field in response"
        assert isinstance(json_data["metrics"], dict), "'metrics' field should be a dict"

    except requests.exceptions.RequestException as e:
        assert False, f"Request failed: {e}"

test_simple_query_endpoint_returns_semantic_cache_response()