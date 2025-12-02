"""
Redis Storage Backend for DSI Persistence
==========================================

Production-ready Redis implementation with:
- Connection pooling
- Automatic reconnection
- JSON serialisation
- Atomic operations
- Cluster support

Requirements:
    pip install redis

Author: John Walker
Version: 1.0.0
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    import redis
    from redis.exceptions import RedisError, ConnectionError
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from dsi_persistence import StorageBackend

logger = logging.getLogger("dsi.persistence.redis")


class RedisStorage(StorageBackend):
    """
    Redis-backed storage for high-performance signal caching.
    
    Optimized for:
    - High read throughput (signal lookups)
    - TTL-based expiration
    - Atomic operations
    - Horizontal scaling via Redis Cluster
    """
    
    def __init__(self, 
                 host: str = "localhost",
                 port: int = 6379,
                 db: int = 0,
                 password: Optional[str] = None,
                 prefix: str = "dsi:",
                 max_connections: int = 50,
                 socket_timeout: float = 5.0,
                 cluster_mode: bool = False,
                 cluster_nodes: Optional[List[Dict]] = None):
        """
        Initialize Redis connection.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password
            prefix: Key prefix for all DSI keys
            max_connections: Connection pool size
            socket_timeout: Socket timeout in seconds
            cluster_mode: Enable Redis Cluster support
            cluster_nodes: List of cluster nodes for cluster mode
        """
        if not REDIS_AVAILABLE:
            raise ImportError("redis package required: pip install redis")
        
        self.prefix = prefix
        self.cluster_mode = cluster_mode
        
        if cluster_mode and cluster_nodes:
            from redis.cluster import RedisCluster
            self.client = RedisCluster(
                startup_nodes=[
                    redis.cluster.ClusterNode(n["host"], n["port"]) 
                    for n in cluster_nodes
                ],
                password=password,
                socket_timeout=socket_timeout,
            )
        else:
            pool = redis.ConnectionPool(
                host=host,
                port=port,
                db=db,
                password=password,
                max_connections=max_connections,
                socket_timeout=socket_timeout,
                decode_responses=True,
            )
            self.client = redis.Redis(connection_pool=pool)
        
        # Test connection
        try:
            self.client.ping()
            logger.info(f"Connected to Redis at {host}:{port}")
        except ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def _key(self, key: str) -> str:
        """Add prefix to key."""
        return f"{self.prefix}{key}"
    
    def _serialize(self, value: Dict) -> str:
        """Serialize value to JSON string."""
        return json.dumps(value, default=str)
    
    def _deserialize(self, data: Optional[str]) -> Optional[Dict]:
        """Deserialize JSON string to dict."""
        if data is None:
            return None
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            logger.error(f"Failed to deserialize: {data[:100]}")
            return None
    
    def set(self, key: str, value: Dict, ttl: Optional[int] = None) -> bool:
        """Store a value with optional TTL."""
        try:
            full_key = self._key(key)
            data = self._serialize(value)
            
            if ttl:
                result = self.client.setex(full_key, ttl, data)
            else:
                result = self.client.set(full_key, data)
            
            return bool(result)
        except RedisError as e:
            logger.error(f"Redis SET error: {e}")
            return False
    
    def get(self, key: str) -> Optional[Dict]:
        """Retrieve a value by key."""
        try:
            full_key = self._key(key)
            data = self.client.get(full_key)
            return self._deserialize(data)
        except RedisError as e:
            logger.error(f"Redis GET error: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete a value by key."""
        try:
            full_key = self._key(key)
            result = self.client.delete(full_key)
            return result > 0
        except RedisError as e:
            logger.error(f"Redis DELETE error: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists."""
        try:
            full_key = self._key(key)
            return bool(self.client.exists(full_key))
        except RedisError as e:
            logger.error(f"Redis EXISTS error: {e}")
            return False
    
    def keys(self, pattern: str) -> List[str]:
        """Find keys matching pattern."""
        try:
            full_pattern = self._key(pattern)
            keys = self.client.keys(full_pattern)
            # Strip prefix from returned keys
            prefix_len = len(self.prefix)
            return [k[prefix_len:] if isinstance(k, str) else k.decode()[prefix_len:] 
                    for k in keys]
        except RedisError as e:
            logger.error(f"Redis KEYS error: {e}")
            return []
    
    def mget(self, keys: List[str]) -> List[Optional[Dict]]:
        """Get multiple values."""
        if not keys:
            return []
        
        try:
            full_keys = [self._key(k) for k in keys]
            results = self.client.mget(full_keys)
            return [self._deserialize(r) for r in results]
        except RedisError as e:
            logger.error(f"Redis MGET error: {e}")
            return [None] * len(keys)
    
    def mset(self, items: Dict[str, Dict], ttl: Optional[int] = None) -> bool:
        """Set multiple values with pipeline for efficiency."""
        if not items:
            return True
        
        try:
            pipe = self.client.pipeline()
            
            for key, value in items.items():
                full_key = self._key(key)
                data = self._serialize(value)
                
                if ttl:
                    pipe.setex(full_key, ttl, data)
                else:
                    pipe.set(full_key, data)
            
            pipe.execute()
            return True
        except RedisError as e:
            logger.error(f"Redis MSET error: {e}")
            return False
    
    # Additional Redis-specific methods
    
    def incr(self, key: str, amount: int = 1) -> int:
        """Increment a counter."""
        try:
            full_key = self._key(key)
            return self.client.incrby(full_key, amount)
        except RedisError as e:
            logger.error(f"Redis INCR error: {e}")
            return 0
    
    def expire(self, key: str, ttl: int) -> bool:
        """Set TTL on existing key."""
        try:
            full_key = self._key(key)
            return bool(self.client.expire(full_key, ttl))
        except RedisError as e:
            logger.error(f"Redis EXPIRE error: {e}")
            return False
    
    def ttl(self, key: str) -> int:
        """Get remaining TTL for a key."""
        try:
            full_key = self._key(key)
            return self.client.ttl(full_key)
        except RedisError as e:
            logger.error(f"Redis TTL error: {e}")
            return -2
    
    def scan_iter(self, pattern: str, count: int = 100) -> List[str]:
        """Iterate through keys matching pattern (more efficient than KEYS)."""
        try:
            full_pattern = self._key(pattern)
            keys = []
            for key in self.client.scan_iter(match=full_pattern, count=count):
                k = key if isinstance(key, str) else key.decode()
                keys.append(k[len(self.prefix):])
            return keys
        except RedisError as e:
            logger.error(f"Redis SCAN error: {e}")
            return []
    
    def flush_prefix(self) -> int:
        """Delete all keys with current prefix (use with caution!)."""
        try:
            keys = self.client.keys(f"{self.prefix}*")
            if keys:
                return self.client.delete(*keys)
            return 0
        except RedisError as e:
            logger.error(f"Redis FLUSH error: {e}")
            return 0
    
    def info(self) -> Dict:
        """Get Redis server info."""
        try:
            info = self.client.info()
            return {
                "redis_version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
                "total_keys": self.client.dbsize(),
                "dsi_keys": len(self.keys("*")),
            }
        except RedisError as e:
            logger.error(f"Redis INFO error: {e}")
            return {}


class RedisStorageWithMetrics(RedisStorage):
    """
    Redis storage with built-in metrics collection.
    
    Tracks:
    - Cache hit/miss rates
    - Operation latencies
    - Error counts
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._metrics = {
            "gets": 0,
            "sets": 0,
            "hits": 0,
            "misses": 0,
            "errors": 0,
        }
    
    def get(self, key: str) -> Optional[Dict]:
        self._metrics["gets"] += 1
        result = super().get(key)
        
        if result is not None:
            self._metrics["hits"] += 1
        else:
            self._metrics["misses"] += 1
        
        return result
    
    def set(self, key: str, value: Dict, ttl: Optional[int] = None) -> bool:
        self._metrics["sets"] += 1
        return super().set(key, value, ttl)
    
    def get_metrics(self) -> Dict:
        """Get current metrics."""
        total_gets = self._metrics["gets"]
        return {
            **self._metrics,
            "hit_rate": self._metrics["hits"] / total_gets if total_gets > 0 else 0,
            "miss_rate": self._metrics["misses"] / total_gets if total_gets > 0 else 0,
        }
    
    def reset_metrics(self):
        """Reset metrics counters."""
        self._metrics = {k: 0 for k in self._metrics}


# Factory function
def create_redis_storage(config: Dict) -> RedisStorage:
    """
    Create Redis storage from configuration dict.
    
    Example config:
        {
            "host": "redis.example.com",
            "port": 6379,
            "password": "secret",
            "db": 0,
            "prefix": "dsi_prod:",
            "with_metrics": True,
            "cluster_mode": False,
        }
    """
    with_metrics = config.pop("with_metrics", False)
    
    if with_metrics:
        return RedisStorageWithMetrics(**config)
    else:
        return RedisStorage(**config)
