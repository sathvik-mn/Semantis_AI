# Semantis AI - Semantic Caching SDK

Production-ready semantic caching SDK for LLM applications. Provides automatic caching with semantic matching, reducing LLM API costs and improving response times.

## 🚀 Quick Start

### Python

```bash
pip install semantis-cache
```

```python
from semantis_cache import SemanticCache

cache = SemanticCache(api_key="sc-your-key")
response = cache.query("What is our refund policy?")
print(response.answer)
print(f"Cache hit: {response.cache_hit}")  # 'exact', 'semantic', or 'miss'
```

### TypeScript

```bash
npm install semantis-cache
```

```typescript
import { SemanticCache } from 'semantis-cache';

const cache = new SemanticCache({ apiKey: 'sc-your-key' });
const response = await cache.query('What is AI?');
console.log(response.answer);
```

## ✨ Features

- ✅ **Simple API**: `cache.query("prompt")` - easiest way to use
- ✅ **OpenAI-Compatible**: Drop-in replacement for OpenAI SDK
- ✅ **Automatic Caching** - No code changes needed
- ✅ **Semantic Matching** - Similar queries match automatically
- ✅ **Fast Responses** - Cache hits return instantly
- ✅ **Cost Savings** - Fewer LLM API calls
- ✅ **Multi-language** - Python, TypeScript, and more

## 📚 Documentation

All documentation is available in the [`docs/`](docs/) directory:

- **[Quick Start Guide](docs/PLUG_AND_PLAY_GUIDE.md)** - Get started in 5 minutes
- **[SDK Usage Guide](docs/HOW_TO_USE_SDK.md)** - Detailed usage examples
- **[Feature Audit](docs/FEATURE_AUDIT_REPORT.md)** - Complete feature list
- **[Publishing Status](docs/PUBLISHING_STATUS.md)** - Package publishing status

## 🔧 Integrations

- **LangChain**: `from semantis_cache.integrations.langchain import SemantisCacheLLM`
- **LlamaIndex**: `from semantis_cache.integrations.llamaindex import SemantisCacheLLM`
- **FastAPI**: `app.add_middleware(SemanticCacheMiddleware, api_key="...")`
- **Express**: `app.use(semanticCacheMiddleware({ apiKey: '...' }))`
- **Django**: Add to `MIDDLEWARE` in `settings.py`
- **AWS Lambda**: Serverless caching support
- **RAG**: RAG-optimized caching
- **SQL/BI**: SQL query caching

See [Integration Documentation](sdk/integrations/) for details.

## 🏗️ Project Structure

```
.
├── backend/                 # FastAPI backend service
├── frontend/                # React frontend
├── sdk/                     # SDK packages
│   ├── python-wrapper/     # Python SDK (PyPI ready)
│   ├── typescript/         # TypeScript SDK (npm ready)
│   └── integrations/       # Integration wrappers
├── docs/                    # Documentation
└── README.md               # This file
```

## 🚀 Installation

### Python

```bash
pip install semantis-cache
```

### TypeScript

```bash
npm install semantis-cache
```

## 💡 Usage Examples

### Simple Query

```python
from semantis_cache import SemanticCache

cache = SemanticCache(api_key="sc-your-key")
response = cache.query("What is our refund policy?")
print(response.answer)
print(f"Cache hit: {response.cache_hit}")
```

### OpenAI-Compatible

```python
response = cache.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "What is AI?"}]
)
print(response.choices[0].message.content)
```

### OpenAI Proxy (Drop-in Replacement)

```python
from semantis_cache.openai_proxy import ChatCompletion

response = ChatCompletion.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "What is AI?"}]
)
```

## 📖 Documentation

- **[Documentation Index](docs/README.md)** - Complete documentation index
- **[Quick Start](docs/PLUG_AND_PLAY_GUIDE.md)** - Get started quickly
- **[SDK Usage](docs/HOW_TO_USE_SDK.md)** - Detailed usage guide
- **[Feature Audit](docs/FEATURE_AUDIT_REPORT.md)** - Feature status
- **[Publishing Status](docs/PUBLISHING_STATUS.md)** - Publishing info

## 🔗 Links

- **Documentation**: [docs/](docs/)
- **Python SDK**: [sdk/python-wrapper/](sdk/python-wrapper/)
- **TypeScript SDK**: [sdk/typescript/](sdk/typescript/)
- **Integrations**: [sdk/integrations/](sdk/integrations/)

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details

## 🤝 Contributing

Contributions are welcome! Please see our contributing guidelines.

## 📞 Support

For support, please check the [documentation](docs/) or open an issue.

---

**Version**: 1.0.0  
**Status**: ✅ Production Ready

