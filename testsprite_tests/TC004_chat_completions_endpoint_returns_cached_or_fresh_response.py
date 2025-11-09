import requests
import uuid

BASE_URL = "http://localhost:8000"
API_KEY = "sc-test-local"  # Replace with a valid tenant-scoped API key if needed

def chat_completions_endpoint_returns_cached_or_fresh_response():
    url = f"{BASE_URL}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": f"Test message for chat completion {uuid.uuid4()}"
            }
        ],
        "temperature": 0.2,
        "ttl_seconds": 604800
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        resp_json = response.json()

        # Assert required fields in response
        assert isinstance(resp_json.get("id"), str) and len(resp_json["id"]) > 0, "Missing or invalid 'id'"
        assert isinstance(resp_json.get("object"), str) and len(resp_json["object"]) > 0, "Missing or invalid 'object'"
        assert isinstance(resp_json.get("created"), int), "Missing or invalid 'created' timestamp"
        assert isinstance(resp_json.get("model"), str) and len(resp_json["model"]) > 0, "Missing or invalid 'model'"
        assert isinstance(resp_json.get("choices"), list) and len(resp_json["choices"]) > 0, "Missing or invalid 'choices'"
        assert isinstance(resp_json.get("usage"), dict), "Missing or invalid 'usage'"
        assert isinstance(resp_json.get("meta"), dict), "Missing or invalid 'meta'"

        # Validate meta content keys for semantic caching info
        meta = resp_json["meta"]
        # Expected meta keys may include hit type, similarity, latency etc. Check existence at least.
        assert any(hit_type in meta.get("hit", "") for hit_type in ["exact", "semantic", "miss"]), "'meta.hit' value invalid"
        # similarity may be float or absent, optional existence check
        if "similarity" in meta:
            assert isinstance(meta["similarity"], (float, int)), "'meta.similarity' should be a number"
        if "latency_ms" in meta:
            assert isinstance(meta["latency_ms"], (float, int)), "'meta.latency_ms' should be a number"

    except (requests.RequestException, AssertionError) as e:
        raise AssertionError(f"Test failed: {str(e)}")

chat_completions_endpoint_returns_cached_or_fresh_response()