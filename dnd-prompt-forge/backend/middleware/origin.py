"""
DND Prompt Forge - Origin 校验中间件
验证请求 Origin/Referer，防止 CSRF
"""

import logging
from urllib.parse import urlparse

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from config import get_allowed_origins

logger = logging.getLogger(__name__)


class OriginMiddleware(BaseHTTPMiddleware):
    """Origin 校验中间件，验证请求来源。"""

    def __init__(self, app) -> None:
        """初始化中间件，获取允许的 Origin 列表。"""
        super().__init__(app)
        self.allowed_origins = get_allowed_origins()

    async def dispatch(self, request: Request, call_next):
        """拦截请求，验证 Origin/Referer。"""
        method = request.method
        path = request.url.path

        # 安全方法不需要校验
        if method in ("GET", "HEAD", "OPTIONS"):
            return await call_next(request)

        # 白名单路径跳过
        if path in ("/api/session/bootstrap", "/api/health"):
            return await call_next(request)

        # 读取 Origin 或 Referer
        origin = request.headers.get("origin", "")
        if not origin:
            referer = request.headers.get("referer", "")
            if referer:
                try:
                    parsed = urlparse(referer)
                    origin = f"{parsed.scheme}://{parsed.netloc}"
                except Exception:
                    origin = ""
            else:
                # 无 Origin/Referer header，拒绝
                return JSONResponse(
                    status_code=403,
                    content={"detail": "ERR_INVALID_ORIGIN", "error": "Missing Origin/Referer header"},
                )

        # 校验 Origin 是否在允许列表中
        allowed = False
        for allowed_origin in self.allowed_origins:
            try:
                allowed_parsed = urlparse(allowed_origin)
                origin_netloc = urlparse(origin).netloc
                if origin_netloc == allowed_parsed.netloc:
                    allowed = True
                    break
            except Exception:
                continue

        if not allowed:
            return JSONResponse(
                status_code=403,
                content={"detail": "ERR_INVALID_ORIGIN"},
            )

        return await call_next(request)