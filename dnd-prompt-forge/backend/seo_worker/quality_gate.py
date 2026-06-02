"""
DND Prompt Forge - 质量门禁模块
执行多维度质量检查，确保生成内容符合 SEO 和内容质量标准
"""

import hashlib
import logging
import re

from seo_worker.config import WorkerConfig
from seo_worker.models import (
    CheckDetail,
    GateResult,
    GeneratedPage,
)

logger = logging.getLogger(__name__)

# DND/fantasy 相关信号词
_DND_SIGNALS = frozenset({
    "dnd", "d&d", "dungeons", "dragons", "rpg", "tabletop",
    "fantasy", "character", "portrait", "token", "monster",
    "scene", "npc", "campaign", "spell", "quest", "dungeon",
    "dragon", "elf", "dwarf", "tiefling", "paladin", "warlock",
    "ranger", "wizard", "cleric", "rogue", "bard", "druid",
    "barbarian", "fighter", "monk", "sorcerer", "artificer",
    "dragonborn", "halfling", "gnome", "orc", "goblin",
    "prompt", "generator", "ai art", "image",
})

# 垃圾内容信号词
_SPAM_SIGNALS = frozenset({
    "buy cheap", "free money", "click here", "act now",
    "limited offer", "guaranteed", "no risk", "winner",
})


class QualityGate:
    """
    质量门禁评估器。

    对生成的页面执行多维度质量检查，
    只有通过所有必要检查才能发布。
    """

    def __init__(self, config: WorkerConfig, registry: object | None = None) -> None:
        """
        初始化质量门禁。

        Args:
            config: Worker 配置
            registry: 注册表实例，用于检查重复 intent
        """
        self._config = config
        self._registry = registry

    async def evaluate(self, page: GeneratedPage) -> GateResult:
        """
        执行所有质量检查。

        Args:
            page: 待评估的生成页面

        Returns:
            质量门禁结果
        """
        checks: dict[str, CheckDetail] = {}

        checks["relevance"] = self._check_relevance(page)
        checks["duplicate_intent"] = self._check_duplicate_intent(page)
        checks["helpful_content"] = self._check_helpful_content(page)
        checks["spam"] = self._check_spam(page)
        checks["html_validity"] = self._check_html_validity(page)
        checks["build"] = self._check_build(page)
        checks["cost_rate_limit"] = self._check_cost_rate_limit(page)
        checks["content_drift"] = self._check_content_drift(page)

        # 计算综合结果
        all_passed = all(c.passed for c in checks.values())
        avg_score = sum(c.score for c in checks.values()) / max(len(checks), 1)
        failure_reasons = [
            f"{name}: {detail.reason}"
            for name, detail in checks.items()
            if not detail.passed
        ]

        if failure_reasons:
            logger.info(
                "Quality gate FAILED for '%s': %s",
                page.slug,
                "; ".join(failure_reasons),
            )
        else:
            logger.info("Quality gate PASSED for '%s' (score=%.2f)", page.slug, avg_score)

        return GateResult(
            passed=all_passed,
            score=avg_score,
            checks=checks,
            failure_reasons=failure_reasons,
        )

    def _check_relevance(self, page: GeneratedPage) -> CheckDetail:
        """
        检查关键词是否与 DND/fantasy/prompt 相关。

        Args:
            page: 生成页面

        Returns:
            检查详情
        """
        text = f"{page.title} {page.meta_description} {page.h1} {page.intro}".lower()
        words = set(re.findall(r"[a-z&]+", text))
        matched_signals = words & _DND_SIGNALS

        if len(matched_signals) >= 2:
            score = min(len(matched_signals) / 5.0, 1.0)
            return CheckDetail(passed=True, score=score, reason="DND/fantasy relevant")

        if len(matched_signals) == 1:
            return CheckDetail(
                passed=True, score=0.4, reason="Minimally DND relevant"
            )

        return CheckDetail(
            passed=False, score=0.0, reason="No DND/fantasy relevance detected"
        )

    def _check_duplicate_intent(self, page: GeneratedPage) -> CheckDetail:
        """
        检查是否与已有 canonical_group 重叠。

        同时检查 slug 重复和同 canonical_group 内是否已有 published 页面，
        避免为同一意图创建多个页面。

        Args:
            page: 生成页面

        Returns:
            检查详情
        """
        if self._registry is None:
            return CheckDetail(
                passed=True, score=1.0, reason="No registry to check against"
            )

        # 检查 slug 是否已存在
        try:
            published = self._registry.get_published_slugs()  # type: ignore[attr-defined]
        except Exception:
            return CheckDetail(
                passed=True, score=1.0, reason="Registry slug check skipped"
            )

        if page.slug in published:
            return CheckDetail(
                passed=False, score=0.0, reason=f"Slug '{page.slug}' already published"
            )

        # 检查同 canonical_group 是否已有 published 页面
        canonical_group = self._infer_canonical_group(page)
        if canonical_group:
            try:
                group_pages = self._registry.get_pages_by_canonical_group(canonical_group)  # type: ignore[attr-defined]
            except Exception:
                return CheckDetail(
                    passed=True, score=1.0, reason="Registry canonical_group check skipped"
                )

            # 排除自身 slug，检查同组内是否有其他 published 页面
            other_published = [
                p for p in group_pages
                if p.get("slug") != page.slug and p.get("status") == "published"
            ]
            if other_published:
                existing_slugs = ", ".join(p.get("slug", "?") for p in other_published[:3])
                return CheckDetail(
                    passed=False,
                    score=0.0,
                    reason=f"Canonical group '{canonical_group}' already has published page(s): {existing_slugs}",
                )

        return CheckDetail(passed=True, score=1.0, reason="No duplicate intent")

    def _infer_canonical_group(self, page: GeneratedPage) -> str:
        """
        从页面数据推断 canonical_group 标识。

        基于 page_type 和 slug 组合，用于意图重叠检测。

        Args:
            page: 生成页面

        Returns:
            canonical_group 标识字符串
        """
        # NPC 使用与 character 相同的 canonical_group 逻辑
        page_type = page.page_type
        if page_type == "npc":
            page_type = "character"
        return f"{page_type}:{page.slug}"

    def _check_helpful_content(self, page: GeneratedPage) -> CheckDetail:
        """
        检查内容是否足够有用（至少有 examples）。

        Args:
            page: 生成页面

        Returns:
            检查详情
        """
        example_count = len(page.examples)
        faq_count = len(page.faqs)

        if example_count >= 3:
            score = min(0.5 + example_count * 0.1, 1.0)
            return CheckDetail(
                passed=True, score=score, reason=f"{example_count} examples, {faq_count} FAQs"
            )

        if example_count >= 1:
            return CheckDetail(
                passed=True, score=0.4, reason=f"Only {example_count} examples"
            )

        return CheckDetail(
            passed=False, score=0.0, reason="No example prompts provided"
        )

    def _check_spam(self, page: GeneratedPage) -> CheckDetail:
        """
        检查关键词密度是否合理、无隐藏文本。

        Args:
            page: 生成页面

        Returns:
            检查详情
        """
        text = f"{page.title} {page.meta_description} {page.h1} {page.intro}".lower()
        words = re.findall(r"[a-z]+", text)

        # 检查垃圾信号词
        for signal in _SPAM_SIGNALS:
            if signal in text:
                return CheckDetail(
                    passed=False, score=0.0, reason=f"Spam signal detected: '{signal}'"
                )

        # 检查隐藏文本
        if "display:none" in page.html_content.lower():
            return CheckDetail(
                passed=False, score=0.0, reason="Hidden text detected (display:none)"
            )

        # 检查关键词密度
        if not words:
            return CheckDetail(passed=True, score=1.0, reason="No words to check density")

        slug_words = set(page.slug.split("-"))
        keyword_count = sum(1 for w in words if w in slug_words)
        density = keyword_count / len(words)

        if density > 0.30:
            return CheckDetail(
                passed=False, score=0.3, reason=f"Keyword density too high: {density:.1%}"
            )

        return CheckDetail(passed=True, score=1.0, reason="No spam signals")

    def _check_html_validity(self, page: GeneratedPage) -> CheckDetail:
        """
        检查 HTML 结构完整性。

        Args:
            page: 生成页面

        Returns:
            检查详情
        """
        html = page.html_content
        if not html:
            return CheckDetail(passed=False, score=0.0, reason="No HTML content")

        issues: list[str] = []
        score = 1.0

        # 检查必要元素
        required_checks = [
            ("<title", "missing <title>"),
            ('meta name="description"', 'missing meta description'),
            ('rel="canonical"', 'missing canonical link'),
            ("<h1", "missing <h1>"),
        ]

        for tag, issue in required_checks:
            if tag not in html.lower():
                issues.append(issue)
                score -= 0.25

        if issues:
            return CheckDetail(passed=False, score=max(score, 0.0), reason="; ".join(issues))

        return CheckDetail(passed=True, score=1.0, reason="HTML structure valid")

    def _check_build(self, page: GeneratedPage) -> CheckDetail:
        """
        检查生成的文件是否可被 Nginx 正常服务。

        Phase 1 简化实现：检查 HTML 非空且长度合理。

        Args:
            page: 生成页面

        Returns:
            检查详情
        """
        if not page.html_content:
            return CheckDetail(passed=False, score=0.0, reason="Empty HTML content")

        if len(page.html_content) < 200:
            return CheckDetail(
                passed=False, score=0.3, reason="HTML content too short"
            )

        # 检查是否有 DOCTYPE 声明
        if "<!doctype" not in page.html_content.lower():
            return CheckDetail(
                passed=False, score=0.7, reason="Missing DOCTYPE declaration"
            )

        return CheckDetail(passed=True, score=1.0, reason="Build check passed")

    def _check_cost_rate_limit(self, page: GeneratedPage) -> CheckDetail:
        """
        检查 LLM 成本是否在预算内。

        Phase 1 简化实现：基于配置值检查。

        Args:
            page: 生成页面

        Returns:
            检查详情
        """
        # 从 LLM 原始输出中提取成本估计
        cost = page.llm_raw_output.get("estimated_llm_cost_usd", 0.0)
        budget = self._config.seo_llm_daily_cost_budget_usd

        if not isinstance(cost, (int, float)):
            cost = 0.0

        if cost > budget:
            return CheckDetail(
                passed=False,
                score=0.0,
                reason=f"Cost ${cost:.4f} exceeds budget ${budget:.2f}",
            )

        ratio = cost / budget if budget > 0 else 0.0
        return CheckDetail(
            passed=True,
            score=1.0 - ratio,
            reason=f"Cost ${cost:.4f} within budget ${budget:.2f}",
        )

    def _check_content_drift(self, page: GeneratedPage) -> CheckDetail:
        """
        检查内容漂移。

        Phase 1 先做框架：生成内容指纹，实际相似度检测在 Sprint 3 实现。

        Args:
            page: 生成页面

        Returns:
            检查详情
        """
        # 生成内容指纹
        fingerprint = self._compute_fingerprint(page)

        if self._registry is None:
            return CheckDetail(
                passed=True,
                score=1.0,
                reason=f"Fingerprint: {fingerprint[:12]}... (no registry for drift check)",
            )

        # Phase 1: 只检查指纹，不做完整漂移检测
        return CheckDetail(
            passed=True,
            score=1.0,
            reason=f"Fingerprint: {fingerprint[:12]}... (drift detection deferred to Sprint 3)",
        )

    def _compute_fingerprint(self, page: GeneratedPage) -> str:
        """
        计算页面内容的 SHA-256 指纹。

        Args:
            page: 生成页面

        Returns:
            SHA-256 十六进制摘要
        """
        content = f"{page.title}|{page.meta_description}|{page.h1}|{page.intro}"
        for ex in page.examples:
            content += f"|{ex.name}:{ex.positive}"
        for faq in page.faqs:
            content += f"|{faq.question}:{faq.answer}"

        return hashlib.sha256(content.encode("utf-8")).hexdigest()
