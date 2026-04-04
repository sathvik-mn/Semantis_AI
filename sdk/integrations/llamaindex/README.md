# LlamaIndex Integration

LlamaIndex integration for Semantys Cache provides a LlamaIndex-compatible LLM wrapper with automatic semantic caching.

## Installation

```bash
pip install semantys-cache llama-index
```

## Usage

```python
from semantys_cache.integrations.llamaindex import SemantysCacheLLM

# Initialize LLM with caching
llm = SemantysCacheLLM(api_key="sc-your-key")

# Use like any LlamaIndex LLM
response = llm.complete("What is AI?")
print(response.text)

# Use in LlamaIndex pipelines
from llama_index import ServiceContext, VectorStoreIndex

service_context = ServiceContext.from_defaults(llm=llm)
index = VectorStoreIndex.from_documents(documents, service_context=service_context)
```

## Features

- ✅ LlamaIndex-compatible interface
- ✅ Automatic semantic caching
- ✅ Works with all LlamaIndex components
- ✅ No code changes needed
- ✅ Cache hits are transparent

## Configuration

```python
llm = SemantysCacheLLM(
    api_key="sc-your-key",
    base_url="https://api.semantys.ai",  # Optional
    model="gpt-4o-mini",  # Optional
    temperature=0.2,  # Optional
    timeout=30.0  # Optional
)
```

