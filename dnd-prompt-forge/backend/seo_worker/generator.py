"""
DND Prompt Forge - 页面生成模块
使用 LLM 生成结构化内容，Jinja2 渲染 HTML 页面
"""

import html
import json
import logging
import os
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from openai import AsyncOpenAI

from seo_worker.config import WorkerConfig
from seo_worker.models import (
    ClassifiedKeyword,
    ExamplePrompt,
    FAQItem,
    GeneratedPage,
    InternalLink,
    utc_now_iso,
)

logger = logging.getLogger(__name__)

# LLM 生成页面内容的系统提示词
_GENERATE_SYSTEM_PROMPT = """You are a content writer for a DND prompt generator website (dndpromptforge.com).
Generate SEO-optimized content for a specific long-tail keyword page.

The page helps DND players, DMs, and VTT users create AI image prompts for their characters and scenes.

Output must be a JSON object with these EXACT fields:
{
  "title": "string, 10-70 chars, include the keyword naturally",
  "meta_description": "string, 50-160 chars, compelling description with keyword",
  "h1": "string, 5-100 chars, main heading with keyword",
  "intro": "string, 100-300 chars, introduction paragraph",
  "examples": [
    {
      "badge": "string, short label like 'Heroic' or 'Dark'",
      "name": "string, example name",
      "positive": "string, the positive prompt text",
      "negative": "string, the negative prompt text"
    }
  ],
  "faqs": [
    {
      "question": "string, a common question about this keyword topic",
      "answer": "string, helpful answer 50-200 chars"
    }
  ],
  "internal_links": [
    {
      "label": "string, link text",
      "href": "string, relative URL path like /slug"
    }
  ]
}

Requirements:
- Generate 3-8 example prompts that are genuinely useful for AI image generation
- Generate 3-5 FAQ items that answer real questions DND players would have
- Generate 3-5 internal links to related pages on the site
- All content must be original, helpful, and DND-specific
- No keyword stuffing, no hidden text, no spam
- Examples should vary in style and mood"""


def sanitize_slug(keyword: str) -> str:
    """
    将关键词转换为 URL-safe slug，只保留 [a-z0-9-]。

    Args:
        keyword: 原始关键词

    Returns:
        清理后的 slug
    """
    slug = keyword.lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    slug = slug.strip("-")
    return slug


def build_prefill(keyword: ClassifiedKeyword) -> dict | None:
    """
    根据分类关键词构建 generator 预填数据。

    Args:
        keyword: 已分类的关键词

    Returns:
        预填字典或 None
    """
    prefill: dict[str, str] = {}

    # 页面类型映射到 generator 的 output_type
    type_map = {
        "character": "portrait",
        "token": "token",
        "monster": "monster",
        "scene": "scene",
        "npc": "npc",
    }
    if keyword.page_type in type_map:
        prefill["type"] = type_map[keyword.page_type]

    if keyword.race:
        prefill["race"] = keyword.race
    if keyword.character_class:
        prefill["class_role"] = keyword.character_class
    if keyword.theme:
        prefill["mood"] = keyword.theme

    return prefill if prefill else None


class Generator:
    """
    页面生成器。

    使用 LLM 生成结构化内容，Jinja2 渲染为 HTML 页面。
    """

    def __init__(self, config: WorkerConfig, llm_client: AsyncOpenAI | None = None) -> None:
        """
        初始化生成器，创建 Jinja2 环境。

        Args:
            config: Worker 配置，包含模板目录和 LLM 配置
            llm_client: 可选的共享 LLM 客户端，若为 None 则在调用时按需创建
        """
        self._config = config
        self._llm_client = llm_client
        self._jinja_env = self._create_jinja_env()

    def _create_jinja_env(self) -> Environment:
        """
        创建 Jinja2 环境，启用 autoescape。

        Returns:
            配置好的 Jinja2 Environment
        """
        templates_dir = Path(self._config.seo_templates_dir)
        if not templates_dir.is_absolute():
            # 相对路径基于 backend 目录
            backend_dir = Path(__file__).resolve().parent.parent
            templates_dir = backend_dir / templates_dir

        env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        return env

    async def generate(self, keyword: ClassifiedKeyword) -> GeneratedPage:
        """
        为分类关键词生成完整的 SEO 页面。

        Args:
            keyword: 已分类的关键词

        Returns:
            生成的页面数据
        """
        slug = sanitize_slug(keyword.keyword)
        canonical_url = f"{self._config.seo_base_url}/{slug}"
        prefill = build_prefill(keyword)

        # 尝试 LLM 生成内容
        llm_content = await self._llm_generate(keyword)
        if llm_content is None:
            logger.warning("LLM generation failed for '%s', using fallback", keyword.keyword)
            llm_content = self._fallback_content(keyword)

        # 构建生成页面
        page = GeneratedPage(
            slug=slug,
            page_type=keyword.page_type,
            title=llm_content.get("title", f"{keyword.keyword.title()} - DND Prompt Forge"),
            meta_description=llm_content.get("meta_description", f"Generate {keyword.keyword} with our free AI prompt generator."),
            h1=llm_content.get("h1", keyword.keyword.title()),
            intro=llm_content.get("intro", f"Create stunning {keyword.keyword} with our free DND prompt generator."),
            examples=self._parse_examples(llm_content.get("examples", [])),
            faqs=self._parse_faqs(llm_content.get("faqs", [])),
            internal_links=self._parse_internal_links(llm_content.get("internal_links", [])),
            prefill=prefill,
            canonical_url=canonical_url,
            llm_raw_output=llm_content,
        )

        # 渲染 HTML
        page.html_content = self._render_html(page)
        return page

    async def _llm_generate(self, keyword: ClassifiedKeyword) -> dict | None:
        """
        调用 LLM 生成页面内容。

        Args:
            keyword: 分类关键词

        Returns:
            LLM 生成的结构化内容字典，失败返回 None
        """
        api_key = self._config.llm_api_key
        if not api_key:
            return None

        user_prompt = self._build_user_prompt(keyword)

        try:
            client = self._llm_client or AsyncOpenAI(
                api_key=api_key,
                base_url=self._config.llm_base_url,
                timeout=40,
            )
            response = await client.chat.completions.create(
                model=self._config.llm_model,
                messages=[
                    {"role": "system", "content": _GENERATE_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                max_completion_tokens=4096,
                temperature=0.7,
            )
        except Exception as exc:
            logger.warning("LLM page generation failed: %s", exc)
            return None

        content = self._extract_content(response)
        if not content:
            return None

        return self._parse_llm_content(content)

    def _build_user_prompt(self, keyword: ClassifiedKeyword) -> str:
        """
        构建 LLM 用户提示词。

        Args:
            keyword: 分类关键词

        Returns:
            用户提示词文本
        """
        parts = [f"Generate content for keyword: \"{keyword.keyword}\""]
        parts.append(f"Page type: {keyword.page_type}")
        if keyword.race:
            parts.append(f"Race: {keyword.race}")
        if keyword.character_class:
            parts.append(f"Class: {keyword.character_class}")
        if keyword.theme:
            parts.append(f"Theme: {keyword.theme}")
        parts.append(f"Relevance score: {keyword.relevance_score}")
        return "\n".join(parts)

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

    def _parse_llm_content(self, content: str) -> dict | None:
        """
        解析 LLM 返回的内容 JSON。

        Args:
            content: LLM 返回的 JSON 文本

        Returns:
            解析后的字典，失败返回 None
        """
        try:
            data = json.loads(content)
        except (json.JSONDecodeError, TypeError) as exc:
            logger.warning("Failed to parse LLM content JSON: %s", exc)
            return None

        if not isinstance(data, dict):
            logger.warning("LLM content output is not a dict")
            return None

        return data

    def _parse_examples(self, raw: list | object) -> list[ExamplePrompt]:
        """
        解析示例提示词列表。

        Args:
            raw: LLM 返回的示例列表

        Returns:
            ExamplePrompt 列表
        """
        if not isinstance(raw, list):
            return []

        examples: list[ExamplePrompt] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            try:
                examples.append(
                    ExamplePrompt(
                        badge=str(item.get("badge", "Example")),
                        name=str(item.get("name", "Untitled")),
                        positive=str(item.get("positive", "")),
                        negative=str(item.get("negative", "")),
                    )
                )
            except Exception:
                continue
        return examples

    def _parse_faqs(self, raw: list | object) -> list[FAQItem]:
        """
        解析 FAQ 列表。

        Args:
            raw: LLM 返回的 FAQ 列表

        Returns:
            FAQItem 列表
        """
        if not isinstance(raw, list):
            return []

        faqs: list[FAQItem] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            try:
                faqs.append(
                    FAQItem(
                        question=str(item.get("question", "")),
                        answer=str(item.get("answer", "")),
                    )
                )
            except Exception:
                continue
        return faqs

    def _parse_internal_links(self, raw: list | object) -> list[InternalLink]:
        """
        解析内部链接列表。

        Args:
            raw: LLM 返回的链接列表

        Returns:
            InternalLink 列表
        """
        if not isinstance(raw, list):
            return []

        links: list[InternalLink] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            try:
                href = str(item.get("href", ""))
                # 安全检查：只允许合法相对路径，排除路径遍历和协议链接
                if self._is_safe_internal_link(href):
                    links.append(
                        InternalLink(
                            label=str(item.get("label", "")),
                            href=href,
                        )
                    )
            except Exception:
                continue
        return links

    def _is_safe_internal_link(self, href: str) -> bool:
        """
        验证内部链接是否为安全的相对路径。

        只允许以 / 开头、仅含 [a-z0-9/-] 的路径，排除路径遍历和协议链接。

        Args:
            href: 待验证的链接路径

        Returns:
            是否为安全的内部链接
        """
        if not href.startswith("/"):
            return False
        # 排除 // 开头的协议链接（如 //evil.com）
        if href.startswith("//"):
            return False
        # 严格正则：仅允许 / + 小写字母、数字、连字符
        if not re.match(r"^/[a-z0-9/-]+$", href):
            return False
        return True

    def _fallback_content(self, keyword: ClassifiedKeyword) -> dict:
        """
        当 LLM 不可用时生成 fallback 内容。

        Args:
            keyword: 分类关键词

        Returns:
            基础内容字典
        """
        kw_title = keyword.keyword.replace("-", " ").title()
        return {
            "title": f"{kw_title} - Free DND Prompt Generator",
            "meta_description": f"Generate stunning {kw_title.lower()} with our free AI-powered DND prompt generator. Create detailed, copy-ready prompts for your tabletop RPG characters.",
            "h1": f"{kw_title} Generator",
            "intro": f"Create detailed, copy-ready AI image prompts for {kw_title.lower()}. Our free DND prompt generator helps tabletop RPG players, DMs, and VTT users craft the perfect visual for their campaign.",
            "examples": [
                {
                    "badge": "Classic",
                    "name": f"Classic {kw_title}",
                    "positive": f"A {kw_title.lower()}, fantasy art style, detailed, high quality",
                    "negative": "blurry, low quality, deformed",
                },
                {
                    "badge": "Cinematic",
                    "name": f"Cinematic {kw_title}",
                    "positive": f"Cinematic {kw_title.lower()}, dramatic lighting, professional fantasy illustration",
                    "negative": "cartoon, amateur, watermark",
                },
                {
                    "badge": "Token",
                    "name": f"{kw_title} Token",
                    "positive": f"Top-down token of {kw_title.lower()}, centered, clean background, VTT ready",
                    "negative": "multiple figures, busy background, off-center",
                },
            ],
            "faqs": [
                {
                    "question": f"What is a {kw_title.lower()} prompt?",
                    "answer": f"A {kw_title.lower()} prompt is a text description used with AI image generators to create visual representations of your DND characters and scenes.",
                },
                {
                    "question": f"How do I use this {kw_title.lower()} generator?",
                    "answer": "Simply fill in the details about your character or scene, and our AI will generate a detailed, copy-ready prompt you can paste into any image generator.",
                },
                {
                    "question": "Is this DND prompt generator free?",
                    "answer": "Yes, DND Prompt Forge is completely free to use. No signup required.",
                },
            ],
            "internal_links": [
                {"label": "DND Character Prompt Generator", "href": "/dnd-character-prompt-generator"},
                {"label": "DND Token Prompt Generator", "href": "/dnd-token-prompt-generator"},
                {"label": "DND Monster Prompt Generator", "href": "/dnd-monster-prompt-generator"},
            ],
        }

    def _render_html(self, page: GeneratedPage) -> str:
        """
        使用 Jinja2 渲染页面 HTML。

        Args:
            page: 生成页面数据

        Returns:
            渲染后的 HTML 字符串
        """
        # 构建模板数据，匹配 long_tail_page.html 的变量名
        template_data = {
            "page_data": {
                "title": page.title,
                "meta_description": page.meta_description,
                "canonical_url": page.canonical_url,
                "h1": page.h1,
                "intro": page.intro,
                "examples": [
                    {"title": ex.name, "prompt": ex.positive}
                    for ex in page.examples
                ],
                "faq": [
                    {"q": faq.question, "a": faq.answer}
                    for faq in page.faqs
                ],
                "internal_links": [
                    {"anchor": link.label, "url": link.href}
                    for link in page.internal_links
                ],
                "prefill": page.prefill,
            },
        }

        try:
            template = self._jinja_env.get_template("long_tail_page.html")
            return template.render(**template_data)
        except Exception as exc:
            logger.error("Jinja2 rendering failed: %s", exc)
            # 返回最小可用 HTML
            return self._minimal_html(page)

    def _minimal_html(self, page: GeneratedPage) -> str:
        """
        生成最小可用 HTML，作为模板渲染失败的 fallback。

        所有 LLM 衍生内容必须通过 html.escape() 转义，防止 XSS。

        Args:
            page: 生成页面数据

        Returns:
            最小 HTML 字符串
        """
        # 转义所有 LLM 衍生内容，防止 XSS 注入
        safe_title = html.escape(page.title)
        safe_meta = html.escape(page.meta_description)
        safe_canonical = html.escape(page.canonical_url)
        safe_h1 = html.escape(page.h1)
        safe_intro = html.escape(page.intro)

        return (
            f'<!DOCTYPE html>\n<html lang="en">\n<head>\n'
            f'<meta charset="UTF-8">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
            f'<title>{safe_title}</title>\n'
            f'<meta name="description" content="{safe_meta}">\n'
            f'<link rel="canonical" href="{safe_canonical}">\n'
            f'</head>\n<body>\n'
            f'<h1>{safe_h1}</h1>\n'
            f'<p>{safe_intro}</p>\n'
            f'</body>\n</html>'
        )
