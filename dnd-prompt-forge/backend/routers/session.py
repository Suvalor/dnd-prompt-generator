"""
DND Prompt Forge - Session 路由
提供 bootstrap 端点，初始化 session cookie 和 CSRF token
"""

from fastapi import APIRouter, Response

from config import settings
from services.session import (
    generate_session_id,
    generate_csrf_token,
    sign_cookie,
    sign_csrf_token,
)

router = APIRouter()


@router.post("/api/session/bootstrap")
async def bootstrap_session(response: Response):
    """
    签发或刷新签名匿名 Session Cookie，返回 CSRF token。
    """
    session_id = generate_session_id()
    csrf_token = generate_csrf_token()

    # 签名 session cookie
    signed_session = sign_cookie(session_id)
    # 签名 CSRF token（绑定 session_id）
    signed_csrf = sign_csrf_token(session_id, csrf_token)

    # 设置 cookie（生产环境启用 secure）
    response.set_cookie(
        key="session_id",
        value=signed_session,
        httponly=True,
        samesite="lax",
        secure=settings.app_env == "production",
        max_age=86400 * 10,  # 10 天
    )

    return {
        "csrf_token": signed_csrf,
        "features": {
            "llm_enabled": bool(settings.mimo_api_key),
            "image_enabled": False,
            "video_enabled": False,
            "quota_limit": settings.llm_quota_limit,
            "quota_window_seconds": settings.llm_quota_window_seconds,
        },
    }