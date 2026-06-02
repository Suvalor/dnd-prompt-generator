"""
DND Prompt Forge - 注册表管理模块
管理 seo-pages.json 和 seo-failures.json，提供原子写入和 sitemap 更新
"""

import json
import logging
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring, indent

from seo_worker.models import (
    FailureRecord,
    PageRecord,
    utc_now_iso,
)

logger = logging.getLogger(__name__)

# JSON 注册表文件的结构版本
_REGISTRY_VERSION = "1.0"


class Registry:
    """
    页面与失败注册表管理器。

    管理 seo-pages.json 和 seo-failures.json，
    使用 write-tmp-then-rename 模式确保原子写入。
    """

    def __init__(self, data_dir: Path) -> None:
        """
        初始化注册表。

        Args:
            data_dir: 数据目录路径，包含 seo-pages.json 和 seo-failures.json
        """
        self._data_dir = data_dir
        self._pages_file = data_dir / "seo-pages.json"
        self._failures_file = data_dir / "seo-failures.json"
        self._sitemap_file = data_dir / "sitemap.xml"

    def get_published_slugs(self) -> set[str]:
        """
        获取已发布页面的 slug 集合。

        Returns:
            已发布 slug 的集合
        """
        pages = self._read_pages()
        return {
            p["slug"]
            for p in pages
            if p.get("status") == "published"
        }

    def get_pages_by_canonical_group(self, canonical_group: str) -> list[dict]:
        """
        根据 canonical_group 获取页面记录列表。

        用于质量门禁检查同意图是否已有 published 页面。

        Args:
            canonical_group: canonical 分组标识

        Returns:
            同组页面记录字典列表
        """
        pages = self._read_pages()
        return [
            p for p in pages
            if p.get("canonical_group") == canonical_group
        ]

    def get_failed_keywords(self) -> set[str]:
        """
        获取失败关键词集合。

        Returns:
            失败关键词的集合
        """
        failures = self._read_failures()
        return {f["keyword"] for f in failures}

    def add_page(self, record: PageRecord) -> None:
        """
        添加页面记录到注册表。

        如果 slug 已存在则更新，否则追加。

        Args:
            record: 页面记录
        """
        pages = self._read_pages()
        # 查找并更新或追加
        updated = False
        for i, p in enumerate(pages):
            if p["slug"] == record.slug:
                pages[i] = record.model_dump()
                updated = True
                break

        if not updated:
            pages.append(record.model_dump())

        self._write_pages(pages)
        logger.info("Page record %s: %s", "updated" if updated else "added", record.slug)

    def add_failure(self, record: FailureRecord) -> None:
        """
        添加失败记录到注册表。

        如果关键词已存在则更新 attempt_count，否则追加。

        Args:
            record: 失败记录
        """
        failures = self._read_failures()
        # 查找并更新或追加
        updated = False
        for i, f in enumerate(failures):
            if f["keyword"] == record.keyword:
                failures[i] = record.model_dump()
                updated = True
                break

        if not updated:
            failures.append(record.model_dump())

        self._write_failures(failures)
        logger.info("Failure record %s: %s", "updated" if updated else "added", record.keyword)

    def get_retryable_failures(self) -> list[FailureRecord]:
        """
        获取可重试的失败项。

        可重试条件：status 为 retry_later 且 next_retry_after 已过期或为空。

        Returns:
            可重试的失败记录列表
        """
        failures = self._read_failures()
        now = datetime.now(timezone.utc)
        retryable: list[FailureRecord] = []

        for f in failures:
            if f.get("status") != "retry_later":
                continue
            if f.get("attempt_count", 0) >= 3:
                continue
            retry_after = f.get("next_retry_after")
            if retry_after is None:
                retryable.append(FailureRecord(**f))
                continue
            try:
                retry_time = datetime.fromisoformat(retry_after)
                if now >= retry_time:
                    retryable.append(FailureRecord(**f))
            except (ValueError, TypeError):
                # 无法解析时间，视为可重试
                retryable.append(FailureRecord(**f))

        return retryable

    def get_stale_pages(self, threshold_days: int) -> list[PageRecord]:
        """
        获取过期页面。

        Args:
            threshold_days: 过期天数阈值

        Returns:
            超过阈值的页面记录列表
        """
        pages = self._read_pages()
        now = datetime.now(timezone.utc)
        threshold = timedelta(days=threshold_days)
        stale: list[PageRecord] = []

        for p in pages:
            if p.get("status") != "published":
                continue
            last_checked = p.get("last_checked_at")
            if last_checked is None:
                # 从未检查过，视为过期
                stale.append(PageRecord(**p))
                continue
            try:
                checked_time = datetime.fromisoformat(last_checked)
                if now - checked_time > threshold:
                    stale.append(PageRecord(**p))
            except (ValueError, TypeError):
                stale.append(PageRecord(**p))

        return stale

    def update_sitemap(self, base_url: str) -> None:
        """
        基于 seo-pages.json 更新 sitemap.xml。

        只包含 status=published 的页面。

        Args:
            base_url: 站点基础 URL
        """
        pages = self._read_pages()
        published = [p for p in pages if p.get("status") == "published"]

        urlset = Element("urlset")
        urlset.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")

        for p in published:
            url_elem = SubElement(urlset, "url")

            loc = SubElement(url_elem, "loc")
            loc.text = p.get("canonical_url", f"{base_url}/{p.get('slug', '')}")

            lastmod = SubElement(url_elem, "lastmod")
            lastmod.text = p.get("updated_at", utc_now_iso())[:10]

            priority = SubElement(url_elem, "priority")
            # 长尾页面优先级 0.6，首页 0.8
            priority.text = "0.6"

            changefreq = SubElement(url_elem, "changefreq")
            changefreq.text = "weekly"

        indent(urlset, space="  ")

        sitemap_path = self._sitemap_file
        xml_bytes = tostring(urlset, encoding="unicode", xml_declaration=False)
        self._atomic_write(
            sitemap_path,
            '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_bytes + "\n",
        )
        logger.info("Sitemap updated with %d published pages", len(published))

    # ========================================================================
    # 内部方法：文件读写
    # ========================================================================

    def _read_pages(self) -> list[dict]:
        """
        读取 seo-pages.json 中的页面列表。

        Returns:
            页面记录字典列表
        """
        if not self._pages_file.exists():
            return []
        try:
            data = json.loads(self._pages_file.read_text(encoding="utf-8"))
            return data.get("pages", [])
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to read pages file: %s", exc)
            return []

    def _read_failures(self) -> list[dict]:
        """
        读取 seo-failures.json 中的失败列表。

        Returns:
            失败记录字典列表
        """
        if not self._failures_file.exists():
            return []
        try:
            data = json.loads(self._failures_file.read_text(encoding="utf-8"))
            return data.get("failures", [])
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to read failures file: %s", exc)
            return []

    def _write_pages(self, pages: list[dict]) -> None:
        """
        写入 seo-pages.json，使用 write-tmp-then-rename 模式。

        Args:
            pages: 页面记录字典列表
        """
        data = {
            "version": _REGISTRY_VERSION,
            "last_updated": utc_now_iso(),
            "pages": pages,
        }
        self._atomic_write_json(self._pages_file, data)

    def _write_failures(self, failures: list[dict]) -> None:
        """
        写入 seo-failures.json，使用 write-tmp-then-rename 模式。

        Args:
            failures: 失败记录字典列表
        """
        data = {
            "version": _REGISTRY_VERSION,
            "last_updated": utc_now_iso(),
            "failures": failures,
        }
        self._atomic_write_json(self._failures_file, data)

    def _atomic_write_json(self, target: Path, data: dict) -> None:
        """
        原子写入 JSON 文件：先写临时文件，再 rename。

        Args:
            target: 目标文件路径
            data: 要写入的字典数据
        """
        content = json.dumps(data, indent=2, ensure_ascii=False)
        self._atomic_write(target, content)

    def _atomic_write(self, target: Path, content: str) -> None:
        """
        原子写入文件：先写临时文件，再 rename。

        Args:
            target: 目标文件路径
            content: 要写入的文本内容
        """
        # 确保目录存在
        target.parent.mkdir(parents=True, exist_ok=True)

        # 写入临时文件
        fd, tmp_path = tempfile.mkstemp(
            dir=str(target.parent),
            prefix=".tmp-",
            suffix=target.suffix,
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
