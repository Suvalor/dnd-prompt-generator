"""
DND Prompt Forge - 关键词发现模块
从种子列表、Google Trends API、LLM 扩展三个来源发现长尾关键词
"""

import json
import logging
import re
from pathlib import Path

from openai import AsyncOpenAI

from seo_worker.config import WorkerConfig
from seo_worker.models import KeywordCandidate, utc_now_iso

logger = logging.getLogger(__name__)

# LLM 扩展关键词的系统提示词
_EXPAND_SYSTEM_PROMPT = (
    "You are an SEO keyword researcher specializing in DND and tabletop RPG content. "
    "Given a list of seed keywords, generate additional long-tail keyword variations "
    "that DND players, DMs, and VTT users would search for. "
    "Focus on specific race/class combinations, token types, scene types, and art styles. "
    "Output must be a JSON array of objects, each with 'keyword' (string) and "
    "'relevance_hint' (string, one of: high, medium, low). "
    "Generate at most 30 keywords. Do not repeat the seed keywords."
)


class Discoverer:
    """
    关键词发现器。

    三步发现流程：种子列表 -> 趋势 API -> LLM 扩展。
    """

    def __init__(self, config: WorkerConfig, llm_client: AsyncOpenAI | None = None) -> None:
        """
        初始化发现器。

        Args:
            config: Worker 配置，包含种子词路径和 LLM 配置
            llm_client: 可选的共享 LLM 客户端，若为 None 则在调用时按需创建
        """
        self._config = config
        self._llm_client = llm_client
        self._seed_path = Path(config.seo_seed_keywords_path)

    async def discover(self) -> list[KeywordCandidate]:
        """
        执行三步关键词发现流程。

        Returns:
            去重后的关键词候选列表
        """
        candidates: list[KeywordCandidate] = []
        seen_keywords: set[str] = set()

        # 步骤 1: 从种子文件加载
        seed_candidates = self._load_seed_keywords()
        for c in seed_candidates:
            key = c.keyword.lower()
            if key not in seen_keywords:
                candidates.append(c)
                seen_keywords.add(key)

        # 步骤 2: 尝试 Google Trends API
        trend_candidates = await self._fetch_trends()
        for c in trend_candidates:
            key = c.keyword.lower()
            if key not in seen_keywords:
                candidates.append(c)
                seen_keywords.add(key)

        # 步骤 3: LLM 扩展
        llm_candidates = await self._llm_expand(seen_keywords)
        for c in llm_candidates:
            key = c.keyword.lower()
            if key not in seen_keywords:
                candidates.append(c)
                seen_keywords.add(key)

        logger.info(
            "Discovery complete: %d candidates (seed=%d, trend=%d, llm=%d)",
            len(candidates),
            sum(1 for c in candidates if c.source == "seed_list"),
            sum(1 for c in candidates if c.source == "trend_api"),
            sum(1 for c in candidates if c.source == "llm_expand"),
        )
        return candidates

    def _load_seed_keywords(self) -> list[KeywordCandidate]:
        """
        从种子文件加载关键词。

        Returns:
            种子关键词候选列表
        """
        if not self._seed_path.exists():
            logger.warning("Seed keywords file not found: %s", self._seed_path)
            return []

        keywords: list[KeywordCandidate] = []
        now = utc_now_iso()
        for line in self._seed_path.read_text(encoding="utf-8").splitlines():
            cleaned = line.strip().lower()
            if cleaned and not cleaned.startswith("#"):
                keywords.append(
                    KeywordCandidate(
                        keyword=cleaned,
                        source="seed_list",
                        discovered_at=now,
                    )
                )

        logger.info("Loaded %d seed keywords from %s", len(keywords), self._seed_path)
        return keywords

    async def _fetch_trends(self) -> list[KeywordCandidate]:
        """
        尝试从 Google Trends API 获取趋势关键词。

        如果未配置 API key 或请求失败，返回空列表作为 fallback。

        Returns:
            趋势关键词候选列表
        """
        api_key = self._config.seo_trends_api_key
        if not api_key:
            logger.info("No SEO_TRENDS_API_KEY configured, skipping trend fetch")
            return []

        # Phase 1: Trends API 为 alpha 功能，暂不实现完整调用
        # 当 API key 存在时记录日志，实际调用在后续 Sprint 实现
        logger.info("Trends API key found but full integration deferred to Sprint 3")
        return []

    async def _llm_expand(self, existing_keywords: set[str]) -> list[KeywordCandidate]:
        """
        使用 LLM 扩展关键词。

        Args:
            existing_keywords: 已有关键词集合（小写），用于去重

        Returns:
            LLM 扩展的关键词候选列表
        """
        api_key = self._config.llm_api_key
        if not api_key:
            logger.info("No LLM API key configured, skipping LLM expansion")
            return []

        seed_text = ", ".join(sorted(existing_keywords)[:20])
        user_prompt = f"Seed keywords: {seed_text}"

        try:
            client = self._llm_client or AsyncOpenAI(
                api_key=api_key,
                base_url=self._config.llm_base_url,
                timeout=30,
            )
            response = await client.chat.completions.create(
                model=self._config.llm_model,
                messages=[
                    {"role": "system", "content": _EXPAND_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                max_completion_tokens=2048,
                temperature=0.7,
            )
        except Exception as exc:
            logger.warning("LLM expansion failed: %s", exc)
            return []

        content = self._extract_content(response)
        if not content:
            return []

        return self._parse_llm_keywords(content, existing_keywords)

    def _extract_content(self, response: object) -> str:
        """
        从 LLM 响应中提取文本内容，剥离 markdown code fence。

        Args:
            response: OpenAI API 响应对象

        Returns:
            清理后的文本内容
        """
        try:
            content = response.choices[0].message.content  # type: ignore[attr-defined]
        except (IndexError, AttributeError):
            logger.warning("Unexpected LLM response structure")
            return ""

        if not content:
            return ""

        # 剥离 markdown code fence
        content = content.strip()
        content = re.sub(r"^```(?:json)?\s*\n?", "", content)
        content = re.sub(r"\n?```\s*$", "", content.strip())
        return content.strip()

    def _parse_llm_keywords(
        self, content: str, existing: set[str]
    ) -> list[KeywordCandidate]:
        """
        解析 LLM 返回的关键词 JSON。

        Args:
            content: LLM 返回的 JSON 文本
            existing: 已有关键词集合，用于去重

        Returns:
            解析后的关键词候选列表
        """
        try:
            items = json.loads(content)
        except (json.JSONDecodeError, TypeError) as exc:
            logger.warning("Failed to parse LLM keyword JSON: %s", exc)
            return []

        if not isinstance(items, list):
            logger.warning("LLM keyword output is not a list")
            return []

        candidates: list[KeywordCandidate] = []
        now = utc_now_iso()
        for item in items:
            if not isinstance(item, dict):
                continue
            kw = item.get("keyword", "")
            if not isinstance(kw, str) or not kw.strip():
                continue
            cleaned = kw.strip().lower()
            if cleaned in existing:
                continue
            candidates.append(
                KeywordCandidate(
                    keyword=cleaned,
                    source="llm_expand",
                    discovered_at=now,
                )
            )

        logger.info("LLM expansion produced %d new keywords", len(candidates))
        return candidates
