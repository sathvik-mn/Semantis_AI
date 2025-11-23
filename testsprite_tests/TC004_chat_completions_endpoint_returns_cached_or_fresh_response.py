import requests
import time

BASE_URL = "http://localhost:8000"
API_KEY = "sc-test-abc123 "
HEADERS = {
    "Authorization": f"Bearer {API_KEY.strip()}",
    "Content-Type": "application/json"
}
TIMEOUT = 30

def test_chat_completions_endpoint_returns_cached_or_fresh_response():
    # Define the chat completion payload with unique content for test isolation
    messages = [
        {"role": "user", "content": "Hello, what is the capital of France?"}
    ]
    payload = {
        "model": "gpt-4o-mini",
        "messages": messages,
        "temperature": 0.2,
        "ttl_seconds": 604800
    }

    url = f"{BASE_URL}/v1/chat/completions"

    # Attempt first call: should miss cache and store response
    response1 = requests.post(url, headers=HEADERS, json=payload, timeout=TIMEOUT)
    assert response1.status_code == 200, f"Expected 200 OK but got {response1.status_code}"
    json1 = response1.json()

    # Validate structure of response
    assert "choices" in json1, "Response missing 'choices'"
    assert isinstance(json1["choices"], list) and len(json1["choices"]) > 0, "Choices is empty or invalid"
    assert "meta" in json1, "Response missing 'meta' information"
    meta1 = json1["meta"]
    assert "hit" in meta1 and meta1["hit"] in ("exact", "semantic", "miss"), f"Unexpected hit value: {meta1.get('hit')}"
    assert "latency_ms" in meta1 and isinstance(meta1["latency_ms"], (float, int)), "Missing or invalid latency_ms"
    # On first call, hit should be "miss" as cache wasn't hit yet
    assert meta1["hit"] == "miss", f"Expected cache miss on first request, got {meta1['hit']}"

    # Wait a short moment to ensure different timing latency on the second call
    time.sleep(1)

    # Second call with identical payload should hit the cache: exact or semantic
    response2 = requests.post(url, headers=HEADERS, json=payload, timeout=TIMEOUT)
    assert response2.status_code == 200, f"Expected 200 OK but got {response2.status_code}"
    json2 = response2.json()

    assert "choices" in json2, "Second response missing 'choices'"
    assert isinstance(json2["choices"], list) and len(json2["choices"]) > 0, "Second response choices invalid"
    assert "meta" in json2, "Second response missing 'meta' information"
    meta2 = json2["meta"]
    assert "hit" in meta2 and meta2["hit"] in ("exact", "semantic", "miss"), f"Unexpected hit value in second response: {meta2.get('hit')}"
    assert "latency_ms" in meta2 and isinstance(meta2["latency_ms"], (float, int)), "Second response missing or invalid latency_ms"
    # On second request, expect cache hit (exact or semantic), not miss
    assert meta2["hit"] in ("exact", "semantic"), f"Expected cache hit on second request but got {meta2['hit']}"

    # Validate that the cached response content matches between requests (choices content)
    # At least the first choice text should be the same
    first_choice1 = json1["choices"][0]
    first_choice2 = json2["choices"][0]
    assert first_choice1 == first_choice2, "Cached response differs from original response"

test_chat_completions_endpoint_returns_cached_or_fresh_response()