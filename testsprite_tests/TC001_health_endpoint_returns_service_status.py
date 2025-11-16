import requests

def test_health_endpoint_returns_service_status():
    base_url = "http://localhost:8000"
    url = f"{base_url}/health"
    headers = {
        "Accept": "application/json"
    }
    try:
        response = requests.get(url, headers=headers, timeout=30)
    except requests.RequestException as e:
        assert False, f"Request to /health endpoint failed: {e}"

    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"

    try:
        json_data = response.json()
    except ValueError:
        assert False, "Response is not a valid JSON"

    assert isinstance(json_data, dict), f"Response JSON is not an object: {json_data}"
    assert "status" in json_data, "Response JSON missing 'status' field"
    assert "service" in json_data, "Response JSON missing 'service' field"
    assert "version" in json_data, "Response JSON missing 'version' field"

    assert isinstance(json_data["status"], str), "'status' field is not a string"
    assert isinstance(json_data["service"], str), "'service' field is not a string"
    assert isinstance(json_data["version"], str), "'version' field is not a string"


test_health_endpoint_returns_service_status()