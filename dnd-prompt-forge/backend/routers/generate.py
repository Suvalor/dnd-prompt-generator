"""
DND Prompt Forge - Generate 路由
核心端点：生成 DND 提示词
"""

import time
import uuid
import logging
from typing import Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from config import settings
from services.mimo_client import MiMoClient, MiMoClientError
from services.fallback import build_fallback_prompt
from services.quota import check_quota, increment_quota, persist_quota_usage, QuotaResult
from services.audit import log_request
from services.request_helpers import get_client_ip, get_session_id

logger = logging.getLogger(__name__)

router = APIRouter()


class GeneratePromptRequest(BaseModel):
    """生成提示词请求模型。"""

    output_type: str = Field(default="portrait", description="Type of output: portrait, fullbody, token, npc, monster, scene")
    race: str = Field(default="", description="Race or creature type")
    class_role: str = Field(default="", description="Class or role")
    style: str = Field(default="painterly", description="Visual style")
    mood: str = Field(default="brooding", description="Mood/atmosphere")
    description: str = Field(default="", description="Short description")
    alignment: Optional[str] = Field(default=None)
    weapon: Optional[str] = Field(default=None)
    background: Optional[str] = Field(default=None)
    target_model: str = Field(default="midjourney", description="Target AI model")
    gender: Optional[str] = Field(default=None)
    age: Optional[str] = Field(default=None)
    armor: Optional[str] = Field(default=None)
    magic: Optional[str] = Field(default=None)
    palette: Optional[str] = Field(default=None)
    camera: Optional[str] = Field(default=None)
    client_fingerprint_hash: Optional[str] = Field(default=None)
    fallback_prompt_preview: Optional[str] = Field(default=None)


class QuotaInfo(BaseModel):
    """配额信息。"""

    limit: int
    remaining: int
    reset_at: str


class GeneratePromptResponse(BaseModel):
    """生成提示词响应模型。"""

    mode: str
    request_id: str
    quota: QuotaInfo
    main_prompt: str
    short_prompt: str
    negative_prompt: str
    style_notes: str
    usage_tip: str


@router.post("/api/generate-prompt")
async def generate_prompt(req: GeneratePromptRequest, request: Request):
    """
    生成 D&D 提示词。优先 LLM，配额耗尽或 LLM 失败时 fallback。
    """
    request_id = str(uuid.uuid4())

    # 提取客户端标识
    ip = get_client_ip(request)
    session_id = get_session_id(request)
    fingerprint = req.client_fingerprint_hash or ""
    cookie = request.cookies.get("session_id", "")

    # 配额检查
    try:
        quota_result: QuotaResult = await check_quota(ip, fingerprint or None, session_id or None)
    except Exception:
        # 配额检查失败时允许请求
        quota_result = QuotaResult(allowed=True, limit=10, remaining=10, reset_at="")

    # 配额超限时仍返回 fallback（HTTP 200），但标记 quota.remaining=0
    if not quota_result.allowed:
        prompt_data = req.model_dump()
        result = build_fallback_prompt(prompt_data)
        await persist_quota_usage(
            request_id, ip, fingerprint or None, cookie or None,
            "/api/generate-prompt", "fallback",
        )
        log_request(
            request_id, ip, "/api/generate-prompt",
            prompt_data, result, "fallback", "Quota exceeded", 0,
        )
        return {
            "mode": "fallback",
            "request_id": request_id,
            "quota": {
                "limit": quota_result.limit,
                "remaining": 0,
                "reset_at": quota_result.reset_at,
            },
            "main_prompt": result["main_prompt"],
            "short_prompt": result["short_prompt"],
            "negative_prompt": result["negative_prompt"],
            "style_notes": result["style_notes"],
            "usage_tip": result["usage_tip"],
        }

    # 构建提示词数据
    prompt_data = req.model_dump()

    # 尝试 MiMo 生成
    start_time = time.monotonic()
    mode = "fallback"
    error_msg: Optional[str] = None

    mimo = MiMoClient()
    if mimo.is_available() and quota_result.allowed:
        try:
            result = await mimo.generate_prompt(prompt_data)
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            mode = "llm"

            await increment_quota(ip, fingerprint or None, cookie or None)
            await persist_quota_usage(
                request_id, ip, fingerprint or None, cookie or None,
                "/api/generate-prompt", "mimo",
            )
            log_request(
                request_id, ip, "/api/generate-prompt",
                prompt_data, result, "success", None, elapsed_ms,
            )

            return {
                "mode": mode,
                "request_id": request_id,
                "quota": {
                    "limit": quota_result.limit,
                    "remaining": max(0, quota_result.remaining - 1),
                    "reset_at": quota_result.reset_at,
                },
                "main_prompt": result["main_prompt"],
                "short_prompt": result["short_prompt"],
                "negative_prompt": result["negative_prompt"],
                "style_notes": result["style_notes"],
                "usage_tip": result["usage_tip"],
            }
        except MiMoClientError as e:
            error_msg = f"MiMo API not configured: {e}" if e.category == "no_api_key" else str(e)
            logger.warning("MiMo generation failed, falling back: %s", e)
        except Exception as e:
            error_msg = str(e)
            logger.warning("MiMo unexpected error, falling back: %s", e)

    # Fallback 生成
    result = build_fallback_prompt(prompt_data)
    elapsed_ms = int((time.monotonic() - start_time) * 1000)

    await increment_quota(ip, fingerprint or None, cookie or None)
    await persist_quota_usage(
        request_id, ip, fingerprint or None, cookie or None,
        "/api/generate-prompt", "fallback",
    )
    log_request(
        request_id, ip, "/api/generate-prompt",
        prompt_data, result, "fallback", error_msg, elapsed_ms,
    )

    return {
        "mode": "fallback",
        "request_id": request_id,
        "quota": {
            "limit": quota_result.limit,
            "remaining": max(0, quota_result.remaining - 1),
            "reset_at": quota_result.reset_at,
        },
        "main_prompt": result["main_prompt"],
        "short_prompt": result["short_prompt"],
        "negative_prompt": result["negative_prompt"],
        "style_notes": result["style_notes"],
        "usage_tip": result["usage_tip"],
    }