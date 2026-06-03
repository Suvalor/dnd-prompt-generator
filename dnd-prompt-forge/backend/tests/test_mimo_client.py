"""
DND Prompt Forge - MiMo 客户端响应验证测试
覆盖 MiMoClient 的响应解析与验证逻辑
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.mimo_client import MiMoClient, MiMoClientError


class TestMiMoClientInit:
    """测试 MiMoClient 初始化。"""

    def test_init_without_api_key(self):
        """未配置 API key 时 client 属性应为 None。"""
        with patch("services.mimo_client.settings") as mock_settings:
            mock_settings.mimo_api_key = ""
            client = MiMoClient()
            assert client.client is None

    def test_is_available_without_api_key(self):
        """未配置 API key 时 is_available 返回 False。"""
        with patch("services.mimo_client.settings") as mock_settings:
            mock_settings.mimo_api_key = ""
            client = MiMoClient()
            assert client.is_available() is False

    def test_is_available_with_api_key(self):
        """配置 API key 时 is_available 返回 True。"""
        with patch("services.mimo_client.settings") as mock_settings:
            mock_settings.mimo_api_key = "test-key"
            mock_settings.mimo_base_url = "https://test.com"
            mock_settings.mimo_model = "test-model"
            mock_settings.mimo_max_completion_tokens = 1024
            mock_settings.llm_timeout_seconds = 30
            client = MiMoClient()
            assert client.is_available() is True


class TestMiMoClientGeneratePrompt:
    """测试 generate_prompt 方法。"""

    def _create_mock_response(self, content_dict):
        """创建模拟 API 响应。"""
        mock_message = MagicMock()
        mock_message.content = json.dumps(content_dict)
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        return mock_response

    @pytest.mark.asyncio
    async def test_generate_prompt_success(self):
        """正常响应应返回解析后的字典。"""
        expected = {
            "main_prompt": "A heroic dragonborn paladin...",
            "short_prompt": "Dragonborn paladin, heroic",
            "negative_prompt": "blurry, lowres",
            "style_notes": "Use dramatic lighting",
            "usage_tip": "Add --ar 4:5 for portrait",
        }
        mock_response = self._create_mock_response(expected)
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("services.mimo_client.settings") as mock_settings:
            mock_settings.mimo_api_key = "test-key"
            mock_settings.mimo_base_url = "https://test.com"
            mock_settings.mimo_model = "test-model"
            mock_settings.mimo_max_completion_tokens = 1024
            mock_settings.llm_timeout_seconds = 30
            client = MiMoClient()
            client._client = mock_client

            result = await client.generate_prompt({"output_type": "portrait"})
            assert result["main_prompt"] == expected["main_prompt"]
            assert result["short_prompt"] == expected["short_prompt"]
            assert result["negative_prompt"] == expected["negative_prompt"]
            assert result["style_notes"] == expected["style_notes"]
            assert result["usage_tip"] == expected["usage_tip"]

    @pytest.mark.asyncio
    async def test_generate_prompt_missing_fields(self):
        """缺少必需字段应抛出 MiMoClientError。"""
        # 只返回部分字段
        mock_response = self._create_mock_response({"main_prompt": "only this"})
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("services.mimo_client.settings") as mock_settings:
            mock_settings.mimo_api_key = "test-key"
            mock_settings.mimo_base_url = "https://test.com"
            mock_settings.mimo_model = "test-model"
            mock_settings.mimo_max_completion_tokens = 1024
            mock_settings.llm_timeout_seconds = 30
            client = MiMoClient()
            client._client = mock_client

            with pytest.raises(MiMoClientError) as exc_info:
                await client.generate_prompt({"output_type": "portrait"})
            assert "Missing required fields" in str(exc_info.value)
            assert exc_info.value.category == "schema_error"

    @pytest.mark.asyncio
    async def test_generate_prompt_invalid_json(self):
        """无效 JSON 响应应抛出 MiMoClientError。"""
        mock_message = MagicMock()
        mock_message.content = "not-json"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("services.mimo_client.settings") as mock_settings:
            mock_settings.mimo_api_key = "test-key"
            mock_settings.mimo_base_url = "https://test.com"
            mock_settings.mimo_model = "test-model"
            mock_settings.mimo_max_completion_tokens = 1024
            mock_settings.llm_timeout_seconds = 30
            client = MiMoClient()
            client._client = mock_client

            with pytest.raises(MiMoClientError) as exc_info:
                await client.generate_prompt({"output_type": "portrait"})
            assert "Failed to parse JSON" in str(exc_info.value)
            assert exc_info.value.category == "parse_error"

    @pytest.mark.asyncio
    async def test_generate_prompt_api_error(self):
        """API 调用失败应抛出 MiMoClientError。"""
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))

        with patch("services.mimo_client.settings") as mock_settings:
            mock_settings.mimo_api_key = "test-key"
            mock_settings.mimo_base_url = "https://test.com"
            mock_settings.mimo_model = "test-model"
            mock_settings.mimo_max_completion_tokens = 1024
            mock_settings.llm_timeout_seconds = 30
            client = MiMoClient()
            client._client = mock_client

            with pytest.raises(MiMoClientError) as exc_info:
                await client.generate_prompt({"output_type": "portrait"})
            assert "MiMo API error" in str(exc_info.value)
            assert exc_info.value.category == "provider_error"

    @pytest.mark.asyncio
    async def test_generate_prompt_not_available(self):
        """客户端不可用时调用应抛出 MiMoClientError。"""
        with patch("services.mimo_client.settings") as mock_settings:
            mock_settings.mimo_api_key = ""
            client = MiMoClient()
            with pytest.raises(MiMoClientError) as exc_info:
                await client.generate_prompt({"output_type": "portrait"})
            assert "not configured" in str(exc_info.value)
            assert exc_info.value.category == "no_api_key"


class TestMiMoClientValidateResponse:
    """测试 _validate_response 方法。"""

    def test_validates_all_string_fields(self):
        """所有字段应为字符串类型。"""
        with patch("services.mimo_client.settings") as mock_settings:
            mock_settings.mimo_api_key = ""
            client = MiMoClient()
            result = client._validate_response({
                "main_prompt": "test",
                "short_prompt": "test",
                "negative_prompt": "test",
                "style_notes": "test",
                "usage_tip": "test",
            })
            assert result["main_prompt"] == "test"

    def test_converts_non_string_to_string(self):
        """非字符串字段应转换为字符串。"""
        with patch("services.mimo_client.settings") as mock_settings:
            mock_settings.mimo_api_key = ""
            client = MiMoClient()
            result = client._validate_response({
                "main_prompt": 123,
                "short_prompt": "test",
                "negative_prompt": "test",
                "style_notes": "test",
                "usage_tip": "test",
            })
            assert result["main_prompt"] == "123"

    def test_missing_fields_raises_error(self):
        """缺少必需字段应抛出 MiMoClientError。"""
        with patch("services.mimo_client.settings") as mock_settings:
            mock_settings.mimo_api_key = ""
            client = MiMoClient()
            with pytest.raises(MiMoClientError) as exc_info:
                client._validate_response({"main_prompt": "test"})
            assert "Missing required fields" in str(exc_info.value)


class TestMiMoClientError:
    """测试 MiMoClientError 异常类。"""

    def test_default_category(self):
        """默认类别应为 provider_error。"""
        err = MiMoClientError("test error")
        assert err.category == "provider_error"

    def test_custom_category(self):
        """自定义类别应正确存储。"""
        err = MiMoClientError("test error", category="timeout")
        assert err.category == "timeout"
