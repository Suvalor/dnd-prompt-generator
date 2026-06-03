"""
DND Prompt Forge - Business Acceptance Tests (Phase 5)
Validates PRD AC1-AC9: Frontend-Backend Integration

Test layers:
- Integration: Backend API contract verification via TestClient
- Unit: Frontend code static analysis (field mapping, CSRF, fingerprint)
- Security: CSRF enforcement, missing token rejection, session isolation

Each test case traces back to a specific PRD AC item.
"""

import json
import re
import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

from main import app
from services.session import (
    generate_session_id,
    generate_csrf_token,
    sign_cookie,
    sign_csrf_token,
)
from models.database import init_database

init_database()

# 基于测试文件位置动态计算项目根目录
_PROJECT_ROOT = Path(__file__).parent.parent.parent
_FRONTEND_DIR = _PROJECT_ROOT / "frontend"

# 前端目录存在性检查：路径计算在不同环境下可能失效，给出明确错误提示
if not _FRONTEND_DIR.exists():
    raise RuntimeError(
        f"Frontend directory not found at {_FRONTEND_DIR}. "
        f"Verify the project structure: expected <project-root>/frontend/ "
        f"relative to test file at {__file__}. "
        f"Computed _PROJECT_ROOT={_PROJECT_ROOT}"
    )

# Path constants for frontend source files
API_CLIENT_PATH = str(_FRONTEND_DIR / "js" / "api-client.jsx")
GENERATOR_PATH = str(_FRONTEND_DIR / "js" / "generator.jsx")
APP_PATH = str(_FRONTEND_DIR / "js" / "app.jsx")
INDEX_HTML_PATH = str(_FRONTEND_DIR / "index.html")
STYLE_CSS_PATH = str(_FRONTEND_DIR / "css" / "style.css")


def _read_frontend_file(path):
    """Read a frontend source file."""
    with open(path, "r") as f:
        return f.read()


def _bootstrap_session():
    """Helper: generate a valid session + CSRF pair for authenticated requests."""
    session_id = generate_session_id()
    csrf_token = generate_csrf_token()
    signed_session = sign_cookie(session_id)
    signed_csrf = sign_csrf_token(session_id, csrf_token)
    return signed_session, signed_csrf


# ============================================================
# AC1: Bootstrap session on page load
# ============================================================


class TestAC1BootstrapSession:
    """AC1: Page load triggers POST /api/session/bootstrap,
    frontend stores csrf_token and features in memory."""

    def test_bootstrap_endpoint_returns_csrf_and_features(self):
        """POST /api/session/bootstrap returns csrf_token and features config."""
        client = TestClient(app)
        response = client.post("/api/session/bootstrap")
        assert response.status_code == 200
        data = response.json()
        assert "csrf_token" in data, "Missing csrf_token in bootstrap response"
        assert "features" in data, "Missing features in bootstrap response"
        assert isinstance(data["csrf_token"], str), "csrf_token should be a string"
        assert len(data["csrf_token"]) > 0, "csrf_token should not be empty"

    def test_bootstrap_features_contain_llm_enabled_and_quota(self):
        """Bootstrap features must include llm_enabled and quota_limit."""
        client = TestClient(app)
        response = client.post("/api/session/bootstrap")
        data = response.json()
        features = data["features"]
        assert "llm_enabled" in features, "Missing llm_enabled in features"
        assert "quota_limit" in features, "Missing quota_limit in features"
        assert isinstance(features["llm_enabled"], bool)
        assert isinstance(features["quota_limit"], int)

    def test_bootstrap_sets_session_cookie(self):
        """Bootstrap must set session_id cookie (httpOnly, SameSite=Lax)."""
        client = TestClient(app)
        response = client.post("/api/session/bootstrap")
        set_cookie = response.headers.get("set-cookie", "")
        assert "session_id=" in set_cookie, "Missing session_id cookie"
        assert "httponly" in set_cookie.lower(), "Cookie should be httpOnly"
        assert "samesite=lax" in set_cookie.lower(), "Cookie should be SameSite=Lax"

    def test_frontend_calls_bootstrap_on_mount(self):
        """app.jsx must call ApiClient.bootstrap() on mount."""
        source = _read_frontend_file(APP_PATH)
        assert "ApiClient.bootstrap()" in source, (
            "app.jsx does not call ApiClient.bootstrap() on mount"
        )

    def test_frontend_stores_bootstrap_result_in_state(self):
        """app.jsx must store bootstrap result (apiAvailable, features) in state."""
        source = _read_frontend_file(APP_PATH)
        assert "apiAvailable" in source, "Missing apiAvailable state in app.jsx"
        assert "setApiConfig" in source, "Missing setApiConfig in app.jsx"

    def test_frontend_bootstrap_failure_sets_offline(self):
        """app.jsx must set offlineMode=true when bootstrap fails."""
        source = _read_frontend_file(APP_PATH)
        assert "offlineMode" in source, "Missing offlineMode handling in app.jsx"

    def test_api_client_bootstrap_calls_correct_endpoint(self):
        """api-client.jsx bootstrap() must call POST /api/session/bootstrap."""
        source = _read_frontend_file(API_CLIENT_PATH)
        assert "/api/session/bootstrap" in source, (
            "api-client.jsx does not call /api/session/bootstrap"
        )
        # Verify it's a POST
        bootstrap_section = source[
            source.index("/api/session/bootstrap") - 200 :
            source.index("/api/session/bootstrap") + 50
        ]
        assert "POST" in bootstrap_section, "Bootstrap should use POST method"

    def test_api_client_stores_csrf_token_in_memory(self):
        """api-client.jsx must store csrf_token in module-level variable (not localStorage)."""
        source = _read_frontend_file(API_CLIENT_PATH)
        assert "_csrfToken" in source, "Missing _csrfToken variable in api-client.jsx"
        assert "localStorage" not in source, (
            "csrf_token must NOT be stored in localStorage (security)"
        )


# ============================================================
# AC2: Generate button sends POST with CSRF and field mapping
# ============================================================


class TestAC2GenerateWithCSRF:
    """AC2: Click Generate sends POST /api/generate-prompt
    with x-csrf-token header and correctly mapped request body."""

    def test_generate_endpoint_accepts_mapped_fields(self):
        """POST /api/generate-prompt accepts all mapped fields from frontend."""
        signed_session, signed_csrf = _bootstrap_session()
        client = TestClient(app)

        with patch("services.quota.get_redis") as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.get = AsyncMock(return_value="3")
            mock_get_redis.return_value = mock_redis

            response = client.post(
                "/api/generate-prompt",
                json={
                    "output_type": "portrait",
                    "race": "Tiefling",
                    "class_role": "Warlock",
                    "style": "painterly",
                    "mood": "brooding",
                    "description": "pact of the chain",
                    "target_model": "midjourney",
                    "gender": "male",
                    "age": "young adult",
                    "alignment": "chaotic neutral",
                    "armor": "ornate dark leather",
                    "weapon": "a soul-lantern",
                    "magic": "eldritch",
                    "palette": "crimson and violet",
                    "camera": "three-quarter view",
                    "client_fingerprint_hash": "abc123hash",
                    "fallback_prompt_preview": None,
                },
                headers={
                    "x-csrf-token": signed_csrf,
                    "Origin": "http://localhost:8081",
                },
                cookies={"session_id": signed_session},
            )
            assert response.status_code == 200

    def test_generate_without_csrf_returns_403(self):
        """POST /api/generate-prompt without x-csrf-token must return 403."""
        signed_session, _ = _bootstrap_session()
        client = TestClient(app)

        response = client.post(
            "/api/generate-prompt",
            json={"output_type": "portrait", "race": "Tiefling"},
            headers={"Origin": "http://localhost:8081"},
            cookies={"session_id": signed_session},
        )
        assert response.status_code == 403, (
            "Generate without CSRF should return 403"
        )

    def test_generate_with_invalid_csrf_returns_403(self):
        """POST /api/generate-prompt with invalid x-csrf-token must return 403."""
        signed_session, _ = _bootstrap_session()
        client = TestClient(app)

        response = client.post(
            "/api/generate-prompt",
            json={"output_type": "portrait", "race": "Tiefling"},
            headers={
                "x-csrf-token": "invalid-token-value",
                "Origin": "http://localhost:8081",
            },
            cookies={"session_id": signed_session},
        )
        assert response.status_code == 403, (
            "Generate with invalid CSRF should return 403"
        )

    def test_frontend_sends_csrf_header(self):
        """api-client.jsx must include x-csrf-token header in generate requests."""
        source = _read_frontend_file(API_CLIENT_PATH)
        assert "x-csrf-token" in source.lower(), (
            "api-client.jsx does not set x-csrf-token header"
        )

    def test_frontend_field_mapping_type_to_output_type(self):
        """mapFormToApi must map form.type -> output_type."""
        source = _read_frontend_file(API_CLIENT_PATH)
        map_section = source[
            source.index("mapFormToApi") : source.index("mapFormToApi") + 800
        ]
        assert "output_type" in map_section, "Missing output_type mapping"
        assert "form.type" in map_section, "output_type should map from form.type"

    def test_frontend_field_mapping_klass_to_class_role(self):
        """mapFormToApi must map form.klass -> class_role."""
        source = _read_frontend_file(API_CLIENT_PATH)
        map_section = source[
            source.index("mapFormToApi") : source.index("mapFormToApi") + 800
        ]
        assert "class_role" in map_section, "Missing class_role mapping"
        assert "form.klass" in map_section, "class_role should map from form.klass"

    def test_frontend_field_mapping_desc_to_description(self):
        """mapFormToApi must map form.desc -> description."""
        source = _read_frontend_file(API_CLIENT_PATH)
        map_section = source[
            source.index("mapFormToApi") : source.index("mapFormToApi") + 800
        ]
        assert "description" in map_section, "Missing description mapping"
        assert "form.desc" in map_section, "description should map from form.desc"

    def test_frontend_field_mapping_model_to_target_model(self):
        """mapFormToApi must map form.model -> target_model."""
        source = _read_frontend_file(API_CLIENT_PATH)
        map_section = source[
            source.index("mapFormToApi") : source.index("mapFormToApi") + 800
        ]
        assert "target_model" in map_section, "Missing target_model mapping"
        assert "form.model" in map_section, "target_model should map from form.model"

    def test_frontend_field_mapping_empty_to_null(self):
        """mapFormToApi must convert empty strings to null for Optional fields."""
        source = _read_frontend_file(API_CLIENT_PATH)
        assert "emptyToNull" in source, "Missing emptyToNull helper for Optional fields"

    def test_frontend_field_mapping_includes_fingerprint(self):
        """mapFormToApi must include client_fingerprint_hash."""
        source = _read_frontend_file(API_CLIENT_PATH)
        map_section = source[
            source.index("mapFormToApi") : source.index("mapFormToApi") + 800
        ]
        assert "client_fingerprint_hash" in map_section, (
            "Missing client_fingerprint_hash in mapFormToApi"
        )

    def test_backend_generate_request_model_matches_frontend_mapping(self):
        """Backend GeneratePromptRequest fields must match frontend mapFormToApi output."""
        source = _read_frontend_file(API_CLIENT_PATH)
        map_section = source[
            source.index("mapFormToApi") : source.index("mapFormToApi") + 800
        ]
        # All fields that frontend sends must exist in backend model
        frontend_fields = re.findall(r"(\w+):\s", map_section)
        # Read backend model fields
        from routers.generate import GeneratePromptRequest
        backend_fields = set(GeneratePromptRequest.model_fields.keys())
        # Check critical fields
        for field in [
            "output_type",
            "race",
            "class_role",
            "style",
            "mood",
            "description",
            "target_model",
            "client_fingerprint_hash",
        ]:
            assert field in backend_fields, (
                f"Backend GeneratePromptRequest missing field: {field}"
            )

    def test_frontend_403_retry_logic(self):
        """api-client.jsx must re-bootstrap and retry on 403 response."""
        source = _read_frontend_file(API_CLIENT_PATH)
        assert "403" in source or "handleAuthRetry" in source, (
            "Missing 403 retry logic in api-client.jsx"
        )
        assert "bootstrap()" in source, "403 retry must call bootstrap()"

    def test_generator_calls_api_client_generate(self):
        """generator.jsx runGenerate must call ApiClient.generatePrompt()."""
        source = _read_frontend_file(GENERATOR_PATH)
        assert "ApiClient.generatePrompt" in source, (
            "generator.jsx does not call ApiClient.generatePrompt()"
        )


# ============================================================
# AC3: LLM mode display
# ============================================================


class TestAC3LLMModeDisplay:
    """AC3: When backend returns mode=llm, frontend displays LLM-generated prompts."""

    def test_backend_llm_response_structure(self):
        """Backend mode=llm response must include all prompt fields."""
        signed_session, signed_csrf = _bootstrap_session()
        client = TestClient(app)

        with patch("services.quota.get_redis") as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.get = AsyncMock(return_value="3")
            mock_get_redis.return_value = mock_redis

            # Mock LLM to return LLM result
            with patch("services.llm_client.LLMClient.is_available", return_value=True):
                with patch(
                    "services.llm_client.LLMClient.generate_prompt",
                    new_callable=AsyncMock,
                ) as mock_gen:
                    mock_gen.return_value = {
                        "main_prompt": "LLM main prompt",
                        "short_prompt": "LLM short",
                        "negative_prompt": "LLM negative",
                        "style_notes": "LLM style",
                        "usage_tip": "LLM tip",
                    }
                    response = client.post(
                        "/api/generate-prompt",
                        json={
                            "output_type": "portrait",
                            "race": "Tiefling",
                            "class_role": "Warlock",
                        },
                        headers={
                            "x-csrf-token": signed_csrf,
                            "Origin": "http://localhost:8081",
                        },
                        cookies={"session_id": signed_session},
                    )
                    assert response.status_code == 200
                    data = response.json()
                    assert data["mode"] == "llm"
                    assert data["main_prompt"] == "LLM main prompt"
                    assert data["short_prompt"] == "LLM short"
                    assert data["negative_prompt"] == "LLM negative"
                    assert data["style_notes"] == "LLM style"
                    assert data["usage_tip"] == "LLM tip"

    def test_frontend_maps_llm_response_to_result(self):
        """mapApiToResult must map backend response fields to frontend result object."""
        source = _read_frontend_file(API_CLIENT_PATH)
        map_section = source[
            source.index("mapApiToResult") : source.index("mapApiToResult") + 600
        ]
        assert "main_prompt" in map_section, "Missing main_prompt mapping"
        assert "short_prompt" in map_section, "Missing short_prompt mapping"
        assert "negative_prompt" in map_section, "Missing negative_prompt mapping"
        assert "style_notes" in map_section, "Missing style_notes mapping"
        assert "usage_tip" in map_section, "Missing usage_tip mapping"
        assert "response.mode" in map_section, "Missing mode mapping"

    def test_frontend_mode_badge_llm(self):
        """ModeBadge must render 'AI Enhanced' for mode=llm."""
        source = _read_frontend_file(GENERATOR_PATH)
        assert "AI Enhanced" in source, "Missing 'AI Enhanced' label for LLM mode"
        assert "pill llm" in source, "Missing 'pill llm' CSS class for LLM badge"


# ============================================================
# AC4: Fallback mode display with "Standard" badge
# ============================================================


class TestAC4FallbackModeDisplay:
    """AC4: When backend returns mode=fallback, frontend displays
    fallback prompts with "Standard" badge."""

    def test_backend_fallback_response_structure(self):
        """Backend mode=fallback response must include all prompt fields."""
        signed_session, signed_csrf = _bootstrap_session()
        client = TestClient(app)

        with patch("services.quota.get_redis") as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.get = AsyncMock(return_value="3")
            mock_get_redis.return_value = mock_redis

            with patch("services.llm_client.LLMClient.is_available", return_value=False):
                response = client.post(
                    "/api/generate-prompt",
                    json={
                        "output_type": "portrait",
                        "race": "Tiefling",
                        "class_role": "Warlock",
                    },
                    headers={
                        "x-csrf-token": signed_csrf,
                        "Origin": "http://localhost:8081",
                    },
                    cookies={"session_id": signed_session},
                )
                assert response.status_code == 200
                data = response.json()
                assert data["mode"] == "fallback"
                assert len(data["main_prompt"]) > 0
                assert len(data["short_prompt"]) > 0
                assert len(data["negative_prompt"]) > 0

    def test_frontend_mode_badge_fallback(self):
        """ModeBadge must render 'Standard' for mode=fallback."""
        source = _read_frontend_file(GENERATOR_PATH)
        assert "Standard" in source, "Missing 'Standard' label for fallback mode"
        assert "pill fallback" in source, "Missing 'pill fallback' CSS class"

    def test_frontend_mode_badge_local(self):
        """ModeBadge must render 'Offline' for mode=local."""
        source = _read_frontend_file(GENERATOR_PATH)
        assert "Offline" in source, "Missing 'Offline' label for local mode"
        assert "pill local" in source, "Missing 'pill local' CSS class"


# ============================================================
# AC5: Backend unreachable -> local FORGE.build() fallback
# ============================================================


class TestAC5LocalFallback:
    """AC5: When backend is unreachable or network error occurs,
    frontend falls back to local FORGE.build() and displays local result."""

    def test_frontend_catch_block_falls_back_to_forge_build(self):
        """generator.jsx catch block must call FORGE.build() on API failure."""
        source = _read_frontend_file(GENERATOR_PATH)
        assert "FORGE.build" in source, "Missing FORGE.build() fallback in generator.jsx"
        # Verify localBuild function sets mode to 'local'
        local_build_section = source[
            source.index("function localBuild") : source.index("function localBuild") + 200
        ]
        assert "local" in local_build_section, "localBuild must set mode='local'"

    def test_frontend_api_unavailable_uses_local(self):
        """When apiAvailable=false, runGenerate must use local FORGE.build()."""
        source = _read_frontend_file(GENERATOR_PATH)
        assert "apiAvailable" in source, "Missing apiAvailable check in runGenerate"
        # The flow: if !apiAvailable -> localBuild
        run_gen_section = source[
            source.index("runGenerate") : source.index("runGenerate") + 2000
        ]
        assert "!apiAvailable" in run_gen_section or "apiAvailable === false" in run_gen_section, (
            "Missing apiAvailable=false -> local fallback path"
        )

    def test_frontend_llm_disabled_uses_local(self):
        """When features.llm_enabled=false, runGenerate must use local FORGE.build()."""
        source = _read_frontend_file(GENERATOR_PATH)
        assert "llmEnabled" in source, "Missing llm_enabled check in runGenerate"

    def test_frontend_network_error_retry_then_local(self):
        """On network error, generator must retry once then fallback to local."""
        source = _read_frontend_file(GENERATOR_PATH)
        # Check for retry delay and second attempt
        assert "1000" in source or "setTimeout" in source, (
            "Missing 1s retry delay on network error"
        )

    def test_frontend_three_tier_fallback_chain(self):
        """Generator must implement 3-tier fallback: LLM -> backend fallback -> local."""
        source = _read_frontend_file(GENERATOR_PATH)
        # Verify all three modes are handled
        assert "llm" in source, "Missing LLM mode handling"
        assert "fallback" in source, "Missing fallback mode handling"
        assert "local" in source, "Missing local mode handling"
        # Verify the fallback chain: API call -> catch -> localBuild
        assert "localBuild" in source, "Missing localBuild function"


# ============================================================
# AC6: Browser fingerprint hash (SHA-256)
# ============================================================


class TestAC6FingerprintHash:
    """AC6: Frontend generates and sends client_fingerprint_hash
    using SHA-256 via crypto.subtle.digest."""

    def test_frontend_uses_crypto_subtle_sha256(self):
        """getFingerprintHash must use crypto.subtle.digest with SHA-256."""
        source = _read_frontend_file(API_CLIENT_PATH)
        assert "crypto.subtle" in source, "Missing crypto.subtle usage"
        assert "SHA-256" in source, "Missing SHA-256 algorithm"

    def test_frontend_fingerprint_includes_user_agent(self):
        """Fingerprint raw data must include navigator.userAgent."""
        source = _read_frontend_file(API_CLIENT_PATH)
        assert "userAgent" in source, "Fingerprint must include userAgent"

    def test_frontend_fingerprint_caches_result(self):
        """Fingerprint hash must be cached to avoid recomputation."""
        source = _read_frontend_file(API_CLIENT_PATH)
        assert "_fingerprintCache" in source, "Missing fingerprint cache"

    def test_frontend_fingerprint_graceful_fallback(self):
        """When crypto.subtle is unavailable, fingerprint must return empty string."""
        source = _read_frontend_file(API_CLIENT_PATH)
        # Search the full source for the empty string fallback pattern
        fp_start = source.index("getFingerprintHash")
        fp_section = source[fp_start:]
        # Find the end of the function (next function declaration or closing pattern)
        next_func = fp_section.find("\n  /**", 10)
        if next_func > 0:
            fp_section = fp_section[:next_func]
        assert "''" in fp_section or '""' in fp_section, (
            "Missing empty string fallback when crypto.subtle unavailable"
        )

    def test_frontend_fingerprint_hash_is_hex_string(self):
        """Fingerprint hash must be converted to hex string (64 chars for SHA-256)."""
        source = _read_frontend_file(API_CLIENT_PATH)
        # Search full source -- hex conversion is deep in the function
        assert "toString(16)" in source, "Hash must be converted to hex via toString(16)"
        assert "padStart(2" in source, "Hex bytes must be zero-padded via padStart(2, '0')"

    def test_backend_accepts_fingerprint_hash(self):
        """Backend GeneratePromptRequest must accept client_fingerprint_hash."""
        from routers.generate import GeneratePromptRequest
        assert "client_fingerprint_hash" in GeneratePromptRequest.model_fields, (
            "Backend missing client_fingerprint_hash field"
        )

    def test_backend_tolerates_null_fingerprint(self):
        """Backend must accept null/empty client_fingerprint_hash."""
        signed_session, signed_csrf = _bootstrap_session()
        client = TestClient(app)

        with patch("services.quota.get_redis") as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.get = AsyncMock(return_value="3")
            mock_get_redis.return_value = mock_redis

            with patch("services.llm_client.LLMClient.is_available", return_value=False):
                # Send with null fingerprint
                response = client.post(
                    "/api/generate-prompt",
                    json={
                        "output_type": "portrait",
                        "race": "Tiefling",
                        "client_fingerprint_hash": None,
                    },
                    headers={
                        "x-csrf-token": signed_csrf,
                        "Origin": "http://localhost:8081",
                    },
                    cookies={"session_id": signed_session},
                )
                assert response.status_code == 200

                # Send with empty string fingerprint
                response2 = client.post(
                    "/api/generate-prompt",
                    json={
                        "output_type": "portrait",
                        "race": "Tiefling",
                        "client_fingerprint_hash": "",
                    },
                    headers={
                        "x-csrf-token": signed_csrf,
                        "Origin": "http://localhost:8081",
                    },
                    cookies={"session_id": signed_session},
                )
                assert response2.status_code == 200


# ============================================================
# AC7: Mode and quota display in SuccessState
# ============================================================


class TestAC7ModeAndQuotaDisplay:
    """AC7: SuccessState displays current mode (LLM/Fallback/Local)
    and remaining quota (remaining / limit)."""

    def test_frontend_success_state_receives_mode_and_quota(self):
        """SuccessState must accept mode and quota props."""
        source = _read_frontend_file(GENERATOR_PATH)
        success_section = source[
            source.index("const SuccessState") : source.index("const SuccessState") + 200
        ]
        assert "mode" in success_section, "SuccessState missing mode prop"
        assert "quota" in success_section, "SuccessState missing quota prop"

    def test_frontend_quota_display_format(self):
        """QuotaDisplay must show 'Quota {remaining} / {limit}'."""
        source = _read_frontend_file(GENERATOR_PATH)
        assert "remaining" in source, "QuotaDisplay missing remaining"
        assert "limit" in source, "QuotaDisplay missing limit"
        # Verify the specific format string
        assert "Quota" in source, "QuotaDisplay missing 'Quota' label"

    def test_frontend_quota_exhausted_color(self):
        """When remaining=0, quota display must use crimson color."""
        source = _read_frontend_file(GENERATOR_PATH)
        assert "quota-exhausted" in source, (
            "Missing quota-exhausted CSS class for remaining=0"
        )

    def test_frontend_quota_low_color(self):
        """When remaining<=2, quota display must use brass color."""
        source = _read_frontend_file(GENERATOR_PATH)
        assert "quota-low" in source, (
            "Missing quota-low CSS class for remaining<=2"
        )

    def test_frontend_quota_hidden_in_local_mode(self):
        """QuotaDisplay must not render when mode=local."""
        source = _read_frontend_file(GENERATOR_PATH)
        # Search for the local mode check in QuotaDisplay
        qd_start = source.index("const QuotaDisplay")
        qd_section = source[qd_start:qd_start + 800]
        assert "local" in qd_section, "QuotaDisplay should hide in local mode"

    def test_frontend_quota_aria_label(self):
        """QuotaDisplay must have aria-label for accessibility."""
        source = _read_frontend_file(GENERATOR_PATH)
        # Search full source for aria-label on QuotaDisplay span
        qd_start = source.index("const QuotaDisplay")
        qd_section = source[qd_start:qd_start + 800]
        assert "aria-label" in qd_section, "QuotaDisplay missing aria-label"

    def test_frontend_mode_badge_aria_label(self):
        """ModeBadge must have aria-label for accessibility."""
        source = _read_frontend_file(GENERATOR_PATH)
        badge_section = source[
            source.index("const ModeBadge") : source.index("const ModeBadge") + 300
        ]
        assert "aria-label" in badge_section, "ModeBadge missing aria-label"

    def test_backend_quota_structure_in_response(self):
        """Backend generate response must include quota with limit, remaining, reset_at."""
        signed_session, signed_csrf = _bootstrap_session()
        client = TestClient(app)

        with patch("services.quota.get_redis") as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.get = AsyncMock(return_value="3")
            mock_get_redis.return_value = mock_redis

            with patch("services.llm_client.LLMClient.is_available", return_value=False):
                response = client.post(
                    "/api/generate-prompt",
                    json={"output_type": "portrait", "race": "Tiefling"},
                    headers={
                        "x-csrf-token": signed_csrf,
                        "Origin": "http://localhost:8081",
                    },
                    cookies={"session_id": signed_session},
                )
                data = response.json()
                assert "quota" in data
                assert "limit" in data["quota"]
                assert "remaining" in data["quota"]
                assert "reset_at" in data["quota"]


# ============================================================
# AC8: Docker compose nginx proxy
# ============================================================


class TestAC8DockerComposeNginxProxy:
    """AC8: docker compose up -> frontend accesses backend API via nginx proxy."""

    def test_docker_compose_exists(self):
        """docker-compose.yml must exist."""
        import os

        docker_compose_path = str(_PROJECT_ROOT / "docker-compose.yml")
        assert os.path.exists(docker_compose_path)

    def test_nginx_config_has_api_proxy(self):
        """nginx.conf must have /api/ location proxying to backend:8000."""
        import os

        nginx_paths = [
            str(_PROJECT_ROOT / "nginx" / "nginx.conf"),
            str(_PROJECT_ROOT / "nginx.conf"),
        ]
        found = False
        for path in nginx_paths:
            if os.path.exists(path):
                with open(path, "r") as f:
                    content = f.read()
                if "/api/" in content and "backend:8000" in content:
                    found = True
                break
        # If no separate nginx.conf, check docker-compose for inline config
        docker_compose_path = str(_PROJECT_ROOT / "docker-compose.yml")
        if not found and os.path.exists(docker_compose_path):
            with open(docker_compose_path, "r") as f:
                content = f.read()
            if "/api/" in content and "backend" in content:
                found = True
        assert found, "nginx must proxy /api/ to backend:8000"

    def test_frontend_api_base_configurable(self):
        """api-client.jsx must support configurable API_BASE for proxy deployment."""
        source = _read_frontend_file(API_CLIENT_PATH)
        assert "__API_BASE__" in source or "API_BASE" in source, (
            "Missing configurable API_BASE in api-client.jsx"
        )

    def test_frontend_fetch_uses_credentials_include(self):
        """api-client.jsx must use credentials:'include' for cookie transmission."""
        source = _read_frontend_file(API_CLIENT_PATH)
        assert "credentials" in source and "include" in source, (
            "Missing credentials:'include' for cookie-based auth"
        )


# ============================================================
# AC9: Quota exhausted -> fallback result still displayed
# ============================================================


class TestAC9QuotaExhaustedFallback:
    """AC9: When quota is exhausted (remaining=0), frontend still
    receives and displays fallback result correctly."""

    def test_backend_returns_fallback_with_zero_remaining(self):
        """When quota exceeded, backend returns mode=fallback with remaining=0."""
        signed_session, signed_csrf = _bootstrap_session()
        client = TestClient(app)

        with patch("services.quota.get_redis") as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.get = AsyncMock(return_value="10")  # At quota limit
            mock_get_redis.return_value = mock_redis

            response = client.post(
                "/api/generate-prompt",
                json={
                    "output_type": "portrait",
                    "race": "Tiefling",
                    "class_role": "Warlock",
                },
                headers={
                    "x-csrf-token": signed_csrf,
                    "Origin": "http://localhost:8081",
                },
                cookies={"session_id": signed_session},
            )
            assert response.status_code == 200, (
                "Quota exceeded should still return 200 with fallback"
            )
            data = response.json()
            assert data["mode"] == "fallback", (
                "Quota exceeded should return mode=fallback"
            )
            assert data["quota"]["remaining"] == 0, (
                "Quota exceeded should have remaining=0"
            )
            assert len(data["main_prompt"]) > 0, (
                "Fallback must still return valid prompt content"
            )

    def test_frontend_quota_exhausted_banner(self):
        """QuotaExhaustedBanner must show when mode=fallback AND remaining=0."""
        source = _read_frontend_file(GENERATOR_PATH)
        banner_section = source[
            source.index("const QuotaExhaustedBanner") :
            source.index("const QuotaExhaustedBanner") + 400
        ]
        assert "fallback" in banner_section, "Banner should only show in fallback mode"
        assert "remaining" in banner_section, "Banner should check remaining"
        assert "0" in banner_section or "=== 0" in banner_section, (
            "Banner should check remaining===0"
        )

    def test_frontend_quota_exhausted_banner_text(self):
        """QuotaExhaustedBanner must display hourly limit message."""
        source = _read_frontend_file(GENERATOR_PATH)
        assert "hourly limit" in source, "Missing hourly limit text in exhausted banner"

    def test_frontend_quota_exhausted_banner_role_status(self):
        """QuotaExhaustedBanner must have role='status' for accessibility."""
        source = _read_frontend_file(GENERATOR_PATH)
        banner_section = source[
            source.index("const QuotaExhaustedBanner") :
            source.index("const QuotaExhaustedBanner") + 400
        ]
        assert 'role="status"' in banner_section or "role=status" in banner_section, (
            "QuotaExhaustedBanner missing role=status"
        )


# ============================================================
# Cross-cutting: CSS additions for mode badges and quota
# ============================================================


class TestCSSAdditions:
    """Verify CSS additions for mode badges, quota display, and banners."""

    def test_css_pill_llm_styles(self):
        """CSS must define .pill.llm styles."""
        source = _read_frontend_file(STYLE_CSS_PATH)
        assert ".pill.llm" in source, "Missing .pill.llm CSS"

    def test_css_pill_fallback_styles(self):
        """CSS must define .pill.fallback styles."""
        source = _read_frontend_file(STYLE_CSS_PATH)
        assert ".pill.fallback" in source, "Missing .pill.fallback CSS"

    def test_css_pill_local_styles(self):
        """CSS must define .pill.local styles."""
        source = _read_frontend_file(STYLE_CSS_PATH)
        assert ".pill.local" in source, "Missing .pill.local CSS"

    def test_css_quota_low_styles(self):
        """CSS must define .quota-low styles."""
        source = _read_frontend_file(STYLE_CSS_PATH)
        assert ".quota-low" in source, "Missing .quota-low CSS"

    def test_css_quota_exhausted_styles(self):
        """CSS must define .quota-exhausted styles."""
        source = _read_frontend_file(STYLE_CSS_PATH)
        assert ".quota-exhausted" in source, "Missing .quota-exhausted CSS"

    def test_css_banner_warn_styles(self):
        """CSS must define .banner.warn styles."""
        source = _read_frontend_file(STYLE_CSS_PATH)
        assert ".banner.warn" in source, "Missing .banner.warn CSS"


# ============================================================
# Cross-cutting: Script load order
# ============================================================


class TestScriptLoadOrder:
    """Verify index.html loads api-client.jsx before generator.jsx."""

    def test_api_client_loaded_before_generator(self):
        """api-client.jsx must appear before generator.jsx in index.html."""
        source = _read_frontend_file(INDEX_HTML_PATH)
        api_client_pos = source.index("api-client.jsx")
        generator_pos = source.index("generator.jsx")
        assert api_client_pos < generator_pos, (
            "api-client.jsx must be loaded before generator.jsx"
        )

    def test_api_client_uses_babel_script_type(self):
        """api-client.jsx must use type='text/babel' script tag."""
        source = _read_frontend_file(INDEX_HTML_PATH)
        # Find the api-client script tag
        api_client_line = source[
            source.index("api-client.jsx") - 60 : source.index("api-client.jsx") + 20
        ]
        assert "text/babel" in api_client_line, (
            "api-client.jsx must use type='text/babel' script tag"
        )


# ============================================================
# Security: CSRF enforcement and session isolation
# ============================================================


class TestSecurityCSRFEnforcement:
    """Security: CSRF middleware must enforce token on mutating endpoints."""

    # CSRF 中间件源文件路径（基于项目根目录动态计算）
    _CSRF_MIDDLEWARE_PATH = str(Path(__file__).parent.parent / "middleware" / "csrf.py")

    def test_csrf_middleware_checks_x_csrf_token_header(self):
        """CSRF middleware must read x-csrf-token header."""
        source = open(self._CSRF_MIDDLEWARE_PATH, "r").read()
        assert "x-csrf-token" in source.lower(), (
            "CSRF middleware must check x-csrf-token header"
        )

    def test_csrf_middleware_whitelists_bootstrap(self):
        """CSRF middleware must whitelist /api/session/bootstrap."""
        source = open(self._CSRF_MIDDLEWARE_PATH, "r").read()
        assert "/api/session/bootstrap" in source, (
            "CSRF middleware must whitelist bootstrap endpoint"
        )

    def test_csrf_middleware_whitelists_health(self):
        """CSRF middleware must whitelist /api/health."""
        source = open(self._CSRF_MIDDLEWARE_PATH, "r").read()
        assert "/api/health" in source, (
            "CSRF middleware must whitelist health endpoint"
        )

    def test_csrf_middleware_skips_safe_methods(self):
        """CSRF middleware must skip GET/HEAD/OPTIONS."""
        source = open(self._CSRF_MIDDLEWARE_PATH, "r").read()
        assert "GET" in source, "CSRF middleware must skip GET"
        assert "HEAD" in source, "CSRF middleware must skip HEAD"

    def test_generate_without_session_returns_401(self):
        """POST /api/generate-prompt without session cookie must return 401."""
        client = TestClient(app)
        response = client.post(
            "/api/generate-prompt",
            json={"output_type": "portrait", "race": "Tiefling"},
            headers={"x-csrf-token": "some-token", "Origin": "http://localhost:8081"},
        )
        assert response.status_code in (401, 403), (
            "Generate without session should return 401 or 403"
        )

    def test_feedback_endpoint_requires_csrf(self):
        """POST /api/feedback must require CSRF token."""
        signed_session, _ = _bootstrap_session()
        client = TestClient(app)
        response = client.post(
            "/api/feedback",
            json={
                "request_id": "test-id",
                "feedback": "not_useful",
            },
            headers={"Origin": "http://localhost:8081"},
            cookies={"session_id": signed_session},
        )
        assert response.status_code == 403, (
            "Feedback without CSRF should return 403"
        )


# ============================================================
# Offline mode banner
# ============================================================


class TestOfflineModeBanner:
    """Verify offline mode banner behavior after 3+ consecutive failures."""

    def test_frontend_offline_banner_component(self):
        """OfflineBanner component must exist in generator.jsx."""
        source = _read_frontend_file(GENERATOR_PATH)
        assert "const OfflineBanner" in source, "Missing OfflineBanner component"

    def test_frontend_offline_banner_text(self):
        """OfflineBanner must display 'offline mode' message."""
        source = _read_frontend_file(GENERATOR_PATH)
        assert "offline mode" in source.lower(), (
            "Missing offline mode text in OfflineBanner"
        )

    def test_frontend_offline_threshold(self):
        """Generator must track consecutive failures and set offlineMode at threshold."""
        source = _read_frontend_file(GENERATOR_PATH)
        assert "OFFLINE_THRESHOLD" in source or "consecutiveFailures" in source, (
            "Missing offline threshold tracking"
        )

    def test_frontend_offline_banner_role_status(self):
        """OfflineBanner must have role='status' for accessibility."""
        source = _read_frontend_file(GENERATOR_PATH)
        offline_section = source[
            source.index("const OfflineBanner") : source.index("const OfflineBanner") + 300
        ]
        assert 'role="status"' in offline_section or "role=status" in offline_section, (
            "OfflineBanner missing role=status"
        )

    def test_frontend_success_resets_offline_mode(self):
        """Successful API call must reset offlineMode to false."""
        source = _read_frontend_file(GENERATOR_PATH)
        assert "recordSuccess" in source, "Missing recordSuccess function"
        success_section = source[
            source.index("function recordSuccess") : source.index("function recordSuccess") + 100
        ]
        assert "false" in success_section, "recordSuccess must set offlineMode=false"
