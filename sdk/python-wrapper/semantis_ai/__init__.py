"""
Semantis AI - Semantic Caching SDK (Backward Compatibility Alias)

This module is an alias for semantis_cache for backward compatibility.
Use 'from semantis_cache import SemanticCache' for the recommended import.
"""

# Import from semantis_cache for backward compatibility
import sys
from pathlib import Path

# Add parent directory to path to import semantis_cache
_parent_dir = Path(__file__).parent.parent
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))

try:
    from semantis_cache import SemanticCache, ChatCompletion, __version__
    __all__ = ["SemanticCache", "ChatCompletion", "__version__"]
except ImportError:
    # Fallback: import directly if semantis_cache not available
    from .client import SemanticCache
    from .openai_proxy import ChatCompletion
    __version__ = "1.0.0"
    __all__ = ["SemanticCache", "ChatCompletion", "__version__"]
