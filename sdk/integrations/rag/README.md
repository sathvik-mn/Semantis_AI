# RAG Integration

RAG-optimized caching for Semantis Cache provides specialized caching for RAG applications.

## Installation

```bash
pip install semantis-cache
```

## Usage

```python
from semantis_cache.integrations.rag import SemantisRAG

# Initialize RAG cache
rag = SemantisRAG(api_key="sc-your-key")

# Query with context
context = [
    "Document 1: Artificial intelligence is...",
    "Document 2: Machine learning is a subset of AI..."
]

response = rag.query(
    question="What is the relationship between AI and ML?",
    context=context
)

print(response.answer)
print(f"Cache hit: {response.cache_hit}")
```

## Features

- ✅ Context-aware caching
- ✅ Question + context combination
- ✅ Metadata support
- ✅ Automatic semantic matching
- ✅ Fast responses for cached queries

## Configuration

```python
rag = SemantisRAG(
    api_key="sc-your-key",
    base_url="https://api.semantis.ai",  # Optional
    model="gpt-4o-mini",  # Optional
    cache_context=True  # Include context in cache key
)
```

## Use Cases

- RAG applications
- Document Q&A systems
- Knowledge bases
- Enterprise search

