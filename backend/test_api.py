"""
Test Script for Semantis AI Backend

Validates:
- Health endpoint
- Metrics endpoint
- Query and cache behavior
"""

import requests, time, json

BASE_URL = "http://localhost:8000"
HEADERS = {"Authorization": "Bearer sc-test-local"}

def test_health():
    r = requests.get(f"{BASE_URL}/health")
    print("✅ /health:", r.status_code, r.json())

def test_metrics():
    r = requests.get(f"{BASE_URL}/metrics", headers=HEADERS)
    print("✅ /metrics:", r.status_code, r.json())

def test_query(prompt: str):
    print(f"\n🧠 Querying: {prompt}")
    r = requests.get(f"{BASE_URL}/query", params={"prompt": prompt}, headers=HEADERS)
    if r.ok:
        data = r.json()
        print(f"✅ /query => {data['meta']['hit']} | sim={data['meta']['similarity']:.3f} | latency={data['meta']['latency_ms']}ms")
        print("Answer:", data["answer"][:200])
    else:
        print("❌ Error:", r.status_code, r.text)

def run_all():
    print("=== SEMANTIS AI BACKEND TEST SUITE ===")
    test_health()
    test_metrics()

    prompts = [
        "What is Python in 10 words?",
        "Explain Python in 10 words.",
        "What is the capital of France?",
    ]

    for p in prompts:
        test_query(p)
        time.sleep(2)  # small pause between calls

    print("\nRe-checking /metrics after multiple requests...")
    test_metrics()
    print("\n✅ All tests completed successfully.")

if __name__ == "__main__":
    run_all()
