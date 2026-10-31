import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.core.encryption import token_encryption_service
from app.services.credential_service import credential_service

client = TestClient(app)


# =============================================================================
# 1. Encryption Service Tests
# =============================================================================

def test_token_encryption_and_decryption():
    """Verify authenticated symmetric encryption and decryption of tokens."""
    plaintext = "EAABtestMetaLongLivedToken123456789!@#"
    ciphertext = token_encryption_service.encrypt(plaintext)

    assert ciphertext != plaintext
    assert isinstance(ciphertext, str)
    assert len(ciphertext) > len(plaintext)

    decrypted = token_encryption_service.decrypt(ciphertext)
    assert decrypted == plaintext


def test_encryption_fallback_handles_empty_or_corrupt_data():
    """Verify graceful handling for empty or corrupt ciphertexts."""
    assert token_encryption_service.encrypt("") == ""
    assert token_encryption_service.decrypt("") is None
    assert token_encryption_service.decrypt(None) is None
    assert token_encryption_service.decrypt("invalid-non-fernet-token") is None


# =============================================================================
# 2. Meta OAuth Authorization Initiation Tests
# =============================================================================

def test_meta_oauth_initiate_facebook():
    """Verify Facebook OAuth authorization URL and state generation."""
    with patch.object(settings, "META_APP_ID", "2231204290777395"):
        response = client.post("/api/v1/connections/meta/authorize", json={"platform": "facebook"})
        assert response.status_code == 200
        data = response.json()

        assert "auth_url" in data
        assert "state" in data
        assert data["platform"] == "facebook"

        url = data["auth_url"]
        assert "https://www.facebook.com/v19.0/dialog/oauth" in url
        assert "client_id=2231204290777395" in url
        assert f"state={data['state']}" in url
        assert "pages_manage_posts" in url
        assert "pages_read_engagement" in url


def test_meta_oauth_initiate_instagram():
    """Verify Instagram OAuth authorization URL includes Instagram scopes."""
    with patch.object(settings, "META_APP_ID", "2231204290777395"):
        response = client.post("/api/v1/connections/meta/authorize", json={"platform": "instagram"})
        assert response.status_code == 200
        data = response.json()

        url = data["auth_url"]
        assert "instagram_basic" in url
        assert "instagram_content_publish" in url


def test_meta_oauth_initiate_unsupported_platform():
    """Verify rejection when initiating Meta OAuth for non-Meta platforms."""
    response = client.post("/api/v1/connections/meta/authorize", json={"platform": "bluesky"})
    assert response.status_code == 400
    assert "either 'facebook' or 'instagram'" in response.json()["detail"]


# =============================================================================
# 3. Meta OAuth Callback & Error Handling Tests
# =============================================================================

def test_meta_oauth_callback_missing_or_expired_state():
    """Verify callback fails safely when state is unknown or expired."""
    response = client.get("/api/v1/connections/meta/callback?code=mock_code&state=non_existent_state_123")
    assert response.status_code == 400
    assert "Invalid or expired OAuth state session" in response.text


def test_meta_oauth_callback_access_denied_from_provider():
    """Verify callback handles user cancellation gracefully with safe HTML response."""
    response = client.get(
        "/api/v1/connections/meta/callback?error=access_denied&error_description=User+cancelled+authorization&state=ignored"
    )
    assert response.status_code == 400
    assert "User cancelled authorization" in response.text
    assert "OMNIPULSE_OAUTH_ERROR" in response.text


@pytest.mark.anyio
async def test_meta_oauth_callback_facebook_success():
    """Verify full Facebook OAuth token exchange, page lookup, and connection persistence."""
    init_res = client.post("/api/v1/connections/meta/authorize", json={"platform": "facebook"})
    state = init_res.json()["state"]

    mock_short_token = {"access_token": "short_user_token_abc"}
    mock_long_token = {"access_token": "long_user_token_xyz"}
    mock_accounts_data = {
        "data": [
            {
                "id": "page_987654321",
                "name": "OmniPulse Brand Page",
                "access_token": "page_access_token_long_live_123",
            }
        ]
    }

    async def mock_async_client_get(url, *args, **kwargs):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        if "oauth/access_token" in url:
            if "grant_type=fb_exchange_token" in str(kwargs.get("params", {})):
                mock_resp.json.return_value = mock_long_token
            else:
                mock_resp.json.return_value = mock_short_token
        elif "/me/accounts" in url:
            mock_resp.json.return_value = mock_accounts_data
        elif "/page_987654321" in url:
            mock_resp.json.return_value = {"id": "page_987654321", "name": "OmniPulse Brand Page"}
        return mock_resp

    with patch("httpx.AsyncClient.get", side_effect=mock_async_client_get), \
         patch.object(settings, "META_APP_SECRET", "mock_meta_app_secret"):

        callback_res = client.get(f"/api/v1/connections/meta/callback?code=mock_auth_code_123&state={state}")

        assert callback_res.status_code == 200
        assert "OMNIPULSE_OAUTH_SUCCESS" in callback_res.text
        assert "OmniPulse Brand Page" in callback_res.text

        # Verify Facebook connection is now recorded and active
        conn = credential_service.get_safe_connection_item("facebook")
        assert conn["status"] == "connected"
        assert conn["accountId"] == "page_987654321"
        assert conn["accountName"] == "OmniPulse Brand Page"


@pytest.mark.anyio
async def test_meta_oauth_callback_instagram_missing_business_account():
    """Verify Instagram OAuth fails gracefully when user has pages but no Instagram Business Account linked."""
    init_res = client.post("/api/v1/connections/meta/authorize", json={"platform": "instagram"})
    state = init_res.json()["state"]

    mock_short_token = {"access_token": "short_user_token_abc"}
    mock_long_token = {"access_token": "long_user_token_xyz"}
    mock_accounts_no_ig = {
        "data": [
            {
                "id": "page_111",
                "name": "Personal Page",
                "access_token": "page_tok_111",
            }
        ]
    }

    async def mock_async_client_get(url, *args, **kwargs):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        if "oauth/access_token" in url:
            mock_resp.json.return_value = mock_long_token
        elif "/me/accounts" in url:
            mock_resp.json.return_value = mock_accounts_no_ig
        return mock_resp

    with patch("httpx.AsyncClient.get", side_effect=mock_async_client_get), \
         patch.object(settings, "META_APP_SECRET", "mock_meta_app_secret"):

        callback_res = client.get(f"/api/v1/connections/meta/callback?code=mock_code&state={state}")
        assert callback_res.status_code == 400
        assert "No Instagram Business or Creator account found" in callback_res.text


@pytest.mark.anyio
async def test_meta_oauth_callback_instagram_success():
    """Verify successful Instagram OAuth callback with linked Instagram Business Account."""
    init_res = client.post("/api/v1/connections/meta/authorize", json={"platform": "instagram"})
    state = init_res.json()["state"]

    mock_short_token = {"access_token": "short_ig_user_token"}
    mock_long_token = {"access_token": "long_ig_user_token"}
    mock_accounts_with_ig = {
        "data": [
            {
                "id": "page_222",
                "name": "OmniPulse Official Page",
                "access_token": "page_token_222",
                "instagram_business_account": {
                    "id": "178414000998877",
                    "username": "omnipulse_app",
                    "name": "OmniPulse App",
                },
            }
        ]
    }

    async def mock_async_client_get(url, *args, **kwargs):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        if "oauth/access_token" in url:
            mock_resp.json.return_value = mock_long_token
        elif "/me/accounts" in url:
            mock_resp.json.return_value = mock_accounts_with_ig
        elif "/178414000998877" in url:
            mock_resp.json.return_value = {"id": "178414000998877", "username": "omnipulse_app", "name": "OmniPulse App"}
        return mock_resp

    with patch("httpx.AsyncClient.get", side_effect=mock_async_client_get), \
         patch.object(settings, "META_APP_SECRET", "mock_meta_app_secret"):

        callback_res = client.get(f"/api/v1/connections/meta/callback?code=mock_code&state={state}")
        assert callback_res.status_code == 200
        assert "OMNIPULSE_OAUTH_SUCCESS" in callback_res.text
        assert "omnipulse_app" in callback_res.text

        conn = credential_service.get_safe_connection_item("instagram")
        assert conn["status"] == "connected"
        assert conn["accountId"] == "178414000998877"
        assert conn["handle"] == "@omnipulse_app"


# =============================================================================
# 4. Bluesky & LinkedIn Connection and Disconnection Tests
# =============================================================================

def test_bluesky_connect_and_disconnect():
    """Verify Bluesky connection via AT Protocol mock, safe persistence, and disconnection."""
    mock_session = {
        "did": "did:plc:abcdef1234567890",
        "handle": "omnipulse.bsky.social",
        "accessJwt": "mock_atproto_jwt_token_secret",
        "refreshJwt": "mock_atproto_refresh_jwt",
    }

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_session
        mock_post.return_value = mock_resp

        # 1. Connect
        connect_res = client.post(
            "/api/v1/connections/bluesky/connect",
            json={"handle": "omnipulse.bsky.social", "app_password": "test-app-password-xxxx"},
        )
        assert connect_res.status_code == 200
        assert connect_res.json()["is_valid"] is True
        assert connect_res.json()["status"] == "connected"

        # 2. Check connection list - zero secrets exposed!
        list_res = client.get("/api/v1/connections")
        assert list_res.status_code == 200
        connections = {c["id"]: c for c in list_res.json()["connections"]}
        assert connections["bluesky"]["status"] == "connected"
        assert connections["bluesky"]["handle"].lstrip("@") == "omnipulse.bsky.social"
        assert "accessJwt" not in str(connections["bluesky"])
        assert "test-app-password-xxxx" not in str(connections["bluesky"])

        # 3. Disconnect
        del_res = client.delete("/api/v1/connections/bluesky")
        assert del_res.status_code == 200
        assert del_res.json()["status"] == "disconnected"

        # 4. Verify disconnected
        recheck_res = client.get("/api/v1/connections")
        connections_after = {c["id"]: c for c in recheck_res.json()["connections"]}
        assert connections_after["bluesky"]["status"] == "disconnected"


def test_linkedin_connect_and_disconnect():
    """Verify LinkedIn connection via /v2/userinfo mock, safe persistence, and disconnection."""
    mock_userinfo = {
        "sub": "user_linkedin_sub_12345",
        "name": "OmniPulse Founder",
        "email": "founder@omnipulse.ai",
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_userinfo
        mock_get.return_value = mock_resp

        # 1. Connect
        connect_res = client.post(
            "/api/v1/connections/linkedin/connect",
            json={"access_token": "AQX_mock_linkedin_bearer_token_123"},
        )
        assert connect_res.status_code == 200
        assert connect_res.json()["is_valid"] is True
        assert connect_res.json()["account_name"] == "OmniPulse Founder"

        # 2. Check connection list - zero secrets exposed!
        list_res = client.get("/api/v1/connections")
        connections = {c["id"]: c for c in list_res.json()["connections"]}
        assert connections["linkedin"]["status"] == "connected"
        assert connections["linkedin"]["accountName"] == "OmniPulse Founder"
        assert connections["linkedin"]["account_name"] == "OmniPulse Founder"
        assert "AQX_mock" not in str(connections["linkedin"])

        # 3. Disconnect
        del_res = client.delete("/api/v1/connections/linkedin")
        assert del_res.status_code == 200
        assert del_res.json()["status"] == "disconnected"


# =============================================================================
# 5. Security & Zero Token Exposure Verification
# =============================================================================

@pytest.mark.anyio
async def test_safe_connections_endpoint_never_exposes_tokens_or_secrets():
    """Strict audit verifying that /api/v1/connections NEVER returns raw or encrypted tokens."""
    await credential_service.save_connection(
        platform="facebook",
        handle="fb.com/testpage",
        access_token="SUPER_SECRET_PAGE_ACCESS_TOKEN_DO_NOT_LEAK",
        account_id="page_12345",
        account_name="Test FB Page",
    )
    await credential_service.save_connection(
        platform="bluesky",
        handle="user.bsky.social",
        access_token="SUPER_SECRET_BLUESKY_PASSWORD_DO_NOT_LEAK",
        account_id="did:plc:mockdid",
    )

    resp = client.get("/api/v1/connections")
    assert resp.status_code == 200
    data = resp.json()
    response_str = str(data)

    # 1. Ensure secrets are absent
    assert "SUPER_SECRET" not in response_str
    assert "DO_NOT_LEAK" not in response_str
    assert "encrypted_access_token" not in response_str
    assert "encrypted_refresh_token" not in response_str
    assert "access_token" not in response_str
    assert "app_password" not in response_str

    # Clean up
    await credential_service.delete_connection("facebook")
    await credential_service.delete_connection("instagram")
    await credential_service.delete_connection("bluesky")
    await credential_service.delete_connection("linkedin")


# =============================================================================
# 6. Phase 2A Platform Registry & Coming Soon Integration Tests
# =============================================================================

def test_six_platform_registry_presence_and_coming_soon_status():
    """Verify all 6 platforms are registered and Pinterest & YouTube are marked Coming Soon."""
    resp = client.get("/api/v1/connections")
    assert resp.status_code == 200
    data = resp.json()
    conns = data.get("connections", [])
    assert len(conns) == 6

    conn_map = {c["id"]: c for c in conns}
    assert "pinterest" in conn_map
    assert "youtube" in conn_map

    pinterest = conn_map["pinterest"]
    assert pinterest["status"] == "coming_soon"
    assert pinterest["handle"] == "Coming Soon"
    assert pinterest.get("is_coming_soon") is True
    assert pinterest.get("is_configured") is False

    youtube = conn_map["youtube"]
    assert youtube["status"] == "coming_soon"
    assert youtube["handle"] == "Coming Soon"
    assert youtube.get("is_coming_soon") is True
    assert youtube.get("is_configured") is False


def test_coming_soon_platforms_cannot_falsely_verify():
    """Verify that unbuilt platforms cannot falsely report valid or connected status."""
    for p in ["pinterest", "youtube"]:
        verify_res = client.post(f"/api/v1/connections/{p}/verify")
        assert verify_res.status_code == 200
        data = verify_res.json()
        assert data["is_valid"] is False
        assert data["status"] == "coming_soon"
        assert "Coming soon" in data["message"]


def test_coming_soon_platforms_cannot_initiate_meta_oauth():
    """Verify Meta OAuth initiation explicitly rejects Pinterest and YouTube."""
    for p in ["pinterest", "youtube"]:
        auth_res = client.post("/api/v1/connections/meta/authorize", json={"platform": p})
        assert auth_res.status_code == 400
        assert "either 'facebook' or 'instagram'" in auth_res.json()["detail"]
