"""
AWS Lambda Handler for Semantis Cache

Lambda function handler for semantic caching in serverless applications.
"""
import os
import json
from typing import Dict, Any, Optional


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for semantic caching.
    
    This handler can be used as a proxy for OpenAI API calls in Lambda functions.
    
    Example:
        >>> # In Lambda function
        >>> from semantis_cache.integrations.lambda_handler import lambda_handler
        >>> 
        >>> # Lambda will automatically cache OpenAI API calls
        >>> def handler(event, context):
        ...     return lambda_handler(event, context)
    """
    try:
        from semantis_cache import SemanticCache
        
        # Get API key from environment
        api_key = os.getenv('SEMANTIS_API_KEY')
        if not api_key:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'SEMANTIS_API_KEY not set'})
            }
        
        # Initialize cache client
        cache = SemanticCache(api_key=api_key)
        
        # Parse request
        body = json.loads(event.get('body', '{}'))
        path = event.get('path', '')
        method = event.get('httpMethod', '')
        
        # Handle different endpoints
        if path == '/v1/chat/completions' and method == 'POST':
            # Extract prompt from messages
            messages = body.get('messages', [])
            if not messages:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'No messages provided'})
                }
            
            # Get the last user message
            user_messages = [msg for msg in messages if msg.get('role') == 'user']
            if not user_messages:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'No user messages provided'})
                }
            
            prompt = user_messages[-1].get('content', '')
            if not prompt:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'No prompt provided'})
                }
            
            # Query cache
            response = cache.query(prompt, model=body.get('model', 'gpt-4o-mini'))
            
            # Format as OpenAI response
            import time
            cached_response = {
                'id': f'chatcmpl-lambda-{hash(prompt)}',
                'object': 'chat.completion',
                'created': int(time.time()),
                'model': body.get('model', 'gpt-4o-mini'),
                'choices': [{
                    'index': 0,
                    'message': {
                        'role': 'assistant',
                        'content': response.answer
                    },
                    'finish_reason': 'stop'
                }],
                'usage': {
                    'prompt_tokens': 0,
                    'completion_tokens': 0,
                    'total_tokens': 0
                },
                'meta': {
                    'hit': response.cache_hit,
                    'similarity': response.similarity,
                    'latency_ms': response.latency_ms
                }
            }
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(cached_response)
            }
        
        elif path == '/query' and method == 'GET':
            # Simple query endpoint
            prompt = event.get('queryStringParameters', {}).get('prompt', '')
            if not prompt:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'No prompt provided'})
                }
            
            model = event.get('queryStringParameters', {}).get('model', 'gpt-4o-mini')
            response = cache.query(prompt, model=model)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'answer': response.answer,
                    'meta': {
                        'hit': response.cache_hit,
                        'similarity': response.similarity,
                        'latency_ms': response.latency_ms
                    }
                })
            }
        
        else:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Not found'})
            }
    
    except ImportError:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'semantis_cache package is required. Install it in Lambda layer.'
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

