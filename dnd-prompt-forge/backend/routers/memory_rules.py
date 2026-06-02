"""
DND Prompt Forge - Memory Rules 路由
记忆规则管理（读取与更新）
"""

from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from models.database import db

router = APIRouter()


class RuleUpdate(BaseModel):
    """规则更新模型。"""

    rule_id: int
    action: str  # "activate", "deactivate", "delete"
    rule_text: str | None = None


class RuleResponse(BaseModel):
    """规则操作响应。"""

    updated: bool
    message: str


@router.get("/api/memory-rules")
async def list_memory_rules(status: str = "active"):
    """
    获取当前有效的记忆规则列表。
    """
    if status == "all":
        rules = db.fetchall("SELECT * FROM memory_rules ORDER BY created_at DESC")
    else:
        rules = db.fetchall(
            "SELECT * FROM memory_rules WHERE status = ? ORDER BY created_at DESC",
            (status,),
        )
    return {"rules": rules}


@router.post("/api/memory-rules", response_model=RuleResponse)
async def update_memory_rule(update: RuleUpdate):
    """
    更新记忆规则状态。
    """
    now = datetime.now(timezone.utc).isoformat()

    if update.action == "delete":
        db.execute("DELETE FROM memory_rules WHERE id = ?", (update.rule_id,))
    elif update.action == "activate":
        db.execute(
            "UPDATE memory_rules SET status = 'active', updated_at = ? WHERE id = ?",
            (now, update.rule_id),
        )
    elif update.action == "deactivate":
        db.execute(
            "UPDATE memory_rules SET status = 'inactive', updated_at = ? WHERE id = ?",
            (now, update.rule_id),
        )
    else:
        return RuleResponse(updated=False, message=f"Unknown action: {update.action}")

    return RuleResponse(updated=True, message=f"Rule {update.action}d successfully")