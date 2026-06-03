"""
DND Prompt Forge - 配额服务测试
覆盖 QuotaResult、check_quota、increment_quota、_hash_identifier、_reset_time
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone
from services.quota import (
    QuotaResult,
    check_quota,
    increment_quota,
    _hash_identifier,
    _reset_time,
    _get_hour_bucket,
)


class TestHashIdentifier:
    """测试标识符哈希。"""

    def test_returns_hex_string(self):
        """应返回 16 位十六进制字符串。"""
        result = _hash_identifier("test-value")
        assert isinstance(result, str)
        assert len(result) == 16
        assert all(c in "0123456789abcdef" for c in result)

    def test_same_input_same_output(self):
        """相同输入应返回相同哈希。"""
        assert _hash_identifier("same") == _hash_identifier("same")

    def test_different_input_different_output(self):
        """不同输入应返回不同哈希。"""
        assert _hash_identifier("a") != _hash_identifier("b")

    def test_empty_string(self):
        """空字符串也应返回哈希。"""
        result = _hash_identifier("")
        assert len(result) == 16


class TestGetHourBucket:
    """测试小时桶计算。"""

    def test_returns_string(self):
        """应返回字符串格式的时间桶。"""
        result = _get_hour_bucket()
        assert isinstance(result, str)
        assert result.isdigit()


class TestResetTime:
    """测试配额重置时间计算。"""

    def test_returns_iso_string(self):
        """应返回 ISO 格式时间字符串。"""
        bucket = "1000"
        result = _reset_time(bucket)
        assert isinstance(result, str)
        # 验证是有效的 ISO 格式
        datetime.fromisoformat(result.replace("Z", "+00:00"))


class TestQuotaResult:
    """测试 QuotaResult 数据类。"""

    def test_attributes(self):
        """QuotaResult 应正确存储属性。"""
        result = QuotaResult(allowed=True, limit=10, remaining=5, reset_at="2026-01-01T00:00:00")
        assert result.allowed is True
        assert result.limit == 10
        assert result.remaining == 5
        assert result.reset_at == "2026-01-01T00:00:00"

    def test_denied_result(self):
        """拒绝结果应正确设置属性。"""
        result = QuotaResult(allowed=False, limit=10, remaining=0, reset_at="2026-01-01T00:00:00")
        assert result.allowed is False
        assert result.remaining == 0


class TestCheckQuota:
    """测试配额检查。"""

    @pytest.mark.asyncio
    async def test_redis_not_available_falls_back_to_sqlite(self):
        """Redis 不可用时回退到 SQLite。"""
        with patch("services.quota.get_redis", return_value=None):
            with patch("services.quota._check_quota_sqlite", new=AsyncMock(return_value=QuotaResult(
                allowed=True, limit=10, remaining=9, reset_at="2026-01-01T00:00:00"
            ))) as mock_sqlite:
                result = await check_quota("127.0.0.1", "fp123", "cookie123")
                assert result.allowed is True
                assert result.limit == 10
                mock_sqlite.assert_called_once()

    @pytest.mark.asyncio
    async def test_redis_quota_exceeded(self):
        """Redis 配额超限应返回拒绝。"""
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value="10")

        with patch("services.quota.get_redis", return_value=mock_redis):
            result = await check_quota("127.0.0.1", "fp123", "cookie123")
            assert result.allowed is False
            assert result.remaining == 0

    @pytest.mark.asyncio
    async def test_redis_quota_available(self):
        """Redis 配额充足应返回允许。"""
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value="3")

        with patch("services.quota.get_redis", return_value=mock_redis):
            result = await check_quota("127.0.0.1", "fp123", "cookie123")
            assert result.allowed is True
            assert result.remaining == 7  # limit(10) - max_count(3)

    @pytest.mark.asyncio
    async def test_redis_read_error_falls_back(self):
        """Redis 读取错误时回退到 SQLite。"""
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(side_effect=Exception("Redis error"))

        with patch("services.quota.get_redis", return_value=mock_redis):
            with patch("services.quota._check_quota_sqlite", new=AsyncMock(return_value=QuotaResult(
                allowed=True, limit=10, remaining=9, reset_at="2026-01-01T00:00:00"
            ))):
                result = await check_quota("127.0.0.1", "fp123", "cookie123")
                assert result.allowed is True


class TestIncrementQuota:
    """测试配额递增。"""

    @pytest.mark.asyncio
    async def test_redis_increment(self):
        """Redis 可用时应递增计数器。"""
        mock_redis = MagicMock()
        mock_redis.incr = AsyncMock()
        mock_redis.expire = AsyncMock()

        with patch("services.quota.get_redis", return_value=mock_redis):
            await increment_quota("127.0.0.1", "fp123", "cookie123")
            assert mock_redis.incr.call_count == 3
            assert mock_redis.expire.call_count == 3

    @pytest.mark.asyncio
    async def test_redis_error_ignored(self):
        """Redis 错误不应抛出异常。"""
        mock_redis = MagicMock()
        mock_redis.incr = AsyncMock(side_effect=Exception("Redis down"))

        with patch("services.quota.get_redis", return_value=mock_redis):
            # 不应抛出异常
            await increment_quota("127.0.0.1", "fp123", "cookie123")
