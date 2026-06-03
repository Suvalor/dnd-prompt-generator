"""
DND Prompt Forge - MiMo 客户端
OpenAI-compatible API 封装，JSON 输出验证
"""

import json
import logging
import re
import time
from typing import Dict, Optional

from openai import APIConnectionError, APIStatusError, APITimeoutError, AsyncOpenAI

from config import settings

logger = logging.getLogger(__name__)


def _chat_completions_endpoint() -> str:
    """Return the effective OpenAI-compatible chat completions URL."""
    return f"{settings.mimo_base_url.rstrip('/')}/chat/completions"


def _preview(value: str, limit: int = 500) -> str:
    """Return a compact single-line log preview without leaking huge payloads."""
    compact = " ".join((value or "").split())
    if len(compact) <= limit:
        return compact
    return compact[:limit] + "...[truncated]"


def _safe_model_dump(value) -> dict:
    """Best-effort dump for SDK response objects used only in diagnostics."""
    if value is None:
        return {}
    if hasattr(value, "model_dump"):
        try:
            return value.model_dump()
        except Exception:
            return {}
    if isinstance(value, dict):
        return value
    return {}


class MiMoClientError(Exception):
    """MiMo 客户端异常，包含错误类别。"""

    def __init__(self, message: str, category: str = "provider_error") -> None:
        """初始化异常。"""
        super().__init__(message)
        self.category = category


class MiMoClient:
    """MiMo LLM 客户端，封装 OpenAI-compatible API 调用。"""

    def __init__(self) -> None:
        """初始化客户端，根据配置创建 OpenAI 异步客户端。"""
        if settings.mimo_api_key:
            self._client = AsyncOpenAI(
                api_key=settings.mimo_api_key,
                base_url=settings.mimo_base_url,
                timeout=settings.llm_timeout_seconds,
            )
        else:
            self._client = None

    @property
    def client(self) -> Optional[AsyncOpenAI]:
        """获取底层 OpenAI 客户端实例。"""
        return self._client

    def is_available(self) -> bool:
        """检查 MiMo 客户端是否可用（已配置 API key）。"""
        return self._client is not None

    async def generate_prompt(self, prompt_data: dict) -> Dict[str, str]:
        """
        调用 MiMo API 生成 DND 提示词。

        Args:
            prompt_data: 包含生成参数的字典

        Returns:
            包含 main_prompt, short_prompt, negative_prompt, style_notes, usage_tip 的字典

        Raises:
            MiMoClientError: 当客户端不可用、API 调用失败或响应格式错误时
        """
        if not self.is_available():
            raise MiMoClientError("MiMo API not configured", category="no_api_key")

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(prompt_data)

        endpoint = _chat_completions_endpoint()
        prompt_preview = _preview(user_prompt)

        # ── 请求日志 ──
        logger.info(
            "LLM request start ▸ endpoint=%s base_url=%s model=%s max_tokens=%s timeout_seconds=%s prompt_chars=%s",
            endpoint,
            settings.mimo_base_url,
            settings.mimo_model,
            settings.mimo_max_completion_tokens,
            settings.llm_timeout_seconds,
            len(user_prompt),
        )
        logger.debug("LLM request ▸ system_prompt=%s", system_prompt)
        logger.info("LLM request prompt preview ▸ %s", prompt_preview)

        started_at = time.monotonic()
        try:
            response = await self._client.chat.completions.create(
                model=settings.mimo_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_completion_tokens=settings.mimo_max_completion_tokens,
                temperature=0.8,
                extra_body={"thinking": {"type": "disabled"}},
            )
        except APITimeoutError as e:
            elapsed_ms = int((time.monotonic() - started_at) * 1000)
            logger.error(
                "LLM request timeout ▸ endpoint=%s model=%s timeout_seconds=%s elapsed_ms=%s error_type=%s error=%s",
                endpoint,
                settings.mimo_model,
                settings.llm_timeout_seconds,
                elapsed_ms,
                type(e).__name__,
                e,
            )
            raise MiMoClientError(f"MiMo API timeout after {settings.llm_timeout_seconds}s", category="timeout") from e
        except APIStatusError as e:
            elapsed_ms = int((time.monotonic() - started_at) * 1000)
            response_text = getattr(e.response, "text", "") if getattr(e, "response", None) else ""
            logger.error(
                "LLM request HTTP error ▸ endpoint=%s model=%s status_code=%s elapsed_ms=%s response=%s",
                endpoint,
                settings.mimo_model,
                getattr(e, "status_code", None),
                elapsed_ms,
                _preview(response_text, 800),
            )
            raise MiMoClientError(
                f"MiMo API HTTP error: status={getattr(e, 'status_code', None)}",
                category="provider_http_error",
            ) from e
        except APIConnectionError as e:
            elapsed_ms = int((time.monotonic() - started_at) * 1000)
            logger.error(
                "LLM request connection error ▸ endpoint=%s model=%s elapsed_ms=%s error_type=%s error=%s",
                endpoint,
                settings.mimo_model,
                elapsed_ms,
                type(e).__name__,
                e,
            )
            raise MiMoClientError(f"MiMo API connection error: {e}", category="connection_error") from e
        except Exception as e:
            elapsed_ms = int((time.monotonic() - started_at) * 1000)
            logger.exception(
                "LLM request unexpected failure ▸ endpoint=%s model=%s elapsed_ms=%s error_type=%s",
                endpoint,
                settings.mimo_model,
                elapsed_ms,
                type(e).__name__,
            )
            raise MiMoClientError(f"MiMo API error: {e}", category="provider_error") from e
        elapsed_ms = int((time.monotonic() - started_at) * 1000)

        # 提取响应内容
        try:
            choice = response.choices[0]
            message = choice.message
            content = message.content or ""
        except (IndexError, AttributeError) as e:
            logger.error(
                "LLM response malformed ▸ endpoint=%s model=%s elapsed_ms=%s error_type=%s error=%s",
                endpoint,
                settings.mimo_model,
                elapsed_ms,
                type(e).__name__,
                e,
            )
            raise MiMoClientError(f"MiMo API error: {e}", category="provider_error") from e

        message_dump = _safe_model_dump(message)
        reasoning_content = message_dump.get("reasoning_content") or ""
        finish_reason = getattr(choice, "finish_reason", None)
        usage_dump = _safe_model_dump(getattr(response, "usage", None))
        completion_details = usage_dump.get("completion_tokens_details") or {}
        reasoning_tokens = completion_details.get("reasoning_tokens")

        # ── 响应日志 ──
        logger.info(
            "LLM response received ▸ endpoint=%s model=%s elapsed_ms=%s finish_reason=%s content_chars=%s reasoning_chars=%s reasoning_tokens=%s",
            endpoint,
            settings.mimo_model,
            elapsed_ms,
            finish_reason,
            len(content or ""),
            len(reasoning_content or ""),
            reasoning_tokens,
        )
        logger.debug("LLM response raw_content ▸ %s", content)
        if not content:
            logger.warning(
                "LLM response empty content ▸ endpoint=%s model=%s finish_reason=%s message=%s",
                endpoint,
                settings.mimo_model,
                finish_reason,
                _preview(json.dumps(message_dump, ensure_ascii=False, default=str), 1200),
            )
        if hasattr(response, "usage") and response.usage:
            logger.info(
                "LLM response ▸ usage: prompt_tokens=%s completion_tokens=%s total_tokens=%s",
                response.usage.prompt_tokens,
                response.usage.completion_tokens,
                response.usage.total_tokens,
            )

        # 剥离 LLM 返回的 markdown code fence 包裹
        content = content.strip()
        content = re.sub(r'^```(?:json)?\s*\n?', '', content)
        content = re.sub(r'\n?```\s*$', '', content.strip())

        # 解析 JSON
        try:
            result = json.loads(content)
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(
                "LLM response JSON parse failed ▸ endpoint=%s model=%s elapsed_ms=%s error=%s content_preview=%s",
                endpoint,
                settings.mimo_model,
                elapsed_ms,
                e,
                _preview(content, 800),
            )
            raise MiMoClientError(
                f"Failed to parse JSON from MiMo response: {e}",
                category="parse_error",
            ) from e

        # 验证响应字段
        validated = self._validate_response(result)
        logger.info("LLM response ▸ validated keys=%s", list(validated.keys()))
        return validated

    def _build_system_prompt(self) -> str:
        """构建系统提示词。"""
        return (
            "You are a DND prompt generator. Given a description of a DND character, token, "
            "monster, or scene, you generate a detailed image prompt suitable for AI image models. "
            "Output must be a JSON object with these keys: "
            "main_prompt (string, detailed image prompt), "
            "short_prompt (string, concise version under 80 words), "
            "negative_prompt (string, things to exclude), "
            "style_notes (string, art style suggestions), "
            "usage_tip (string, how to use the prompt effectively)."
        )

    def _build_user_prompt(self, data: dict) -> str:
        """构建用户提示词。"""
        parts = [f"Generate a DND prompt with these details:"]
        parts.append(f"- Output type: {data.get('output_type', 'portrait')}")
        parts.append(f"- Race/Creature: {data.get('race', '')}")
        parts.append(f"- Class/Role: {data.get('class_role', '')}")
        parts.append(f"- Style: {data.get('style', 'painterly')}")
        parts.append(f"- Mood: {data.get('mood', 'brooding')}")
        parts.append(f"- Description: {data.get('description', '')}")
        parts.append(f"- Target model: {data.get('target_model', 'midjourney')}")

        optional_fields = {
            "alignment": "Alignment",
            "weapon": "Weapon",
            "armor": "Armor",
            "magic": "Magic",
            "palette": "Color palette",
            "gender": "Gender",
            "age": "Age",
        }
        for field, label in optional_fields.items():
            if data.get(field):
                parts.append(f"- {label}: {data[field]}")

        return "\n".join(parts)

    def _validate_response(self, result: dict) -> Dict[str, str]:
        """
        验证 LLM 响应包含所有必需字段。

        Args:
            result: LLM 返回的字典

        Returns:
            验证后的字典，所有值转为字符串

        Raises:
            MiMoClientError: 当缺少必需字段时
        """
        required = {"main_prompt", "short_prompt", "negative_prompt", "style_notes", "usage_tip"}
        missing = required - set(result.keys())
        if missing:
            raise MiMoClientError(
                f"Missing required fields: {', '.join(sorted(missing))}",
                category="schema_error",
            )

        # 确保所有值为字符串类型
        for key in required:
            if not isinstance(result[key], str):
                result[key] = str(result[key])

        return result
