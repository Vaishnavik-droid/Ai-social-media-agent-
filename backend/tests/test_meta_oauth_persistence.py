"""
OmniPulse AI - Meta OAuth Persistence, Foreign Key Integrity, & Logging Security Test Suite
Covers all 10 required test scenarios from the Meta OAuth Persistence specification:
  1. Existing Auth user with a matching profile.
  2. Auth user whose profile is missing (auto-restored from auth.users).
  3. Facebook OAuth persistence with true user ID.
  4. Instagram OAuth persistence with true user ID.
  5. Facebook followed by Instagram authentication (independent rows, no collision).
  6. Instagram followed by Facebook authentication (independent rows, no collision).
  7. Both connections surviving application refresh (in-memory cache cleared).
  8. Both connections surviving a fresh backend invocation.
  9. Independent disconnect operations.
 10. No credentials or OAuth states appearing in application logs.
 11. Supabase persistence failure prevents misleading in-memory connected status.
"""
import logging
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.logging_redactor import SensitiveDataFilter, redact_sensitive_str, redact_sensitive_dict
from app.main import app
from app.services.credential_service import credential_service, _MEMORY_CONNECTIONS, _MEMORY_OAUTH_STATES
from app.api.v1.routes.posts import get_default_user_id

client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_memory():
    """Ensure in-memory connection dictionaries are clean between tests."""
    yield
    _MEMORY_CONNECTIONS.clear()
    _MEMORY_OAUTH_STATES.clear()


# =============================================================================
# 1. Profile Verification & Auto-Restoration Tests
# =============================================================================

@pytest.mark.anyio
async def test_1_existing_auth_user_with_matching_profile():
    """Scenario 1: Confirmed existing user exists in public.profiles."""
    active_uid = get_default_user_id()
    assert active_uid is not None
    # Ensure profile check succeeds
    has_profile = await credential_service._ensure_profile_exists(active_uid)
    assert has_profile is True


@pytest.mark.anyio
async def test_2_auth_user_whose_profile_is_missing():
    """Scenario 2: Auth user whose profile is temporarily missing in public.profiles is auto-restored."""
    mock_auth_user = MagicMock()
    mock_auth_user.id = "88782b79-1b78-4e79-b3ab-294e179b3274"
    mock_auth_user.email = "vaishnavikolekar2023@gmail.com"
    mock_auth_user.user_metadata = {"full_name": "Vaishnavi Kolekar", "username": "vaishnavik"}

    mock_client = MagicMock()
    # First select returns empty (profile missing)
    mock_client.table().select().eq().single().execute.return_value = MagicMock(data=None)
    # Auth admin returns user
    mock_client.auth.admin.get_user_by_id.return_value = MagicMock(user=mock_auth_user)
    mock_client.table().upsert().execute.return_value = MagicMock(data=[{"id": mock_auth_user.id}])

    restored = await credential_service._ensure_profile_exists(mock_auth_user.id, client=mock_client)
    assert restored is True
    # Verify upsert called to restore profile
    assert mock_client.table().upsert.called


# =============================================================================
# 2. Independent Meta OAuth Persistence Tests (Facebook & Instagram)
# =============================================================================

@pytest.mark.anyio
async def test_3_facebook_oauth_persistence():
    """Scenario 3: Facebook OAuth persistence saves durable record with true user ID."""
    uid = get_default_user_id()
    conn = await credential_service.save_connection(
        platform="facebook",
        handle="Test OmniPulse Facebook Page",
        access_token="EAAB_test_facebook_page_token",
        account_id="fb_page_1001",
        account_name="Test FB Page",
        metadata={"category": "Brand", "page_id": "fb_page_1001"},
        user_id=uid,
    )
    assert conn["status"] == "connected"
    assert conn["handle"] == "Test OmniPulse Facebook Page"
    assert conn["accountId"] == "fb_page_1001"

    # Verify retrieval
    safe_item = credential_service.get_safe_connection_item("facebook", user_id=uid)
    assert safe_item["status"] == "connected"
    assert safe_item["handle"] == "Test OmniPulse Facebook Page"


@pytest.mark.anyio
async def test_4_instagram_oauth_persistence():
    """Scenario 4: Instagram OAuth persistence saves durable record with true user ID."""
    uid = get_default_user_id()
    conn = await credential_service.save_connection(
        platform="instagram",
        handle="@omnipulse_official",
        access_token="EAAB_test_instagram_token",
        account_id="ig_biz_2002",
        account_name="omnipulse_official",
        metadata={"instagram_username": "omnipulse_official"},
        user_id=uid,
    )
    assert conn["status"] == "connected"
    assert conn["handle"] == "@omnipulse_official"
    assert conn["accountId"] == "ig_biz_2002"

    safe_item = credential_service.get_safe_connection_item("instagram", user_id=uid)
    assert safe_item["status"] == "connected"
    assert safe_item["handle"] == "@omnipulse_official"


@pytest.mark.anyio
async def test_5_facebook_followed_by_instagram_authentication():
    """Scenario 5: Facebook followed by Instagram does NOT overwrite Facebook."""
    uid = get_default_user_id()

    # 1. Connect Facebook
    await credential_service.save_connection(
        platform="facebook",
        handle="Primary FB Page",
        access_token="token_fb_1",
        account_id="fb_page_999",
        user_id=uid,
    )

    # 2. Connect Instagram
    await credential_service.save_connection(
        platform="instagram",
        handle="@primary_ig",
        access_token="token_ig_1",
        account_id="ig_acc_999",
        user_id=uid,
    )

    # 3. Verify both remain connected with distinct data
    fb_item = credential_service.get_safe_connection_item("facebook", user_id=uid)
    ig_item = credential_service.get_safe_connection_item("instagram", user_id=uid)

    assert fb_item["status"] == "connected"
    assert fb_item["handle"] == "Primary FB Page"
    assert fb_item["accountId"] == "fb_page_999"

    assert ig_item["status"] == "connected"
    assert ig_item["handle"] == "@primary_ig"
    assert ig_item["accountId"] == "ig_acc_999"


@pytest.mark.anyio
async def test_6_instagram_followed_by_facebook_authentication():
    """Scenario 6: Instagram followed by Facebook does NOT overwrite Instagram."""
    uid = get_default_user_id()

    # 1. Connect Instagram
    await credential_service.save_connection(
        platform="instagram",
        handle="@insta_first",
        access_token="token_ig_2",
        account_id="ig_acc_888",
        user_id=uid,
    )

    # 2. Connect Facebook
    await credential_service.save_connection(
        platform="facebook",
        handle="FB Page Second",
        access_token="token_fb_2",
        account_id="fb_page_888",
        user_id=uid,
    )

    # 3. Verify both remain connected with distinct data
    ig_item = credential_service.get_safe_connection_item("instagram", user_id=uid)
    fb_item = credential_service.get_safe_connection_item("facebook", user_id=uid)

    assert ig_item["status"] == "connected"
    assert ig_item["handle"] == "@insta_first"
    assert fb_item["status"] == "connected"
    assert fb_item["handle"] == "FB Page Second"


# =============================================================================
# 3. Persistence Across App Refresh & Fresh Invocations
# =============================================================================

@pytest.mark.anyio
async def test_7_both_connections_surviving_application_refresh():
    """Scenario 7: Both connections survive application refresh (clearing memory cache)."""
    uid = get_default_user_id()

    await credential_service.save_connection(
        platform="facebook",
        handle="Persisted FB Page",
        access_token="token_fb_persist",
        account_id="fb_page_persist",
        user_id=uid,
    )
    await credential_service.save_connection(
        platform="instagram",
        handle="@persisted_ig",
        access_token="token_ig_persist",
        account_id="ig_page_persist",
        user_id=uid,
    )

    # Simulate browser / UI refresh: wipe local process memory
    _MEMORY_CONNECTIONS.clear()

    # Query connection items - should load directly from Supabase
    fb = credential_service.get_safe_connection_item("facebook", user_id=uid)
    ig = credential_service.get_safe_connection_item("instagram", user_id=uid)

    assert fb["status"] == "connected"
    assert fb["handle"] == "Persisted FB Page"
    assert ig["status"] == "connected"
    assert ig["handle"] == "@persisted_ig"


@pytest.mark.anyio
async def test_8_both_connections_surviving_fresh_backend_invocation():
    """Scenario 8: Both connections survive a fresh backend invocation through list_all_connections."""
    uid = get_default_user_id()

    # Memory is cleared
    _MEMORY_CONNECTIONS.clear()

    all_conns = await credential_service.list_all_connections(user_id=uid)
    conns_by_id = {c["id"]: c for c in all_conns}

    assert "facebook" in conns_by_id
    assert "instagram" in conns_by_id
    assert conns_by_id["facebook"]["status"] == "connected"
    assert conns_by_id["instagram"]["status"] == "connected"


# =============================================================================
# 4. Independent Disconnect Operations
# =============================================================================

@pytest.mark.anyio
async def test_9_independent_disconnect_operations():
    """Scenario 9: Disconnecting Facebook leaves Instagram intact, and vice versa."""
    uid = get_default_user_id()

    # 1. Disconnect Facebook only
    await credential_service.delete_connection("facebook", user_id=uid)

    fb = credential_service.get_safe_connection_item("facebook", user_id=uid)
    ig = credential_service.get_safe_connection_item("instagram", user_id=uid)

    assert fb["status"] == "disconnected"
    assert ig["status"] == "connected"

    # 2. Disconnect Instagram only
    await credential_service.delete_connection("instagram", user_id=uid)

    ig_after = credential_service.get_safe_connection_item("instagram", user_id=uid)
    assert ig_after["status"] == "disconnected"


# =============================================================================
# 5. Security & Log Redaction
# =============================================================================

def test_10_no_credentials_appearing_in_application_logs():
    """Scenario 10: Verify sensitive parameters and OAuth states are never logged."""
    filter_instance = SensitiveDataFilter()

    # Test sensitive query string in URL
    raw_url = "https://graph.facebook.com/v19.0/oauth/access_token?client_id=123&client_secret=supersecret123&code=AQB_secret_code_12345&state=meta_secure_state_987654321"
    redacted_url = redact_sensitive_str(raw_url)
    assert "supersecret123" not in redacted_url
    assert "AQB_secret_code_12345" not in redacted_url
    assert "meta_secure_state_987654321" not in redacted_url
    assert "client_secret=[REDACTED]" in redacted_url
    assert "code=[REDACTED]" in redacted_url
    assert "state=[REDACTED]" in redacted_url

    # Test dictionary redaction
    payload = {
        "access_token": "EAAB_raw_user_token",
        "refresh_token": "AQX_raw_refresh_token",
        "client_secret": "my_secret",
        "state": "meta_xyz",
        "code": "AQ123456",
        "nested": {
            "token": "secret_nested_token",
            "safe_field": "hello world"
        }
    }
    redacted_dict = redact_sensitive_dict(payload)
    assert redacted_dict["access_token"] == "[REDACTED]"
    assert redacted_dict["refresh_token"] == "[REDACTED]"
    assert redacted_dict["client_secret"] == "[REDACTED]"
    assert redacted_dict["state"] == "[REDACTED]"
    assert redacted_dict["code"] == "[REDACTED]"
    assert redacted_dict["nested"]["token"] == "[REDACTED]"
    assert redacted_dict["nested"]["safe_field"] == "hello world"

    # Test LogRecord intercept
    logger = logging.getLogger("test_redactor")
    log_record = logger.makeRecord(
        "test_redactor",
        logging.ERROR,
        "test.py",
        42,
        "OAuth failed with code=%s and client_secret=%s",
        ("AQB_secret_code_9999", "secret_value_xyz"),
        None,
    )
    filter_instance.filter(log_record)
    assert "AQB_secret_code_9999" not in str(log_record.msg)
    assert "secret_value_xyz" not in str(log_record.msg)
    assert "AQB_secret_code_9999" not in str(log_record.args)
    assert "secret_value_xyz" not in str(log_record.args)


@pytest.mark.anyio
async def test_11_database_persistence_failure_prevents_fake_connected_status():
    """Scenario 11: A database write failure raises RuntimeError and NEVER reports false success."""
    mock_client = MagicMock()
    mock_client.table().select().eq().single().execute.return_value = MagicMock(data=[{"id": "valid_id"}])
    # Upsert throws database exception
    mock_client.table().upsert().execute.side_effect = Exception('insert or update violates foreign key constraint')

    with patch("app.services.credential_service._get_supabase_client", return_value=mock_client):
        with pytest.raises(RuntimeError) as exc_info:
            await credential_service.save_connection(
                platform="facebook",
                handle="Unpersisted Page",
                access_token="tok_123",
                account_id="page_fail",
                user_id="invalid-uid",
            )
        assert "Database persistence failed" in str(exc_info.value)

    # In-memory store must NOT have 'facebook' marked as connected
    assert _MEMORY_CONNECTIONS.get("facebook") is None
