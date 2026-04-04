# How Users Will Use Semantys Cache SDK

## Installation Methods

### 1. **Via PyPI (Production - Recommended)**
Once published to PyPI, users will install it like any other Python package:

```bash
pip install semantys-cache
```

This is the standard way Python packages are distributed and used. Users just need to:
1. Install via pip
2. Import and use it in their code

### 2. **From Local Source (Development)**
For development or if not yet on PyPI, users can install from the local directory:

```bash
cd sdk/python-wrapper
pip install -e .
```

Or install from a wheel file directly:

```bash
pip install dist/semantys_cache-1.0.0-py3-none-any.whl
```

## Usage After Installation

Once installed (via pip or locally), users import it like any Python package:

### Example 1: Simple Usage

```python
# Import the SDK (just like any other package)
from semantys_cache import SemanticCache

# Initialize with API key
cache = SemanticCache(api_key="sc-your-api-key")

# Use it
response = cache.query("What is AI?")
print(response.answer)
print(f"Cache hit: {response.cache_hit}")
```

### Example 2: OpenAI-Compatible Usage

```python
# Import the SDK
from semantys_cache import SemanticCache

# Initialize
cache = SemanticCache(api_key="sc-your-api-key")

# Use OpenAI-compatible interface
response = cache.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "What is machine learning?"}]
)

print(response.choices[0].message.content)
print(f"Cache hit: {response.cache_hit}")
```

### Example 3: Drop-in OpenAI Replacement

```python
# Instead of: from openai import ChatCompletion
from semantys_cache.openai_proxy import ChatCompletion

# Use exactly like OpenAI
response = ChatCompletion.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "What is Python?"}]
)

print(response.choices[0].message.content)
```

## Complete User Workflow

### Step 1: Install
```bash
pip install semantys-cache
```

### Step 2: Use in Code
```python
from semantys_cache import SemanticCache

cache = SemanticCache(api_key="sc-your-api-key-here")
response = cache.query("What is the weather today?")
print(response.answer)
```

That's it! Just like using any other Python package (requests, numpy, etc.)

## Comparison with Other Packages

Users will use it exactly like popular packages:

```python
# Like requests
import requests
r = requests.get("https://api.example.com")

# Like numpy
import numpy as np
arr = np.array([1, 2, 3])

# Like semantys-cache
from semantys_cache import SemanticCache
cache = SemanticCache(api_key="sc-key")
response = cache.query("What is AI?")
```

## Distribution Methods

1. **PyPI (Recommended)**: `pip install semantys-cache`
   - Standard Python package distribution
   - Automatic dependency management
   - Version control
   - Works with virtual environments

2. **GitHub Releases**: Download wheel file and install locally
   - For users who want to install from GitHub
   - Still requires pip install

3. **Local Development**: `pip install -e .`
   - For contributors or development
   - Editable install (changes reflected immediately)

## Requirements

Users only need:
- Python 3.10+
- pip (comes with Python)
- Internet connection (for initial install)

After installation, all dependencies are automatically installed via pip.

