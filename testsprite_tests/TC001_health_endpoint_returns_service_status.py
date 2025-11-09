import requests

def test_health_endpoint_returns_service_status():
    base_url = "http://localhost:8000"
    url = f"{base_url}/health"
    timeout = 30
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as e:
        assert False, f"Request to {url} failed: {e}"

    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    try:
        data = response.json()
    except ValueError:
        assert False, "Response is not valid JSON"

    assert isinstance(data, dict), "Response JSON is not an object"
    assert data.get("status") == "ok", f"Expected 'status' to be 'ok', got {data.get('status')}"
    assert data.get("service") == "semantic-cache", f"Expected 'service' to be 'semantic-cache', got {data.get('service')}"
    version = data.get("version")
    assert isinstance(version, str) and len(version) > 0, f"Expected non-empty 'version' string, got {version}"

test_health_endpoint_returns_service_status()