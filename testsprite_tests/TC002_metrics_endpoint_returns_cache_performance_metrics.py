import requests

base_url = "http://localhost:8000"
api_key = "sc-test-local-authkey"  # Replace with a valid tenant API key

def test_metrics_endpoint_returns_cache_performance_metrics():
    url = f"{base_url}/metrics"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }
    try:
        response = requests.get(url, headers=headers, timeout=30)
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        data = response.json()
        # Validate presence and types of expected fields
        expected_fields = {
            "tenant": str,
            "requests": int,
            "hits": int,
            "semantic_hits": int,
            "misses": int,
            "hit_ratio": (float, int),
            "sim_threshold": (float, int),
            "entries": int,
            "p50_latency_ms": (float, int),
            "p95_latency_ms": (float, int),
        }
        for field, field_type in expected_fields.items():
            assert field in data, f"Missing field '{field}' in response"
            assert isinstance(data[field], field_type), f"Field '{field}' expected type {field_type}, got {type(data[field])}"
    except requests.exceptions.RequestException as e:
        assert False, f"Request failed: {e}"

test_metrics_endpoint_returns_cache_performance_metrics()