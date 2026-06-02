"""
DND Prompt Forge - SEO Worker 主流水线
编排完整的 SEO 内容生成流水线：发现 -> 分类 -> 生成 -> 门禁 -> 发布 -> 漂移检测 -> 报告
"""

import asyncio
import fcntl
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from openai import AsyncOpenAI

from seo_worker.classifier import Classifier
from seo_worker.config import WorkerConfig
from seo_worker.discoverer import Discoverer
from seo_worker.drift_detector import DriftDetector
from seo_worker.generator import Generator
from seo_worker.models import (
    ClassifiedKeyword,
    FailureRecord,
    GeneratedPage,
    KeywordCandidate,
    PageRecord,
    utc_now_iso,
)
from seo_worker.publisher import Publisher
from seo_worker.quality_gate import QualityGate
from seo_worker.registry import Registry
from seo_worker.report import PipelineResult, ReportGenerator, _serialize_for_json

logger = logging.getLogger(__name__)

# 文件锁路径
_LOCK_FILE = ".worker.lock"

# 漂移检测过期阈值天数
_STALE_THRESHOLD_DAYS = 30


class SEOPipeline:
    """
    SEO Worker 主流水线。

    编排完整的 SEO 内容生成流程：
    1. 获取文件锁（防并发）
    2. 加载注册表
    3. 运行关键词发现
    4. 运行分类评分
    5. 对每个选中关键词：生成 -> 门禁 -> 发布/记录失败
    6. 运行内容漂移检测
    7. 生成运行报告
    8. 释放文件锁
    """

    def __init__(self, config: WorkerConfig) -> None:
        """
        初始化流水线。

        Args:
            config: Worker 配置
        """
        self._config = config
        self._data_dir = Path(config.seo_data_dir)
        self._lock_path = self._data_dir / _LOCK_FILE

    async def run(
        self,
        dry_run: bool = False,
        max_pages: int | None = None,
    ) -> PipelineResult:
        """
        执行完整的 SEO Worker 流水线。

        Args:
            dry_run: 干跑模式，不写入文件不调用 LLM
            max_pages: 覆盖每轮最大生成页数

        Returns:
            流水线运行结果
        """
        run_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        result = PipelineResult(run_date=run_date)

        # 获取文件锁
        lock_fd = self._acquire_lock()
        if lock_fd is None:
            result.errors.append("Another SEO Worker instance is already running")
            return result

        try:
            await self._execute_pipeline(
                result, dry_run=dry_run, max_pages=max_pages
            )
        except Exception as exc:
            logger.error("Pipeline execution failed: %s", exc)
            result.errors.append(f"Pipeline execution failed: {exc}")
        finally:
            self._release_lock(lock_fd)

        return result

    def _acquire_lock(self) -> int | None:
        """
        获取文件锁，确保单实例运行。

        使用 fcntl.flock 非阻塞模式，获取失败返回 None。

        Returns:
            锁文件描述符，获取失败返回 None
        """
        self._data_dir.mkdir(parents=True, exist_ok=True)

        try:
            fd = os.open(str(self._lock_path), os.O_CREAT | os.O_WRONLY)
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            # 写入当前 PID
            os.write(fd, str(os.getpid()).encode("utf-8"))
            return fd
        except (OSError, IOError):
            logger.warning("Failed to acquire worker lock - another instance is running")
            return None

    def _release_lock(self, lock_fd: int | None) -> None:
        """
        释放文件锁。

        Args:
            lock_fd: 锁文件描述符
        """
        if lock_fd is not None:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
                os.close(lock_fd)
            except (OSError, IOError):
                pass

            # 清理锁文件
            try:
                os.unlink(str(self._lock_path))
            except OSError:
                pass

    async def _execute_pipeline(
        self,
        result: PipelineResult,
        dry_run: bool = False,
        max_pages: int | None = None,
    ) -> None:
        """
        执行流水线各阶段。

        某步失败不阻断整个流水线，错误记录到 result.errors。

        Args:
            result: 流水线运行结果（就地修改）
            dry_run: 干跑模式
            max_pages: 覆盖最大生成页数
        """
        # 初始化注册表
        self._data_dir.mkdir(parents=True, exist_ok=True)
        registry = Registry(self._data_dir)

        # 创建单例 LLM 客户端
        llm_client = None if dry_run else self._create_llm_client()

        # 阶段 1: 关键词发现
        candidates = await self._run_discovery(
            llm_client, dry_run, result
        )
        result.candidates_discovered = len(candidates)

        # 阶段 2: 分类评分
        classified = await self._run_classification(
            candidates, llm_client, dry_run, result
        )
        result.candidates_classified = len(classified)

        # 阶段 3: 内容生成 + 质量门禁 + 发布
        max_pages_limit = max_pages or self._config.seo_llm_max_generated_pages_per_run
        await self._run_generation_loop(
            classified, registry, llm_client, dry_run, max_pages_limit, result
        )

        # 阶段 4: 内容漂移检测
        drift_results = await self._run_drift_detection(registry, result)

        # 阶段 5: 生成运行报告
        self._generate_reports(result, registry)

        logger.info(
            "Pipeline complete: discovered=%d, classified=%d, "
            "published=%d, failed=%d, errors=%d",
            result.candidates_discovered,
            result.candidates_classified,
            result.pages_published,
            result.pages_failed,
            len(result.errors),
        )

    def _create_llm_client(self) -> AsyncOpenAI | None:
        """
        创建单例 LLM 客户端，供所有模块复用。

        Returns:
            AsyncOpenAI 客户端实例，无 API key 时返回 None
        """
        api_key = self._config.llm_api_key
        if not api_key:
            logger.info("No LLM API key configured, LLM calls will be skipped")
            return None

        return AsyncOpenAI(
            api_key=api_key,
            base_url=self._config.llm_base_url,
            timeout=40,
        )

    async def _run_discovery(
        self,
        llm_client: AsyncOpenAI | None,
        dry_run: bool,
        result: PipelineResult,
    ) -> list[KeywordCandidate]:
        """
        执行关键词发现阶段。

        Args:
            llm_client: LLM 客户端
            dry_run: 干跑模式
            result: 流水线结果（记录错误）

        Returns:
            发现的关键词候选列表
        """
        logger.info("Phase 1: Keyword discovery")
        try:
            discoverer = Discoverer(self._config, llm_client=llm_client)
            candidates = await discoverer.discover()
            logger.info("Discovered %d keyword candidates", len(candidates))
            return candidates
        except Exception as exc:
            logger.error("Keyword discovery failed: %s", exc)
            result.errors.append(f"Discovery failed: {exc}")
            return []

    async def _run_classification(
        self,
        candidates: list[KeywordCandidate],
        llm_client: AsyncOpenAI | None,
        dry_run: bool,
        result: PipelineResult,
    ) -> list[ClassifiedKeyword]:
        """
        执行分类评分阶段。

        Args:
            candidates: 关键词候选列表
            llm_client: LLM 客户端
            dry_run: 干跑模式
            result: 流水线结果（记录错误）

        Returns:
            分类后的关键词列表
        """
        logger.info("Phase 2: Keyword classification")
        try:
            classifier = Classifier(self._config, llm_client=llm_client)
            classified = await classifier.classify(candidates)
            logger.info("Classified %d keywords", len(classified))
            return classified
        except Exception as exc:
            logger.error("Classification failed: %s", exc)
            result.errors.append(f"Classification failed: {exc}")
            return []

    async def _run_generation_loop(
        self,
        classified: list[ClassifiedKeyword],
        registry: Registry,
        llm_client: AsyncOpenAI | None,
        dry_run: bool,
        max_pages: int,
        result: PipelineResult,
    ) -> None:
        """
        执行内容生成 + 质量门禁 + 发布循环。

        对每个选中关键词：生成页面 -> 质量门禁 -> 通过则发布，未通过则记录失败。
        每步之间插入 2 秒延迟控制 LLM 频率。

        Args:
            classified: 分类后的关键词列表
            registry: 注册表实例
            llm_client: LLM 客户端
            dry_run: 干跑模式
            max_pages: 最大生成页数
            result: 流水线结果（就地修改）
        """
        logger.info("Phase 3: Content generation + quality gate + publish")

        generator = Generator(self._config, llm_client=llm_client)
        gate = QualityGate(self._config, registry=registry)
        publisher = Publisher(self._config, registry)

        published_count = 0
        failed_count = 0

        for keyword in classified[:max_pages]:
            # 检查 LLM 成本预算
            if not self._check_budget(result):
                logger.warning("LLM budget exceeded, stopping generation")
                break

            # 生成页面
            page = await self._generate_page(generator, keyword, result)
            if page is None:
                failed_count += 1
                result.pages_failed = failed_count
                continue

            result.pages_generated += 1

            # 生成后立即检查 LLM 成本预算（C-04 修复）
            if not self._check_budget(result):
                logger.warning("LLM budget exceeded after generation, stopping")
                result.pages_published = published_count
                result.pages_failed = failed_count
                break

            # 质量门禁
            gate_result = await gate.evaluate(page)

            if gate_result.passed:
                published = await self._publish_page(
                    publisher, page, dry_run, result
                )
                if published:
                    published_count += 1
                    result.pages_published = published_count
            else:
                failed_count += 1
                result.pages_failed = failed_count
                self._record_failure(registry, keyword, gate_result, dry_run)

            # LLM 调用频率控制：2 秒间隔
            if not dry_run and llm_client is not None:
                await asyncio.sleep(2)

    def _check_budget(self, result: PipelineResult) -> bool:
        """
        检查 LLM 成本是否仍在预算内。

        超过 50% token 预算用于候选分析时停止内容生成。

        Args:
            result: 流水线结果

        Returns:
            是否仍在预算内
        """
        if result.llm_cost_usd > self._config.seo_llm_daily_cost_budget_usd:
            return False

        if result.llm_tokens_used > self._config.seo_llm_daily_token_budget:
            return False

        return True

    async def _generate_page(
        self,
        generator: Generator,
        keyword: ClassifiedKeyword,
        result: PipelineResult,
    ) -> GeneratedPage | None:
        """
        生成单个页面，处理异常。

        Args:
            generator: 页面生成器
            keyword: 分类关键词
            result: 流水线结果（记录错误）

        Returns:
            生成的页面，失败返回 None
        """
        try:
            page = await generator.generate(keyword)
            # 累计 LLM 成本（从 raw output 提取）
            cost = page.llm_raw_output.get("estimated_llm_cost_usd", 0.0)
            if isinstance(cost, (int, float)):
                result.llm_cost_usd += cost
            tokens = page.llm_raw_output.get("token_budget", 0)
            if isinstance(tokens, int):
                result.llm_tokens_used += tokens
            return page
        except Exception as exc:
            logger.error("Page generation failed for '%s': %s", keyword.keyword, exc)
            result.errors.append(f"Generation failed for '{keyword.keyword}': {exc}")
            return None

    async def _publish_page(
        self,
        publisher: Publisher,
        page: GeneratedPage,
        dry_run: bool,
        result: PipelineResult,
    ) -> bool:
        """
        发布单个页面，处理异常。

        Args:
            publisher: 发布器
            page: 待发布的页面
            dry_run: 干跑模式
            result: 流水线结果（记录错误）

        Returns:
            是否发布成功
        """
        if dry_run:
            logger.info("Dry run: would publish '%s'", page.slug)
            return True

        try:
            pub_result = await publisher.publish(page)
            if pub_result.success:
                logger.info("Published: %s", pub_result.slug)
                return True
            else:
                logger.error(
                    "Publish failed for '%s': %s",
                    pub_result.slug,
                    pub_result.error,
                )
                result.errors.append(
                    f"Publish failed for '{pub_result.slug}': {pub_result.error}"
                )
                return False
        except Exception as exc:
            logger.error("Publish exception for '%s': %s", page.slug, exc)
            result.errors.append(f"Publish exception for '{page.slug}': {exc}")
            return False

    def _record_failure(
        self,
        registry: Registry,
        keyword: ClassifiedKeyword,
        gate_result: object,
        dry_run: bool,
    ) -> None:
        """
        记录质量门禁失败的关键词到失败注册表。

        Args:
            registry: 注册表实例
            keyword: 失败的分类关键词
            gate_result: 质量门禁结果
            dry_run: 干跑模式
        """
        if dry_run:
            return

        try:
            failure_reasons = getattr(gate_result, "failure_reasons", [])
            reasons = failure_reasons if isinstance(failure_reasons, list) else []
            failed_gate = reasons[0] if reasons else "unknown"

            record = FailureRecord(
                keyword=keyword.keyword,
                page_type=keyword.page_type,
                status="retry_later",
                failure_reasons=reasons,
                attempt_count=1,
                failed_gate=failed_gate,
                recommended_next_action="retry_next_day",
            )
            registry.add_failure(record)
        except Exception as exc:
            logger.error("Failed to record failure for '%s': %s", keyword.keyword, exc)

    async def _run_drift_detection(
        self,
        registry: Registry,
        result: PipelineResult,
    ) -> list[dict]:
        """
        执行内容漂移检测。

        检查已有页面的过期状态，结果写入流水线结果。

        Args:
            registry: 注册表实例
            result: 流水线结果（就地修改）

        Returns:
            漂移检测结果列表（字典格式）
        """
        logger.info("Phase 4: Content drift detection")
        try:
            detector = DriftDetector(self._config)
            drift_results = await detector.check_stale_pages(
                registry, _STALE_THRESHOLD_DAYS
            )
            result.drift_check_results = [
                _serialize_for_json(r.model_dump()) for r in drift_results
            ]
            return result.drift_check_results
        except Exception as exc:
            logger.error("Drift detection failed: %s", exc)
            result.errors.append(f"Drift detection failed: {exc}")
            return []

    def _generate_reports(
        self,
        result: PipelineResult,
        registry: Registry,
    ) -> None:
        """
        生成运行报告。

        包括成功运行报告和失败候选报告。

        Args:
            result: 流水线运行结果
            registry: 注册表实例
        """
        logger.info("Phase 5: Report generation")
        try:
            report_gen = ReportGenerator(self._config, self._data_dir)

            # 生成成功报告
            report_gen.generate_published_report(result)

            # 生成失败候选报告
            failures = registry.get_retryable_failures()
            if failures:
                report_gen.generate_failed_report(failures)

        except Exception as exc:
            logger.error("Report generation failed: %s", exc)
            result.errors.append(f"Report generation failed: {exc}")