"""
DND Prompt Forge - 页面发布模块
将质量门禁通过的页面写入前端目录，更新 sitemap 和注册表
"""

import logging
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from seo_worker.config import WorkerConfig
from seo_worker.models import GeneratedPage, PageRecord, utc_now_iso
from seo_worker.registry import Registry

logger = logging.getLogger(__name__)


class PublishResult:
    """
    发布操作结果。

    记录发布成功/失败状态及相关信息。
    """

    def __init__(
        self,
        success: bool,
        slug: str,
        output_path: str = "",
        error: str = "",
    ) -> None:
        """
        初始化发布结果。

        Args:
            success: 是否成功
            slug: 页面 slug
            output_path: 输出文件路径
            error: 错误信息
        """
        self.success = success
        self.slug = slug
        self.output_path = output_path
        self.error = error


class Publisher:
    """
    页面发布器。

    将质量门禁通过的页面写入 frontend/generated/<slug>/index.html，
    使用 write-tmp-then-rename 原子写入，写入前备份旧版本。
    """

    def __init__(self, config: WorkerConfig, registry: Registry) -> None:
        """
        初始化发布器。

        Args:
            config: Worker 配置，包含输出目录路径
            registry: 注册表实例，用于更新页面记录和 sitemap
        """
        self._config = config
        self._registry = registry
        self._output_dir = Path(config.seo_output_dir)
        self._data_dir = Path(config.seo_data_dir)
        self._backup_dir = self._data_dir / "backups"

    async def publish(self, page: GeneratedPage) -> PublishResult:
        """
        发布页面到前端目录，更新 sitemap 和注册表。

        使用 write-tmp-then-rename 原子写入，写入前备份旧版本。

        Args:
            page: 待发布的生成页面

        Returns:
            发布结果
        """
        slug = page.slug
        page_dir = self._output_dir / slug
        target_file = page_dir / "index.html"

        try:
            # 备份旧版本
            if target_file.exists():
                self._backup_old_version(slug, target_file)

            # 原子写入新文件
            self._atomic_write_html(target_file, page.html_content)

            # 更新注册表
            record = self._build_page_record(page)
            self._registry.add_page(record)

            # 更新 sitemap
            self._registry.update_sitemap(self._config.seo_base_url)

            logger.info("Published page: %s -> %s", slug, target_file)
            return PublishResult(
                success=True,
                slug=slug,
                output_path=str(target_file),
            )

        except Exception as exc:
            logger.error("Failed to publish page '%s': %s", slug, exc)
            return PublishResult(
                success=False,
                slug=slug,
                error=str(exc),
            )

    async def rollback(self, slug: str) -> None:
        """
        回滚已发布的页面，从备份恢复旧版本。

        Args:
            slug: 要回滚的页面 slug

        Raises:
            FileNotFoundError: 当备份不存在时
        """
        page_dir = self._output_dir / slug
        target_file = page_dir / "index.html"

        # 查找最近的备份
        backup_pattern = f"{slug}_*.html"
        backups = sorted(self._backup_dir.glob(backup_pattern), reverse=True)

        if not backups:
            raise FileNotFoundError(f"No backup found for slug '{slug}'")

        latest_backup = backups[0]

        try:
            # 原子写入恢复的备份
            self._atomic_write_html(target_file, latest_backup.read_text(encoding="utf-8"))

            # 清理已使用的备份
            latest_backup.unlink()

            logger.info("Rolled back page '%s' from backup %s", slug, latest_backup.name)

        except Exception as exc:
            logger.error("Failed to rollback page '%s': %s", slug, exc)
            raise

    def _backup_old_version(self, slug: str, target_file: Path) -> None:
        """
        备份旧版本页面到 seo_data/backups/。

        Args:
            slug: 页面 slug
            target_file: 当前文件路径
        """
        self._backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        backup_name = f"{slug}_{timestamp}.html"
        backup_path = self._backup_dir / backup_name

        shutil.copy2(str(target_file), str(backup_path))
        logger.debug("Backed up '%s' to %s", slug, backup_path)

    def _atomic_write_html(self, target: Path, content: str) -> None:
        """
        原子写入 HTML 文件：先写临时文件，再 rename。

        Args:
            target: 目标文件路径
            content: HTML 内容
        """
        # 确保目录存在
        target.parent.mkdir(parents=True, exist_ok=True)

        # 写入临时文件
        fd, tmp_path = tempfile.mkstemp(
            dir=str(target.parent),
            prefix=".tmp-",
            suffix=".html",
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
            # rename 是原子操作
            os.replace(tmp_path, str(target))
        except Exception:
            # 清理临时文件
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    def _build_page_record(self, page: GeneratedPage) -> PageRecord:
        """
        从生成页面构建注册表记录。

        Args:
            page: 生成页面数据

        Returns:
            页面记录
        """
        # 推断 canonical_group：NPC 归入 character 组
        page_type_for_group = page.page_type
        if page_type_for_group == "npc":
            page_type_for_group = "character"

        return PageRecord(
            slug=page.slug,
            keyword=page.h1,
            page_type=page.page_type,
            status="published",
            url_path=f"/{page.slug}",
            canonical_url=page.canonical_url,
            canonical_group=f"{page_type_for_group}:{page.slug}",
            primary_keyword=page.h1,
            intent=page.page_type,
            published_at=utc_now_iso(),
            last_checked_at=utc_now_iso(),
        )
