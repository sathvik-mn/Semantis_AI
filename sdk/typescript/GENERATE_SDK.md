# TypeScript SDK Generation Guide

## Prerequisites

```bash
# Install OpenAPI Generator
npm install -g @openapitools/openapi-generator-cli

# Or use npx (no installation needed)
npx @openapitools/openapi-generator-cli version
```

## Generate TypeScript SDK

```bash
cd sdk/typescript

# Generate TypeScript SDK from OpenAPI spec
npx @openapitools/openapi-generator-cli generate \
  -i http://localhost:8000/openapi.json \
  -g typescript-axios \
  -o . \
  --additional-properties=supportsES6=true,npmName=semantis-cache,npmVersion=1.0.0

# Or from local file
npx @openapitools/openapi-generator-cli generate \
  -i ../../backend/openapi.json \
  -g typescript-axios \
  -o . \
  --additional-properties=supportsES6=true,npmName=semantis-cache,npmVersion=1.0.0
```

## Create npm Package

```bash
cd sdk/typescript

# Initialize npm package
npm init -y

# Update package.json with correct details
# - name: semantis-cache
# - version: 1.0.0
# - description: Semantis Cache - Semantic Caching SDK for LLM Applications
# - main: index.ts
# - types: index.ts
```

## Build and Publish

```bash
# Build package
npm run build

# Publish to npm
npm publish
```

## Usage

```typescript
import { Configuration, DefaultApi } from 'semantis-cache';

const config = new Configuration({
  basePath: 'https://api.semantis.ai',
  accessToken: 'sc-your-key'
});

const api = new DefaultApi(config);

// Simple query
const response = await api.simpleQueryQueryGet('What is AI?');
console.log(response.data.answer);

// Chat completion
const chatResponse = await api.openaiCompatibleV1ChatCompletionsPost({
  model: 'gpt-4o-mini',
  messages: [{ role: 'user', content: 'What is AI?' }]
});
console.log(chatResponse.data.choices[0].message.content);
```

