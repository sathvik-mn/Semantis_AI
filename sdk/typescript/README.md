# Semantis Cache - TypeScript SDK

TypeScript/JavaScript SDK for Semantis AI Semantic Caching.

## Installation

```bash
npm install semantis-cache
```

## Quick Start

```typescript
import { SemanticCache } from 'semantis-cache';

// Initialize client
const cache = new SemanticCache({
  apiKey: 'sc-your-key',
  baseUrl: 'https://api.semantis.ai'
});

// Simple query
const response = await cache.query('What is our refund policy?');
console.log(response.answer);
console.log(`Cache hit: ${response.cacheHit}`);

// OpenAI-compatible
const chatResponse = await cache.chat.completions.create({
  model: 'gpt-4o-mini',
  messages: [{ role: 'user', content: 'What is AI?' }]
});
console.log(chatResponse.choices[0].message.content);
```

## Features

- ✅ TypeScript support
- ✅ Automatic caching
- ✅ Semantic matching
- ✅ OpenAI-compatible API
- ✅ Simple query method

## License

MIT

