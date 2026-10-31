import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.platforms.pinterest import PinterestAdapter
from app.platforms.youtube import YouTubeAdapter
from app.services.credential_service import credential_service

client = TestClient(app)


@pytest.mark.anyio
async def test_pinterest_length_validation():
    adapter = PinterestAdapter()
    long_desc = "P" * 505
    res = await adapter.publish_post(content=long_desc, dry_run=False)
    assert res.status == "failed"
    assert "500 characters" in res.error_message


@pytest.mark.anyio
async def test_pinterest_dry_run_mode():
    adapter = PinterestAdapter()
    res = await adapter.publish_post(content="Inspiring Pinterest visual idea", dry_run=True)
    assert res.status == "published"
    assert res.is_mock is True
    assert "mock_pin_" in res.remote_post_id
    assert "pinterest.com/pin/" in res.remote_post_url


@pytest.mark.anyio
async def test_pinterest_requires_media():
    adapter = PinterestAdapter()
    with patch("app.services.credential_service.credential_service.get_credentials", new_callable=AsyncMock) as mock_creds:
        mock_creds.return_value = {"access_token": "pin_token_123", "account_id": "pin_user"}
        res = await adapter.publish_post(content="Test pin", media_url=None, dry_run=False)
        assert res.status == "failed"
        assert "require an image or video URL" in res.error_message


@pytest.mark.anyio
async def test_youtube_length_validation():
    adapter = YouTubeAdapter()
    long_desc = "Y" * 5005
    res = await adapter.publish_post(content=long_desc, dry_run=False)
    assert res.status == "failed"
    assert "5,000 characters" in res.error_message


@pytest.mark.anyio
async def test_youtube_dry_run_mode():
    adapter = YouTubeAdapter()
    res = await adapter.publish_post(content="OmniPulse automated video upload walkthrough", dry_run=True)
    assert res.status == "published"
    assert res.is_mock is True
    assert "mock_yt_" in res.remote_post_id
    assert "youtube.com/watch?v=" in res.remote_post_url


@pytest.mark.anyio
async def test_youtube_requires_video():
    adapter = YouTubeAdapter()
    with patch("app.services.credential_service.credential_service.get_credentials", new_callable=AsyncMock) as mock_creds:
        mock_creds.return_value = {"access_token": "yt_token_123", "account_id": "UC123456789"}
        res = await adapter.publish_post(content="Test video description", media_url=None, dry_run=False)
        assert res.status == "failed"
        assert "requires a video file" in res.error_message


def test_media_upload_json():
    # Base64 for 1x1 transparent PNG
    b64_png = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    resp = client.post("/api/v1/media/upload-json", json={"data": b64_png, "filename": "test.png", "content_type": "image/png"})
    assert resp.status_code == 200
    data = resp.json()
    assert "url" in data
    assert data["filename"] == "test.png"
    assert data["content_type"] == "image/png"
    assert data["storage"] in ("supabase", "inline")

