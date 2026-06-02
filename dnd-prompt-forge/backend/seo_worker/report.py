"""
DND Prompt Forge - 运行报告生成模块
生成每日 SEO Worker 运行报告：published/failed/calibration 三种报告
"""

import json as _json
import logging
import os
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field

from seo_worker.config import WorkerConfig
from seo_worker.models import FailureRecord, utc_now_iso

logger = logging.getLogger(__name__)

# 报告输出目录
_REPORTS_DIR = Path("docs/seo-runs")


def _serialize_for_json(obj: object) -> object:
    """
    递归转换数据结构中的 datetime 对象为 ISO 格式字符串，防止 asdict(datetime) 序列化失败。

    Args:
        obj: 待序列化的对象（dict/list/基本类型/datetime）

    Returns:
        可 JSON 序列化的对象
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: _serialize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize_for_json(v) for v in obj]
    return obj


class PipelineResult(BaseModel):
    """
    流水线运行结果数据模型。

    记录单次 SEO Worker 流水线的完整运行结果。
    """

    run_date: str = Field(..., description="运行日期 YYYY-MM-DD")
    candidates_discovered: int = Field(
        default=0, description="发现的关键词候选数"
    )
    candidates_classified: int = Field(
        default=0, description="分类后的关键词数"
    )
    pages_generated: int = Field(default=0, description="生成的页面数")
    pages_published: int = Field(default=0, description="发布的页面数")
    pages_failed: int = Field(default=0, description="失败的页面数")
    drift_check_results: list[dict] = Field(
        default_factory=list, description="漂移检测结果列表"
    )
    llm_cost_usd: float = Field(default=0.0, description="LLM 成本 USD")
    llm_tokens_used: int = Field(default=0, description="LLM Token 使用量")
    errors: list[str] = Field(default_factory=list, description="错误列表")


class ReportGenerator:
    """
    SEO Worker 运行报告生成器。

    生成三种类型的报告：
    - published: 成功运行报告
    - failed: 失败候选报告
    - calibration: 相似度校准报告
    """

    def __init__(self, config: WorkerConfig, data_dir: Path) -> None:
        """
        初始化报告生成器。

        Args:
            config: Worker 配置
            data_dir: 数据目录路径
        """
        self._config = config
        self._data_dir = data_dir
        self._reports_dir = _REPORTS_DIR

    def _ensure_reports_dir(self) -> Path:
        """
        确保报告输出目录存在。

        Returns:
            报告目录路径
        """
        self._reports_dir.mkdir(parents=True, exist_ok=True)
        return self._reports_dir

    def _atomic_write(self, target: Path, content: str) -> None:
        """
        原子写入文件：先写临时文件，再 rename。

        Args:
            target: 目标文件路径
            content: 要写入的文本内容
        """
        target.parent.mkdir(parents=True, exist_ok=True)

        fd, tmp_path = tempfile.mkstemp(
            dir=str(target.parent),
            prefix=".tmp-",
            suffix=".md",
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
            os.replace(tmp_path, str(target))
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    def generate_published_report(self, result: PipelineResult) -> Path:
        """
        生成成功运行报告。

        输出格式为 YYYYMMDD-published.md，包含运行日期、候选词数量、
        选中词、生成页面、门禁通过率、LLM 成本、token 消耗等信息。

        Args:
            result: 流水线运行结果

        Returns:
            报告文件路径
        """
        reports_dir = self._ensure_reports_dir()
        filename = f"{result.run_date}-published.md"
        target = reports_dir / filename

        pass_rate = (
            result.pages_published / max(result.pages_generated, 1) * 100
        )

        content = self._build_published_content(result, pass_rate)
        self._atomic_write(target, content)

        logger.info("Published report generated: %s", target)
        return target

    def _build_published_content(
        self, result: PipelineResult, pass_rate: float
    ) -> str:
        """
        构建成功运行报告的 Markdown 内容。

        Args:
            result: 流水线运行结果
            pass_rate: 门禁通过率百分比

        Returns:
            Markdown 报告文本
        """
        lines: list[str] = []

        lines.append(f"# SEO Worker Run Report - {result.run_date}")
        lines.append("")
        lines.append("**Status**: Published")
        lines.append(f"**Run Date**: {result.run_date}")
        lines.append("")

        # 关键词统计
        lines.append("## Keyword Statistics")
        lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Candidates discovered | {result.candidates_discovered} |")
        lines.append(f"| Candidates classified | {result.candidates_classified} |")
        lines.append("")

        # 页面生成统计
        lines.append("## Page Generation")
        lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Pages generated | {result.pages_generated} |")
        lines.append(f"| Pages published | {result.pages_published} |")
        lines.append(f"| Pages failed (gate) | {result.pages_failed} |")
        lines.append(f"| Gate pass rate | {pass_rate:.1f}% |")
        lines.append("")

        # LLM 成本统计
        lines.append("## LLM Cost & Token Usage")
        lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| LLM cost (USD) | ${result.llm_cost_usd:.4f} |")
        lines.append(f"| LLM tokens used | {result.llm_tokens_used} |")
        lines.append(f"| Cost budget (USD) | ${self._config.seo_llm_daily_cost_budget_usd:.2f} |")
        lines.append(f"| Token budget | {self._config.seo_llm_daily_token_budget} |")
        lines.append("")

        # 漂移检测结果
        if result.drift_check_results:
            lines.append("## Drift Check Results")
            lines.append("")
            lines.append("| Slug | Similarity | Drifted | Checked At |")
            lines.append("|------|------------|---------|------------|")
            for drift in result.drift_check_results:
                lines.append(
                    f"| {drift.get('slug', 'N/A')} | "
                    f"{drift.get('similarity', 0):.3f} | "
                    f"{'Yes' if drift.get('is_drifted', False) else 'No'} | "
                    f"{drift.get('checked_at', 'N/A')} |"
                )
            lines.append("")

        # 错误列表
        if result.errors:
            lines.append("## Errors")
            lines.append("")
            for error in result.errors:
                lines.append(f"- {error}")
            lines.append("")

        return "\n".join(lines)

    def generate_failed_report(
        self, failures: list[FailureRecord]
    ) -> Path:
        """
        生成失败候选报告。

        输出格式为 YYYYMMDD-failed-candidates.md，
        包含每个被拒候选的 keyword/failed_gate/reason/recommended_next_action。

        Args:
            failures: 失败记录列表

        Returns:
            报告文件路径
        """
        reports_dir = self._ensure_reports_dir()
        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        filename = f"{today}-failed-candidates.md"
        target = reports_dir / filename

        content = self._build_failed_content(failures)
        self._atomic_write(target, content)

        logger.info("Failed candidates report generated: %s", target)
        return target

    def _build_failed_content(
        self, failures: list[FailureRecord]
    ) -> str:
        """
        构建失败候选报告的 Markdown 内容。

        Args:
            failures: 失败记录列表

        Returns:
            Markdown 报告文本
        """
        lines: list[str] = []
        today = datetime.now(timezone.utc).strftime("%Y%m%d")

        lines.append(f"# SEO Worker Failed Candidates Report - {today}")
        lines.append("")
        lines.append(f"**Total Failed Candidates**: {len(failures)}")
        lines.append("")

        # 汇总表
        lines.append("## Summary")
        lines.append("")
        lines.append("| Keyword | Failed Gate | Status | Retry Count | Next Action |")
        lines.append("|---------|-------------|--------|-------------|-------------|")

        for f in failures:
            lines.append(
                f"| {f.keyword} | {f.failed_gate} | {f.status} | "
                f"{f.attempt_count} | {f.recommended_next_action} |"
            )
        lines.append("")

        # 详细信息
        lines.append("## Detailed Failure Records")
        lines.append("")
        for f in failures:
            lines.append(f"### {f.keyword}")
            lines.append("")
            lines.append(f"- **Keyword**: {f.keyword}")
            lines.append(f"- **Page Type**: {f.page_type or 'N/A'}")
            lines.append(f"- **Failed Gate**: {f.failed_gate}")
            lines.append(f"- **Status**: {f.status}")
            lines.append(f"- **Attempt Count**: {f.attempt_count}")
            lines.append(f"- **Failure Reasons**: {', '.join(f.failure_reasons)}")
            lines.append(f"- **Recommended Next Action**: {f.recommended_next_action}")
            lines.append(f"- **Last Attempt**: {f.last_attempt_at}")
            if f.next_retry_after:
                lines.append(f"- **Next Retry After**: {f.next_retry_after}")
            lines.append("")

        return "\n".join(lines)

    def generate_calibration_report(
        self, drift_results: list[dict]
    ) -> Path:
        """
        生成相似度校准报告。

        输出格式为 similarity-calibration-YYYYMMDD.md，
        包含各区块的相似度阈值和检测结果统计。

        Args:
            drift_results: 漂移检测结果列表（字典格式）

        Returns:
            报告文件路径
        """
        reports_dir = self._ensure_reports_dir()
        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        filename = f"similarity-calibration-{today}.md"
        target = reports_dir / filename

        content = self._build_calibration_content(drift_results)
        self._atomic_write(target, content)

        logger.info("Calibration report generated: %s", target)
        return target

    def _build_calibration_content(
        self, drift_results: list[dict]
    ) -> str:
        """
        构建相似度校准报告的 Markdown 内容。

        Args:
            drift_results: 漂移检测结果列表

        Returns:
            Markdown 报告文本
        """
        lines: list[str] = []
        today = datetime.now(timezone.utc).strftime("%Y%m%d")

        lines.append(f"# Similarity Calibration Report - {today}")
        lines.append("")
        lines.append(f"**Generated**: {utc_now_iso()}")
        lines.append(f"**Pages Checked**: {len(drift_results)}")
        lines.append("")

        # 当前阈值
        lines.append("## Current Thresholds")
        lines.append("")
        lines.append("| Section | Threshold |")
        lines.append("|---------|-----------|")
        lines.append("| title | 0.85 |")
        lines.append("| meta_description | 0.85 |")
        lines.append("| body | 0.82 |")
        lines.append("| example | 0.78 |")
        lines.append("| faq | 0.80 |")
        lines.append("")

        # 检测结果统计
        drifted_count = sum(
            1 for r in drift_results if r.get("is_drifted", False)
        )
        lines.append("## Drift Statistics")
        lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Pages checked | {len(drift_results)} |")
        lines.append(f"| Pages drifted | {drifted_count} |")
        lines.append(f"| Pages stable | {len(drift_results) - drifted_count} |")
        lines.append("")

        # 各页面结果
        if drift_results:
            lines.append("## Per-Page Results")
            lines.append("")
            lines.append("| Slug | Similarity | Drifted | Section Scores |")
            lines.append("|------|------------|---------|----------------|")
            for r in drift_results:
                scores = r.get("section_scores", {})
                scores_str = ", ".join(
                    f"{k}={v:.3f}" for k, v in scores.items()
                ) if scores else "N/A"
                lines.append(
                    f"| {r.get('slug', 'N/A')} | "
                    f"{r.get('similarity', 0):.3f} | "
                    f"{'Yes' if r.get('is_drifted', False) else 'No'} | "
                    f"{scores_str} |"
                )
            lines.append("")

        # 校准建议
        lines.append("## Calibration Notes")
        lines.append("")
        lines.append("- Initial thresholds set per scope document specifications")
        lines.append("- Recalibrate after 25 published pages")
        lines.append("- Recalibrate again after 100 published pages")
        lines.append("- Current page count: check seo-pages.json for total published")
        lines.append("")

        return "\n".join(lines)