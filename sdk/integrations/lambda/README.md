# AWS Lambda Handler Integration

AWS Lambda handler for semantic caching in serverless applications.

## Installation

```bash
pip install semantis-cache -t .
```

Or add to Lambda Layer.

## Usage

### Lambda Function

```python
from semantis_cache.integrations.lambda_handler import lambda_handler

def handler(event, context):
    return lambda_handler(event, context)
```

### Environment Variables

```bash
SEMANTIS_API_KEY=sc-your-key
SEMANTIS_API_URL=https://api.semantis.ai
```

## API Gateway Configuration

1. Create API Gateway REST API
2. Create resource: `/v1/chat/completions`
3. Create method: POST
4. Set integration type: Lambda Function
5. Select your Lambda function
6. Deploy API

## Supported Endpoints

- `POST /v1/chat/completions` - Chat completions with caching
- `GET /query?prompt=...` - Simple query with caching

## Features

- ✅ Serverless semantic caching
- ✅ Automatic caching of OpenAI API calls
- ✅ Fast responses for cached queries
- ✅ Cost savings
- ✅ Works with API Gateway

