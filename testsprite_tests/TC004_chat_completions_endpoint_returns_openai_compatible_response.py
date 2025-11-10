import requests

def test_chat_completions_endpoint_returns_openai_compatible_response():
    base_url = "http://localhost:8000"
    endpoint = "/v1/chat/completions"
    url = base_url + endpoint

    api_key = "sc-test-local"  # Example tenant API key; replace with a valid key if needed
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
        "ttl_seconds": 600
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        data = response.json()

        assert isinstance(data, dict), "Response is not a JSON object"

        # Validate required top-level fields
        for field in ["id", "object", "created", "model", "choices", "usage", "meta"]:
            assert field in data, f"Missing '{field}' in response"

        assert isinstance(data["id"], str) and data["id"], "'id' should be a non-empty string"
        assert isinstance(data["object"], str) and data["object"], "'object' should be a non-empty string"
        assert isinstance(data["created"], int) and data["created"] > 0, "'created' should be a positive integer"
        assert isinstance(data["model"], str) and data["model"], "'model' should be a non-empty string"

        # Validate 'choices' is a non-empty list
        choices = data["choices"]
        assert isinstance(choices, list) and len(choices) > 0, "'choices' should be a non-empty list"

        # Each choice should be a dict
        for choice in choices:
            assert isinstance(choice, dict), "Each item in 'choices' should be an object/dict"

        # usage should be a dict (content not strictly specified)
        usage = data["usage"]
        assert isinstance(usage, dict), "'usage' should be an object/dict"

        # meta should be a dict (content not strictly specified)
        meta = data["meta"]
        assert isinstance(meta, dict), "'meta' should be an object/dict"

    except requests.RequestException as e:
        raise AssertionError(f"Request to {url} failed: {str(e)}")

test_chat_completions_endpoint_returns_openai_compatible_response()