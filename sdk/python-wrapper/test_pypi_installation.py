"""
Test SDK installation as if it was installed from PyPI
This simulates what users will experience after pip install semantis-cache
"""
import subprocess
import sys
import os
import tempfile
import shutil

def create_venv_test():
    """Create a virtual environment and test installation"""
    print("=" * 60)
    print("Testing SDK Installation (PyPI Simulation)")
    print("=" * 60)
    
    # Create temporary directory for test
    test_dir = tempfile.mkdtemp(prefix="semantis_cache_test_")
    venv_path = os.path.join(test_dir, "venv")
    
    try:
        print(f"\n1. Creating virtual environment at: {venv_path}")
        
        # Create virtual environment
        subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)
        
        # Determine pip path based on OS
        if sys.platform == "win32":
            pip_path = os.path.join(venv_path, "Scripts", "pip.exe")
            python_path = os.path.join(venv_path, "Scripts", "python.exe")
        else:
            pip_path = os.path.join(venv_path, "bin", "pip")
            python_path = os.path.join(venv_path, "bin", "python")
        
        print("2. Installing SDK from local wheel...")
        
        # Get the path to the built wheel
        wheel_path = os.path.join(os.path.dirname(__file__), "dist", "semantis_cache-1.0.0-py3-none-any.whl")
        
        if not os.path.exists(wheel_path):
            print(f"   [FAIL] Wheel not found at: {wheel_path}")
            print("   Please build the package first: python -m build")
            return False
        
        print(f"   Installing from: {wheel_path}")
        
        # Install from wheel
        result = subprocess.run(
            [pip_path, "install", wheel_path],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"   [FAIL] Installation failed:")
            print(result.stderr)
            return False
        
        print("   [OK] SDK installed successfully")
        
        print("\n3. Testing imports...")
        
        # Test import
        test_script = """
import sys
try:
    from semantis_cache import SemanticCache, ChatCompletion, __version__
    print(f"   [OK] Import successful (v{__version__})")
    
    # Test initialization
    cache = SemanticCache(api_key="sc-test-key")
    print("   [OK] Initialization successful")
    
    # Test attributes
    assert hasattr(cache, 'chat'), "cache.chat missing"
    assert hasattr(cache, 'query'), "cache.query missing"
    print("   [OK] All attributes present")
    
    # Test OpenAI proxy
    from semantis_cache.openai_proxy import ChatCompletion as ProxyChatCompletion
    assert hasattr(ProxyChatCompletion, 'create'), "ChatCompletion.create missing"
    print("   [OK] OpenAI proxy works")
    
    print("\\n[SUCCESS] All tests passed!")
    sys.exit(0)
except Exception as e:
    print(f"   [FAIL] Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
"""
        
        result = subprocess.run(
            [python_path, "-c", test_script],
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        if result.returncode == 0:
            print("\n" + "=" * 60)
            print("[SUCCESS] SDK works correctly when installed from wheel!")
            print("=" * 60)
            return True
        else:
            print("\n" + "=" * 60)
            print("[FAILURE] SDK installation test failed")
            print("=" * 60)
            return False
            
    except Exception as e:
        print(f"\n[FAIL] Test setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        print(f"\nCleaning up test environment: {test_dir}")
        try:
            shutil.rmtree(test_dir)
        except Exception as e:
            print(f"Warning: Could not clean up {test_dir}: {e}")

if __name__ == "__main__":
    success = create_venv_test()
    sys.exit(0 if success else 1)

