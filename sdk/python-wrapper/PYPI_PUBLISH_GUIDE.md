# PyPI Publishing Guide

## Prerequisites

1. Create PyPI account: https://pypi.org/account/register/
2. Install build tools: `pip install build twine`
3. Get API token: https://pypi.org/manage/account/token/

## Build Package

```bash
cd sdk/python-wrapper

# Build distribution packages
python -m build

# This creates:
# - dist/semantis-cache-1.0.0.tar.gz (source distribution)
# - dist/semantis_cache-1.0.0-py3-none-any.whl (wheel)
```

## Test Installation

```bash
# Test installing from local build
pip install dist/semantis-cache-1.0.0-py3-none-any.whl

# Test import
python -c "from semantis_cache import SemanticCache; print('OK')"
```

## Publish to PyPI

### Test PyPI (Recommended First)

```bash
# Upload to Test PyPI
twine upload --repository testpypi dist/*

# Test install from Test PyPI
pip install --index-url https://test.pypi.org/simple/ semantis-cache
```

### Production PyPI

```bash
# Upload to PyPI
twine upload dist/*

# Install from PyPI
pip install semantis-cache
```

## Verify Publication

```bash
# Check package on PyPI
# Visit: https://pypi.org/project/semantis-cache/

# Install and test
pip install semantis-cache
python -c "from semantis_cache import SemanticCache; print('OK')"
```

## Update Version

1. Update version in `setup.py` and `pyproject.toml`
2. Update version in `semantis_cache/__init__.py`
3. Build and publish: `python -m build && twine upload dist/*`

## Notes

- Package name: `semantis-cache` (PyPI uses hyphens)
- Import name: `semantis_cache` (Python uses underscores)
- Both `semantis_cache` and `semantis_ai` packages are included for compatibility

