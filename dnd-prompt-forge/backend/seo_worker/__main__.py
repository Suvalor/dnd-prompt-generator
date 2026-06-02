"""
DND Prompt Forge - SEO Worker CLI 入口点
支持 python -m seo_worker run 启动完整流水线
"""

import argparse
import asyncio
import logging
import sys

from seo_worker.config import WorkerConfig
from seo_worker.pipeline import SEOPipeline

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        prog="seo_worker",
        description="DND Prompt Forge - SEO Content Worker",
    )
    subparsers = parser.add_subparsers(dest="command")

    # run 子命令
    run_parser = subparsers.add_parser("run", help="Run the SEO content generation pipeline")
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode: no files written, no LLM calls made",
    )
    run_parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Override max generated pages per run",
    )

    return parser.parse_args()


def main() -> None:
    """CLI 主入口。"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    args = parse_args()

    if args.command is None:
        logger.error("No command specified. Usage: python -m seo_worker <command> [options]")
        sys.exit(1)

    config = WorkerConfig()
    logger.info(
        "SEO Worker config loaded: data_dir=%s, output_dir=%s",
        config.seo_data_dir,
        config.seo_output_dir,
    )

    if args.command == "run":
        asyncio.run(
            _run_pipeline(config, dry_run=args.dry_run, max_pages=args.max_pages)
        )


async def _run_pipeline(
    config: WorkerConfig,
    dry_run: bool = False,
    max_pages: int | None = None,
) -> None:
    """
    使用 SEOPipeline 执行 SEO 内容生成流水线。

    Args:
        config: Worker 配置
        dry_run: 干跑模式，不写入文件不调用 LLM
        max_pages: 覆盖每轮最大生成页数
    """
    logger.info("Starting SEO Worker pipeline (dry_run=%s)", dry_run)

    pipeline = SEOPipeline(config)
    result = await pipeline.run(dry_run=dry_run, max_pages=max_pages)

    logger.info(
        "SEO Worker pipeline complete: published=%d, failed=%d, errors=%d",
        result.pages_published,
        result.pages_failed,
        len(result.errors),
    )

    if result.errors:
        for error in result.errors:
            logger.error("Pipeline error: %s", error)


if __name__ == "__main__":
    main()
