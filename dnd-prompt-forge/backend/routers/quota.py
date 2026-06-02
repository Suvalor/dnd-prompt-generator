"""
DND Prompt Forge - Quota 路由
配额查询端点
"""

from fastapi import APIRouter, Request
from pydantic import BaseModel

from services.quota import check_quota
from services.request_helpers import get_client_ip, get_session_id

router = APIRouter()


class QuotaResponse(BaseModel):
    """配额响应模型。"""

    limit: int
    remaining: int
    reset_at: str
    mode_available: str = "mimo"


@router.get("/api/quota", response_model=QuotaResponse)
async def get_quota(request: Request):
    """获取当前配额状态。"""
    ip = get_client_ip(request)
    session_id = get_session_id(request)

    headers = request.headers
    fingerprint = headers.get("x-fingerprint", "")

    quota_result = await check_quota(ip, fingerprint or None, session_id or None)

    mode_available = "mimo" if quota_result.allowed else "fallback"

    return QuotaResponse(
        limit=quota_result.limit,
        remaining=quota_result.remaining,
        reset_at=quota_result.reset_at,
        mode_available=mode_available,
    )