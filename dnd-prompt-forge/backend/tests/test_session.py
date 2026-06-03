"""
DND Prompt Forge - Session 签名/验证测试
覆盖 sign_cookie / verify_cookie / sign_csrf_token / verify_csrf
"""

import pytest
from services.session import (
    generate_session_id,
    generate_csrf_token,
    sign_cookie,
    verify_cookie,
    sign_csrf_token,
    verify_csrf,
)


class TestSignCookie:
    """测试 cookie 签名与验证。"""

    def test_sign_and_verify_roundtrip(self):
        """签名后的值应能正确验证并返回原始值。"""
        original = "test-session-123"
        signed = sign_cookie(original)
        assert signed != original
        assert "." in signed
        result = verify_cookie(signed)
        assert result == original

    def test_verify_invalid_signature(self):
        """验证篡改后的签名应抛出 ValueError。"""
        signed = sign_cookie("test-session")
        tampered = signed[:-1] + "x"
        with pytest.raises(ValueError):
            verify_cookie(tampered)

    def test_verify_empty_string(self):
        """验证空字符串应抛出 ValueError。"""
        with pytest.raises(ValueError):
            verify_cookie("")

    def test_verify_no_dot(self):
        """验证不含点的字符串应抛出 ValueError。"""
        with pytest.raises(ValueError):
            verify_cookie("no-dot-here")


class TestSignCsrfToken:
    """测试 CSRF token 签名与验证。"""

    def test_sign_and_verify_roundtrip(self):
        """CSRF token 签名后应能正确验证。"""
        session_id = generate_session_id()
        csrf_token = generate_csrf_token()
        signed = sign_csrf_token(session_id, csrf_token)
        assert verify_csrf(session_id, csrf_token, signed) is True

    def test_verify_wrong_session_id(self):
        """使用错误的 session_id 验证应失败。"""
        session_id = generate_session_id()
        csrf_token = generate_csrf_token()
        signed = sign_csrf_token(session_id, csrf_token)
        wrong_session = generate_session_id()
        assert verify_csrf(wrong_session, csrf_token, signed) is False

    def test_verify_wrong_csrf_token(self):
        """使用错误的 csrf_token 验证应失败。"""
        session_id = generate_session_id()
        csrf_token = generate_csrf_token()
        signed = sign_csrf_token(session_id, csrf_token)
        wrong_csrf = generate_csrf_token()
        assert verify_csrf(session_id, wrong_csrf, signed) is False

    def test_verify_tampered_signed_value(self):
        """篡改签名值后验证应失败。"""
        session_id = generate_session_id()
        csrf_token = generate_csrf_token()
        signed = sign_csrf_token(session_id, csrf_token)
        tampered = signed[:-1] + "x"
        assert verify_csrf(session_id, csrf_token, tampered) is False

    def test_verify_empty_signed_value(self):
        """验证空签名值应返回 False。"""
        session_id = generate_session_id()
        csrf_token = generate_csrf_token()
        assert verify_csrf(session_id, csrf_token, "") is False

    def test_verify_no_dot_in_signed_value(self):
        """签名值不含点时应返回 False。"""
        session_id = generate_session_id()
        csrf_token = generate_csrf_token()
        assert verify_csrf(session_id, csrf_token, "no-dot") is False


class TestGenerateSessionId:
    """测试 session ID 生成。"""

    def test_generates_unique_values(self):
        """多次生成应产生不同的 session ID。"""
        ids = {generate_session_id() for _ in range(100)}
        assert len(ids) == 100

    def test_generates_non_empty(self):
        """生成的 session ID 不应为空。"""
        assert len(generate_session_id()) > 0


class TestGenerateCsrfToken:
    """测试 CSRF token 生成。"""

    def test_generates_unique_values(self):
        """多次生成应产生不同的 CSRF token。"""
        tokens = {generate_csrf_token() for _ in range(100)}
        assert len(tokens) == 100

    def test_generates_non_empty(self):
        """生成的 CSRF token 不应为空。"""
        assert len(generate_csrf_token()) > 0
