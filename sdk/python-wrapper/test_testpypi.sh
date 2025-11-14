#!/bin/bash
# Test uploading to Test PyPI and installing from it
# This simulates the real PyPI experience

set -e

echo "============================================================"
echo "Testing SDK on Test PyPI"
echo "============================================================"

# Check if twine is installed
if ! command -v twine &> /dev/null; then
    echo "Error: twine is not installed. Installing..."
    pip install twine
fi

# Check if package is built
if [ ! -f "dist/semantis_cache-1.0.0-py3-none-any.whl" ]; then
    echo "Building package..."
    python -m build
fi

echo ""
echo "1. Uploading to Test PyPI..."
echo "   (You will need Test PyPI credentials)"
echo ""
echo "   Test PyPI URL: https://test.pypi.org/"
echo "   Test PyPI Upload URL: https://test.pypi.org/legacy/"
echo ""
read -p "Press Enter to continue uploading to Test PyPI, or Ctrl+C to cancel..."

# Upload to Test PyPI
twine upload --repository testpypi dist/*

echo ""
echo "2. Testing installation from Test PyPI..."
echo ""
read -p "Press Enter to continue testing installation from Test PyPI..."

# Create test virtual environment
TEST_DIR=$(mktemp -d)
echo "Creating test environment in: $TEST_DIR"
python -m venv "$TEST_DIR/venv"

# Activate virtual environment (platform-specific)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source "$TEST_DIR/venv/Scripts/activate"
else
    source "$TEST_DIR/venv/bin/activate"
fi

# Install from Test PyPI
echo "Installing from Test PyPI..."
pip install --index-url https://test.pypi.org/simple/ semantis-cache

# Test import
echo ""
echo "3. Testing imports..."
python -c "
from semantis_cache import SemanticCache, ChatCompletion, __version__
print(f'  [OK] Import successful (v{__version__})')

cache = SemanticCache(api_key='sc-test-key')
print('  [OK] Initialization successful')

assert hasattr(cache, 'chat'), 'cache.chat missing'
assert hasattr(cache, 'query'), 'cache.query missing'
print('  [OK] All attributes present')

from semantis_cache.openai_proxy import ChatCompletion as ProxyChatCompletion
assert hasattr(ProxyChatCompletion, 'create'), 'ChatCompletion.create missing'
print('  [OK] OpenAI proxy works')

print('')
print('[SUCCESS] All tests passed!')
"

# Cleanup
deactivate
rm -rf "$TEST_DIR"

echo ""
echo "============================================================"
echo "[SUCCESS] SDK works correctly on Test PyPI!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "  1. Verify the package on Test PyPI: https://test.pypi.org/project/semantis-cache/"
echo "  2. If everything looks good, upload to production PyPI:"
echo "     twine upload dist/*"
echo ""

