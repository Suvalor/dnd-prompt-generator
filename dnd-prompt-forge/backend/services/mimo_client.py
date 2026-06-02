"""
DND Prompt Forge - MiMo 客户端
OpenAI-compatible API 封装，JSON 输出验证
"""

import json
import re
from typing import Dict, Optional

from openai import AsyncOpenAI

from config import settings


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

        try:
            response = await self._client.chat.completions.create(
                model=settings.mimo_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_completion_tokens=settings.mimo_max_completion_tokens,
                temperature=0.8,
            )
        except Exception as e:
            raise MiMoClientError(f"MiMo API error: {e}", category="provider_error") from e

        # 提取响应内容
        try:
            content = response.choices[0].message.content
        except (IndexError, AttributeError) as e:
            raise MiMoClientError(f"MiMo API error: {e}", category="provider_error") from e

        # 剥离 LLM 返回的 markdown code fence 包裹
        content = content.strip()
        content = re.sub(r'^```(?:json)?\s*\n?', '', content)
        content = re.sub(r'\n?```\s*$', '', content.strip())

        # 解析 JSON
        try:
            result = json.loads(content)
        except (json.JSONDecodeError, TypeError) as e:
            raise MiMoClientError(
                f"Failed to parse JSON from MiMo response: {e}",
                category="parse_error",
            ) from e

        # 验证响应字段
        validated = self._validate_response(result)
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