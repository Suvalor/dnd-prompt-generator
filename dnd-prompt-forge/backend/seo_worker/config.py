"""
DND Prompt Forge - SEO Worker 配置
使用 Pydantic BaseSettings 管理环境变量，LLM 配置复用主 config
"""

from pydantic_settings import BaseSettings, SettingsConfigDict

from config import settings as main_settings


class WorkerConfig(BaseSettings):
    """
    SEO Worker 配置。

    所有值可从 .env 文件或环境变量读取。
    环境变量名使用大写下划线格式（如 SEO_LLM_DAILY_TOKEN_BUDGET）。
    LLM 配置复用主 config.py 的 settings 对象。
    """

    # SEO Worker LLM 预算控制
    seo_llm_daily_token_budget: int = 100000
    seo_llm_daily_cost_budget_usd: float = 5.00
    seo_llm_max_candidates_per_run: int = 100
    seo_llm_max_generated_pages_per_run: int = 1
    seo_llm_max_updated_pages_per_run: int = 10
    seo_llm_max_retries_per_step: int = 1

    # SEO 关键词与趋势
    seo_seed_keywords_path: str = "seo_worker/seed_keywords.txt"
    seo_trends_api_key: str = ""

    # SEO 站点配置
    seo_base_url: str = "https://dndpromptforge.com"
    seo_data_dir: str = "seo_data"
    seo_output_dir: str = "../frontend/generated"
    seo_templates_dir: str = "seo_worker/templates"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def llm_api_key(self) -> str:
        """获取 LLM API key，复用主配置。"""
        return main_settings.llm_api_key

    @property
    def llm_base_url(self) -> str:
        """获取 LLM base URL，复用主配置。"""
        return main_settings.llm_base_url

    @property
    def llm_model(self) -> str:
        """获取 LLM 模型名，复用主配置。"""
        return main_settings.llm_model
