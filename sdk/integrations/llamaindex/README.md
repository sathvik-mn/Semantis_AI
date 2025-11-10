# LlamaIndex Integration

LlamaIndex integration for Semantis Cache provides a LlamaIndex-compatible LLM wrapper with automatic semantic caching.

## Installation

```bash
pip install semantis-cache llama-index
```

## Usage

```python
from semantis_cache.integrations.llamaindex import SemantisCacheLLM

# Initialize LLM with caching
llm = SemantisCacheLLM(api_key="sc-your-key")

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
llm = SemantisCacheLLM(
    api_key="sc-your-key",
    base_url="https://api.semantis.ai",  # Optional
    model="gpt-4o-mini",  # Optional
    temperature=0.2,  # Optional
    timeout=30.0  # Optional
)
```

