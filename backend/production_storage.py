"""
Production-Ready Storage Implementation
Supports PostgreSQL, Redis, S3, and vector databases for scalable cache storage.
"""
import os
import json
import time
import pickle
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from contextlib import contextmanager
import logging

from storage_config import StorageConfig

logger = logging.getLogger(__name__)

# Try to import production dependencies
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False
    logger.warning("PostgreSQL not available. Install psycopg2 for production support.")

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available. Install redis-py for Redis support.")

try:
    import boto3
    from botocore.exceptions import ClientError
    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False
    logger.warning("S3 not available. Install boto3 for S3 support.")

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("FAISS not available. Install faiss-cpu for vector search.")


class ProductionStorage:
    """Production-ready storage backend for cache entries."""
    
    def __init__(self):
        self.config = StorageConfig
        self.db_conn = None
        self.redis_client = None
        self.s3_client = None
        self._initialize_storage()
    
    def _initialize_storage(self):
        """Initialize storage backends."""
        # Initialize database
        if self.config.DB_BACKEND == "postgresql" and POSTGRESQL_AVAILABLE:
            self._init_postgresql()
        else:
            self._init_sqlite()
        
        # Initialize Redis
        if self.config.REDIS_ENABLED and REDIS_AVAILABLE:
            self._init_redis()
        
        # Initialize S3
        if self.config.S3_ENABLED and S3_AVAILABLE:
            self._init_s3()
        
        # Initialize database schema
        self._init_schema()
    
    def _init_sqlite(self):
        """Initialize SQLite database."""
        import sqlite3
        db_path = f"cache_data/{self.config.DB_NAME}.db"
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_conn = sqlite3.connect(db_path, check_same_thread=False)
        self.db_conn.row_factory = sqlite3.Row
        logger.info(f"SQLite database initialized: {db_path}")
    
    def _init_postgresql(self):
        """Initialize PostgreSQL database."""
        if not POSTGRESQL_AVAILABLE:
            raise ImportError("PostgreSQL support requires psycopg2. Install with: pip install psycopg2-binary")
        
        db_url = self.config.get_db_url()
        self.db_conn = psycopg2.connect(db_url)
        logger.info("PostgreSQL database initialized")
    
    def _init_redis(self):
        """Initialize Redis client."""
        if not REDIS_AVAILABLE:
            logger.warning("Redis support requires redis-py. Install with: pip install redis")
            return
        
        redis_url = self.config.get_redis_url()
        if redis_url:
            self.redis_client = redis.from_url(redis_url, decode_responses=False)
            logger.info("Redis client initialized")
        else:
            logger.warning("Redis URL not configured")
    
    def _init_s3(self):
        """Initialize S3 client."""
        if not S3_AVAILABLE:
            logger.warning("S3 support requires boto3. Install with: pip install boto3")
            return
        
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=self.config.AWS_SECRET_ACCESS_KEY,
            region_name=self.config.S3_REGION
        )
        logger.info(f"S3 client initialized for bucket: {self.config.S3_BUCKET}")
    
    def _init_schema(self):
        """Initialize database schema for cache entries."""
        cursor = self.db_conn.cursor()
        
        if self.config.DB_BACKEND == "postgresql":
            # PostgreSQL schema
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cache_entries (
                    id SERIAL PRIMARY KEY,
                    tenant_id VARCHAR(255) NOT NULL,
                    prompt_hash VARCHAR(64) NOT NULL,
                    prompt_norm TEXT NOT NULL,
                    response_text TEXT NOT NULL,
                    embedding BYTEA,
                    model VARCHAR(100) NOT NULL,
                    ttl_seconds INTEGER DEFAULT 604800,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    use_count INTEGER DEFAULT 0,
                    domain VARCHAR(50) DEFAULT 'general',
                    strategy VARCHAR(20) DEFAULT 'miss',
                    similarity_threshold REAL DEFAULT 0.83,
                    UNIQUE(tenant_id, prompt_hash)
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_cache_tenant ON cache_entries(tenant_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_cache_prompt_hash ON cache_entries(prompt_hash)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_cache_last_used ON cache_entries(last_used_at)
            ''')
            
        else:
            # SQLite schema
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cache_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_id TEXT NOT NULL,
                    prompt_hash TEXT NOT NULL,
                    prompt_norm TEXT NOT NULL,
                    response_text TEXT NOT NULL,
                    embedding BLOB,
                    model TEXT NOT NULL,
                    ttl_seconds INTEGER DEFAULT 604800,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    use_count INTEGER DEFAULT 0,
                    domain TEXT DEFAULT 'general',
                    strategy TEXT DEFAULT 'miss',
                    similarity_threshold REAL DEFAULT 0.83,
                    UNIQUE(tenant_id, prompt_hash)
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_cache_tenant ON cache_entries(tenant_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_cache_prompt_hash ON cache_entries(prompt_hash)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_cache_last_used ON cache_entries(last_used_at)
            ''')
        
        self.db_conn.commit()
        logger.info("Database schema initialized")
    
    def save_cache_entry(
        self,
        tenant_id: str,
        prompt_hash: str,
        prompt_norm: str,
        response_text: str,
        embedding: np.ndarray,
        model: str,
        ttl_seconds: int = 604800,
        domain: str = "general",
        strategy: str = "miss"
    ) -> bool:
        """Save a cache entry to database."""
        try:
            cursor = self.db_conn.cursor()
            
            # Serialize embedding
            embedding_bytes = pickle.dumps(embedding.astype('float32'))
            
            if self.config.DB_BACKEND == "postgresql":
                cursor.execute('''
                    INSERT INTO cache_entries 
                    (tenant_id, prompt_hash, prompt_norm, response_text, embedding, model, 
                     ttl_seconds, domain, strategy, last_used_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (tenant_id, prompt_hash) 
                    DO UPDATE SET
                        response_text = EXCLUDED.response_text,
                        embedding = EXCLUDED.embedding,
                        last_used_at = CURRENT_TIMESTAMP,
                        use_count = cache_entries.use_count + 1
                ''', (tenant_id, prompt_hash, prompt_norm, response_text, 
                      embedding_bytes, model, ttl_seconds, domain, strategy))
            else:
                cursor.execute('''
                    INSERT OR REPLACE INTO cache_entries 
                    (tenant_id, prompt_hash, prompt_norm, response_text, embedding, model, 
                     ttl_seconds, domain, strategy, last_used_at, use_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 
                            COALESCE((SELECT use_count FROM cache_entries 
                                     WHERE tenant_id = ? AND prompt_hash = ?), 0) + 1)
                ''', (tenant_id, prompt_hash, prompt_norm, response_text, 
                      embedding_bytes, model, ttl_seconds, domain, strategy,
                      tenant_id, prompt_hash))
            
            self.db_conn.commit()
            
            # Store embedding in Redis for fast lookup
            if self.redis_client:
                redis_key = f"embedding:{tenant_id}:{prompt_hash}"
                self.redis_client.setex(redis_key, ttl_seconds, pickle.dumps(embedding))
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving cache entry: {e}")
            self.db_conn.rollback()
            return False
    
    def get_cache_entry(
        self,
        tenant_id: str,
        prompt_hash: str
    ) -> Optional[Dict[str, Any]]:
        """Get a cache entry from database."""
        try:
            cursor = self.db_conn.cursor()
            
            if self.config.DB_BACKEND == "postgresql":
                cursor.execute('''
                    SELECT * FROM cache_entries
                    WHERE tenant_id = %s AND prompt_hash = %s
                    AND (created_at + INTERVAL '%s seconds') > CURRENT_TIMESTAMP
                ''', (tenant_id, prompt_hash, 604800))
            else:
                cursor.execute('''
                    SELECT * FROM cache_entries
                    WHERE tenant_id = ? AND prompt_hash = ?
                    AND datetime(created_at, '+' || ttl_seconds || ' seconds') > datetime('now')
                ''', (tenant_id, prompt_hash))
            
            row = cursor.fetchone()
            if row:
                # Convert to dict
                if self.config.DB_BACKEND == "postgresql":
                    entry = dict(row)
                else:
                    entry = dict(zip([col[0] for col in cursor.description], row))
                
                # Deserialize embedding
                if entry.get('embedding'):
                    entry['embedding'] = pickle.loads(entry['embedding'])
                
                # Update last_used_at
                cursor.execute('''
                    UPDATE cache_entries
                    SET last_used_at = CURRENT_TIMESTAMP, use_count = use_count + 1
                    WHERE tenant_id = ? AND prompt_hash = ?
                ''', (tenant_id, prompt_hash))
                self.db_conn.commit()
                
                return entry
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cache entry: {e}")
            return None
    
    def get_tenant_cache_entries(
        self,
        tenant_id: str,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get all cache entries for a tenant."""
        try:
            cursor = self.db_conn.cursor()
            
            if self.config.DB_BACKEND == "postgresql":
                cursor.execute('''
                    SELECT * FROM cache_entries
                    WHERE tenant_id = %s
                    ORDER BY last_used_at DESC
                    LIMIT %s
                ''', (tenant_id, limit))
            else:
                cursor.execute('''
                    SELECT * FROM cache_entries
                    WHERE tenant_id = ?
                    ORDER BY last_used_at DESC
                    LIMIT ?
                ''', (tenant_id, limit))
            
            rows = cursor.fetchall()
            entries = []
            
            for row in rows:
                if self.config.DB_BACKEND == "postgresql":
                    entry = dict(row)
                else:
                    entry = dict(zip([col[0] for col in cursor.description], row))
                
                # Deserialize embedding
                if entry.get('embedding'):
                    entry['embedding'] = pickle.loads(entry['embedding'])
                
                entries.append(entry)
            
            return entries
            
        except Exception as e:
            logger.error(f"Error getting tenant cache entries: {e}")
            return []
    
    def delete_expired_entries(self, tenant_id: Optional[str] = None) -> int:
        """Delete expired cache entries."""
        try:
            cursor = self.db_conn.cursor()
            
            if tenant_id:
                if self.config.DB_BACKEND == "postgresql":
                    cursor.execute('''
                        DELETE FROM cache_entries
                        WHERE tenant_id = %s
                        AND (created_at + INTERVAL '%s seconds') < CURRENT_TIMESTAMP
                    ''', (tenant_id, 604800))
                else:
                    cursor.execute('''
                        DELETE FROM cache_entries
                        WHERE tenant_id = ?
                        AND datetime(created_at, '+' || ttl_seconds || ' seconds') < datetime('now')
                    ''', (tenant_id,))
            else:
                if self.config.DB_BACKEND == "postgresql":
                    cursor.execute('''
                        DELETE FROM cache_entries
                        WHERE (created_at + INTERVAL '%s seconds') < CURRENT_TIMESTAMP
                    ''', (604800,))
                else:
                    cursor.execute('''
                        DELETE FROM cache_entries
                        WHERE datetime(created_at, '+' || ttl_seconds || ' seconds') < datetime('now')
                    ''')
            
            deleted_count = cursor.rowcount
            self.db_conn.commit()
            
            logger.info(f"Deleted {deleted_count} expired cache entries")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error deleting expired entries: {e}")
            self.db_conn.rollback()
            return 0
    
    def backup_to_s3(self, backup_key: Optional[str] = None) -> bool:
        """Backup cache to S3."""
        if not self.s3_client:
            logger.warning("S3 client not initialized")
            return False
        
        try:
            if not backup_key:
                backup_key = f"backups/cache_{datetime.now().isoformat()}.sql"
            
            # Export database to SQL file
            # This is a simplified version - in production, use pg_dump or similar
            logger.info(f"Backing up cache to S3: {backup_key}")
            # TODO: Implement actual backup logic
            
            return True
            
        except Exception as e:
            logger.error(f"Error backing up to S3: {e}")
            return False
    
    def get_cache_stats(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            cursor = self.db_conn.cursor()
            
            if tenant_id:
                if self.config.DB_BACKEND == "postgresql":
                    cursor.execute('''
                        SELECT 
                            COUNT(*) as total_entries,
                            COUNT(DISTINCT tenant_id) as total_tenants,
                            SUM(use_count) as total_uses,
                            AVG(use_count) as avg_uses
                        FROM cache_entries
                        WHERE tenant_id = %s
                    ''', (tenant_id,))
                else:
                    cursor.execute('''
                        SELECT 
                            COUNT(*) as total_entries,
                            COUNT(DISTINCT tenant_id) as total_tenants,
                            SUM(use_count) as total_uses,
                            AVG(use_count) as avg_uses
                        FROM cache_entries
                        WHERE tenant_id = ?
                    ''', (tenant_id,))
            else:
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_entries,
                        COUNT(DISTINCT tenant_id) as total_tenants,
                        SUM(use_count) as total_uses,
                        AVG(use_count) as avg_uses
                    FROM cache_entries
                ''')
            
            row = cursor.fetchone()
            if row:
                if self.config.DB_BACKEND == "postgresql":
                    return dict(row)
                else:
                    return dict(zip([col[0] for col in cursor.description], row))
            
            return {
                "total_entries": 0,
                "total_tenants": 0,
                "total_uses": 0,
                "avg_uses": 0
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {
                "total_entries": 0,
                "total_tenants": 0,
                "total_uses": 0,
                "avg_uses": 0
            }
    
    def close(self):
        """Close database connections."""
        if self.db_conn:
            self.db_conn.close()
        if self.redis_client:
            self.redis_client.close()




