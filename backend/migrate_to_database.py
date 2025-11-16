"""
Migration Script: Pickle to Database Storage
Migrates cache entries from pickle files to PostgreSQL database.
"""
import os
import sys
import pickle
import time
from typing import Dict, Optional
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from production_storage import ProductionStorage
from cache_persistence import load_cache, CACHE_FILE
from storage_config import StorageConfig
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_cache_to_database(
    cache_file: str = CACHE_FILE,
    storage: Optional[ProductionStorage] = None
) -> Dict[str, int]:
    """
    Migrate cache entries from pickle file to database.
    
    Args:
        cache_file: Path to pickle cache file
        storage: ProductionStorage instance (optional)
    
    Returns:
        Dictionary with migration statistics
    """
    stats = {
        "tenants_migrated": 0,
        "entries_migrated": 0,
        "entries_skipped": 0,
        "errors": 0
    }
    
    # Initialize storage
    if not storage:
        storage = ProductionStorage()
    
    # Load cache from pickle
    logger.info(f"Loading cache from {cache_file}")
    cache_data = load_cache(cache_file)
    
    if not cache_data:
        logger.warning(f"No cache data found in {cache_file}")
        return stats
    
    tenants = cache_data.get("tenants", {})
    logger.info(f"Found {len(tenants)} tenants to migrate")
    
    # Migrate each tenant
    for tenant_id, tenant_state in tenants.items():
        logger.info(f"Migrating tenant: {tenant_id}")
        stats["tenants_migrated"] += 1
        
        # Migrate exact cache entries
        exact_cache = tenant_state.exact
        for prompt_norm, entry in exact_cache.items():
            try:
                # Generate prompt hash
                import hashlib
                prompt_hash = hashlib.md5(prompt_norm.encode()).hexdigest()
                
                # Save to database
                success = storage.save_cache_entry(
                    tenant_id=tenant_id,
                    prompt_hash=prompt_hash,
                    prompt_norm=prompt_norm,
                    response_text=entry.response_text,
                    embedding=entry.embedding,
                    model=entry.model,
                    ttl_seconds=entry.ttl_seconds,
                    domain=getattr(entry, 'domain', 'general'),
                    strategy='exact'
                )
                
                if success:
                    stats["entries_migrated"] += 1
                else:
                    stats["entries_skipped"] += 1
                    
            except Exception as e:
                logger.error(f"Error migrating entry {prompt_norm[:50]}: {e}")
                stats["errors"] += 1
        
        # Migrate rows (semantic cache entries)
        rows = tenant_state.rows
        for entry in rows:
            try:
                # Generate prompt hash
                import hashlib
                prompt_hash = hashlib.md5(entry.prompt_norm.encode()).hexdigest()
                
                # Save to database
                success = storage.save_cache_entry(
                    tenant_id=tenant_id,
                    prompt_hash=prompt_hash,
                    prompt_norm=entry.prompt_norm,
                    response_text=entry.response_text,
                    embedding=entry.embedding,
                    model=entry.model,
                    ttl_seconds=entry.ttl_seconds,
                    domain=getattr(entry, 'domain', 'general'),
                    strategy=getattr(entry, 'strategy', 'semantic')
                )
                
                if success:
                    stats["entries_migrated"] += 1
                else:
                    stats["entries_skipped"] += 1
                    
            except Exception as e:
                logger.error(f"Error migrating entry {entry.prompt_norm[:50]}: {e}")
                stats["errors"] += 1
    
    # Close storage
    storage.close()
    
    logger.info(f"Migration complete: {stats}")
    return stats


def verify_migration(storage: Optional[ProductionStorage] = None) -> bool:
    """
    Verify migration success.
    
    Args:
        storage: ProductionStorage instance (optional)
    
    Returns:
        True if verification successful
    """
    if not storage:
        storage = ProductionStorage()
    
    try:
        # Get cache stats
        stats = storage.get_cache_stats()
        logger.info(f"Cache stats: {stats}")
        
        # Verify entries exist
        if stats.get("total_entries", 0) > 0:
            logger.info("Migration verification successful")
            return True
        else:
            logger.warning("No entries found in database")
            return False
            
    except Exception as e:
        logger.error(f"Error verifying migration: {e}")
        return False
    finally:
        storage.close()


def main():
    """Main migration function."""
    logger.info("Starting cache migration to database")
    
    # Check if cache file exists
    if not os.path.exists(CACHE_FILE):
        logger.warning(f"Cache file not found: {CACHE_FILE}")
        logger.info("No migration needed - cache file doesn't exist")
        return
    
    # Check if database is configured
    if not StorageConfig.is_production():
        logger.warning("Database not configured for production")
        logger.info("Set DB_BACKEND=postgresql or DB_BACKEND=mysql in .env")
        return
    
    # Initialize storage
    storage = ProductionStorage()
    
    # Migrate cache
    stats = migrate_cache_to_database(CACHE_FILE, storage)
    
    # Verify migration
    if stats["entries_migrated"] > 0:
        verification = verify_migration(storage)
        if verification:
            logger.info("Migration completed successfully")
        else:
            logger.warning("Migration completed with verification issues")
    else:
        logger.info("No entries to migrate")
    
    # Close storage
    storage.close()
    
    logger.info(f"Migration statistics: {stats}")


if __name__ == "__main__":
    main()



