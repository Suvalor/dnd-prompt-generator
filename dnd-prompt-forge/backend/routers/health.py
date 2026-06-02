"""
DND Prompt Forge - 健康检查路由
"""

from fastapi import APIRouter

from config import settings
from services.quota import get_redis

router = APIRouter()


@router.get("/api/health")
async def health_check():
    """
    健康检查端点。
    """
    # 检查 Redis 连接
    redis_status = "unavailable"
    try:
        r = await get_redis()
        if r:
            await r.ping()
            redis_status = "ok"
    except Exception:
        redis_status = "degraded"

    return {
        "ok": True,
        "version": "1.0.0",
        "services": {
            "database": True,
            "redis": redis_status,
        },
    }