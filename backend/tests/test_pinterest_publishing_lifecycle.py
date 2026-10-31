import os
import pytest
import uuid
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
import httpx

from app.main import app
from app.platforms.pinterest import PinterestAdapter
from app.api.v1.routes.posts import to_uuid, _MEMORY_POSTS
from app.api.v1.routes.publishing import publish_post_endpoint
from app.schemas.publishing import PublishRequest

client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. Post Creation & Platform Record Upsert (Preventing Duplicates)
# ---------------------------------------------------------------------------

def test_create_post_and_platform_record_safeguard():
    """
    Test 1: Creating a post ensures post_platforms is upserted with deterministic UUID
    and on_conflict='post_id,platform' to prevent duplicate violations.
    """
    post_payload = {
        "id": f"test-post-{uuid.uuid4().hex[:8]}",
        "title": "Pinterest Strategy 2026",
        "content": "A high-conversion visual marketing workflow for Pinterest.",
        "platforms": ["pinterest"],
        "status": "draft",
        "media_url": "https://example.com/banner.jpg",
    }

    mock_sb_client = MagicMock()
    mock_table = MagicMock()
    mock_sb_client.table.return_value = mock_table
    mock_table.upsert.return_value.execute.return_value = MagicMock(data=[{"id": "dummy"}])

    with patch("app.api.v1.routes.posts._get_supabase_client", return_value=mock_sb_client):
        resp = client.post("/api/v1/posts", json=post_payload)
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert data["title"] == post_payload["title"]

        # Verify post_platforms upsert called with on_conflict="post_id,platform"
        calls = mock_table.upsert.call_args_list
        post_platform_calls = [
            c for c in calls
            if c.kwargs.get("on_conflict") == "post_id,platform"
        ]
        assert len(post_platform_calls) >= 1
        args, kwargs = post_platform_calls[0]
        record = args[0]
        assert record["platform"] == "pinterest"
        assert record["post_id"] == to_uuid(post_payload["id"])
        # Deterministic ID check
        assert record["id"] == to_uuid(f"{record['post_id']}-pinterest")


def test_repeated_post_creation_does_not_duplicate():
    """
    Test 2 & 3: Repeated creation with identical (post_id, platform) uses on_conflict,
    updating the existing platform record rather than raising unique constraint violations.
    """
    shared_id = f"test-repeat-{uuid.uuid4().hex[:8]}"
    post_payload = {
        "id": shared_id,
        "title": "Repeated Post Test",
        "content": "Content to test idempotent insertion",
        "platforms": ["pinterest"],
        "status": "draft",
    }

    mock_sb_client = MagicMock()
    mock_table = MagicMock()
    mock_sb_client.table.return_value = mock_table
    mock_table.upsert.return_value.execute.return_value = MagicMock(data=[{"id": "dummy"}])

    with patch("app.api.v1.routes.posts._get_supabase_client", return_value=mock_sb_client):
        resp1 = client.post("/api/v1/posts", json=post_payload)
        assert resp1.status_code in (200, 201)

        # Call again with same ID (e.g. re-save or duplicate dispatch)
        resp2 = client.post("/api/v1/posts", json=post_payload)
        assert resp2.status_code in (200, 201)

        # Both calls specify on_conflict='post_id,platform' and same deterministic row ID
        expected_row_id = to_uuid(f"{to_uuid(shared_id)}-pinterest")
        for c in mock_table.upsert.call_args_list:
            if c.kwargs.get("on_conflict") == "post_id,platform":
                assert c.args[0]["id"] == expected_row_id


# ---------------------------------------------------------------------------
# 2. Pinterest Sandbox Integration Tests
# ---------------------------------------------------------------------------

def test_pinterest_adapter_uses_sandbox_base_url():
    """
    Verify the adapter's API base URL is configured to the Pinterest Sandbox environment.
    """
    adapter = PinterestAdapter()
    assert adapter.API_BASE_URL == "https://api-sandbox.pinterest.com/v5"


def test_no_production_pinterest_api_urls_in_pinterest_module():
    """
    Verify no hardcoded production Pinterest API URLs (api.pinterest.com) remain
    in the Pinterest platform adapter module.
    """
    module_path = os.path.join(os.path.dirname(__file__), "..", "app", "platforms", "pinterest.py")
    with open(module_path, "r", encoding="utf-8") as f:
        code = f.read()
    assert "https://api.pinterest.com" not in code, "Found production Pinterest API URL in pinterest.py"


@pytest.mark.anyio
async def test_pinterest_sandbox_token_prioritized_over_production_oauth():
    """
    Verify that when PINTEREST_SANDBOX_TOKEN is present in environment or settings,
    _resolve_credentials() returns the sandbox token directly and does NOT use
    production OAuth credentials.
    """
    adapter = PinterestAdapter()
    fake_sandbox_token = "pina_sandbox_secret_token_12345"

    with patch.dict(os.environ, {"PINTEREST_SANDBOX_TOKEN": fake_sandbox_token}), \
         patch("app.services.credential_service.credential_service.get_credentials", new_callable=AsyncMock) as mock_creds:

        token, account_id = await adapter._resolve_credentials()
        assert token == fake_sandbox_token
        assert account_id == "pinterest_sandbox_user"
        # Production credentials should not even be queried
        mock_creds.assert_not_called()


@pytest.mark.anyio
async def test_pinterest_sandbox_pin_creation_dispatches_to_sandbox_api():
    """
    Verify Pin creation dispatches to https://api-sandbox.pinterest.com/v5/pins
    using the Sandbox token in the Authorization header.
    """
    adapter = PinterestAdapter()
    fake_pin_id = "sandbox_pin_987654321"
    fake_sandbox_token = "pina_sandbox_valid_test_token"

    fake_response = httpx.Response(
        201,
        json={
            "id": fake_pin_id,
            "created_at": "2026-11-01T00:00:00Z",
            "board_id": "sandbox_board_1",
            "title": "Sandbox Test Pin",
            "description": "Created in Pinterest Sandbox",
        },
        request=httpx.Request("POST", "https://api-sandbox.pinterest.com/v5/pins"),
    )

    with patch.dict(os.environ, {"PINTEREST_SANDBOX_TOKEN": fake_sandbox_token}), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=fake_response) as mock_post:

        res = await adapter.publish_post(
            content="Created in Pinterest Sandbox",
            media_url="https://images.unsplash.com/photo-1518770660439-4636190af475",
            dry_run=False,
            title="Sandbox Test Pin",
            board_id="sandbox_board_1",
        )

        assert res.status == "published"
        assert res.remote_post_id == fake_pin_id
        assert res.remote_post_url == f"https://www.pinterest.com/pin/{fake_pin_id}/"

        # Verify Sandbox URL and Sandbox Authorization header were used
        mock_post.assert_called_once()
        called_url = mock_post.call_args.args[0]
        called_headers = mock_post.call_args.kwargs["headers"]
        assert called_url == "https://api-sandbox.pinterest.com/v5/pins"
        assert called_headers["Authorization"] == f"Bearer {fake_sandbox_token}"


@pytest.mark.anyio
async def test_pinterest_sandbox_board_fetching_dispatches_to_sandbox_api():
    """
    Verify get_boards() calls https://api-sandbox.pinterest.com/v5/boards
    using the Sandbox token so the dropdown matches Sandbox boards.
    """
    adapter = PinterestAdapter()
    fake_sandbox_token = "pina_sandbox_valid_test_token"

    fake_response = httpx.Response(
        200,
        json={
            "items": [
                {"id": "sandbox_b1", "name": "Testing Sandbox Board"},
                {"id": "sandbox_b2", "name": "Product Launch Sandbox"}
            ]
        },
        request=httpx.Request("GET", "https://api-sandbox.pinterest.com/v5/boards"),
    )

    with patch.dict(os.environ, {"PINTEREST_SANDBOX_TOKEN": fake_sandbox_token}), \
         patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=fake_response) as mock_get:

        boards = await adapter.get_boards()
        assert len(boards) == 2
        assert boards[0]["id"] == "sandbox_b1"
        assert boards[0]["name"] == "Testing Sandbox Board"

        mock_get.assert_called_once()
        called_url = mock_get.call_args.args[0]
        called_headers = mock_get.call_args.kwargs["headers"]
        assert called_url == "https://api-sandbox.pinterest.com/v5/boards"
        assert called_headers["Authorization"] == f"Bearer {fake_sandbox_token}"


@pytest.mark.anyio
async def test_pinterest_sandbox_does_not_attempt_oauth_refresh():
    """
    Verify _refresh_access_token() immediately returns None when PINTEREST_SANDBOX_TOKEN
    is configured, preventing invalid OAuth refresh attempts with static Sandbox tokens.
    """
    adapter = PinterestAdapter()
    with patch.dict(os.environ, {"PINTEREST_SANDBOX_TOKEN": "some_sandbox_token"}):
        res = await adapter._refresh_access_token()
        assert res is None


@pytest.mark.anyio
async def test_pinterest_title_strictly_truncated_to_100_chars():
    """
    Pinterest API v5 strictly rejects titles longer than 100 characters with HTTP 400.
    Verify title is safely trimmed to <= 100 characters.
    """
    adapter = PinterestAdapter()
    long_title = "A" * 150
    fake_response = httpx.Response(
        201,
        json={"id": "998877"},
        request=httpx.Request("POST", "https://api-sandbox.pinterest.com/v5/pins"),
    )

    with patch.dict(os.environ, {"PINTEREST_SANDBOX_TOKEN": "sandbox_token"}), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=fake_response) as mock_post:

        await adapter.publish_post(
            content="Short content",
            media_url="https://example.com/pic.jpg",
            title=long_title,
            board_id="board_123",
        )

        sent_payload = mock_post.call_args.kwargs["json"]
        assert len(sent_payload["title"]) <= 100
        assert sent_payload["title"] == "A" * 100


@pytest.mark.anyio
async def test_pinterest_handles_missing_board_gracefully():
    """
    If board_id is omitted and user has no boards on Pinterest,
    returns actionable error rather than throwing an unhandled exception.
    """
    adapter = PinterestAdapter()

    with patch.dict(os.environ, {"PINTEREST_SANDBOX_TOKEN": "sandbox_token"}), \
         patch.object(adapter, "get_boards", new_callable=AsyncMock, return_value=[]):

        res = await adapter.publish_post(
            content="Pin with no board",
            media_url="https://example.com/pic.jpg",
            board_id="",
        )

        assert res.status == "failed"
        assert "No Pinterest boards found" in res.error_message


@pytest.mark.anyio
async def test_pinterest_api_rejection_returns_descriptive_error():
    """
    When Pinterest API rejects the request (e.g. HTTP 400 with message & details),
    the adapter captures the rejection message and returns status='failed'.
    """
    adapter = PinterestAdapter()
    error_response = httpx.Response(
        400,
        json={
            "code": 2,
            "message": "Image cannot be downloaded from the provided url.",
            "details": [{"message": "Invalid host or connection timed out fetching image"}]
        },
        request=httpx.Request("POST", "https://api-sandbox.pinterest.com/v5/pins"),
    )

    with patch.dict(os.environ, {"PINTEREST_SANDBOX_TOKEN": "sandbox_token"}), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=error_response):

        res = await adapter.publish_post(
            content="Pin with broken image",
            media_url="https://invalid-host-unreachable.xyz/bad.jpg",
            board_id="board_123",
        )

        assert res.status == "failed"
        assert "Pinterest:" in res.error_message
        assert "Image cannot be downloaded" in res.error_message


# ---------------------------------------------------------------------------
# 3. Publishing Endpoint: Persistence & Supabase Resilience
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_publishing_endpoint_persists_with_schema_fallback():
    """
    Publishing endpoint persists remote_post_id and remote_post_url when columns exist,
    and seamlessly falls back to published_url if remote_post_id column is missing in schema cache.
    """
    test_post_id = f"publish-test-{uuid.uuid4().hex[:8]}"
    _MEMORY_POSTS[test_post_id] = {
        "id": test_post_id,
        "content": "Test pin content",
        "media_url": "https://example.com/test.jpg",
        "status": "pending",
    }

    mock_sb_client = MagicMock()
    mock_table = MagicMock()
    mock_sb_client.table.return_value = mock_table

    mock_table.upsert.side_effect = [
        Exception("Could not find the 'remote_post_id' column of 'post_platforms' in the schema cache"),
        MagicMock(execute=MagicMock(return_value=MagicMock(data=[{"id": "ok"}])))
    ]

    with patch("app.api.v1.routes.publishing._get_supabase_client", return_value=mock_sb_client):
        req = PublishRequest(
            post_id=test_post_id,
            platforms=["pinterest"],
            dry_run=True,
        )
        resp = await publish_post_endpoint(req)

        assert resp.success is True
        assert len(resp.results) == 1
        assert resp.results[0].status == "published"
        assert resp.results[0].remote_post_id is not None

        assert mock_table.upsert.call_count == 2
        fallback_call = mock_table.upsert.call_args_list[1]
        fallback_record = fallback_call.args[0]
        assert "published_url" in fallback_record
        assert fallback_record["published_url"] is not None
        assert fallback_call.kwargs.get("on_conflict") == "post_id,platform"


@pytest.mark.anyio
async def test_publishing_endpoint_preserves_published_status_on_db_write_failure():
    """
    If the remote publish succeeds on Pinterest, but Supabase persistence raises an error,
    the PlatformResult must STILL report status='published' and provide remote_post_id,
    never falsifying a real publish into a failure.
    """
    test_post_id = f"publish-db-err-{uuid.uuid4().hex[:8]}"
    _MEMORY_POSTS[test_post_id] = {
        "id": test_post_id,
        "content": "Test pin content",
        "media_url": "https://example.com/test.jpg",
        "status": "pending",
    }

    mock_sb_client = MagicMock()
    mock_table = MagicMock()
    mock_sb_client.table.return_value = mock_table
    mock_table.update.side_effect = Exception("Supabase connection reset by peer")
    mock_table.upsert.side_effect = Exception("Supabase connection reset by peer")

    with patch("app.api.v1.routes.publishing._get_supabase_client", return_value=mock_sb_client):
        req = PublishRequest(
            post_id=test_post_id,
            platforms=["pinterest"],
            dry_run=True,
        )
        resp = await publish_post_endpoint(req)

        assert resp.success is True
        assert resp.results[0].status == "published"
        assert "mock_pin_" in resp.results[0].remote_post_id
