import json
import asyncio
import redis.asyncio as redis
from typing import Dict, Any, Callable, List, Optional
from redis.asyncio import ConnectionPool
from .config import get_settings
from .logging_config import get_logger

logger = get_logger("redis_client")


class RedisPublisher:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def publish_event(self, channel: str, event_data: Dict[str, Any]) -> bool:
        try:
            serialized_data = json.dumps(event_data)
            result = await self.redis.publish(channel, serialized_data)
            logger.info(f"Published event to channel {channel}", {
                "channel": channel,
                "subscribers": result,
                "event_type": event_data.get("event_type", "unknown")
            })
            return result > 0
        except Exception as e:
            logger.error(f"Failed to publish event to {channel}: {e}", {
                "channel": channel,
                "error": str(e),
                "event_data": event_data
            })
            return False


class RedisSubscriber:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.pubsub = None
        self.running = False
    
    async def subscribe_to_events(self, channels: List[str], callback: Callable[[str, Dict[str, Any]], None]):
        try:
            self.pubsub = self.redis.pubsub()
            await self.pubsub.subscribe(*channels)
            self.running = True
            
            logger.info(f"Subscribed to channels: {channels}")
            
            async for message in self.pubsub.listen():
                if not self.running:
                    break
                
                if message["type"] == "message":
                    try:
                        channel = message["channel"].decode("utf-8")
                        data = json.loads(message["data"].decode("utf-8"))
                        await callback(channel, data)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to decode message from {channel}: {e}")
                    except Exception as e:
                        logger.error(f"Error processing message from {channel}: {e}")
        
        except Exception as e:
            logger.error(f"Subscription error: {e}")
            raise
        finally:
            if self.pubsub:
                await self.pubsub.unsubscribe()
                await self.pubsub.close()
    
    async def stop(self):
        self.running = False
        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()


class RedisClient:
    def __init__(self):
        self.settings = get_settings()
        self.pool = None
        self.redis = None
        self.publisher = None
        self.subscriber = None
    
    async def connect(self):
        try:
            self.pool = ConnectionPool(
                host=self.settings.redis.host,
                port=self.settings.redis.port,
                db=self.settings.redis.db,
                password=self.settings.redis.password,
                decode_responses=False,
                max_connections=20,
                retry_on_timeout=True
            )
            
            self.redis = redis.Redis(connection_pool=self.pool)
            self.publisher = RedisPublisher(self.redis)
            self.subscriber = RedisSubscriber(self.redis)
            
            await self.health_check()
            logger.info("Redis connection established successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self):
        try:
            if self.subscriber:
                await self.subscriber.stop()
            if self.redis:
                await self.redis.close()
            if self.pool:
                await self.pool.disconnect()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")
    
    async def health_check(self) -> bool:
        try:
            await self.redis.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    
    async def publish_event(self, channel: str, event_data: Dict[str, Any]) -> bool:
        if not self.publisher:
            logger.error("Publisher not initialized")
            return False
        return await self.publisher.publish_event(channel, event_data)
    
    async def subscribe_to_events(self, channels: List[str], callback: Callable[[str, Dict[str, Any]], None]):
        if not self.subscriber:
            logger.error("Subscriber not initialized")
            return
        await self.subscriber.subscribe_to_events(channels, callback)


_redis_client = None


async def get_redis_client() -> RedisClient:
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
        await _redis_client.connect()
    return _redis_client


async def close_redis_client():
    global _redis_client
    if _redis_client:
        await _redis_client.disconnect()
        _redis_client = None