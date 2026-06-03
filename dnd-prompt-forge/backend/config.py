"""
DND Prompt Forge - 配置模块
环境变量管理与 Pydantic Settings 封装
"""

import os
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置，所有值从环境变量读取。"""

    app_env: str = "development"
    log_level: str = "INFO"

    # OpenAI-compatible LLM 配置
    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_model: str = ""
    llm_max_completion_tokens: int = 2048
    llm_timeout_seconds: int = 60

    # 配额配置
    llm_quota_limit: int = 10
    llm_quota_window_seconds: int = 3600

    # 安全配置
    session_cookie_secret: str = ""
    csrf_secret: str = ""

    # Redis 配置
    redis_url: str = "redis://redis:6379/0"
    redis_enabled: bool = True

    # 数据库配置
    db_path: str = "./prompt_forge.db"

    # CORS 配置
    allowed_origins: str = ""

    # 端口配置
    frontend_port: str = "8081"
    backend_port: str = "8000"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()


def get_allowed_origins() -> List[str]:
    """获取 CORS 允许的 Origin 列表。"""
    if settings.app_env == "development":
        return ["http://localhost:8081", "http://localhost:3000", "http://localhost:80"]
    if settings.allowed_origins:
        return [o.strip() for o in settings.allowed_origins.split(",")]
    return []
