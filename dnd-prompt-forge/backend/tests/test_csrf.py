"""
DND Prompt Forge - CSRF 中间件验证测试
"""

import pytest
from unittest.mock import MagicMock, patch
from starlette.requests import Request
from starlette.responses import JSONResponse
from middleware.csrf import CSRFMiddleware
from services.session import generate_session_id, generate_csrf_token, sign_cookie, sign_csrf_token


class TestCSRFDispatch:
    """测试 CSRF 中间件 dispatch 逻辑。"""

    async def _create_request(self, method="POST", path="/api/generate-prompt", headers=None, cookies=None):
        """创建模拟请求对象。"""
        scope = {
            "type": "http",
            "method": method,
            "url": f"http://localhost:8000{path}",
            "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()],
            "path": path,
        }
        request = Request(scope, receive=lambda: {"type": "http.request", "body": b""})
        # 手动设置 cookies
        request._cookies = cookies or {}
        return request

    @pytest.mark.asyncio
    async def test_skips_get_requests(self):
        """GET 请求应跳过 CSRF 验证。"""
        middleware = CSRFMiddleware(None)
        request = await self._create_request(method="GET")
        call_next_called = False

        async def call_next(req):
            nonlocal call_next_called
            call_next_called = True
            return JSONResponse({"ok": True})

        response = await middleware.dispatch(request, call_next)
        assert call_next_called is True
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_skips_bootstrap_endpoint(self):
        """/api/session/bootstrap 应跳过 CSRF 验证。"""
        middleware = CSRFMiddleware(None)
        request = await self._create_request(path="/api/session/bootstrap")
        call_next_called = False

        async def call_next(req):
            nonlocal call_next_called
            call_next_called = True
            return JSONResponse({"ok": True})

        response = await middleware.dispatch(request, call_next)
        assert call_next_called is True

    @pytest.mark.asyncio
    async def test_rejects_missing_csrf_header(self):
        """缺少 X-CSRF-Token 头应返回 403。"""
        middleware = CSRFMiddleware(None)
        request = await self._create_request()

        async def call_next(req):
            return JSONResponse({"ok": True})

        response = await middleware.dispatch(request, call_next)
        assert response.status_code == 403
        body = response.body
        assert b"ERR_INVALID_CSRF" in body

    @pytest.mark.asyncio
    async def test_rejects_missing_session_cookie(self):
        """缺少 session cookie 应返回 401。"""
        middleware = CSRFMiddleware(None)
        request = await self._create_request(headers={"X-CSRF-Token": "some-token"})

        async def call_next(req):
            return JSONResponse({"ok": True})

        response = await middleware.dispatch(request, call_next)
        assert response.status_code == 401
        body = response.body
        assert b"ERR_MISSING_SESSION" in body

    @pytest.mark.asyncio
    async def test_rejects_invalid_session_cookie(self):
        """无效的 session cookie 应返回 401。"""
        middleware = CSRFMiddleware(None)
        request = await self._create_request(
            headers={"X-CSRF-Token": "some-token"},
            cookies={"session_id": "invalid-signed-value"},
        )

        async def call_next(req):
            return JSONResponse({"ok": True})

        response = await middleware.dispatch(request, call_next)
        assert response.status_code == 401
        body = response.body
        assert b"ERR_MISSING_SESSION" in body

    @pytest.mark.asyncio
    async def test_rejects_invalid_csrf_format(self):
        """CSRF token 格式无效应返回 403。"""
        session_id = generate_session_id()
        signed_session = sign_cookie(session_id)

        middleware = CSRFMiddleware(None)
        request = await self._create_request(
            headers={"X-CSRF-Token": "no-dot-format"},
            cookies={"session_id": signed_session},
        )

        async def call_next(req):
            return JSONResponse({"ok": True})

        response = await middleware.dispatch(request, call_next)
        assert response.status_code == 403
        body = response.body
        assert b"ERR_INVALID_CSRF" in body

    @pytest.mark.asyncio
    async def test_accepts_valid_csrf(self):
        """有效的 CSRF token 和 session 应通过验证。"""
        session_id = generate_session_id()
        csrf_token = generate_csrf_token()
        signed_session = sign_cookie(session_id)
        signed_csrf = sign_csrf_token(session_id, csrf_token)

        middleware = CSRFMiddleware(None)
        request = await self._create_request(
            headers={"X-CSRF-Token": signed_csrf},
            cookies={"session_id": signed_session},
        )

        call_next_called = False

        async def call_next(req):
            nonlocal call_next_called
            call_next_called = True
            return JSONResponse({"ok": True})

        response = await middleware.dispatch(request, call_next)
        assert call_next_called is True
        assert response.status_code == 200
