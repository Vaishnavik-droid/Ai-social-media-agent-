import os
import tempfile
from pathlib import Path
from unittest.mock import patch, AsyncMock
import pytest
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.config import Settings, settings
from app.platforms.bluesky import BlueskyAdapter, bluesky_adapter
from app.platforms.facebook import FacebookAdapter, facebook_adapter
from app.platforms.instagram import InstagramAdapter, instagram_adapter
from app.services.credential_service import credential_service


def test_core_settings_loaded_properly():
    """Verify that core settings are properly populated from .env."""
    assert settings.ENVIRONMENT in ["development", "production", "test"]
    assert settings.PORT == 8000
    assert settings.HOST == "127.0.0.1"
    assert settings.API_PREFIX == "/api/v1"
    assert isinstance(settings.CORS_ORIGINS, list)
    assert len(settings.CORS_ORIGINS) > 0
    assert settings.GROQ_MODEL == "llama-3.3-70b-versatile"
    assert bool(settings.SUPABASE_URL) is True
    assert bool(settings.SUPABASE_ANON_KEY) is True
    assert bool(settings.TOKEN_ENCRYPTION_KEY) is True


def test_platform_credentials_loaded_from_platform_env():
    """Verify that platform developer credentials load from platform_credentials.env."""
    assert settings.META_APP_ID == "2231204290777395"
    assert settings.BLUESKY_HANDLE == "curator06.bsky.social"
    assert settings.BLUESKY_SERVICE_URL == "https://bsky.social"


def test_pinterest_and_youtube_readiness():
    """Verify Pinterest and YouTube settings are defined and have safe default fallbacks."""
    # Settings object must contain these attributes for seamless future integration
    assert hasattr(settings, "PINTEREST_APP_ID")
    assert hasattr(settings, "PINTEREST_APP_SECRET")
    assert hasattr(settings, "PINTEREST_REDIRECT_URI")

    assert hasattr(settings, "GOOGLE_CLIENT_ID")
    assert hasattr(settings, "GOOGLE_CLIENT_SECRET")
    assert hasattr(settings, "YOUTUBE_REDIRECT_URI")

    # In blank environment, defaults are safe strings
    blank = Settings(_env_file=None)
    assert blank.PINTEREST_APP_ID == ""
    assert blank.PINTEREST_APP_SECRET == ""
    assert blank.GOOGLE_CLIENT_ID == ""
    assert blank.GOOGLE_CLIENT_SECRET == ""


def test_process_environment_variable_precedence():
    """Verify that environment variables in os.environ take highest precedence over file settings."""
    test_key = "ENVIRONMENT"
    original_val = os.environ.get(test_key)

    try:
        os.environ[test_key] = "staging-override"
        custom_settings = Settings()
        assert custom_settings.ENVIRONMENT == "staging-override"
    finally:
        if original_val is not None:
            os.environ[test_key] = original_val
        else:
            os.environ.pop(test_key, None)


def test_multi_env_file_resolution_order():
    """Verify that core .env and platform_credentials.env merge seamlessly."""
    f_core = tempfile.NamedTemporaryFile("w", delete=False, suffix=".env")
    f_plat = tempfile.NamedTemporaryFile("w", delete=False, suffix=".env")
    try:
        f_core.write("ENVIRONMENT=staging\nGROQ_MODEL=custom-llm\n")
        f_core.close()
        f_plat.write("META_APP_ID=555123456789\nPINTEREST_APP_ID=pin_app_999\n")
        f_plat.close()

        class TestMergedSettings(BaseSettings):
            ENVIRONMENT: str = "dev"
            GROQ_MODEL: str = "default-llm"
            META_APP_ID: str = ""
            PINTEREST_APP_ID: str = ""
            model_config = SettingsConfigDict(
                env_file=(f_core.name, f_plat.name),
                extra="ignore"
            )

        merged = TestMergedSettings()
        assert merged.ENVIRONMENT == "staging"
        assert merged.GROQ_MODEL == "custom-llm"
        assert merged.META_APP_ID == "555123456789"
        assert merged.PINTEREST_APP_ID == "pin_app_999"
    finally:
        try:
            Path(f_core.name).unlink(missing_ok=True)
            Path(f_plat.name).unlink(missing_ok=True)
        except Exception:
            pass


@pytest.mark.anyio
async def test_legacy_facebook_tokens_not_used_in_active_publishing():
    """Verify FacebookAdapter refuses live publish without Supabase credentials, ignoring legacy tokens."""
    adapter = FacebookAdapter()
    with patch("app.services.credential_service.credential_service.get_credentials", new_callable=AsyncMock) as mock_creds:
        mock_creds.return_value = None  # No active connected account in Supabase
        res = await adapter.publish_post(content="Test active publish", dry_run=False)
        assert res.status == "failed"
        assert "Please connect your Facebook Page" in res.error_message


@pytest.mark.anyio
async def test_legacy_instagram_tokens_not_used_in_active_publishing():
    """Verify InstagramAdapter refuses live publish without Supabase credentials, ignoring legacy tokens."""
    adapter = InstagramAdapter()
    with patch("app.services.credential_service.credential_service.get_credentials", new_callable=AsyncMock) as mock_creds:
        mock_creds.return_value = None  # No active connected account in Supabase
        res = await adapter.publish_post(content="Test IG active publish", media_url="https://example.com/img.jpg", dry_run=False)
        assert res.status == "failed"
        assert "Please connect your Instagram" in res.error_message


def test_legacy_meta_tokens_do_not_report_connected_status():
    """Verify that Facebook and Instagram report disconnected when no OAuth credentials exist in Supabase."""
    from app.services.credential_service import _MEMORY_CONNECTIONS
    _MEMORY_CONNECTIONS.pop("facebook", None)
    _MEMORY_CONNECTIONS.pop("instagram", None)

    fb_status = credential_service.get_safe_connection_item("facebook")
    assert fb_status["status"] == "disconnected"
    assert fb_status["handle"] == "Not Connected"
    assert fb_status["is_configured"] is False

    ig_status = credential_service.get_safe_connection_item("instagram")
    assert ig_status["status"] == "disconnected"
    assert ig_status["handle"] == "Not Connected"
    assert ig_status["is_configured"] is False


def test_bluesky_service_url_configuration():
    """Verify BlueskyAdapter dynamically uses the configured BLUESKY_SERVICE_URL."""
    adapter = BlueskyAdapter()
    assert adapter.BSKY_HOST == "https://bsky.social"

    with patch.object(settings, "BLUESKY_SERVICE_URL", "https://custom.pds.social/"):
        assert adapter.BSKY_HOST == "https://custom.pds.social"
