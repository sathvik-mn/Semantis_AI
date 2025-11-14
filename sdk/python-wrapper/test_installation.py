"""
Test script to verify SDK installation works correctly
Tests all major functionality before publishing to PyPI
"""
import sys
import os

# Add current directory to path for testing
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_import():
    """Test that all imports work"""
    print("Testing imports...")
    try:
        from semantis_cache import SemanticCache, ChatCompletion, __version__
        print(f"  [OK] semantis_cache imported successfully (v{__version__})")
    except ImportError as e:
        print(f"  [FAIL] Failed to import semantis_cache: {e}")
        return False
    
    try:
        from semantis_cache.openai_proxy import ChatCompletion as ProxyChatCompletion
        print("  [OK] OpenAI proxy imported successfully")
    except ImportError as e:
        print(f"  [FAIL] Failed to import OpenAI proxy: {e}")
        return False
    
    try:
        from semantis_cache.client import SemanticCache
        print("  [OK] Client module imported successfully")
    except ImportError as e:
        print(f"  [FAIL] Failed to import client: {e}")
        return False
    
    try:
        from semantis_cache.chat import ChatCompletions
        print("  [OK] Chat module imported successfully")
    except ImportError as e:
        print(f"  [FAIL] Failed to import chat: {e}")
        return False
    
    try:
        from semantis_cache.query import SimpleQuery
        print("  [OK] Query module imported successfully")
    except ImportError as e:
        print(f"  [FAIL] Failed to import query: {e}")
        return False
    
    return True

def test_initialization():
    """Test SDK initialization"""
    print("\nTesting initialization...")
    try:
        from semantis_cache import SemanticCache
        
        # Test with API key
        cache = SemanticCache(api_key="sc-test-key-12345")
        print("  [OK] SemanticCache initialized with API key")
        
        # Test with base URL
        cache = SemanticCache(
            api_key="sc-test-key-12345",
            base_url="http://localhost:8000"
        )
        print("  [OK] SemanticCache initialized with base URL")
        
        # Test that chat attribute exists
        assert hasattr(cache, 'chat'), "cache.chat should exist"
        print("  [OK] cache.chat attribute exists")
        
        # Test that query method exists
        assert hasattr(cache, 'query'), "cache.query should exist"
        print("  [OK] cache.query method exists")
        
        return True
    except Exception as e:
        print(f"  [FAIL] Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_openai_proxy():
    """Test OpenAI proxy interface"""
    print("\nTesting OpenAI proxy...")
    try:
        from semantis_cache.openai_proxy import ChatCompletion
        
        # Test that ChatCompletion.create exists
        assert hasattr(ChatCompletion, 'create'), "ChatCompletion.create should exist"
        print("  [OK] ChatCompletion.create method exists")
        
        return True
    except Exception as e:
        print(f"  [FAIL] OpenAI proxy test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_package_structure():
    """Test that package structure is correct"""
    print("\nTesting package structure...")
    try:
        import semantis_cache
        import semantis_cache.semantis_ai_semantic_cache_api_client
        
        # Check that OpenAPI client is bundled
        assert hasattr(semantis_cache, 'semantis_ai_semantic_cache_api_client'), \
            "OpenAPI client should be bundled"
        print("  [OK] OpenAPI client is bundled")
        
        # Check that models are accessible
        from semantis_cache.semantis_ai_semantic_cache_api_client.models import ChatRequest, ChatMessage
        print("  [OK] Models are accessible")
        
        return True
    except Exception as e:
        print(f"  [FAIL] Package structure test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_version():
    """Test version information"""
    print("\nTesting version...")
    try:
        from semantis_cache import __version__
        assert __version__ == "1.0.0", f"Expected version 1.0.0, got {__version__}"
        print(f"  [OK] Version is correct: {__version__}")
        return True
    except Exception as e:
        print(f"  [FAIL] Version test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("SDK Installation Test")
    print("=" * 60)
    
    tests = [
        ("Imports", test_import),
        ("Initialization", test_initialization),
        ("OpenAI Proxy", test_openai_proxy),
        ("Package Structure", test_package_structure),
        ("Version", test_version),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  [FAIL] {name} test crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print("Test Results")
    print("=" * 60)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n[SUCCESS] All tests passed! SDK is ready for PyPI.")
        return 0
    else:
        print("\n[FAILURE] Some tests failed. Please fix issues before publishing.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

