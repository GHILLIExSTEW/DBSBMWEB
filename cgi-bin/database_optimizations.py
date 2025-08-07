
# Database Performance Optimizations

import asyncpg
from functools import lru_cache
import redis
import pickle

# Redis cache for frequently accessed data
redis_client = None

def get_redis_client():
    """Get or create Redis client for caching."""
    global redis_client
    if redis_client is None:
        try:
            redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=int(os.getenv('REDIS_DB', 0)),
                password=os.getenv('REDIS_PASSWORD'),
                decode_responses=False,  # We'll handle encoding
                socket_connect_timeout=5,
                socket_timeout=5,
                health_check_interval=30
            )
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            redis_client = None
    return redis_client

def cache_get(key, default=None):
    """Get value from Redis cache."""
    try:
        client = get_redis_client()
        if client:
            data = client.get(f"dbsbm:{key}")
            if data:
                return pickle.loads(data)
    except Exception as e:
        logger.error(f"Cache get error: {e}")
    return default

def cache_set(key, value, ttl=300):
    """Set value in Redis cache with TTL."""
    try:
        client = get_redis_client()
        if client:
            client.setex(f"dbsbm:{key}", ttl, pickle.dumps(value))
    except Exception as e:
        logger.error(f"Cache set error: {e}")

@lru_cache(maxsize=100)
def get_guild_settings_cached(guild_id):
    """Get guild settings with LRU cache."""
    cache_key = f"guild_settings:{guild_id}"
    
    # Try Redis first
    cached = cache_get(cache_key)
    if cached:
        return cached
    
    # Get from database
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT 
                    guild_id, guild_name, embed_channel_1, command_channel_1,
                    admin_channel_1, live_game_updates, units_display_mode,
                    min_units, max_units, embed_color, timezone
                FROM guild_settings 
                WHERE guild_id = %s
            """, (guild_id,))
            
            result = cursor.fetchone()
            if result:
                guild_data = dict(zip([desc[0] for desc in cursor.description], result))
                # Cache for 5 minutes
                cache_set(cache_key, guild_data, 300)
                return guild_data
        except Exception as e:
            logger.error(f"Database error getting guild settings: {e}")
        finally:
            connection.close()
    
    return None

def invalidate_guild_cache(guild_id):
    """Invalidate guild cache when data changes."""
    cache_key = f"guild_settings:{guild_id}"
    try:
        client = get_redis_client()
        if client:
            client.delete(f"dbsbm:{cache_key}")
        # Clear LRU cache
        get_guild_settings_cached.cache_clear()
    except Exception as e:
        logger.error(f"Cache invalidation error: {e}")

# Optimized database connection with pooling
class DatabasePool:
    def __init__(self):
        self.pool = None
    
    async def create_pool(self):
        """Create async database connection pool."""
        try:
            self.pool = await asyncpg.create_pool(
                host=os.getenv('POSTGRES_HOST', 'localhost'),
                port=int(os.getenv('POSTGRES_PORT', 5432)),
                user=os.getenv('POSTGRES_USER', 'postgres'),
                password=os.getenv('POSTGRES_PASSWORD'),
                database=os.getenv('POSTGRES_DB', 'DBSBM'),
                min_size=2,
                max_size=10,
                command_timeout=30,
                server_settings={
                    'application_name': 'DBSBM_Web',
                    'tcp_keepalives_idle': '600',
                    'tcp_keepalives_interval': '30',
                    'tcp_keepalives_count': '3',
                }
            )
            logger.info("Database pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
    
    async def get_connection(self):
        """Get connection from pool."""
        if self.pool is None:
            await self.create_pool()
        return await self.pool.acquire()
    
    async def release_connection(self, connection):
        """Release connection back to pool."""
        if self.pool:
            await self.pool.release(connection)

# Global database pool
db_pool = DatabasePool()

async def async_get_guild_settings(guild_id):
    """Async version of guild settings query."""
    cache_key = f"guild_settings:{guild_id}"
    
    # Try cache first
    cached = cache_get(cache_key)
    if cached:
        return cached
    
    # Get from database
    connection = await db_pool.get_connection()
    try:
        result = await connection.fetchrow("""
            SELECT 
                guild_id, guild_name, embed_channel_1, command_channel_1,
                admin_channel_1, live_game_updates, units_display_mode,
                min_units, max_units, embed_color, timezone
            FROM guild_settings 
            WHERE guild_id = $1
        """, guild_id)
        
        if result:
            guild_data = dict(result)
            cache_set(cache_key, guild_data, 300)
            return guild_data
        
    except Exception as e:
        logger.error(f"Async database error: {e}")
    finally:
        await db_pool.release_connection(connection)
    
    return None
