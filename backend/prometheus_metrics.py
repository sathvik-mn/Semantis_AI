"""
Prometheus Metrics for Cache Monitoring
Provides metrics for cache performance, hit rates, latency, and system health.
"""
import time
from typing import Dict, Optional
from prometheus_client import Counter, Histogram, Gauge, Summary, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client.core import CollectorRegistry
from fastapi import Response
import logging

logger = logging.getLogger(__name__)

# Create a custom registry for metrics
registry = CollectorRegistry()

# Cache metrics
cache_requests_total = Counter(
    'cache_requests_total',
    'Total number of cache requests',
    ['tenant_id', 'hit_type'],  # hit_type: exact, semantic, miss
    registry=registry
)

cache_hits_total = Counter(
    'cache_hits_total',
    'Total number of cache hits',
    ['tenant_id', 'hit_type'],
    registry=registry
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total number of cache misses',
    ['tenant_id'],
    registry=registry
)

cache_latency_seconds = Histogram(
    'cache_latency_seconds',
    'Cache request latency in seconds',
    ['tenant_id', 'hit_type'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0],
    registry=registry
)

cache_embedding_latency_seconds = Histogram(
    'cache_embedding_latency_seconds',
    'Embedding generation latency in seconds',
    ['tenant_id'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
    registry=registry
)

cache_llm_latency_seconds = Histogram(
    'cache_llm_latency_seconds',
    'LLM API call latency in seconds',
    ['tenant_id', 'model'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
    registry=registry
)

cache_entries_total = Gauge(
    'cache_entries_total',
    'Total number of cache entries',
    ['tenant_id'],
    registry=registry
)

cache_hit_ratio = Gauge(
    'cache_hit_ratio',
    'Cache hit ratio (0.0 to 1.0)',
    ['tenant_id'],
    registry=registry
)

cache_similarity_threshold = Gauge(
    'cache_similarity_threshold',
    'Current similarity threshold',
    ['tenant_id'],
    registry=registry
)

# API metrics
api_requests_total = Counter(
    'api_requests_total',
    'Total number of API requests',
    ['endpoint', 'method', 'status_code'],
    registry=registry
)

api_latency_seconds = Histogram(
    'api_latency_seconds',
    'API request latency in seconds',
    ['endpoint', 'method'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
    registry=registry
)

# System metrics
system_memory_usage_bytes = Gauge(
    'system_memory_usage_bytes',
    'System memory usage in bytes',
    registry=registry
)

system_cpu_usage_percent = Gauge(
    'system_cpu_usage_percent',
    'System CPU usage percentage',
    registry=registry
)

system_cache_size_bytes = Gauge(
    'system_cache_size_bytes',
    'Cache size in bytes',
    registry=registry
)

# Token metrics
tokens_used_total = Counter(
    'tokens_used_total',
    'Total tokens used',
    ['tenant_id', 'model', 'type'],  # type: prompt, completion, total
    registry=registry
)

tokens_saved_total = Counter(
    'tokens_saved_total',
    'Total tokens saved by cache',
    ['tenant_id'],
    registry=registry
)

cost_estimate_total = Counter(
    'cost_estimate_total',
    'Total estimated cost in USD',
    ['tenant_id', 'model'],
    registry=registry
)


class CacheMetrics:
    """Cache metrics collector."""
    
    @staticmethod
    def record_cache_request(tenant_id: str, hit_type: str, latency: float):
        """Record a cache request."""
        cache_requests_total.labels(tenant_id=tenant_id, hit_type=hit_type).inc()
        cache_latency_seconds.labels(tenant_id=tenant_id, hit_type=hit_type).observe(latency)
        
        if hit_type in ['exact', 'semantic']:
            cache_hits_total.labels(tenant_id=tenant_id, hit_type=hit_type).inc()
        else:
            cache_misses_total.labels(tenant_id=tenant_id).inc()
    
    @staticmethod
    def record_embedding_generation(tenant_id: str, latency: float):
        """Record embedding generation latency."""
        cache_embedding_latency_seconds.labels(tenant_id=tenant_id).observe(latency)
    
    @staticmethod
    def record_llm_call(tenant_id: str, model: str, latency: float):
        """Record LLM API call latency."""
        cache_llm_latency_seconds.labels(tenant_id=tenant_id, model=model).observe(latency)
    
    @staticmethod
    def update_cache_entries(tenant_id: str, count: int):
        """Update cache entries count."""
        cache_entries_total.labels(tenant_id=tenant_id).set(count)
    
    @staticmethod
    def update_hit_ratio(tenant_id: str, ratio: float):
        """Update cache hit ratio."""
        cache_hit_ratio.labels(tenant_id=tenant_id).set(ratio)
    
    @staticmethod
    def update_similarity_threshold(tenant_id: str, threshold: float):
        """Update similarity threshold."""
        cache_similarity_threshold.labels(tenant_id=tenant_id).set(threshold)
    
    @staticmethod
    def record_api_request(endpoint: str, method: str, status_code: int, latency: float):
        """Record API request."""
        api_requests_total.labels(endpoint=endpoint, method=method, status_code=status_code).inc()
        api_latency_seconds.labels(endpoint=endpoint, method=method).observe(latency)
    
    @staticmethod
    def record_tokens(tenant_id: str, model: str, prompt_tokens: int, completion_tokens: int):
        """Record token usage."""
        tokens_used_total.labels(tenant_id=tenant_id, model=model, type='prompt').inc(prompt_tokens)
        tokens_used_total.labels(tenant_id=tenant_id, model=model, type='completion').inc(completion_tokens)
        tokens_used_total.labels(tenant_id=tenant_id, model=model, type='total').inc(prompt_tokens + completion_tokens)
    
    @staticmethod
    def record_tokens_saved(tenant_id: str, tokens: int):
        """Record tokens saved by cache."""
        tokens_saved_total.labels(tenant_id=tenant_id).inc(tokens)
    
    @staticmethod
    def record_cost(tenant_id: str, model: str, cost: float):
        """Record estimated cost."""
        cost_estimate_total.labels(tenant_id=tenant_id, model=model).inc(cost)
    
    @staticmethod
    def update_system_metrics():
        """Update system metrics."""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            system_memory_usage_bytes.set(memory_info.rss)
            system_cpu_usage_percent.set(process.cpu_percent())
        except ImportError:
            logger.warning("psutil not available for system metrics")
        except Exception as e:
            logger.error(f"Error updating system metrics: {e}")


def get_metrics_response() -> Response:
    """Get Prometheus metrics response."""
    return Response(
        content=generate_latest(registry),
        media_type=CONTENT_TYPE_LATEST
    )


# Initialize metrics
metrics = CacheMetrics()



