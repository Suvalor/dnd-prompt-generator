"""
DND Prompt Forge - 内容漂移检测模块
使用 TF-IDF + cosine similarity 检测 SEO 页面内容漂移
"""

import logging
import re
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field

from seo_worker.config import WorkerConfig
from seo_worker.models import PageRecord, utc_now_iso
from seo_worker.registry import Registry

logger = logging.getLogger(__name__)

# 漂移相似度阈值（来自 scope 文档）
_THRESHOLDS: dict[str, float] = {
    "title": 0.85,
    "meta_description": 0.85,
    "body": 0.82,
    "example": 0.78,
    "faq": 0.80,
}


class DriftResult(BaseModel):
    """
    漂移检测结果数据模型。

    记录单个页面的漂移检测结果，包含相似度分数和阈值信息。
    """

    slug: str = Field(..., description="页面 slug")
    similarity: float = Field(..., ge=0.0, le=1.0, description="综合相似度分数")
    is_drifted: bool = Field(..., description="是否检测到漂移")
    checked_at: str = Field(
        default_factory=utc_now_iso, description="检测时间 ISO 8601"
    )
    thresholds: dict[str, float] = Field(
        default_factory=lambda: dict(_THRESHOLDS),
        description="实际使用的阈值配置",
    )
    section_scores: dict[str, float] = Field(
        default_factory=dict, description="各内容区块的相似度分数"
    )


def _strip_html_tags(html_content: str) -> str:
    """
    剥离 HTML 标签，保留纯文本内容。

    Args:
        html_content: 包含 HTML 标签的内容

    Returns:
        去除标签后的纯文本
    """
    text = re.sub(r"<script[^>]*>.*?</script>", "", html_content, flags=re.DOTALL)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&[a-zA-Z]+;", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.lower()


def _extract_sections(html_content: str) -> dict[str, str]:
    """
    从 HTML 中提取各内容区块的纯文本。

    分别提取 title、meta_description、body、example、faq 的文本，
    用于逐区块计算相似度。

    Args:
        html_content: 页面 HTML 内容

    Returns:
        区块名称到纯文本的映射字典
    """
    sections: dict[str, str] = {}

    # 提取 title
    title_match = re.search(r"<title>(.*?)</title>", html_content, re.IGNORECASE)
    sections["title"] = title_match.group(1).strip().lower() if title_match else ""

    # 提取 meta description
    meta_match = re.search(
        r'<meta\s+name="description"\s+content="(.*?)"',
        html_content,
        re.IGNORECASE,
    )
    sections["meta_description"] = meta_match.group(1).strip().lower() if meta_match else ""

    # 提取 H1 和 intro（归入 body）
    h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", html_content, re.IGNORECASE | re.DOTALL)
    body_parts = []
    if h1_match:
        body_parts.append(h1_match.group(1).strip())
    intro_match = re.search(
        r'<div\s+class="intro">(.*?)</div>',
        html_content,
        re.IGNORECASE | re.DOTALL,
    )
    if intro_match:
        body_parts.append(intro_match.group(1).strip())
    sections["body"] = " ".join(body_parts).lower() if body_parts else ""

    # 提取 examples 区块
    example_matches = re.findall(
        r'<article\s+class="example-card">(.*?)</article>',
        html_content,
        re.IGNORECASE | re.DOTALL,
    )
    example_texts = []
    for m in example_matches:
        clean = _strip_html_tags(m)
        if clean:
            example_texts.append(clean)
    sections["example"] = " ".join(example_texts).lower() if example_texts else ""

    # 提取 FAQ 区块
    faq_matches = re.findall(
        r'<article\s+class="faq-item">(.*?)</article>',
        html_content,
        re.IGNORECASE | re.DOTALL,
    )
    faq_texts = []
    for m in faq_matches:
        clean = _strip_html_tags(m)
        if clean:
            faq_texts.append(clean)
    sections["faq"] = " ".join(faq_texts).lower() if faq_texts else ""

    return sections


def _compute_tfidf_cosine(text_a: str, text_b: str) -> float:
    """
    计算两段文本之间的 TF-IDF cosine 相似度。

    使用 scikit-learn TfidfVectorizer + cosine_similarity。

    Args:
        text_a: 第一段文本
        text_b: 第二段文本

    Returns:
        相似度分数 0.0-1.0
    """
    if not text_a.strip() or not text_b.strip():
        return 0.0

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words="english",
            token_pattern=r"[a-zA-Z0-9]+",
        )
        tfidf_matrix = vectorizer.fit_transform([text_a, text_b])
        sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        # clamp: scikit-learn cosine_similarity 对相同文本可能返回 1.0000000000000002，
        # 超过 DriftResult.similarity 的 le=1.0 约束导致 pydantic ValidationError
        return float(min(sim, 1.0))
    except Exception as exc:
        logger.warning("TF-IDF computation failed: %s", exc)
        return 0.0


class DriftDetector:
    """
    内容漂移检测器。

    使用 TF-IDF + cosine similarity 检测 SEO 页面内容漂移，
    对每个内容区块分别计算相似度并与阈值比较。
    """

    def __init__(self, config: WorkerConfig) -> None:
        """
        初始化漂移检测器。

        Args:
            config: Worker 配置
        """
        self._config = config
        self._thresholds = dict(_THRESHOLDS)

    async def check(self, existing_html: str, fresh_html: str) -> DriftResult:
        """
        检测两个版本之间的内容漂移。

        对每个内容区块分别计算 TF-IDF cosine similarity，
        任一区块低于阈值即判定为漂移。

        Args:
            existing_html: 现有版本 HTML
            fresh_html: 新版本 HTML

        Returns:
            漂移检测结果
        """
        existing_sections = _extract_sections(existing_html)
        fresh_sections = _extract_sections(fresh_html)

        section_scores: dict[str, float] = {}
        is_drifted = False

        for section_name in self._thresholds:
            existing_text = existing_sections.get(section_name, "")
            fresh_text = fresh_sections.get(section_name, "")
            if not existing_text or not fresh_text:
                # 缺少内容视为漂移
                section_scores[section_name] = 0.0
                is_drifted = True
                continue

            similarity = _compute_tfidf_cosine(existing_text, fresh_text)
            section_scores[section_name] = similarity

            threshold = self._thresholds[section_name]
            if similarity < threshold:
                logger.info(
                    "Drift detected in '%s': similarity=%.3f < threshold=%.3f",
                    section_name,
                    similarity,
                    threshold,
                )
                is_drifted = True

        # 综合相似度取各区块最小值
        overall_similarity = min(section_scores.values()) if section_scores else 0.0

        return DriftResult(
            slug="",
            similarity=overall_similarity,
            is_drifted=is_drifted,
            thresholds=dict(self._thresholds),
            section_scores=section_scores,
        )

    async def check_stale_pages(
        self, registry: Registry, threshold_days: int
    ) -> list[DriftResult]:
        """
        检查过期页面的内容漂移状态。

        先按年龄筛选过期页面，然后对每个过期页面调用 detect_drift()
        进行实际的 TF-IDF 相似度检测。只有实际漂移的页面才返回。

        Args:
            registry: 注册表实例
            threshold_days: 过期天数阈值

        Returns:
            漂移检测结果列表（仅包含实际漂移的页面）
        """
        # 步骤 1: 年龄过滤 - 获取过期页面
        stale_pages = registry.get_stale_pages(threshold_days)
        results: list[DriftResult] = []

        if not stale_pages:
            logger.info("No stale pages to check for drift")
            return results

        data_dir = Path(self._config.seo_data_dir)
        output_dir = Path(self._config.seo_output_dir)

        # 步骤 2: 对每个过期页面执行实际的漂移检测
        for page_record in stale_pages:
            result = await self._check_single_stale_page_drift(
                page_record, data_dir, output_dir
            )
            # 步骤 3: 只返回实际漂移的页面
            if result.is_drifted:
                results.append(result)

        logger.info(
            "Drift check: %d stale pages, %d drifted",
            len(stale_pages),
            len(results),
        )
        return results

    async def _check_single_stale_page_drift(
        self,
        page_record: PageRecord,
        data_dir: Path,
        output_dir: Path,
    ) -> DriftResult:
        """
        对单个过期页面执行实际的 TF-IDF 漂移检测。

        读取现有 HTML 文件，生成 fresh 版本（通过 fallback 内容模拟），
        然后调用 detect_drift() 计算相似度。

        Args:
            page_record: 页面记录
            data_dir: 数据目录路径
            output_dir: 输出目录路径

        Returns:
            漂移检测结果
        """
        slug = page_record.slug
        existing_file = output_dir / slug / "index.html"

        if not existing_file.exists():
            # 文件不存在，视为需要重新生成
            return DriftResult(
                slug=slug,
                similarity=0.0,
                is_drifted=True,
                thresholds=dict(self._thresholds),
                section_scores={},
            )

        existing_html = existing_file.read_text(encoding="utf-8")

        # 生成 fresh 版本用于比对
        # 由于漂移检测在 pipeline 中运行，我们使用现有内容作为 baseline
        # 如果有 Generator 可用，应该生成新版本；这里使用简化检测
        fresh_html = self._generate_fresh_html_for_comparison(page_record)

        # 调用 detect_drift() 进行实际的 TF-IDF 相似度检测
        result = await self.check(existing_html, fresh_html)
        result.slug = slug

        return result

    def _generate_fresh_html_for_comparison(self, page_record: PageRecord) -> str:
        """
        生成用于漂移比对的 fresh HTML 版本。

        由于漂移检测需要两个版本比较，这里生成一个基于页面记录的
        最小 HTML 作为 fresh 版本。实际生产中应该调用 Generator 生成。

        Args:
            page_record: 页面记录

        Returns:
            最小 HTML 字符串
        """
        # 使用页面记录中的信息构建最小 HTML
        # 包含所有漂移检测所需的区块：title, meta_description, body, example, faq
        kw_title = page_record.keyword.replace("-", " ").title()
        return (
            f'<!DOCTYPE html>\n<html lang="en">\n<head>\n'
            f'<title>{kw_title} - Free DND Prompt Generator</title>\n'
            f'<meta name="description" content="Generate stunning {page_record.keyword} with our free AI-powered DND prompt generator.">\n'
            f'</head>\n<body>\n'
            f'<h1>{kw_title} Generator</h1>\n'
            f'<div class="intro">Create detailed, copy-ready AI image prompts for {page_record.keyword}. Our free DND prompt generator helps tabletop RPG players.</div>\n'
            f'<article class="example-card">A {page_record.keyword}, fantasy art style, detailed, high quality</article>\n'
            f'<article class="faq-item"><p>What is a {page_record.keyword} prompt?</p></article>\n'
            f'</body>\n</html>'
        )