# Production Storage Setup Guide

## Overview

This guide explains how to set up production-ready storage for Semantis AI Cache, including:
- PostgreSQL for structured data
- Redis for fast cache lookups
- S3 for backups
- Prometheus for monitoring
- Grafana for dashboards

## Architecture

```
┌─────────────────┐
│   FastAPI App   │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐  ┌─▼────┐
│PostgreSQL│ │ Redis │
│  (Cache) │ │(Fast) │
└─────────┘ └───────┘
    │
    │
┌───▼────┐
│   S3   │
│(Backups)│
└────────┘
```

## Prerequisites

1. **PostgreSQL** (version 12+)
2. **Redis** (version 6+)
3. **AWS S3** (optional, for backups)
4. **Prometheus** (for metrics)
5. **Grafana** (for dashboards)

## Installation

### 1. Install Production Dependencies

```bash
pip install -r requirements_production.txt
```

### 2. Set Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# Database Configuration
DB_BACKEND=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=semantis_cache
DB_USER=semantis
DB_PASSWORD=your_password
# Or use full URL:
# DATABASE_URL=postgresql://user:password@localhost:5432/semantis_cache

# Redis Configuration
REDIS_ENABLED=true
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password
REDIS_DB=0
# Or use full URL:
# REDIS_URL=redis://:password@localhost:6379/0

# S3 Configuration (optional)
S3_ENABLED=true
S3_BUCKET=semantis-cache-backups
S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# Cache Configuration
CACHE_PERSISTENCE_ENABLED=true
CACHE_SAVE_INTERVAL=10
CACHE_BACKUP_INTERVAL=3600
CACHE_MAX_ENTRIES_PER_TENANT=100000

# Monitoring
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
GRAFANA_ENABLED=true
GRAFANA_PORT=3000

# OpenAI
OPENAI_API_KEY=your_openai_key
```

## Setup Steps

### 1. PostgreSQL Setup

#### Install PostgreSQL

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
```

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

**Windows:**
Download from https://www.postgresql.org/download/windows/

#### Create Database

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE DATABASE semantis_cache;
CREATE USER semantis WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE semantis_cache TO semantis;
\q
```

#### Initialize Schema

The schema will be automatically created when the application starts, or you can run:

```bash
python backend/production_storage.py
```

### 2. Redis Setup

#### Install Redis

**Ubuntu/Debian:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

**macOS:**
```bash
brew install redis
brew services start redis
```

**Windows:**
Download from https://github.com/microsoftarchive/redis/releases

#### Configure Redis

Edit `/etc/redis/redis.conf`:

```conf
# Set password
requirepass your_redis_password

# Enable persistence
save 900 1
save 300 10
save 60 10000
```

#### Start Redis

```bash
redis-server /etc/redis/redis.conf
```

### 3. AWS S3 Setup (Optional)

#### Create S3 Bucket

```bash
aws s3 mb s3://semantis-cache-backups --region us-east-1
```

#### Configure IAM User

1. Create an IAM user with S3 access
2. Generate access keys
3. Set environment variables:
   ```bash
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   ```

### 4. Prometheus Setup

#### Install Prometheus

**Ubuntu/Debian:**
```bash
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
tar xvfz prometheus-2.45.0.linux-amd64.tar.gz
cd prometheus-2.45.0.linux-amd64
```

**macOS:**
```bash
brew install prometheus
```

#### Configure Prometheus

Create `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'semantis-cache'
    static_configs:
      - targets: ['localhost:8000']
```

#### Start Prometheus

```bash
./prometheus --config.file=prometheus.yml
```

### 5. Grafana Setup

#### Install Grafana

**Ubuntu/Debian:**
```bash
sudo apt-get install -y adduser libfontconfig1
wget https://dl.grafana.com/enterprise/release/grafana-enterprise_10.0.0_amd64.deb
sudo dpkg -i grafana-enterprise_10.0.0_amd64.deb
```

**macOS:**
```bash
brew install grafana
```

#### Start Grafana

```bash
sudo systemctl start grafana-server
sudo systemctl enable grafana-server
```

#### Configure Grafana

1. Access Grafana at http://localhost:3000
2. Login with admin/admin (change password)
3. Add Prometheus data source:
   - URL: http://localhost:9090
   - Access: Server
4. Import dashboard (see `grafana_dashboard.json`)

## Migration from Pickle to Database

### 1. Backup Current Cache

```bash
cp backend/cache_data/cache.pkl backend/cache_data/cache.pkl.backup
```

### 2. Run Migration Script

```bash
python backend/migrate_to_database.py
```

This will:
- Load existing cache from `cache.pkl`
- Migrate entries to PostgreSQL
- Store embeddings in Redis
- Verify migration success

## Monitoring

### Prometheus Metrics

Access metrics at: http://localhost:8000/metrics

Available metrics:
- `cache_requests_total` - Total cache requests
- `cache_hits_total` - Total cache hits
- `cache_misses_total` - Total cache misses
- `cache_latency_seconds` - Cache latency
- `cache_entries_total` - Cache entries count
- `cache_hit_ratio` - Cache hit ratio
- `tokens_used_total` - Tokens used
- `tokens_saved_total` - Tokens saved
- `cost_estimate_total` - Estimated cost

### Grafana Dashboards

Import the dashboard from `grafana_dashboard.json` to visualize:
- Cache performance
- Hit rates
- Latency metrics
- Token usage
- Cost estimates
- System health

## Backup Strategy

### Automatic Backups

Backups are configured via `CACHE_BACKUP_INTERVAL` (default: 3600 seconds).

### Manual Backup

```bash
python backend/backup_cache.py
```

### Restore from Backup

```bash
python backend/restore_cache.py --backup-file s3://semantis-cache-backups/backups/cache_2025-01-13.sql
```

## Performance Optimization

### Database Indexes

Indexes are automatically created for:
- `tenant_id`
- `prompt_hash`
- `last_used_at`

### Redis Caching

- Embeddings are cached in Redis for fast lookup
- TTL matches cache entry TTL
- Redis is used for hot cache entries

### Connection Pooling

- PostgreSQL connection pooling via SQLAlchemy
- Redis connection pooling via redis-py
- Configure pool size based on load

## Troubleshooting

### Database Connection Issues

```bash
# Test PostgreSQL connection
psql -h localhost -U semantis -d semantis_cache

# Check Redis connection
redis-cli -h localhost -p 6379 ping
```

### Cache Not Persisting

1. Check `CACHE_PERSISTENCE_ENABLED=true`
2. Verify database connection
3. Check logs for errors
4. Verify disk space

### Performance Issues

1. Check database indexes
2. Monitor Redis memory usage
3. Optimize query patterns
4. Scale database/Redis as needed

## Production Checklist

- [ ] PostgreSQL installed and configured
- [ ] Redis installed and configured
- [ ] S3 configured (optional)
- [ ] Prometheus installed and running
- [ ] Grafana installed and configured
- [ ] Environment variables set
- [ ] Database schema initialized
- [ ] Migration completed (if applicable)
- [ ] Backups configured
- [ ] Monitoring dashboards imported
- [ ] Performance tested
- [ ] Security hardened
- [ ] Documentation updated

## Support

For issues or questions:
- Check logs: `backend/logs/`
- Review metrics: http://localhost:8000/metrics
- Check Grafana dashboards
- Review documentation



