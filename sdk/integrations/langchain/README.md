# LangChain Integration

LangChain integration for Semantis Cache provides a LangChain-compatible LLM wrapper with automatic semantic caching.

## Installation

```bash
pip install semantis-cache langchain
```

## Usage

```python
from semantis_cache.integrations.langchain import SemantisCacheLLM

# Initialize LLM with caching
llm = SemantisCacheLLM(api_key="sc-your-key")

# Use like any LangChain LLM
response = llm("What is AI?")
print(response)

# Use in chains
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

prompt = PromptTemplate(
    input_variables=["topic"],
    template="Tell me about {topic}"
)

chain = LLMChain(llm=llm, prompt=prompt)
result = chain.run(topic="artificial intelligence")
print(result)
```

## Features

- ✅ LangChain-compatible interface
- ✅ Automatic semantic caching
- ✅ Works with all LangChain chains
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

