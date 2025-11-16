"""
Production-Ready Storage Configuration
Supports multiple storage backends: SQLite (dev), PostgreSQL (production), Redis (cache), S3 (backups)
"""
import os
from typing import Optional, Dict, Any
from enum import Enum

class StorageBackend(Enum):
    """Storage backend types."""
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    REDIS = "redis"
    S3 = "s3"

class StorageConfig:
    """Storage configuration for production-ready cache storage."""
    
    # Database configuration
    DB_BACKEND = os.getenv("DB_BACKEND", "sqlite")  # sqlite, postgresql, mysql
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "5432"))
    DB_NAME = os.getenv("DB_NAME", "semantis_cache")
    DB_USER = os.getenv("DB_USER", "semantis")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_URL = os.getenv("DATABASE_URL", None)  # Full connection string
    
    # Redis configuration (for vector cache and session storage)
    REDIS_ENABLED = os.getenv("REDIS_ENABLED", "false").lower() == "true"
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    REDIS_URL = os.getenv("REDIS_URL", None)  # Full connection string
    
    # S3 configuration (for backups)
    S3_ENABLED = os.getenv("S3_ENABLED", "false").lower() == "true"
    S3_BUCKET = os.getenv("S3_BUCKET", "semantis-cache-backups")
    S3_REGION = os.getenv("S3_REGION", "us-east-1")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", None)
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", None)
    
    # Vector database configuration
    VECTOR_DB_BACKEND = os.getenv("VECTOR_DB_BACKEND", "faiss")  # faiss, milvus, pinecone, redis
    VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "cache_data/vectors")
    
    # Milvus configuration
    MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
    MILVUS_PORT = int(os.getenv("MILVUS_PORT", "19530"))
    
    # Pinecone configuration
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", None)
    PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
    PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "semantis-cache")
    
    # Cache persistence configuration
    CACHE_PERSISTENCE_ENABLED = os.getenv("CACHE_PERSISTENCE_ENABLED", "true").lower() == "true"
    CACHE_SAVE_INTERVAL = int(os.getenv("CACHE_SAVE_INTERVAL", "10"))  # Save every N entries
    CACHE_BACKUP_INTERVAL = int(os.getenv("CACHE_BACKUP_INTERVAL", "3600"))  # Backup every N seconds
    CACHE_MAX_ENTRIES_PER_TENANT = int(os.getenv("CACHE_MAX_ENTRIES_PER_TENANT", "100000"))
    
    # Monitoring configuration
    PROMETHEUS_ENABLED = os.getenv("PROMETHEUS_ENABLED", "true").lower() == "true"
    PROMETHEUS_PORT = int(os.getenv("PROMETHEUS_PORT", "9090"))
    
    # Grafana configuration
    GRAFANA_ENABLED = os.getenv("GRAFANA_ENABLED", "true").lower() == "true"
    GRAFANA_PORT = int(os.getenv("GRAFANA_PORT", "3000"))
    
    @classmethod
    def get_db_url(cls) -> str:
        """Get database connection URL."""
        if cls.DB_URL:
            return cls.DB_URL
        
        if cls.DB_BACKEND == "postgresql":
            return f"postgresql://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"
        elif cls.DB_BACKEND == "mysql":
            return f"mysql+pymysql://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"
        else:
            return f"sqlite:///cache_data/{cls.DB_NAME}.db"
    
    @classmethod
    def get_redis_url(cls) -> Optional[str]:
        """Get Redis connection URL."""
        if cls.REDIS_URL:
            return cls.REDIS_URL
        
        if cls.REDIS_ENABLED:
            if cls.REDIS_PASSWORD:
                return f"redis://:{cls.REDIS_PASSWORD}@{cls.REDIS_HOST}:{cls.REDIS_PORT}/{cls.REDIS_DB}"
            else:
                return f"redis://{cls.REDIS_HOST}:{cls.REDIS_PORT}/{cls.REDIS_DB}"
        return None
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production mode."""
        return cls.DB_BACKEND != "sqlite" or cls.REDIS_ENABLED or cls.S3_ENABLED
    
    @classmethod
    def get_config_summary(cls) -> Dict[str, Any]:
        """Get configuration summary."""
        return {
            "db_backend": cls.DB_BACKEND,
            "db_url": cls.get_db_url().split("@")[-1] if "@" in cls.get_db_url() else cls.get_db_url(),
            "redis_enabled": cls.REDIS_ENABLED,
            "redis_url": cls.get_redis_url(),
            "s3_enabled": cls.S3_ENABLED,
            "s3_bucket": cls.S3_BUCKET if cls.S3_ENABLED else None,
            "vector_db_backend": cls.VECTOR_DB_BACKEND,
            "cache_persistence_enabled": cls.CACHE_PERSISTENCE_ENABLED,
            "prometheus_enabled": cls.PROMETHEUS_ENABLED,
            "grafana_enabled": cls.GRAFANA_ENABLED,
            "is_production": cls.is_production(),
        }




