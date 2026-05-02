"""
Redis 缓存工具
提供异步缓存功能，提升 API 响应速度
"""
import json
import hashlib
from typing import Optional, Any, Callable
import asyncio
from functools import wraps
from redis import asyncio as aioredis

from app.core.config import settings
from app.core.logging import logger, log_performance_metric


class RedisCache:
    """Redis 缓存管理器"""

    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None
        self._connected = False

    async def connect(self):
        """建立 Redis 连接"""
        if self._connected:
            return

        try:
            self._redis = await aioredis.from_url(
                settings.REDIS_URL,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=3,    # 连接超时 3 秒（原 5 秒）
                socket_timeout=2,            # 操作超时 2 秒（新增）
                socket_keepalive=True,
                retry_on_timeout=True,       # 超时后自动重试一次
            )

            # 测试连接
            await self._redis.ping()
            self._connected = True
            logger.info(f"Redis 缓存已连接: {settings.REDIS_URL}")

        except Exception as e:
            logger.error(f"Redis 连接失败: {e}")
            self._redis = None
            self._connected = False

    async def disconnect(self):
        """关闭 Redis 连接"""
        if self._redis:
            await self._redis.close()
            self._connected = False
            logger.info("Redis 缓存已断开")

    async def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存的值，如果不存在则返回 None
        """
        if not self._connected or not self._redis:
            return None

        try:
            value = await self._redis.get(key)
            if value:
                log_performance_metric("cache_hit", 1, "count")
                return json.loads(value)
            else:
                log_performance_metric("cache_miss", 1, "count")
                return None

        except Exception as e:
            logger.error(f"获取缓存失败 [{key}]: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> bool:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            expire: 过期时间（秒），None 表示使用默认值

        Returns:
            是否设置成功
        """
        if not self._connected or not self._redis:
            return False

        try:
            expire_time = expire if expire is not None else settings.CACHE_EXPIRE_SECONDS

            # 序列化为 JSON
            serialized_value = json.dumps(value, ensure_ascii=False)

            # 设置缓存
            await self._redis.setex(key, expire_time, serialized_value)

            logger.debug(f"缓存已设置: {key} (过期: {expire_time}s)")
            return True

        except Exception as e:
            logger.error(f"设置缓存失败 [{key}]: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        删除缓存

        Args:
            key: 缓存键

        Returns:
            是否删除成功
        """
        if not self._connected or not self._redis:
            return False

        try:
            await self._redis.delete(key)
            logger.debug(f"缓存已删除: {key}")
            return True

        except Exception as e:
            logger.error(f"删除缓存失败 [{key}]: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """
        批量删除匹配模式的缓存

        Args:
            pattern: 键模式（支持通配符 *）

        Returns:
            删除的键数量
        """
        if not self._connected or not self._redis:
            return 0

        try:
            keys = []
            async for key in self._redis.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                deleted = await self._redis.delete(*keys)
                logger.info(f"批量删除缓存: {pattern} ({deleted} 个)")
                return deleted

            return 0

        except Exception as e:
            logger.error(f"批量删除缓存失败 [{pattern}]: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """
        检查键是否存在

        Args:
            key: 缓存键

        Returns:
            是否存在
        """
        if not self._connected or not self._redis:
            return False

        try:
            return await self._redis.exists(key) > 0
        except Exception as e:
            logger.error(f"检查缓存失败 [{key}]: {e}")
            return False

    async def get_ttl(self, key: str) -> Optional[int]:
        """
        获取键的剩余生存时间

        Args:
            key: 缓存键

        Returns:
            剩余秒数，-1 表示永久，-2 表示不存在
        """
        if not self._connected or not self._redis:
            return None

        try:
            return await self._redis.ttl(key)
        except Exception as e:
            logger.error(f"获取TTL失败 [{key}]: {e}")
            return None


# 全局缓存实例
cache = RedisCache()


def generate_cache_key(*args, **kwargs) -> str:
    """
    生成缓存键

    Args:
        *args: 位置参数
        **kwargs: 关键字参数

    Returns:
        MD5 哈希的缓存键
    """
    key_data = json.dumps(
        {"args": args, "kwargs": kwargs},
        sort_keys=True,
        ensure_ascii=False
    )
    return hashlib.md5(key_data.encode()).hexdigest()


def cached(
    expire: Optional[int] = None,
    key_prefix: str = "",
    key_builder: Optional[Callable] = None
):
    """
    缓存装饰器

    Args:
        expire: 过期时间（秒）
        key_prefix: 键前缀
        key_builder: 自定义键生成函数

    示例:
        @cached(expire=3600, key_prefix="punctuation")
        async def punctuate_text(text: str):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 检查缓存是否可用
            if not cache._connected:
                logger.debug(f"缓存不可用，直接执行函数: {func.__name__}")
                return await func(*args, **kwargs)

            # 生成缓存键
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = generate_cache_key(*args, **kwargs)

            # 添加前缀
            full_key = f"{key_prefix}:{func.__name__}:{cache_key}" if key_prefix else f"{func.__name__}:{cache_key}"

            # 尝试获取缓存
            cached_result = await cache.get(full_key)
            if cached_result is not None:
                logger.debug(f"缓存命中: {full_key}")
                return cached_result

            # 执行函数
            logger.debug(f"缓存未命中，执行函数: {func.__name__}")
            result = await func(*args, **kwargs)

            # 保存缓存
            await cache.set(full_key, result, expire)

            return result

        return wrapper

    return decorator


async def init_cache():
    """初始化缓存连接（在应用启动时调用）"""
    await cache.connect()


async def close_cache():
    """关闭缓存连接（在应用关闭时调用）"""
    await cache.disconnect()


# 导出
__all__ = [
    "cache",
    "cached",
    "generate_cache_key",
    "init_cache",
    "close_cache",
    "RedisCache"
]
