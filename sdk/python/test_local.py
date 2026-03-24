"""
Test SDK against local running server.

Usage:
  1. Start the backend: cd backend && python semantic_cache_server.py
  2. Run this: cd sdk/python && python test_local.py
"""

import os
import sys
sys.path.insert(0, ".")

from semantis import SemantisCache

# Replace with your actual API key from Supabase api_keys table
API_KEY = os.environ.get("SEMANTIS_API_KEY", "YOUR_API_KEY_HERE")
BASE_URL = "http://localhost:8000"

client = SemantisCache(api_key=API_KEY, base_url=BASE_URL)


def test_health():
    print("=" * 50)
    print("TEST 1: Health check")
    print("=" * 50)
    resp = client.health()
    print(f"  Status: {resp.get('status')}")
    print()


def test_non_streaming():
    print("=" * 50)
    print("TEST 2: Non-streaming completion")
    print("=" * 50)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "What is semantic caching in one sentence?"}],
    )
    print(f"  Response: {resp.choices[0].message.content[:100]}...")
    print(f"  Model:    {resp.model}")
    if resp.meta:
        print(f"  Cache:    hit={resp.meta.hit}, similarity={resp.meta.similarity}")
    print()


def test_streaming():
    print("=" * 50)
    print("TEST 3: Streaming completion")
    print("=" * 50)
    print("  Response: ", end="")
    for chunk in client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "What is Python in one sentence?"}],
        stream=True,
    ):
        content = chunk.choices[0].delta.content if chunk.choices else None
        if content:
            print(content, end="", flush=True)
    print("\n")


def test_cache_hit():
    print("=" * 50)
    print("TEST 4: Cache hit (repeat same question)")
    print("=" * 50)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "What is semantic caching in one sentence?"}],
    )
    print(f"  Response: {resp.choices[0].message.content[:100]}...")
    if resp.meta:
        print(f"  Cache:    hit={resp.meta.hit}, similarity={resp.meta.similarity}")
        print(f"  Strategy: {resp.meta.strategy}")
    print()


def test_metrics():
    print("=" * 50)
    print("TEST 5: Metrics")
    print("=" * 50)
    resp = client.metrics()
    print(f"  Total requests: {resp.get('requests', 'N/A')}")
    print(f"  Hit rate:       {resp.get('hit_rate', 'N/A')}")
    print()


if __name__ == "__main__":
    print("\nSemantis SDK Local Test")
    print("=" * 50)
    print(f"Server: {BASE_URL}")
    print()

    if API_KEY == "YOUR_API_KEY_HERE":
        print("ERROR: Edit test_local.py and set your API key.")
        print("Find it in Supabase → api_keys table (the one with usage_count 1131)")
        sys.exit(1)

    test_health()
    test_non_streaming()
    test_streaming()
    test_cache_hit()
    test_metrics()

    client.close()
    print("All tests complete!")
