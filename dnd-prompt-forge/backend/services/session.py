"""
DND Prompt Forge - Session 服务
签名 Cookie 生成/验证，CSRF nonce 生成/验证
"""

import hmac
import hashlib
import secrets
import logging
from typing import Optional

from config import settings

logger = logging.getLogger(__name__)

# Cookie 签名密钥：从配置读取，缺省时生成随机密钥（仅开发环境）
_session_cookie_secret = settings.session_cookie_secret
if not _session_cookie_secret:
    _session_cookie_secret = secrets.token_bytes(32)
    logger.warning(
        "SESSION_COOKIE_SECRET not set in environment. A random secret was generated, "
        "which will cause session validation failures across multiple workers. "
        "Please set SESSION_COOKIE_SECRET in production."
    )
SESSION_SECRET: str | bytes = _session_cookie_secret
if isinstance(SESSION_SECRET, str):
    SESSION_SECRET = SESSION_SECRET.encode()

# CSRF 签名密钥
_csrf_secret = settings.csrf_secret
if not _csrf_secret:
    _csrf_secret = secrets.token_bytes(32)
    logger.warning(
        "CSRF_SECRET not set in environment. A random secret was generated, "
        "which will cause CSRF validation failures across multiple workers. "
        "Please set CSRF_SECRET in production."
    )
CSRF_SECRET: str | bytes = _csrf_secret
if isinstance(CSRF_SECRET, str):
    CSRF_SECRET = CSRF_SECRET.encode()


def _hmac_sign(value: str, secret: bytes) -> str:
    """使用 HMAC-SHA256 对值签名。"""
    signature = hmac.new(secret, value.encode(), hashlib.sha256).hexdigest()
    return f"{value}.{signature}"


def _hmac_verify(signed_value: str, secret: bytes) -> Optional[str]:
    """验证 HMAC 签名，返回原始值或 None。"""
    if "." not in signed_value:
        return None
    value, sig = signed_value.rsplit(".", 1)
    expected = hmac.new(secret, value.encode(), hashlib.sha256).hexdigest()
    if hmac.compare_digest(sig, expected):
        return value
    return None


def generate_session_id() -> str:
    """生成随机 session ID。"""
    return secrets.token_hex(16)


def generate_csrf_token() -> str:
    """生成随机 CSRF token。"""
    return secrets.token_hex(16)


def sign_cookie(value: str) -> str:
    """对 cookie 值签名。"""
    return _hmac_sign(value, SESSION_SECRET)


def verify_cookie(signed_value: str) -> str:
    """验证并提取 cookie 原始值，无效时抛出 ValueError。"""
    if not signed_value:
        raise ValueError("Empty signed value")
    result = _hmac_verify(signed_value, SESSION_SECRET)
    if result is None:
        raise ValueError("Invalid cookie signature")
    return result


def sign_csrf_token(session_id: str, csrf_token: str) -> str:
    """对 CSRF token 签名，绑定 session_id。"""
    payload = f"{session_id}:{csrf_token}"
    return _hmac_sign(payload, CSRF_SECRET)


def verify_csrf(session_id: str, csrf_token: str, signed_value: str) -> bool:
    """验证 CSRF token 签名是否匹配 session_id 和 csrf_token。"""
    if not signed_value or "." not in signed_value:
        return False
    payload = f"{session_id}:{csrf_token}"
    result = _hmac_verify(signed_value, CSRF_SECRET)
    return result == payload