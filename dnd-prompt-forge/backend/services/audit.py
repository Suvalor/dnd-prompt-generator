"""
DND Prompt Forge - 审计日志服务
请求日志写入 SQLite
"""

import hashlib
from datetime import datetime, timezone
from typing import Optional

from models.database import db


def _hash_value(value: str) -> str:
    """对值进行 SHA-256 哈希。"""
    return hashlib.sha256(value.encode()).hexdigest()


def _sanitize_input(data: dict) -> str:
    """脱敏输入数据，生成摘要。"""
    safe_keys = ("output_type", "race", "class_role", "style", "mood", "target_model")
    summary_parts = []
    for key in safe_keys:
        if key in data:
            val = str(data[key])
            if len(val) > 100:
                val = val[:100] + "..."
            summary_parts.append(f"{key}={val}")
    return ", ".join(summary_parts)


def _sanitize_output(data: dict) -> str:
    """脱敏输出数据，生成摘要。"""
    return "fields=" + ", ".join(list(data.keys())[:10])


def log_request(
    request_id: str,
    ip: str,
    endpoint: str,
    input_data: dict,
    output_data: dict,
    status: str,
    error_message: str | None = None,
    duration_ms: int | None = None,
) -> None:
    """
    记录请求日志（脱敏后写入 SQLite）。

    Args:
        request_id: 请求追踪 ID
        ip: 客户端 IP（会被哈希）
        endpoint: 端点路径
        input_data: 输入数据（会被脱敏）
        output_data: 输出数据（会被脱敏）
        status: 状态（success / fallback / error）
        error_message: 错误信息（不含敏感数据）
        duration_ms: 请求耗时（毫秒）
    """
    ip_hash = _hash_value(ip)
    input_summary = _sanitize_input(input_data)
    output_summary = _sanitize_output(output_data)
    created_at = datetime.now(timezone.utc).isoformat()

    db.execute(
        """INSERT INTO request_logs
           (request_id, ip_hash, endpoint, input_summary, output_summary, status, error_message, duration_ms, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            request_id,
            ip_hash,
            endpoint,
            input_summary,
            output_summary,
            status,
            error_message,
            duration_ms or 0,
            created_at,
        ),
    )