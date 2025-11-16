import requests

endpoint = "http://localhost:8000"
api_key = "sc-test-local"  # Replace with a valid tenant API key

def test_chat_completions_endpoint_returns_openai_compatible_response():
    url = f"{endpoint}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": "Hello, how are you?"}
        ],
        "temperature": 0.2,
        "ttl_seconds": 3600
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
    except requests.RequestException as e:
        assert False, f"Request failed: {e}"

    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    try:
        data = response.json()
    except ValueError:
        assert False, "Response is not valid JSON"

    required_fields = ["id", "object", "created", "model", "choices", "usage", "meta"]
    for field in required_fields:
        assert field in data, f"Response missing required field: {field}"

    assert isinstance(data["id"], str), "'id' should be a string"
    assert isinstance(data["object"], str), "'object' should be a string"
    assert isinstance(data["created"], int), "'created' should be an integer"
    assert isinstance(data["model"], str), "'model' should be a string"
    assert isinstance(data["choices"], list) and len(data["choices"]) > 0, "'choices' should be a non-empty list"
    assert isinstance(data["usage"], dict), "'usage' should be an object"
    assert isinstance(data["meta"], dict), "'meta' should be an object"

    # Check messages and params supported in request by consistency with response model field
    assert data["model"] == payload["model"], "Response model does not match request model"

test_chat_completions_endpoint_returns_openai_compatible_response()