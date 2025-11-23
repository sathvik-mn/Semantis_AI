import requests

def test_metrics_endpoint_returns_cache_performance_metrics():
    base_url = "http://localhost:8000"
    headers = {
        "Authorization": "Bearer sc-test-abc123",
        "Accept": "application/json"
    }
    try:
        response = requests.get(f"{base_url}/metrics", headers=headers, timeout=30)
        assert response.status_code == 200, f"Expected status 200, got {response.status_code}"
        data = response.json()

        # Validate required fields presence and types
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
            "p95_latency_ms": (float, int)
        }
        for field, field_type in expected_fields.items():
            assert field in data, f"Missing '{field}' in response"
            assert isinstance(data[field], field_type), f"Field '{field}' is not of type {field_type}"

        # Additional logical checks
        assert data["requests"] >= 0, "'requests' should be non-negative"
        assert data["hits"] >= 0, "'hits' should be non-negative"
        assert data["semantic_hits"] >= 0, "'semantic_hits' should be non-negative"
        assert data["misses"] >= 0, "'misses' should be non-negative"
        assert 0.0 <= data["hit_ratio"] <= 1.0, "'hit_ratio' should be between 0 and 1"
        assert 0.0 <= data["sim_threshold"] <= 1.0, "'sim_threshold' should be between 0 and 1"
        assert data["entries"] >= 0, "'entries' should be non-negative"
        assert data["p50_latency_ms"] >= 0, "'p50_latency_ms' should be non-negative"
        assert data["p95_latency_ms"] >= 0, "'p95_latency_ms' should be non-negative"
    
    except requests.RequestException as e:
        assert False, f"Request to /metrics failed: {e}"

test_metrics_endpoint_returns_cache_performance_metrics()