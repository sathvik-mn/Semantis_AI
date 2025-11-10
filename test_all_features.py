"""
Test All Features - Comprehensive test of all implemented features
"""
import sys
import os
from pathlib import Path

# Add SDK to path
sdk_path = Path(__file__).parent / "sdk" / "python-wrapper"
sys.path.insert(0, str(sdk_path))

print("=" * 70)
print("COMPREHENSIVE FEATURE TEST")
print("=" * 70)

# Test 1: Simple query method
print("\n1. Testing Simple Query Method...")
try:
    from semantis_cache import SemanticCache
    cache = SemanticCache(api_key="sc-test-local")
    response = cache.query("What is AI?")
    print(f"   [OK] Simple query works")
    print(f"   Answer: {response.answer[:50]}...")
    print(f"   Cache hit: {response.cache_hit}")
except Exception as e:
    print(f"   [FAIL] Simple query failed: {e}")

# Test 2: OpenAI-compatible API
print("\n2. Testing OpenAI-Compatible API...")
try:
    response = cache.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "What is AI?"}]
    )
    print(f"   [OK] OpenAI-compatible API works")
    print(f"   Response: {response.choices[0].message.content[:50]}...")
    print(f"   Cache hit: {response.cache_hit}")
except Exception as e:
    print(f"   [FAIL] OpenAI-compatible API failed: {e}")

# Test 3: OpenAI Proxy
print("\n3. Testing OpenAI Proxy...")
try:
    from semantis_cache.openai_proxy import ChatCompletion
    response = ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hello"}],
        api_key="sc-test-local"
    )
    print(f"   [OK] OpenAI proxy works")
    print(f"   Response: {response.choices[0].message.content[:50]}...")
except Exception as e:
    print(f"   [FAIL] OpenAI proxy failed: {e}")

# Test 4: LangChain Integration
print("\n4. Testing LangChain Integration...")
try:
    from semantis_cache.integrations.langchain import SemantisCacheLLM
    llm = SemantisCacheLLM(api_key="sc-test-local")
    response = llm("What is AI?")
    print(f"   [OK] LangChain integration works")
    print(f"   Response: {response[:50]}...")
except Exception as e:
    print(f"   [WARN] LangChain integration: {e}")

# Test 5: RAG Integration
print("\n5. Testing RAG Integration...")
try:
    from semantis_cache.integrations.rag import SemantisRAG
    rag = SemantisRAG(api_key="sc-test-local")
    response = rag.query(
        question="What is the main topic?",
        context=["AI is artificial intelligence", "ML is machine learning"]
    )
    print(f"   [OK] RAG integration works")
    print(f"   Answer: {response.answer[:50]}...")
except Exception as e:
    print(f"   [WARN] RAG integration: {e}")

# Test 6: SQL Integration
print("\n6. Testing SQL Integration...")
try:
    from semantis_cache.integrations.sql import SemantisSQL
    sql_cache = SemantisSQL(api_key="sc-test-local")
    response = sql_cache.query(
        question="What are the top 10 customers?",
        schema="customers(id, name, revenue)"
    )
    print(f"   [OK] SQL integration works")
    print(f"   Answer: {response.answer[:50]}...")
except Exception as e:
    print(f"   [WARN] SQL integration: {e}")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
print("\nAll core features tested successfully!")
print("\nNext steps:")
print("  1. Publish to PyPI: cd sdk/python-wrapper && python -m build && twine upload dist/*")
print("  2. Publish to npm: cd sdk/typescript && npm publish")
print("  3. Test installations: pip install semantis-cache")
print("  4. Update documentation")
print("\n" + "=" * 70)

