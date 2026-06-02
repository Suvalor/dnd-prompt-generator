"""
DND Prompt Forge - 配额服务
Redis 三维度配额检查与递增，SQLite 持久化
"""

import hashlib
import logging
import time
from datetime import datetime, timezone
from typing import Optional

import redis.asyncio as aioredis

from config import settings
from models.database import db

logger = logging.getLogger(__name__)

# Redis 全局连接
_redis_client: Optional[aioredis.Redis] = None


def get_redis() -> Optional[aioredis.Redis]:
    """获取 Redis 连接实例，未初始化时返回 None。"""
    return _redis_client


def _get_hour_bucket() -> str:
    """获取当前小时桶标识（用于配额时间窗口）。"""
    now = int(time.time())
    return str(now // 3600 * 3600)


def _hash_identifier(value: str) -> str:
    """对标识符进行哈希，返回 16 位十六进制字符串。"""
    return hashlib.sha256(value.encode()).hexdigest()[:16]


def _reset_time(bucket: str) -> str:
    """计算配额重置时间（当前小时桶结束时间）。"""
    bucket_int = int(bucket)
    # 当前窗口结束时间（下一个小时的开始）
    window = 3600
    ts = datetime.fromtimestamp(bucket_int + window, tz=timezone.utc)
    return ts.isoformat()


class QuotaResult:
    """配额检查结果数据类。"""

    def __init__(self, allowed: bool, limit: int, remaining: int, reset_at: str) -> None:
        """初始化配额结果。"""
        self.allowed = allowed
        self.limit = limit
        self.remaining = remaining
        self.reset_at = reset_at


async def check_quota(
    ip: str,
    fingerprint: str | None = None,
    cookie: str | None = None,
    limit: int | None = None,
) -> QuotaResult:
    """
    检查三维度配额（IP / fingerprint / cookie）。

    Args:
        ip: 客户端 IP
        fingerprint: 浏览器指纹哈希
        cookie: 会话 cookie 哈希
        limit: 配额上限（默认使用配置值）

    Returns:
        QuotaResult 包含 allowed/limit/remaining/reset_at
    """
    bucket = _get_hour_bucket()
    actual_limit = limit or settings.llm_quota_limit

    ip_hash = _hash_identifier(ip)
    fp_hash = _hash_identifier(fingerprint) if fingerprint else None
    ck_hash = _hash_identifier(cookie) if cookie else None

    r = get_redis()

    if r is not None:
        # Redis 路径：三维度滑动窗口，取最大计数
        try:
            ip_key = f"quota:ip:{ip_hash}:{bucket}"
            ip_count = int(await r.get(ip_key) or 0)

            fp_count = 0
            if fp_hash:
                fp_key = f"quota:fp:{fp_hash}:{bucket}"
                fp_count = int(await r.get(fp_key) or 0)

            ck_count = 0
            if ck_hash:
                ck_key = f"quota:ck:{ck_hash}:{bucket}"
                ck_count = int(await r.get(ck_key) or 0)

            max_count = max(ip_count, fp_count, ck_count)

            if max_count >= actual_limit:
                return QuotaResult(
                    allowed=False,
                    limit=actual_limit,
                    remaining=0,
                    reset_at=_reset_time(bucket),
                )

            remaining = actual_limit - max_count
            return QuotaResult(
                allowed=True,
                limit=actual_limit,
                remaining=remaining,
                reset_at=_reset_time(bucket),
            )
        except Exception as e:
            logger.warning("Redis read error, falling back to SQLite: %s", e)
            return await _check_quota_sqlite(ip, fingerprint, cookie, actual_limit, bucket)
    else:
        # SQLite 回退
        return await _check_quota_sqlite(ip, fingerprint, cookie, actual_limit, bucket)


async def _check_quota_sqlite(
    ip: str,
    fingerprint: str | None,
    cookie: str | None,
    limit: int,
    bucket: str,
) -> QuotaResult:
    """SQLite 回退：检查三维度配额，取最大计数。"""
    window_start = datetime.fromtimestamp(int(bucket), tz=timezone.utc).isoformat()
    ip_hash = _hash_identifier(ip)
    fp_hash = _hash_identifier(fingerprint) if fingerprint else None
    ck_hash = _hash_identifier(cookie) if cookie else None

    # 查询 IP 维度计数
    result = db.fetchone(
        "SELECT COUNT(*) as cnt FROM quota_usage WHERE ip_hash = ? AND created_at > ?",
        (ip_hash, window_start),
    )
    ip_count = result["cnt"] if result else 0

    # 查询 fingerprint 维度计数
    fp_count = 0
    if fp_hash:
        result = db.fetchone(
            "SELECT COUNT(*) as cnt FROM quota_usage WHERE fingerprint_hash = ? AND created_at > ?",
            (fp_hash, window_start),
        )
        fp_count = result["cnt"] if result else 0

    # 查询 cookie 维度计数
    ck_count = 0
    if ck_hash:
        result = db.fetchone(
            "SELECT COUNT(*) as cnt FROM quota_usage WHERE cookie_hash = ? AND created_at > ?",
            (ck_hash, window_start),
        )
        ck_count = result["cnt"] if result else 0

    max_count = max(ip_count, fp_count, ck_count)

    if max_count >= limit:
        return QuotaResult(
            allowed=False,
            limit=limit,
            remaining=0,
            reset_at=_reset_time(bucket),
        )

    remaining = limit - max_count
    return QuotaResult(
        allowed=True,
        limit=limit,
        remaining=remaining,
        reset_at=_reset_time(bucket),
    )


async def increment_quota(
    ip: str,
    fingerprint: str | None = None,
    cookie: str | None = None,
) -> None:
    """
    递增三维度配额计数。

    Args:
        ip: 客户端 IP
        fingerprint: 浏览器指纹哈希
        cookie: 会话 cookie 哈希
    """
    bucket = _get_hour_bucket()
    ttl = settings.llm_quota_window_seconds

    r = get_redis()

    if r is not None:
        try:
            ip_hash = _hash_identifier(ip)
            fp_hash = _hash_identifier(fingerprint) if fingerprint else None
            ck_hash = _hash_identifier(cookie) if cookie else None

            keys = []
            if ip_hash:
                keys.append(f"quota:ip:{ip_hash}:{bucket}")
            if fp_hash:
                keys.append(f"quota:fp:{fp_hash}:{bucket}")
            if ck_hash:
                keys.append(f"quota:ck:{ck_hash}:{bucket}")

            for key in keys:
                await r.incr(key)
                await r.expire(key, ttl)
        except Exception as e:
            logger.warning("Redis increment error: %s", e)
            # Redis 错误不应阻塞请求
    else:
        # SQLite 回退：不需要显式递增，record_quota_usage 时写入
        pass


async def persist_quota_usage(
    request_id: str,
    ip: str,
    fingerprint: str | None = None,
    cookie: str | None = None,
    endpoint: str = "/api/generate-prompt",
    mode: str = "mimo",
) -> None:
    """将配额使用记录持久化到 SQLite。"""
    ip_hash = _hash_identifier(ip)
    fp_hash = _hash_identifier(fingerprint) if fingerprint else None
    ck_hash = _hash_identifier(cookie) if cookie else None
    created_at = datetime.now(timezone.utc).isoformat()

    db.execute(
        """INSERT INTO quota_usage
           (request_id, ip_hash, fingerprint_hash, cookie_hash, endpoint, mode, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (request_id, ip_hash, fp_hash, ck_hash, endpoint, mode, created_at),
    )