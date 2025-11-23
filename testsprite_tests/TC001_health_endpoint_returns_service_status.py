import requests

BASE_URL = "http://localhost:8000"
TOKEN = "sc-test-abc123 "
HEADERS = {
    "Authorization": f"Bearer {TOKEN.strip()}",
    "Accept": "application/json"
}
TIMEOUT = 30

def test_health_endpoint_returns_service_status():
    url = f"{BASE_URL}/health"
    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request to /health failed: {e}"

    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    try:
        data = response.json()
    except ValueError:
        assert False, "Response is not a valid JSON"

    assert "status" in data, "Response JSON missing 'status' field"
    assert "service" in data, "Response JSON missing 'service' field"
    assert "version" in data, "Response JSON missing 'version' field"
    assert isinstance(data["status"], str), "'status' field is not a string"
    assert isinstance(data["service"], str), "'service' field is not a string"
    assert isinstance(data["version"], str), "'version' field is not a string"

test_health_endpoint_returns_service_status()