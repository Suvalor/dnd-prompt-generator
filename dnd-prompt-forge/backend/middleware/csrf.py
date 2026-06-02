"""
DND Prompt Forge - CSRF 验证中间件
验证 mutating 请求的 CSRF token
"""

import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from services.session import verify_cookie, verify_csrf

logger = logging.getLogger(__name__)


class CSRFMiddleware(BaseHTTPMiddleware):
    """CSRF 验证中间件，验证 mutating 请求的 CSRF token。"""

    async def dispatch(self, request: Request, call_next):
        """拦截请求，验证 CSRF token。"""
        path = request.url.path
        method = request.method

        # 安全方法（GET、HEAD、OPTIONS）跳过验证
        if method in ("GET", "HEAD", "OPTIONS"):
            return await call_next(request)

        # 白名单路径跳过验证
        if path in ("/api/session/bootstrap", "/api/health"):
            return await call_next(request)

        # 读取 CSRF header
        signed_csrf = request.headers.get("x-csrf-token", "")

        # 读取 session cookie
        session_cookie = request.cookies.get("session_id", "")

        # 缺少 CSRF header
        if not signed_csrf:
            return JSONResponse(
                status_code=403,
                content={"detail": "ERR_INVALID_CSRF"},
            )

        # 缺少 session cookie
        if not session_cookie:
            return JSONResponse(
                status_code=401,
                content={"detail": "ERR_MISSING_SESSION"},
            )

        # 验证 session cookie 签名
        try:
            session_id = verify_cookie(session_cookie)
        except (ValueError, Exception):
            return JSONResponse(
                status_code=401,
                content={"detail": "ERR_MISSING_SESSION"},
            )

        # 验证 CSRF token 格式（必须包含点）
        if "." not in signed_csrf:
            return JSONResponse(
                status_code=403,
                content={"detail": "ERR_INVALID_CSRF"},
            )

        # CSRF token 的格式：session_id:csrf_token 的签名
        # 从 signed_csrf 中提取 payload 部分（点前面的部分是原始值）
        # verify_csrf 需要原始的 session_id, csrf_token, 以及签名值
        # 但 CSRF header 中的格式是 sign_csrf_token(session_id, csrf_token) 的结果
        # 即 "{session_id}:{csrf_token}.{hmac_signature}"
        # 我们需要从签名值中提取 session_id 和 csrf_token

        # 先尝试提取 payload
        payload_part = signed_csrf.rsplit(".", 1)[0]
        if ":" not in payload_part:
            return JSONResponse(
                status_code=403,
                content={"detail": "ERR_INVALID_CSRF"},
            )

        # 从 payload 中提取 csrf_token
        csrf_token = payload_part.split(":", 1)[1]

        # 验证 CSRF 签名
        if not verify_csrf(session_id, csrf_token, signed_csrf):
            return JSONResponse(
                status_code=403,
                content={"detail": "ERR_INVALID_CSRF"},
            )

        return await call_next(request)