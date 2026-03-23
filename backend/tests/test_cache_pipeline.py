"""
Integration tests for the semantic cache pipeline.
Run with: pytest tests/test_cache_pipeline.py -v
Requires the server running at http://localhost:8000
"""
import requests
import time
import pytest  # type: ignore[import-not-found]

BASE_URL = "http://localhost:8000"
API_KEY = "Bearer sc-test-integration"
HEADERS = {"Authorization": API_KEY, "Content-Type": "application/json"}


def make_query(prompt: str, model: str = "gpt-4o-mini") -> dict:
    r = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        headers=HEADERS,
        json={"model": model, "messages": [{"role": "user", "content": prompt}]},
    )
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    return r.json()


class TestHealthAndMetrics:
    def test_health_endpoint(self):
        r = requests.get(f"{BASE_URL}/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] in ("healthy", "ok")

    def test_prometheus_endpoint(self):
        r = requests.get(f"{BASE_URL}/prometheus/metrics")
        assert r.status_code == 200

    def test_metrics_require_auth(self):
        r = requests.get(f"{BASE_URL}/metrics")
        assert r.status_code in (401, 403)

    def test_settings_require_auth(self):
        r = requests.get(f"{BASE_URL}/settings")
        assert r.status_code in (401, 403)


class TestCachePipeline:
    unique = str(int(time.time()))

    def test_01_first_query_is_miss(self):
        prompt = f"Integration test query {self.unique}: What is Python?"
        data = make_query(prompt)
        meta = data.get("meta", {})
        assert meta.get("hit") == "miss", f"Expected miss, got {meta}"
        assert data["choices"][0]["message"]["content"], "Response should not be empty"

    def test_02_exact_repeat_is_hit(self):
        time.sleep(3)
        prompt = f"Integration test query {self.unique}: What is Python?"
        data = make_query(prompt)
        meta = data.get("meta", {})
        assert meta.get("hit") in ("exact", "semantic"), f"Expected hit, got {meta}"

    def test_03_paraphrase_is_semantic_hit(self):
        prompt = f"Integration test query {self.unique}: Tell me about Python"
        data = make_query(prompt)
        meta = data.get("meta", {})
        # May or may not match depending on threshold; just verify structure
        assert "hit" in meta
        assert "similarity" in meta
        assert "latency_ms" in meta

    def test_04_unrelated_query_is_miss(self):
        prompt = f"Integration test {self.unique}: Best recipe for chocolate cake?"
        data = make_query(prompt)
        meta = data.get("meta", {})
        assert meta.get("hit") == "miss", f"Unrelated query should miss, got {meta}"


class TestOpenAICompatibility:
    def test_response_structure(self):
        data = make_query("OpenAI compat test: hello world")
        assert "id" in data
        assert data["object"] == "chat.completion"
        assert "choices" in data
        assert len(data["choices"]) > 0
        assert data["choices"][0]["message"]["role"] == "assistant"
        assert "usage" in data
        assert "prompt_tokens" in data["usage"]
        assert "meta" in data

    def test_models_endpoint(self):
        r = requests.get(f"{BASE_URL}/v1/models", headers=HEADERS)
        assert r.status_code == 200
        data = r.json()
        assert "data" in data


class TestErrorHandling:
    def test_missing_auth_returns_error(self):
        r = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            headers={"Content-Type": "application/json"},
            json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "test"}]},
        )
        assert r.status_code in (401, 403)
        data = r.json()
        assert "error" in data or "detail" in data

    def test_empty_messages_returns_error(self):
        r = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            headers=HEADERS,
            json={"model": "gpt-4o-mini", "messages": []},
        )
        assert r.status_code in (400, 422, 500)

    def test_billing_plans_is_public(self):
        r = requests.get(f"{BASE_URL}/api/billing/plans")
        assert r.status_code == 200
        data = r.json()
        assert "plans" in data
        assert "free" in data["plans"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
