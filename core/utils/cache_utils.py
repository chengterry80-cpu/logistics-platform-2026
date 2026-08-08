"""
Redis 缓存工具函数

提供统一的缓存读写、通配符删除、键生成能力，
所有缓存操作均带降级处理：Redis 不可用时自动回退到数据库查询。
"""

import logging
import hashlib
import json
from typing import Any, Callable, Optional

from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


def cache_key(prefix: str, *args, **kwargs) -> str:
    """
    统一生成缓存键，格式: {app}:{model}:{params}

    Examples:
        cache_key('vehicle', 'available')          -> 'core:vehicle:available'
        cache_key('quote', 'request', 123)         -> 'core:quote:request:123'
        cache_key('request', status='pending')     -> 'core:request:status=pending'
    """
    parts = ['core', prefix]
    parts.extend(str(arg) for arg in args if arg is not None)
    if kwargs:
        # 按 key 排序确保稳定
        sorted_kwargs = sorted(kwargs.items())
        kv_str = '&'.join(f'{k}={v}' for k, v in sorted_kwargs)
        parts.append(kv_str)
    return ':'.join(parts)


def get_or_set_cache(key: str, func: Callable[[], Any], timeout: Optional[int] = None) -> Any:
    """
    从缓存获取数据，若不存在则调用 func 计算并填充缓存。

    带降级处理：Redis 不可用时直接调用 func 返回结果。

    Args:
        key: 缓存键
        func: 无参可调用对象，返回可序列化的数据
        timeout: 缓存超时时间（秒），None 使用默认值

    Returns:
        缓存或新计算的数据
    """
    try:
        cached = cache.get(key)
        if cached is not None:
            logger.info('CACHE HIT: %s', key)
            return cached
    except Exception as e:
        logger.warning('Cache read failed for key=%s, falling back to DB: %s', key, e)
        return func()

    logger.info('CACHE MISS: %s', key)
    data = func()

    try:
        cache.set(key, data, timeout=timeout)
    except Exception as e:
        logger.warning('Cache write failed for key=%s: %s', key, e)

    return data


def delete_cache(key: str) -> bool:
    """删除单个缓存键，带降级处理。"""
    try:
        cache.delete(key)
        logger.info('CACHE DELETE: %s', key)
        return True
    except Exception as e:
        logger.warning('Cache delete failed for key=%s: %s', key, e)
        return False


def delete_cache_pattern(pattern: str) -> int:
    """
    支持通配符删除缓存。

    使用 Redis SCAN 遍历匹配的键并批量删除，
    避免使用 KEYS 命令造成阻塞。

    Args:
        pattern: 通配符模式，如 'core:vehicle:*'

    Returns:
        删除的键数量
    """
    try:
        from django_redis import get_redis_connection
        redis_conn = get_redis_connection('default')

        # 构建带 KEY_PREFIX 的完整模式
        key_prefix = getattr(settings, 'CACHES', {}).get('default', {}).get('KEY_PREFIX', '')
        full_pattern = f'{key_prefix}:{pattern}' if key_prefix else pattern

        deleted = 0
        # 使用 SCAN 批量查找并删除，避免 KEYS 阻塞
        for key in redis_conn.scan_iter(match=full_pattern, count=100):
            redis_conn.delete(key)
            deleted += 1

        if deleted > 0:
            logger.info('CACHE PATTERN DELETE: %s (%d keys)', pattern, deleted)
        return deleted
    except Exception as e:
        logger.warning('Cache pattern delete failed for pattern=%s: %s', pattern, e)
        return 0


def generate_list_cache_key(prefix: str, user_id: int, params: dict) -> str:
    """
    为列表接口生成带查询参数的缓存键。

    将查询参数序列化为稳定的哈希值，避免键过长。

    Args:
        prefix: 缓存前缀（如 'vehicle', 'request'）
        user_id: 用户ID（不同用户缓存隔离）
        params: 查询参数字典

    Returns:
        格式: core:{prefix}:list:{user_id}:{hash}
    """
    # 过滤掉空值和排序
    filtered = {k: v for k, v in sorted(params.items()) if v is not None}
    param_str = json.dumps(filtered, sort_keys=True, default=str)
    param_hash = hashlib.md5(param_str.encode('utf-8')).hexdigest()[:12]
    return cache_key(prefix, 'list', user_id, param_hash)
