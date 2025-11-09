import requests

BASE_URL = "http://localhost:8000"
API_KEY = "sc-test-local"  # Replace with a valid tenant-scoped API key

def test_metrics_endpoint_returns_cache_performance_metrics():
    url = f"{BASE_URL}/metrics"
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    try:
        response = requests.get(url, headers=headers, timeout=30)
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        json_data = response.json()

        # Validate presence and types of required fields
        expected_fields = {
            "tenant": str,
            "requests": int,
            "hits": int,
            "semantic_hits": int,
            "misses": int,
            "hit_ratio": (int, float),
            "sim_threshold": (int, float),
            "entries": int,
            "p50_latency_ms": (int, float),
            "p95_latency_ms": (int, float),
        }

        for field, field_type in expected_fields.items():
            assert field in json_data, f"Missing field '{field}' in response"
            assert isinstance(json_data[field], field_type), (
                f"Field '{field}' expected type {field_type} but got {type(json_data[field])}"
            )

        # Additional sanity checks on metric values (non-negative)
        assert json_data["requests"] >= 0, "requests should be non-negative"
        assert json_data["hits"] >= 0, "hits should be non-negative"
        assert json_data["semantic_hits"] >= 0, "semantic_hits should be non-negative"
        assert json_data["misses"] >= 0, "misses should be non-negative"
        assert 0.0 <= json_data["hit_ratio"] <= 1.0, "hit_ratio should be between 0 and 1"
        assert 0.0 <= json_data["sim_threshold"] <= 1.0, "sim_threshold should be between 0 and 1"
        assert json_data["entries"] >= 0, "entries should be non-negative"
        assert json_data["p50_latency_ms"] >= 0, "p50_latency_ms should be non-negative"
        assert json_data["p95_latency_ms"] >= 0, "p95_latency_ms should be non-negative"

    except requests.RequestException as e:
        assert False, f"Request to /metrics endpoint failed: {e}"

test_metrics_endpoint_returns_cache_performance_metrics()