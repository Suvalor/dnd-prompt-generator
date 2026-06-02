"""
DND Prompt Forge - SEO Worker 数据模型
定义关键词发现、分类、生成、质量门禁、注册表等核心数据结构
"""

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    """返回当前 UTC 时间的 ISO 8601 格式字符串。"""
    return datetime.now(timezone.utc).isoformat()


# ============================================================================
# 关键词发现模块数据模型
# ============================================================================


class KeywordCandidate(BaseModel):
    """
    关键词候选数据模型。

    表示从种子列表、趋势 API 或 LLM 扩展中发现的关键词。
    """

    keyword: str = Field(..., min_length=1, description="关键词文本")
    source: Literal["seed_list", "trend_api", "llm_expand"] = Field(
        default="seed_list", description="关键词来源"
    )
    volume: int | None = Field(default=None, ge=0, description="搜索量（如有）")
    competition: float | None = Field(
        default=None, ge=0.0, le=1.0, description="竞争度 0-1（如有）"
    )
    discovered_at: str = Field(
        default_factory=utc_now_iso, description="发现时间 ISO 8601"
    )


# ============================================================================
# 分类评分模块数据模型
# ============================================================================


class ClassifiedKeyword(KeywordCandidate):
    """
    已分类关键词数据模型。

    继承 KeywordCandidate，增加 LLM 分类和评分信息。
    """

    page_type: Literal["character", "token", "monster", "scene", "npc"] = Field(
        default="character", description="页面类型"
    )
    race: str | None = Field(default=None, description="种族（如 Dragonborn）")
    character_class: str | None = Field(
        default=None, description="职业（如 Paladin）"
    )
    theme: str | None = Field(default=None, description="主题（如 villain, tavern）")
    relevance_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="相关性评分 0-1"
    )


# ============================================================================
# 页面生成模块数据模型
# ============================================================================


class ExamplePrompt(BaseModel):
    """示例提示词数据模型。"""

    badge: str = Field(..., description="示例标签（如 'Heroic'）")
    name: str = Field(..., description="示例名称")
    positive: str = Field(..., description="正面提示词")
    negative: str = Field(..., description="负面提示词")


class FAQItem(BaseModel):
    """FAQ 条目数据模型。"""

    question: str = Field(..., description="问题")
    answer: str = Field(..., description="答案")


class InternalLink(BaseModel):
    """内部链接数据模型。"""

    label: str = Field(..., description="链接文本")
    href: str = Field(..., description="链接路径")


class GeneratedPage(BaseModel):
    """
    生成页面数据模型。

    包含 LLM 生成的结构化内容和最终渲染的 HTML。
    """

    slug: str = Field(..., pattern=r"^[a-z0-9-]+$", description="URL slug")
    page_type: str = Field(..., description="页面类型")
    title: str = Field(..., min_length=10, max_length=70, description="页面标题")
    meta_description: str = Field(
        ..., min_length=50, max_length=160, description="Meta 描述"
    )
    h1: str = Field(..., min_length=5, max_length=100, description="H1 标题")
    intro: str = Field(..., min_length=100, description="介绍段落")
    examples: list[ExamplePrompt] = Field(
        default_factory=list, description="示例提示词列表"
    )
    faqs: list[FAQItem] = Field(default_factory=list, description="FAQ 列表")
    internal_links: list[InternalLink] = Field(
        default_factory=list, description="内部链接列表"
    )
    prefill: dict | None = Field(default=None, description="Generator 预填数据")
    html_content: str = Field(default="", description="渲染后的 HTML 内容")
    canonical_url: str = Field(..., description="Canonical URL")
    llm_raw_output: dict = Field(default_factory=dict, description="LLM 原始输出")
    generated_at: str = Field(
        default_factory=utc_now_iso, description="生成时间 ISO 8601"
    )


# ============================================================================
# 质量门禁模块数据模型
# ============================================================================


class CheckDetail(BaseModel):
    """
    单项检查详情数据模型。

    表示质量门禁中单个检查项的结果。
    """

    passed: bool = Field(..., description="是否通过")
    score: float = Field(default=0.0, ge=0.0, le=1.0, description="评分 0-1")
    reason: str = Field(default="", description="说明原因")


class GateResult(BaseModel):
    """
    质量门禁结果数据模型。

    包含所有检查项的结果和总体判定。
    """

    passed: bool = Field(..., description="是否通过所有检查")
    score: float = Field(default=0.0, ge=0.0, le=1.0, description="综合评分")
    checks: dict[str, CheckDetail] = Field(
        default_factory=dict, description="各检查项详情"
    )
    failure_reasons: list[str] = Field(
        default_factory=list, description="失败原因列表"
    )


# ============================================================================
# 注册表管理模块数据模型
# ============================================================================


class PageRecord(BaseModel):
    """
    页面记录数据模型。

    存储在 seo-pages.json 中，记录已发布页面的元数据。
    """

    slug: str = Field(..., description="URL slug")
    keyword: str = Field(..., description="原始关键词")
    page_type: str = Field(..., description="页面类型")
    status: Literal["published", "pending", "stale"] = Field(
        default="published", description="页面状态"
    )
    url_path: str = Field(..., description="URL 路径")
    canonical_url: str = Field(..., description="Canonical URL")
    canonical_group: str = Field(..., description="Canonical 分组标识")
    primary_keyword: str = Field(..., description="主关键词")
    intent: str = Field(default="", description="搜索意图")
    published_at: str | None = Field(default=None, description="发布时间")
    last_checked_at: str | None = Field(default=None, description="最后检查时间")
    drift_score: float | None = Field(default=None, ge=0.0, le=1.0, description="漂移分数")
    generation_count: int = Field(default=1, ge=1, description="生成次数")
    content_fingerprint: str | None = Field(default=None, description="内容指纹 SHA-256")
    last_trend_score: float | None = Field(default=None, description="最后趋势分数")
    last_helpful_content_score: float | None = Field(
        default=None, description="最后有用内容分数"
    )
    source_keywords: list[str] = Field(default_factory=list, description="来源关键词列表")
    related_pages: list[str] = Field(default_factory=list, description="相关页面列表")
    created_at: str = Field(default_factory=utc_now_iso, description="创建时间")
    updated_at: str = Field(default_factory=utc_now_iso, description="更新时间")


class FailureRecord(BaseModel):
    """
    失败记录数据模型。

    存储在 seo-failures.json 中，记录被质量门禁拒绝的候选。
    """

    keyword: str = Field(..., description="关键词")
    page_type: str | None = Field(default=None, description="页面类型")
    status: Literal["retry_later", "defer_long_term", "update_existing_only", "blocked"] = Field(
        default="retry_later", description="失败状态"
    )
    failure_reasons: list[str] = Field(default_factory=list, description="失败原因列表")
    attempt_count: int = Field(default=1, ge=1, description="尝试次数")
    last_attempt_at: str = Field(default_factory=utc_now_iso, description="最后尝试时间")
    next_retry_after: str | None = Field(default=None, description="下次重试时间")
    recommended_next_action: str = Field(default="", description="建议下一步操作")
    failed_gate: str = Field(default="", description="失败的检查项")


# ============================================================================
# LLM 决策合约数据模型
# ============================================================================


class KeywordScores(BaseModel):
    """关键词评分数据模型，包含各维度评分。"""

    trend_score: int = Field(default=0, ge=0, le=100, description="趋势评分 0-100")
    project_relevance: int = Field(default=0, ge=0, le=100, description="项目相关性 0-100")
    user_value: int = Field(default=0, ge=0, le=100, description="用户价值 0-100")
    content_uniqueness: int = Field(default=0, ge=0, le=100, description="内容独特性 0-100")
    spam_risk: int = Field(default=0, ge=0, le=100, description="垃圾风险 0-100")


class SelectedKeyword(BaseModel):
    """LLM 选中的关键词数据模型。"""

    keyword: str = Field(..., description="关键词")
    page_type: str = Field(..., description="页面类型")
    race: str | None = Field(default=None, description="种族")
    character_class: str | None = Field(default=None, description="职业")
    theme: str | None = Field(default=None, description="主题")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="相关性评分")
    intent: str = Field(default="", description="搜索意图分类")
    action: str = Field(default="create_page", description="建议动作")
    target_url: str = Field(default="", description="目标 URL 路径")
    reason: str = Field(default="", description="选择原因")
    scores: KeywordScores | None = Field(default=None, description="各维度评分")
    prefill: dict | None = Field(default=None, description="预填数据")


class RejectedKeyword(BaseModel):
    """LLM 拒绝的关键词数据模型。"""

    keyword: str = Field(..., description="关键词")
    reason: str = Field(..., description="拒绝原因")


class TokenBudget(BaseModel):
    """Token 预算结构化数据模型。"""

    decision_tokens: int = Field(default=0, ge=0, description="决策阶段 Token 预算")
    generation_tokens: int = Field(default=0, ge=0, description="生成阶段 Token 预算")
    validation_tokens: int = Field(default=0, ge=0, description="验证阶段 Token 预算")


class LLMDecisionContract(BaseModel):
    """
    LLM 决策合约数据模型。

    定义 LLM 输出的标准结构，确保所有必需字段存在。
    """

    date: str = Field(..., description="决策日期 YYYY-MM-DD")
    selected_keywords: list[SelectedKeyword] = Field(
        default_factory=list, description="选中的关键词"
    )
    rejected_keywords: list[RejectedKeyword] = Field(
        default_factory=list, description="拒绝的关键词"
    )
    estimated_llm_cost_usd: float = Field(
        default=0.0, ge=0.0, description="预估 LLM 成本 USD"
    )
    token_budget: int | TokenBudget = Field(
        default=0, description="Token 预算（整数或结构化对象）"
    )
    ssg_target: str = Field(default="", description="SSG 目标路径")
    data_model_action: Literal[
        "create", "update", "skip",
        "create_static_registry_entry", "update_static_registry_entry",
    ] = Field(
        default="skip", description="数据模型动作"
    )
    prefill: dict | None = Field(default=None, description="全局预填数据")
