"""
Cache manager for API responses.
Stores API responses locally to avoid redundant requests and enable offline processing.
"""

import json
import hashlib
import pickle
from pathlib import Path
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
from utils.logger import get_logger

logger = get_logger()


class CacheManager:
    """Manages local caching of API responses."""
    
    def __init__(
        self,
        cache_dir: str = "cache",
        default_ttl: int = 86400,  # 24 hours in seconds
        use_pickle: bool = True
    ):
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Directory for cache files
            default_ttl: Default time-to-live in seconds
            use_pickle: Whether to use pickle for complex objects (faster) or JSON (portable)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl = default_ttl
        self.use_pickle = use_pickle
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """Load cache metadata."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache metadata: {e}")
        return {}
    
    def _save_metadata(self):
        """Save cache metadata."""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save cache metadata: {e}")
    
    def _get_cache_key(self, url: str, params: Optional[Dict] = None) -> str:
        """
        Generate cache key from URL and parameters.
        
        Args:
            url: API URL
            params: Request parameters
            
        Returns:
            Cache key (hash)
        """
        key_string = url
        if params:
            # Sort params for consistent hashing
            sorted_params = sorted(params.items())
            key_string += json.dumps(sorted_params, sort_keys=True)
        
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get file path for cache key."""
        if self.use_pickle:
            return self.cache_dir / f"{cache_key}.pkl"
        else:
            return self.cache_dir / f"{cache_key}.json"
    
    def get(
        self,
        url: str,
        params: Optional[Dict] = None,
        ttl: Optional[int] = None
    ) -> Optional[Any]:
        """
        Get cached response if available and not expired.
        
        Args:
            url: API URL
            params: Request parameters
            ttl: Time-to-live override
            
        Returns:
            Cached data or None if not found/expired
        """
        cache_key = self._get_cache_key(url, params)
        cache_path = self._get_cache_path(cache_key)
        
        if not cache_path.exists():
            return None
        
        # Check metadata for expiration
        if cache_key in self.metadata:
            cached_time = datetime.fromisoformat(self.metadata[cache_key]['timestamp'])
            ttl_seconds = ttl or self.metadata[cache_key].get('ttl', self.default_ttl)
            
            if datetime.now() - cached_time > timedelta(seconds=ttl_seconds):
                logger.debug(f"Cache expired for {url}")
                self.delete(url, params)
                return None
        
        # Load cached data
        try:
            if self.use_pickle:
                with open(cache_path, 'rb') as f:
                    return pickle.load(f)
            else:
                with open(cache_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load cache for {url}: {e}")
            return None
    
    def set(
        self,
        url: str,
        data: Any,
        params: Optional[Dict] = None,
        ttl: Optional[int] = None
    ):
        """
        Cache response data.
        
        Args:
            url: API URL
            data: Response data to cache
            params: Request parameters
            ttl: Time-to-live override
        """
        cache_key = self._get_cache_key(url, params)
        cache_path = self._get_cache_path(cache_key)
        
        try:
            if self.use_pickle:
                with open(cache_path, 'wb') as f:
                    pickle.dump(data, f)
            else:
                with open(cache_path, 'w') as f:
                    json.dump(data, f, indent=2)
            
            # Update metadata
            self.metadata[cache_key] = {
                'url': url,
                'params': params,
                'timestamp': datetime.now().isoformat(),
                'ttl': ttl or self.default_ttl
            }
            self._save_metadata()
            
            logger.debug(f"Cached response for {url}")
        except Exception as e:
            logger.warning(f"Failed to cache response for {url}: {e}")
    
    def delete(self, url: str, params: Optional[Dict] = None):
        """
        Delete cached response.
        
        Args:
            url: API URL
            params: Request parameters
        """
        cache_key = self._get_cache_key(url, params)
        cache_path = self._get_cache_path(cache_key)
        
        if cache_path.exists():
            cache_path.unlink()
        
        if cache_key in self.metadata:
            del self.metadata[cache_key]
            self._save_metadata()
    
    def clear(self, older_than: Optional[timedelta] = None):
        """
        Clear cache entries.
        
        Args:
            older_than: Only clear entries older than this (None = clear all)
        """
        if older_than is None:
            # Clear all
            for cache_file in self.cache_dir.glob("*.*"):
                if cache_file.name != "cache_metadata.json":
                    cache_file.unlink()
            self.metadata = {}
            self._save_metadata()
            logger.info("Cleared all cache entries")
        else:
            # Clear expired entries
            cutoff = datetime.now() - older_than
            keys_to_delete = []
            
            for cache_key, metadata in self.metadata.items():
                cached_time = datetime.fromisoformat(metadata['timestamp'])
                if cached_time < cutoff:
                    keys_to_delete.append(cache_key)
            
            for cache_key in keys_to_delete:
                cache_path = self._get_cache_path(cache_key)
                if cache_path.exists():
                    cache_path.unlink()
                del self.metadata[cache_key]
            
            if keys_to_delete:
                self._save_metadata()
                logger.info(f"Cleared {len(keys_to_delete)} expired cache entries")
    
    def get_cache_stats(self) -> Dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        total_files = len(list(self.cache_dir.glob("*.*"))) - 1  # Exclude metadata
        total_size = sum(
            f.stat().st_size
            for f in self.cache_dir.glob("*.*")
            if f.name != "cache_metadata.json"
        )
        
        return {
            'total_entries': len(self.metadata),
            'total_files': total_files,
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'cache_dir': str(self.cache_dir)
        }


# Global cache manager instance
_cache_manager_instance: Optional[CacheManager] = None


def get_cache_manager(
    cache_dir: str = "cache",
    default_ttl: int = 86400
) -> CacheManager:
    """
    Get or create the global cache manager instance.
    
    Args:
        cache_dir: Directory for cache files
        default_ttl: Default time-to-live in seconds
        
    Returns:
        CacheManager instance
    """
    global _cache_manager_instance
    if _cache_manager_instance is None:
        _cache_manager_instance = CacheManager(cache_dir, default_ttl)
    return _cache_manager_instance

