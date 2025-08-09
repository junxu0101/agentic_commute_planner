"""
Redis service for event-driven job processing and pub/sub messaging
"""

import json
import logging
from typing import Dict, Any, Optional

import redis.asyncio as redis
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class RedisService:
    """Redis service for job queue and pub/sub messaging"""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis: Optional[Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        
    async def connect(self) -> None:
        """Connect to Redis"""
        try:
            self.redis = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30
            )
            
            # Test connection
            await self.redis.ping()
            logger.info(f"Connected to Redis at {self.redis_url}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
            
    async def disconnect(self) -> None:
        """Disconnect from Redis"""
        if self.pubsub:
            await self.pubsub.close()
            
        if self.redis:
            await self.redis.close()
            logger.info("Disconnected from Redis")
            
    async def push_job(self, queue_name: str, job_data: Dict[str, Any]) -> None:
        """Push a job to the queue"""
        if not self.redis:
            raise RuntimeError("Redis not connected")
            
        job_json = json.dumps(job_data)
        await self.redis.lpush(queue_name, job_json)
        logger.info(f"Pushed job to queue {queue_name}: {job_data.get('job_id', 'unknown')}")
        
    async def pop_job(self, queue_name: str, timeout: int = 0) -> Optional[Dict[str, Any]]:
        """Pop a job from the queue using blocking pop (BRPOP)"""
        if not self.redis:
            raise RuntimeError("Redis not connected")
            
        try:
            # BRPOP returns tuple (queue_name, value) or None
            result = await self.redis.brpop(queue_name, timeout=timeout)
            if result:
                _, job_json = result
                job_data = json.loads(job_json)
                logger.info(f"Popped job from queue {queue_name}: {job_data.get('job_id', 'unknown')}")
                return job_data
            return None
            
        except Exception as e:
            logger.error(f"Error popping job from queue {queue_name}: {e}")
            return None
            
    async def publish_progress(self, channel: str, progress_data: Dict[str, Any]) -> None:
        """Publish progress update to a channel"""
        if not self.redis:
            raise RuntimeError("Redis not connected")
            
        progress_json = json.dumps(progress_data)
        await self.redis.publish(channel, progress_json)
        logger.debug(f"Published progress to channel {channel}: {progress_data}")
        
    async def subscribe_to_progress(self, channel: str) -> redis.client.PubSub:
        """Subscribe to progress updates"""
        if not self.redis:
            raise RuntimeError("Redis not connected")
            
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(channel)
        logger.info(f"Subscribed to progress channel: {channel}")
        return pubsub
        
    async def get_queue_length(self, queue_name: str) -> int:
        """Get the current length of a queue"""
        if not self.redis:
            raise RuntimeError("Redis not connected")
            
        return await self.redis.llen(queue_name)
        
    async def health_check(self) -> bool:
        """Check Redis connection health"""
        if not self.redis:
            return False
            
        try:
            await self.redis.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False