"""
DND Prompt Forge - 主应用入口
FastAPI 应用配置、中间件注册、路由挂载、生命周期管理
"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings, get_allowed_origins
from models.database import init_database
from middleware.csrf import CSRFMiddleware
from middleware.origin import OriginMiddleware
from routers import health, session, generate, feedback, memory_rules, quota


def configure_logging() -> None:
    """Configure application loggers so module logs appear in container stdout."""
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"))
        root_logger.addHandler(handler)
    root_logger.setLevel(level)
    for logger_name in ("services", "routers", "middleware", "models", "seo_worker"):
        logging.getLogger(logger_name).setLevel(level)


configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化数据库和 Redis，关闭时清理。"""
    # 初始化数据库
    init_database()
    logger.info("Database initialized at %s", settings.db_path)

    # 初始化 Redis 连接
    if settings.redis_enabled:
        try:
            import redis.asyncio as aioredis
            from services.quota import _redis_client

            # 通过模块级变量设置 Redis 连接
            import services.quota as quota_module
            quota_module._redis_client = aioredis.from_url(
                settings.redis_url,
                socket_timeout=5,
                decode_responses=True,
            )
            logger.info("Redis connected at %s", settings.redis_url)
        except Exception as e:
            logger.warning("Redis connection failed: %s", e)

    yield

    # 关闭 Redis 连接
    import services.quota as quota_module
    if quota_module._redis_client:
        await quota_module._redis_client.close()
        quota_module._redis_client = None
        logger.info("Redis connection closed")


app = FastAPI(
    title="DND Prompt Forge",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Origin 校验中间件
app.add_middleware(OriginMiddleware)

# CSRF 验证中间件
app.add_middleware(CSRFMiddleware)

# 注册路由
app.include_router(health.router)
app.include_router(session.router)
app.include_router(generate.router)
app.include_router(feedback.router)
app.include_router(memory_rules.router)
app.include_router(quota.router)


# 辅助函数（给测试使用的 get_redis）
async def get_redis_connection():
    """获取 Redis 连接。"""
    import services.quota as quota_module
    return quota_module._redis_client
