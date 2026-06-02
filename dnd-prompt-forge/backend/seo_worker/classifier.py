"""
DND Prompt Forge - 分类评分模块
使用 LLM 对关键词进行分类、评分和筛选
"""

import json
import logging
import re
from datetime import date

from openai import AsyncOpenAI

from seo_worker.config import WorkerConfig
from seo_worker.models import (
    ClassifiedKeyword,
    KeywordCandidate,
    LLMDecisionContract,
    RejectedKeyword,
    SelectedKeyword,
)

logger = logging.getLogger(__name__)

# 分类评分的系统提示词
_CLASSIFY_SYSTEM_PROMPT = """You are an SEO classifier for a DND prompt generator website (dndpromptforge.com).
Given a list of keyword candidates, classify each one and decide whether to select or reject it.

For each SELECTED keyword, provide:
- keyword: the original keyword
- page_type: one of "character", "token", "monster", "scene", "npc"
- race: DND race if mentioned (e.g., "Dragonborn", "Tiefling", "Elf"), null if not
- character_class: DND class if mentioned (e.g., "Paladin", "Warlock", "Ranger"), null if not
- theme: theme if mentioned (e.g., "villain", "tavern", "heroic"), null if not
- relevance_score: 0.0-1.0, how relevant to DND prompt generation
- prefill: object with keys matching generator fields (type, race, class_role, etc.), null if not applicable

For each REJECTED keyword, provide:
- keyword: the original keyword
- reason: why it was rejected

Selection criteria:
- Must be related to DND, tabletop RPGs, fantasy art, or AI image prompts
- Must represent a genuine search intent (not gibberish or overly broad)
- Prefer specific race/class combinations over generic terms
- Reject keywords about real people, NSFW content, or non-fantasy topics

Output must be a JSON object with these EXACT fields:
{
  "date": "YYYY-MM-DD",
  "selected_keywords": [...],
  "rejected_keywords": [...],
  "estimated_llm_cost_usd": 0.0,
  "token_budget": 0,
  "ssg_target": "/generated/",
  "data_model_action": "create",
  "prefill": null
}"""


class Classifier:
    """
    关键词分类评分器。

    使用 LLM 对关键词候选进行分类、评分和筛选，
    输出符合决策合约的结构化 JSON。
    """

    def __init__(self, config: WorkerConfig, llm_client: AsyncOpenAI | None = None) -> None:
        """
        初始化分类器。

        Args:
            config: Worker 配置，包含 LLM 连接信息
            llm_client: 可选的共享 LLM 客户端，若为 None 则在调用时按需创建
        """
        self._config = config
        self._llm_client = llm_client

    async def classify(
        self, candidates: list[KeywordCandidate]
    ) -> list[ClassifiedKeyword]:
        """
        对关键词候选进行分类和评分。

        Args:
            candidates: 待分类的关键词候选列表

        Returns:
            分类后的关键词列表（仅包含被选中的关键词）
        """
        if not candidates:
            logger.info("No candidates to classify")
            return []

        api_key = self._config.llm_api_key
        if not api_key:
            logger.warning("No LLM API key, using heuristic classification fallback")
            return self._heuristic_classify(candidates)

        decision = await self._llm_classify(candidates)
        if decision is None:
            logger.warning("LLM classification failed, using heuristic fallback")
            return self._heuristic_classify(candidates)

        return self._apply_decision(candidates, decision)

    async def _llm_classify(
        self, candidates: list[KeywordCandidate]
    ) -> LLMDecisionContract | None:
        """
        调用 LLM 进行分类决策。

        Args:
            candidates: 关键词候选列表

        Returns:
            LLM 决策合约，失败返回 None
        """
        keyword_list = [c.keyword for c in candidates]
        user_prompt = f"Classify these keywords:\n{json.dumps(keyword_list)}"

        try:
            client = self._llm_client or AsyncOpenAI(
                api_key=self._config.llm_api_key,
                base_url=self._config.llm_base_url,
                timeout=30,
            )
            response = await client.chat.completions.create(
                model=self._config.llm_model,
                messages=[
                    {"role": "system", "content": _CLASSIFY_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                max_completion_tokens=4096,
                temperature=0.3,
            )
        except Exception as exc:
            logger.warning("LLM classify call failed: %s", exc)
            return None

        content = self._extract_content(response)
        if not content:
            return None

        return self._parse_decision(content)

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
            return ""

        if not content:
            return ""

        content = content.strip()
        content = re.sub(r"^```(?:json)?\s*\n?", "", content)
        content = re.sub(r"\n?```\s*$", "", content.strip())
        return content.strip()

    def _parse_decision(self, content: str) -> LLMDecisionContract | None:
        """
        解析 LLM 返回的决策 JSON，验证必需字段。

        Args:
            content: LLM 返回的 JSON 文本

        Returns:
            解析后的决策合约，验证失败返回 None
        """
        try:
            data = json.loads(content)
        except (json.JSONDecodeError, TypeError) as exc:
            logger.warning("Failed to parse LLM decision JSON: %s", exc)
            return None

        # 验证必需字段
        required_fields = {
            "date",
            "selected_keywords",
            "rejected_keywords",
            "estimated_llm_cost_usd",
            "token_budget",
            "ssg_target",
            "data_model_action",
        }
        missing = required_fields - set(data.keys())
        if missing:
            logger.warning(
                "LLM decision missing required fields: %s", sorted(missing)
            )
            return None

        try:
            return LLMDecisionContract(**data)
        except Exception as exc:
            logger.warning("LLM decision validation failed: %s", exc)
            return None

    def _apply_decision(
        self,
        candidates: list[KeywordCandidate],
        decision: LLMDecisionContract,
    ) -> list[ClassifiedKeyword]:
        """
        将 LLM 决策应用到关键词候选，生成分类关键词列表。

        Args:
            candidates: 原始关键词候选列表
            decision: LLM 决策合约

        Returns:
            被选中的分类关键词列表
        """
        # 构建原始候选的查找表
        candidate_map: dict[str, KeywordCandidate] = {
            c.keyword.lower(): c for c in candidates
        }

        classified: list[ClassifiedKeyword] = []
        for selected in decision.selected_keywords:
            key = selected.keyword.lower()
            original = candidate_map.get(key)
            if original is None:
                # LLM 可能生成了变体，尝试模糊匹配
                original = self._fuzzy_find(key, candidate_map)
            if original is None:
                logger.debug("Selected keyword not in candidates: %s", selected.keyword)
                continue

            classified.append(
                ClassifiedKeyword(
                    keyword=original.keyword,
                    source=original.source,
                    volume=original.volume,
                    competition=original.competition,
                    discovered_at=original.discovered_at,
                    page_type=selected.page_type,
                    race=selected.race,
                    character_class=selected.character_class,
                    theme=selected.theme,
                    relevance_score=selected.relevance_score,
                )
            )

        logger.info(
            "Classification: %d selected, %d rejected from %d candidates",
            len(classified),
            len(decision.rejected_keywords),
            len(candidates),
        )
        return classified

    def _fuzzy_find(
        self, key: str, candidate_map: dict[str, KeywordCandidate]
    ) -> KeywordCandidate | None:
        """
        模糊查找关键词候选。

        Args:
            key: 待查找的关键词（小写）
            candidate_map: 候选关键词映射

        Returns:
            匹配的候选，未找到返回 None
        """
        # 尝试去掉连字符或空格的变体
        normalized = key.replace("-", " ").replace("  ", " ")
        for map_key, candidate in candidate_map.items():
            map_normalized = map_key.replace("-", " ").replace("  ", " ")
            if map_normalized == normalized:
                return candidate
        return None

    def _heuristic_classify(
        self, candidates: list[KeywordCandidate]
    ) -> list[ClassifiedKeyword]:
        """
        基于规则的启发式分类，作为 LLM 不可用时的 fallback。

        Args:
            candidates: 关键词候选列表

        Returns:
            启发式分类后的关键词列表
        """
        classified: list[ClassifiedKeyword] = []
        for c in candidates:
            kw = c.keyword.lower()
            page_type = self._infer_page_type(kw)
            race = self._extract_race(kw)
            char_class = self._extract_class(kw)
            theme = self._extract_theme(kw)
            relevance = self._compute_relevance(kw)

            if relevance < 0.3:
                continue

            classified.append(
                ClassifiedKeyword(
                    keyword=c.keyword,
                    source=c.source,
                    volume=c.volume,
                    competition=c.competition,
                    discovered_at=c.discovered_at,
                    page_type=page_type,
                    race=race,
                    character_class=char_class,
                    theme=theme,
                    relevance_score=relevance,
                )
            )

        logger.info("Heuristic classification: %d from %d candidates", len(classified), len(candidates))
        return classified

    def _infer_page_type(self, keyword: str) -> str:
        """
        从关键词推断页面类型。

        Args:
            keyword: 小写关键词

        Returns:
            推断的页面类型
        """
        if "token" in keyword:
            return "token"
        if "monster" in keyword or "creature" in keyword or "dragon" in keyword:
            return "monster"
        if "scene" in keyword or "landscape" in keyword or "tavern" in keyword:
            return "scene"
        if "npc" in keyword:
            return "npc"
        return "character"

    def _extract_race(self, keyword: str) -> str | None:
        """
        从关键词提取 DND 种族。

        Args:
            keyword: 小写关键词

        Returns:
            种族名称或 None
        """
        races = [
            "dragonborn", "tiefling", "elf", "dwarf", "halfling",
            "gnome", "half-elf", "half-orc", "orc", "goblin",
            "aasimar", "tabaxi", "kenku", "firbolg", "genasi",
        ]
        for race in races:
            if race in keyword:
                return race.capitalize()
        return None

    def _extract_class(self, keyword: str) -> str | None:
        """
        从关键词提取 DND 职业。

        Args:
            keyword: 小写关键词

        Returns:
            职业名称或 None
        """
        classes = [
            "paladin", "warlock", "ranger", "wizard", "sorcerer",
            "cleric", "rogue", "bard", "druid", "barbarian",
            "fighter", "monk", "artificer",
        ]
        for cls in classes:
            if cls in keyword:
                return cls.capitalize()
        return None

    def _extract_theme(self, keyword: str) -> str | None:
        """
        从关键词提取主题。

        Args:
            keyword: 小写关键词

        Returns:
            主题名称或 None
        """
        themes = {
            "villain": "villain",
            "heroic": "heroic",
            "tavern": "tavern",
            "battle": "battle",
            "portrait": "portrait",
            "dark": "dark",
        }
        for key, theme in themes.items():
            if key in keyword:
                return theme
        return None

    def _compute_relevance(self, keyword: str) -> float:
        """
        计算关键词与 DND prompt 生成的相关性评分。

        Args:
            keyword: 小写关键词

        Returns:
            相关性评分 0-1
        """
        score = 0.0
        dnd_signals = ["dnd", "d&d", "dungeons", "dragons", "rpg", "tabletop"]
        prompt_signals = ["prompt", "generator", "ai art", "image"]
        fantasy_signals = ["fantasy", "character", "portrait", "token", "monster", "scene"]

        for signal in dnd_signals:
            if signal in keyword:
                score += 0.3
                break

        for signal in prompt_signals:
            if signal in keyword:
                score += 0.3
                break

        for signal in fantasy_signals:
            if signal in keyword:
                score += 0.2
                break

        # 种族/职业组合加分
        if self._extract_race(keyword) and self._extract_class(keyword):
            score += 0.2

        return min(score, 1.0)
