# Express.js Middleware Integration

Express.js middleware for automatic semantic caching of OpenAI API calls.

## Installation

```bash
npm install semantis-cache express
```

## Usage

```javascript
const express = require('express');
const semanticCacheMiddleware = require('semantis-cache/integrations/express');

const app = express();
app.use(express.json());

// Add middleware
app.use(semanticCacheMiddleware({
  apiKey: 'sc-your-key',
  cachePaths: ['/v1/chat/completions']
}));

// Your OpenAI endpoint
app.post('/v1/chat/completions', async (req, res) => {
  // This will be cached automatically by middleware
  const response = await callOpenAI(req.body);
  res.json(response);
});
```

## Configuration

```javascript
app.use(semanticCacheMiddleware({
  apiKey: 'sc-your-key',
  baseUrl: 'https://api.semantis.ai',  // Optional
  cachePaths: ['/v1/chat/completions', '/v1/completions']  // Optional
}));
```

## Environment Variables

```bash
export SEMANTIS_API_KEY="sc-your-key"
export SEMANTIS_API_URL="https://api.semantis.ai"
```

## Features

- ✅ Automatic caching of OpenAI API calls
- ✅ No code changes needed
- ✅ Transparent to your application
- ✅ Fast responses for cached queries
- ✅ Cost savings

