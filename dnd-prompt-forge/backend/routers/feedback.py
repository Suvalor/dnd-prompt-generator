"""
DND Prompt Forge - Feedback 路由
用户反馈提交与记忆规则更新
"""

from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel, Field

from models.database import db

router = APIRouter()


class FeedbackRequest(BaseModel):
    """反馈请求模型。"""

    request_id: str = Field(description="关联的请求 ID")
    feedback: str = Field(description="反馈类型: useful / not_useful")
    reason: str | None = Field(default=None, description="反馈原因")
    comment: str | None = Field(default=None, description="详细评论")


class FeedbackResponse(BaseModel):
    """反馈响应模型。"""

    saved: bool
    message: str


@router.post("/api/feedback", response_model=FeedbackResponse)
async def submit_feedback(req: FeedbackRequest):
    """
    提交用户反馈，更新记忆规则。
    """
    now = datetime.now(timezone.utc).isoformat()

    # 存储反馈事件
    db.execute(
        """INSERT INTO feedback_events
           (created_at, request_id, feedback, reason, comment)
           VALUES (?, ?, ?, ?, ?)""",
        (now, req.request_id, req.feedback, req.reason, req.comment),
    )

    # 对负面反馈更新记忆规则
    if req.feedback == "not_useful" and req.reason:
        existing = db.fetchone(
            "SELECT id, times_seen FROM memory_rules WHERE rule_key = ?",
            (req.reason,),
        )
        if existing:
            db.execute(
                "UPDATE memory_rules SET times_seen = times_seen + 1, updated_at = ? WHERE id = ?",
                (now, existing["id"]),
            )
        else:
            db.execute(
                """INSERT INTO memory_rules
                   (created_at, updated_at, status, rule_key, rule_text, trigger_reason, version)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (now, now, "active", req.reason, f"Auto-generated rule for: {req.reason}", req.comment or "", "v1"),
            )

    return FeedbackResponse(saved=True, message="Thanks. Future prompts will use this feedback.")