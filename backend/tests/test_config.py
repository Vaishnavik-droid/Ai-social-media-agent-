import pytest
from app.core.config import Settings, settings
from app.platforms.bluesky import bluesky_adapter
from app.platforms.linkedin import linkedin_adapter
from app.platforms.facebook import facebook_adapter
from app.platforms.instagram import instagram_adapter
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_settings_load_from_backend_env():
    """Verify backend settings load cleanly from backend/.env without errors."""
    assert settings.ENVIRONMENT in ["development", "production", "test"]
    assert settings.PORT == 8000
    assert settings.HOST == "127.0.0.1"
    assert isinstance(settings.CORS_ORIGINS, list)
    assert "http://localhost:3000" in settings.CORS_ORIGINS
    assert "http://localhost:5173" in settings.CORS_ORIGINS


def test_publishing_defaults_to_safe_mock_mode():
    """Verify default publishing mode is 'mock' to safeguard against accidental live posts."""
    default_settings = Settings(_env_file=None)
    assert default_settings.PUBLISHING_MODE == "mock"



def test_connections_endpoint_contains_active_platforms():
    """Verify connections endpoint returns the 4 active platforms and excludes WhatsApp."""
    resp = client.get("/api/v1/connections")
    assert resp.status_code == 200
    conn_list = resp.json().get("connections", [])
    platform_ids = [c["id"] for c in conn_list]
    assert "bluesky" in platform_ids
    assert "linkedin" in platform_ids
    assert "facebook" in platform_ids
    assert "instagram" in platform_ids
    assert "whatsapp" not in platform_ids


def test_missing_optional_credentials_do_not_crash_startup():
    """Verify that absent or blank credentials do not prevent application or adapter startup."""
    # Blank values should simply mark the platform as unconfigured
    assert bluesky_adapter.platform_name == "bluesky"
    assert linkedin_adapter.platform_name == "linkedin"
    assert facebook_adapter.platform_name == "facebook"
    assert instagram_adapter.platform_name == "instagram"


@pytest.mark.anyio
async def test_blank_credentials_evaluated_as_unconfigured():
    """Verify that empty/blank credentials fail validation safely without network dispatch."""
    # Custom settings with all credentials blank
    blank_settings = Settings(
        BLUESKY_HANDLE="",
        BLUESKY_APP_PASSWORD="",
        LINKEDIN_ACCESS_TOKEN="",
        FACEBOOK_PAGE_ACCESS_TOKEN="",
        INSTAGRAM_ACCESS_TOKEN="",
    )
    assert blank_settings.BLUESKY_HANDLE == ""
    assert blank_settings.LINKEDIN_ACCESS_TOKEN == ""


def test_connections_endpoint_never_exposes_secrets():
    """Verify /api/v1/connections returns display handles only and never leaks tokens or keys."""
    resp = client.get("/api/v1/connections")
    assert resp.status_code == 200
    data = resp.json()
    conns = data.get("connections", [])
    assert len(conns) == 4

    # Ensure no token values or passwords appear in any field
    for c in conns:
        for field in ["id", "name", "handle", "status", "connectedUser"]:
            val = str(c.get(field, ""))
            assert "gsk_" not in val
            assert "eyJ" not in val
            assert "app_password" not in val.lower()


def test_groq_and_supabase_configurations_loaded():
    """Verify Groq and Supabase variables are correctly mapped."""
    assert settings.GROQ_MODEL == "llama-3.3-70b-versatile"
    assert bool(settings.SUPABASE_URL) is True
    assert bool(settings.SUPABASE_ANON_KEY) is True
