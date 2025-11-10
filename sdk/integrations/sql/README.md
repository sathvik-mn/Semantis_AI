# SQL/BI Caching Integration

SQL/BI-optimized caching for Semantis Cache provides specialized caching for natural-language SQL queries and BI applications.

## Installation

```bash
pip install semantis-cache
```

## Usage

```python
from semantis_cache.integrations.sql import SemantisSQL

# Initialize SQL cache
sql_cache = SemantisSQL(api_key="sc-your-key")

# Query with schema
response = sql_cache.query(
    question="What are the top 10 customers by revenue?",
    schema="customers(id, name, revenue), orders(customer_id, amount)"
)

print(response.answer)  # SQL query or result
print(f"Cache hit: {response.cache_hit}")
```

## Features

- ✅ Natural-language SQL caching
- ✅ Schema-aware caching
- ✅ Query + result caching
- ✅ Automatic semantic matching
- ✅ Fast responses for cached queries

## Configuration

```python
sql_cache = SemantisSQL(
    api_key="sc-your-key",
    base_url="https://api.semantis.ai",  # Optional
    model="gpt-4o-mini",  # Optional
    cache_schema=False  # Include schema in cache key
)
```

## Use Cases

- Natural-language SQL interfaces
- BI applications
- Analytics dashboards
- Data exploration tools

