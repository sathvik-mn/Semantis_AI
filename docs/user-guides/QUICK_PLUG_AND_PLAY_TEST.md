# Quick Plug & Play Test

## Test if API is working as OpenAI replacement

### 1. Run Automated Test
```bash
cd backend
python test_plug_and_play.py
```

### 2. Manual Test (cURL)
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer sc-demo-user-VFcWBpkaiINmSl41" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### 3. Test with Python
```python
import requests

response = requests.post(
    "http://localhost:8000/v1/chat/completions",
    headers={
        "Authorization": "Bearer sc-demo-user-VFcWBpkaiINmSl41",
        "Content-Type": "application/json"
    },
    json={
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "What is AI?"}]
    }
)
print(response.json())
```

### 4. Test Cache Hit
```python
# Run same query twice
# First: miss (slow)
# Second: hit (fast)
```

### 5. Test Semantic Similarity
```python
# Query 1: "What is artificial intelligence?"
# Query 2: "Tell me about AI"
# Should match semantically!
```

## Expected Results

✅ **Response Format**: OpenAI-compatible
✅ **Cache Hit**: Faster on second query
✅ **Semantic Match**: Similar queries match
✅ **Metadata**: Cache info in `meta` field

## Integration

### Replace OpenAI API
```python
# Before
client = OpenAI(api_key="sk-...")

# After
client = OpenAI(
    api_key="sc-your-tenant-key",
    base_url="http://localhost:8000/v1"
)
# Same code, same format, with caching!
```

## See Also

- `PLUG_AND_PLAY_GUIDE.md` - Full integration guide
- `backend/test_plug_and_play.py` - Automated test script
- `backend/README.md` - API documentation

