import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30
API_KEY = "sc-test-local"  # Example tenant API key for authentication

def test_health_endpoint_returns_service_status():
    url = f"{BASE_URL}/health"
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    try:
        response = requests.get(url, headers=headers, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request to /health failed: {e}"

    assert response.status_code == 200, f"Expected status 200, got {response.status_code}"

    try:
        data = response.json()
    except ValueError:
        assert False, "Response is not valid JSON"

    # Validate keys and types
    required_keys = ["status", "service", "version"]
    for key in required_keys:
        assert key in data, f"Response JSON missing key: {key}"
        assert isinstance(data[key], str), f"Key '{key}' should be of type str"

    # Optional deeper checks against expected values
    assert data["status"].lower() == "ok", f"Expected 'status' to be 'ok', got {data['status']}"
    assert data["service"].lower() == "semantic-cache", f"Expected 'service' to be 'semantic-cache', got {data['service']}"

test_health_endpoint_returns_service_status()