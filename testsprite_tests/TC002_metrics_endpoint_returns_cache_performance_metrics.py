import requests

BASE_URL = "http://localhost:8000"
API_KEY = "sc-test-local"  # Placeholder: replace with a valid tenant API key if available

def test_metrics_endpoint_returns_cache_performance_metrics():
    url = f"{BASE_URL}/metrics"
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    timeout = 30
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
    except requests.RequestException as e:
        assert False, f"Request to /metrics endpoint failed: {e}"

    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"

    try:
        data = response.json()
    except ValueError:
        assert False, "Response is not valid JSON"

    expected_fields = [
        "tenant",
        "requests",
        "hits",
        "semantic_hits",
        "misses",
        "hit_ratio",
        "sim_threshold",
        "entries",
        "p50_latency_ms",
        "p95_latency_ms",
    ]

    for field in expected_fields:
        assert field in data, f"Field '{field}' missing in response"

    # Validate types where applicable
    assert isinstance(data["tenant"], str), "'tenant' field is not a string"
    assert isinstance(data["requests"], int), "'requests' field is not an integer"
    assert isinstance(data["hits"], int), "'hits' field is not an integer"
    assert isinstance(data["semantic_hits"], int), "'semantic_hits' field is not an integer"
    assert isinstance(data["misses"], int), "'misses' field is not an integer"
    assert isinstance(data["hit_ratio"], (int, float)), "'hit_ratio' field is not a number"
    assert isinstance(data["sim_threshold"], (int, float)), "'sim_threshold' field is not a number"
    assert isinstance(data["entries"], int), "'entries' field is not an integer"
    assert isinstance(data["p50_latency_ms"], (int, float)), "'p50_latency_ms' field is not a number"
    assert isinstance(data["p95_latency_ms"], (int, float)), "'p95_latency_ms' field is not a number"

test_metrics_endpoint_returns_cache_performance_metrics()