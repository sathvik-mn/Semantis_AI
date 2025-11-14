# Comprehensive Logging System

## Overview

The Semantis AI backend now has a comprehensive, production-ready logging system that captures **all interactions** from both user and application sides.

## Log Files

All logs are stored in `backend/logs/` with automatic rotation:

1. **`access.log`** - All HTTP requests/responses with detailed metadata
2. **`errors.log`** - All errors and exceptions with stack traces
3. **`semantic_ops.log`** - Cache operations (exact, semantic, miss)
4. **`performance.log`** - Performance metrics and slow requests
5. **`security.log`** - Authentication events and security incidents
6. **`system.log`** - System events (startup, shutdown, cache load/save)
7. **`application.log`** - Application-level events (LLM calls, API key creation)

## What's Logged

### 1. Request/Response Logging (access.log)
Every HTTP request is logged with:
- Request ID (unique per request)
- HTTP method and path
- Client IP address
- User-Agent
- Response status code
- Processing time
- Response size

Example:
```
2024-01-15T10:30:45 | INFO | abc12345 | REQ | POST /v1/chat/completions | tenant=extracting | ip=192.168.1.100 | ua=Mozilla/5.0...
2024-01-15T10:30:46 | INFO | abc12345 | RESP | POST /v1/chat/completions | status=200 | time=1234.56ms | size=1024B
```

### 2. Cache Operations (semantic_ops.log)
Every cache operation is logged:
- Exact cache hits
- Semantic cache hits with similarity scores
- Cache misses
- Typo tolerance adjustments
- Threshold adaptations

Example:
```
2024-01-15T10:30:45 | INFO | tenant123 | semantic | sim=0.856 | threshold=0.720 | key=what is python...
```

### 3. Performance Metrics (performance.log)
Performance-related logs:
- Embedding generation time
- LLM call time and token estimates
- Slow requests (> 5 seconds)
- Performance bottlenecks

Example:
```
2024-01-15T10:30:45 | DEBUG | Embedding generated | model=text-embedding-3-large | text_len=50 | time=234.56ms
```

### 4. Security Events (security.log)
All security-related events:
- Failed authentication attempts (with IP and reason)
- Successful authentications (with tenant and plan)
- New API key creation
- Suspicious patterns

Example:
```
2024-01-15T10:30:45 | WARNING | Auth failed | ip=192.168.1.100 | reason=invalid_format | path=/v1/chat/completions
```

### 5. System Events (system.log)
System-level events:
- Server startup/shutdown
- Cache load/save operations
- Health check results
- System resource usage (if psutil available)

Example:
```
2024-01-15T10:30:45 | INFO | Cache loaded | tenants=5 | entries=1234 | time=1234.56ms
```

### 6. Application Events (application.log)
Application-level business events:
- LLM API calls (model, tokens, time)
- API key auto-creation
- Tenant-specific events

Example:
```
2024-01-15T10:30:45 | INFO | LLM call | model=gpt-4o-mini | temp=0.2 | prompt_tokens~=50 | completion_tokens~=100 | total_tokens~=150 | time=2345.67ms
```

### 7. Error Logging (errors.log)
All errors with full context:
- Exception stack traces
- Request context in errors
- Tenant ID in all errors
- Error timing

Example:
```
2024-01-15T10:30:45 | ERROR | tenant123 | /query | error: Connection failed | prompt_hash=abc12345 | prompt_len=50 | model=gpt-4o-mini
```

## Enhanced Features

### Request Tracking
Every request gets a unique 8-character ID that appears in all related log entries, making it easy to track a request through the entire system.

### Slow Request Detection
Requests taking longer than 5 seconds are automatically logged to `performance.log` with a WARNING level.

### Authentication Logging
All authentication attempts are logged with:
- Client IP address
- Success/failure reason
- Tenant ID
- User plan (if available)

### Database Logging
All API usage is logged to the database (`usage_logs` table) for:
- Billing and analytics
- Per-tenant usage tracking
- Cost estimation

### Cache Operations
Every cache operation includes:
- Tenant ID
- Cache hit type (exact/semantic/miss)
- Similarity scores
- Latency
- Prompt hash (for tracking)

### LLM Call Logging
All OpenAI API calls are logged with:
- Model used
- Temperature
- Token estimates (prompt + completion)
- Response time
- Success/failure

## Log Rotation

All log files automatically rotate:
- **Max file size**: 10 MB per file
- **Backup count**: 5 backup files
- **Format**: ISO 8601 timestamps

## Log Levels

- **DEBUG**: Detailed debugging information (performance metrics)
- **INFO**: General informational messages (normal operations)
- **WARNING**: Warning messages (non-critical issues)
- **ERROR**: Error messages (exceptions, failures)

## Usage Examples

### Viewing Logs

```bash
# View all access logs
tail -f backend/logs/access.log

# View errors only
tail -f backend/logs/errors.log

# View security events
tail -f backend/logs/security.log

# Search for specific tenant
grep "tenant123" backend/logs/*.log

# Search for slow requests
grep "SLOW_REQUEST" backend/logs/performance.log
```

### Monitoring Logs

```bash
# Watch all logs in real-time
tail -f backend/logs/*.log

# Count errors in last hour
grep "$(date -d '1 hour ago' '+%Y-%m-%dT%H')" backend/logs/errors.log | wc -l

# Find slowest requests
grep "SLOW_REQUEST" backend/logs/performance.log | sort -k5 -n -r | head -10
```

## Best Practices

1. **Monitor Error Logs**: Regularly check `errors.log` for issues
2. **Track Performance**: Monitor `performance.log` for slow requests
3. **Security Review**: Regularly review `security.log` for suspicious activity
4. **Log Retention**: Keep logs for at least 30 days for auditing
5. **Log Analysis**: Use log aggregation tools (ELK, Splunk) for production

## Integration with Monitoring

The logging system is designed to integrate with:
- **Log aggregation tools** (ELK Stack, Splunk)
- **APM tools** (New Relic, DataDog)
- **Alerting systems** (PagerDuty, Opsgenie)
- **Business intelligence** tools for analytics

## Summary

✅ **All user interactions logged** (requests, responses, errors)  
✅ **All application events logged** (cache ops, LLM calls, system events)  
✅ **Security events logged** (auth attempts, failures)  
✅ **Performance metrics logged** (timing, bottlenecks)  
✅ **Database logging** (usage tracking, billing)  
✅ **Request tracking** (unique IDs for correlation)  
✅ **Automatic rotation** (disk space management)  
✅ **Production-ready** (structured, searchable, scalable)

