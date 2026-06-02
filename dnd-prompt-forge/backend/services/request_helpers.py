"""
DND Prompt Forge - 请求辅助函数
提取路由间共用的客户端标识提取逻辑
"""

from fastapi import Request, HTTPException

from services.session import verify_cookie


def get_client_ip(request: Request) -> str:
    """获取客户端 IP（支持 X-Forwarded-For 代理头）。"""
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def get_session_id(request: Request) -> str:
    """从 cookie 获取并验证 session_id，无效时抛出 401。"""
    session_cookie = request.cookies.get("session_id", "")
    if not session_cookie:
        raise HTTPException(status_code=401, detail="ERR_MISSING_SESSION")
    try:
        return verify_cookie(session_cookie)
    except Exception:
        raise HTTPException(status_code=401, detail="ERR_MISSING_SESSION")
