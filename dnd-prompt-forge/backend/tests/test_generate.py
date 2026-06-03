"""
DND Prompt Forge - 生成端点集成测试
覆盖 /api/generate-prompt 端点的各种场景
"""

import json
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

from main import app
from services.session import generate_session_id, generate_csrf_token, sign_cookie, sign_csrf_token
from models.database import init_database

# 初始化数据库（测试前创建表）
init_database()


class TestGeneratePrompt:
    """测试 /api/generate-prompt 端点。"""

    def _bootstrap_session(self):
        """创建有效的 session 和 CSRF token。"""
        session_id = generate_session_id()
        csrf_token = generate_csrf_token()
        signed_session = sign_cookie(session_id)
        signed_csrf = sign_csrf_token(session_id, csrf_token)
        return signed_session, signed_csrf

    def test_missing_csrf_header(self):
        """缺少 CSRF header 应返回 403。"""
        signed_session, _ = self._bootstrap_session()
        client = TestClient(app)
        response = client.post(
            "/api/generate-prompt",
            json={"output_type": "portrait"},
            cookies={"session_id": signed_session},
        )
        assert response.status_code == 403

    def test_invalid_csrf_format(self):
        """CSRF token 格式无效应返回 403。"""
        signed_session, _ = self._bootstrap_session()
        client = TestClient(app)
        response = client.post(
            "/api/generate-prompt",
            json={"output_type": "portrait"},
            headers={"X-CSRF-Token": "no-dot"},
            cookies={"session_id": signed_session},
        )
        assert response.status_code == 403

    def test_invalid_session_cookie(self):
        """无效的 session cookie 应返回 401。"""
        client = TestClient(app)
        response = client.post(
            "/api/generate-prompt",
            json={"output_type": "portrait"},
            headers={"X-CSRF-Token": "some-token"},
            cookies={"session_id": "invalid-signed-value"},
        )
        assert response.status_code == 401

    def test_missing_session_cookie(self):
        """缺少 session cookie 应返回 401（CSRF 验证需要 session）。"""
        client = TestClient(app)
        response = client.post(
            "/api/generate-prompt",
            json={"output_type": "portrait"},
            headers={"X-CSRF-Token": "some-token"},
        )
        assert response.status_code == 401

    def test_quota_exceeded_fallback(self):
        """配额超限时应返回 fallback 模式。"""
        signed_session, signed_csrf = self._bootstrap_session()
        client = TestClient(app)

        with patch("services.quota.get_redis") as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.get = AsyncMock(return_value="10")  # 超过配额限制
            mock_get_redis.return_value = mock_redis

            response = client.post(
                "/api/generate-prompt",
                json={
                    "output_type": "portrait",
                    "race": "Elf",
                    "class_role": "Wizard",
                    "style": "painterly",
                    "mood": "mystical",
                    "description": "",
                    "target_model": "midjourney",
                },
                headers={"X-CSRF-Token": signed_csrf, "Origin": "http://localhost:8081"},
                cookies={"session_id": signed_session},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["mode"] == "fallback"
            assert "main_prompt" in data
            assert "short_prompt" in data
            assert "negative_prompt" in data
            assert "style_notes" in data
            assert "usage_tip" in data
            assert "quota" in data
            assert data["quota"]["remaining"] == 0

    def test_valid_request_with_quota(self):
        """配额充足时应返回成功响应。"""
        signed_session, signed_csrf = self._bootstrap_session()
        client = TestClient(app)

        with patch("services.quota.get_redis") as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.get = AsyncMock(return_value="3")  # 配额充足
            mock_get_redis.return_value = mock_redis

            with patch("services.mimo_client.MiMoClient.is_available", return_value=False):
                response = client.post(
                    "/api/generate-prompt",
                    json={
                        "output_type": "portrait",
                        "race": "Elf",
                        "class_role": "Wizard",
                        "style": "painterly",
                        "mood": "mystical",
                        "description": "A wise archmage",
                        "target_model": "midjourney",
                    },
                    headers={"X-CSRF-Token": signed_csrf, "Origin": "http://localhost:8081"},
                    cookies={"session_id": signed_session},
                )
                assert response.status_code == 200
                data = response.json()
                assert data["mode"] == "fallback"  # MiMo 不可用，fallback
                assert "main_prompt" in data
                assert "request_id" in data
                assert "quota" in data

    def test_response_structure(self):
        """响应应包含所有必需字段。"""
        signed_session, signed_csrf = self._bootstrap_session()
        client = TestClient(app)

        with patch("services.quota.get_redis") as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.get = AsyncMock(return_value="10")
            mock_get_redis.return_value = mock_redis

            response = client.post(
                "/api/generate-prompt",
                json={
                    "output_type": "portrait",
                    "race": "Elf",
                    "class_role": "Wizard",
                    "style": "painterly",
                    "mood": "mystical",
                    "description": "",
                    "target_model": "midjourney",
                },
                headers={"X-CSRF-Token": signed_csrf, "Origin": "http://localhost:8081"},
                cookies={"session_id": signed_session},
            )
            assert response.status_code == 200
            data = response.json()
            assert "mode" in data
            assert "request_id" in data
            assert "quota" in data
            assert "main_prompt" in data
            assert "short_prompt" in data
            assert "negative_prompt" in data
            assert "style_notes" in data
            assert "usage_tip" in data
            assert isinstance(data["quota"], dict)
            assert "limit" in data["quota"]
            assert "remaining" in data["quota"]
            assert "reset_at" in data["quota"]

    def test_different_output_types(self):
        """不同 output_type 应正确生成提示词。"""
        signed_session, signed_csrf = self._bootstrap_session()
        client = TestClient(app)

        with patch("services.quota.get_redis") as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.get = AsyncMock(return_value="10")
            mock_get_redis.return_value = mock_redis

            for output_type in ["portrait", "fullbody", "token", "npc", "monster", "scene"]:
                response = client.post(
                    "/api/generate-prompt",
                    json={
                        "output_type": output_type,
                        "race": "Elf",
                        "class_role": "Wizard",
                        "style": "painterly",
                        "mood": "mystical",
                        "description": "",
                        "target_model": "midjourney",
                    },
                    headers={"X-CSRF-Token": signed_csrf, "Origin": "http://localhost:8081"},
                    cookies={"session_id": signed_session},
                )
                assert response.status_code == 200, f"Failed for output_type={output_type}"
                data = response.json()
                assert "main_prompt" in data
                assert len(data["main_prompt"]) > 0

    def test_optional_fields(self):
        """可选字段应被正确处理。"""
        signed_session, signed_csrf = self._bootstrap_session()
        client = TestClient(app)

        with patch("services.quota.get_redis") as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.get = AsyncMock(return_value="10")
            mock_get_redis.return_value = mock_redis

            response = client.post(
                "/api/generate-prompt",
                json={
                    "output_type": "portrait",
                    "race": "Elf",
                    "class_role": "Wizard",
                    "style": "painterly",
                    "mood": "mystical",
                    "description": "A wise archmage",
                    "target_model": "midjourney",
                    "alignment": "Lawful Good",
                    "weapon": "staff",
                    "armor": "robes",
                    "magic": "arcane",
                    "palette": "deep blue",
                    "gender": "male",
                    "age": "elderly",
                },
                headers={"X-CSRF-Token": signed_csrf, "Origin": "http://localhost:8081"},
                cookies={"session_id": signed_session},
            )
            assert response.status_code == 200
            data = response.json()
            assert "main_prompt" in data
            assert "staff" in data["main_prompt"] or "robes" in data["main_prompt"]
