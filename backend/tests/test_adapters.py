import pytest
from unittest.mock import patch, AsyncMock
import httpx

from app.platforms.bluesky import BlueskyAdapter
from app.platforms.linkedin import LinkedInAdapter
from app.platforms.facebook import FacebookAdapter
from app.platforms.instagram import InstagramAdapter
from app.core.config import settings


@pytest.mark.anyio
async def test_bluesky_length_validation():
    adapter = BlueskyAdapter()
    long_text = "A" * 305
    res = await adapter.publish_post(content=long_text, dry_run=False)
    assert res.status == "failed"
    assert "300 characters" in res.error_message


@pytest.mark.anyio
async def test_bluesky_dry_run_mode():
    adapter = BlueskyAdapter()
    res = await adapter.publish_post(content="Valid punchy Bluesky update!", dry_run=True)
    assert res.status == "published"
    assert res.is_mock is True
    assert "at://" in res.remote_post_id
    assert "https://bsky.app" in res.remote_post_url


@pytest.mark.anyio
async def test_bluesky_missing_credentials():
    adapter = BlueskyAdapter()
    with patch.object(settings, "BLUESKY_HANDLE", ""), patch.object(settings, "BLUESKY_APP_PASSWORD", ""):
        res = await adapter.publish_post(content="Test content", dry_run=False)
        assert res.status == "failed"
        assert "Missing BLUESKY_HANDLE" in res.error_message


@pytest.mark.anyio
async def test_linkedin_length_validation():
    adapter = LinkedInAdapter()
    long_text = "L" * 3005
    res = await adapter.publish_post(content=long_text, dry_run=False)
    assert res.status == "failed"
    assert "3,000 characters" in res.error_message


@pytest.mark.anyio
async def test_linkedin_dry_run_mode():
    adapter = LinkedInAdapter()
    res = await adapter.publish_post(content="Insightful professional update.", dry_run=True)
    assert res.status == "published"
    assert res.is_mock is True
    assert "urn:li:share:" in res.remote_post_id
    assert "https://www.linkedin.com" in res.remote_post_url


@pytest.mark.anyio
async def test_linkedin_missing_token():
    adapter = LinkedInAdapter()
    with patch.object(settings, "LINKEDIN_ACCESS_TOKEN", ""):
        res = await adapter.publish_post(content="Valid content", dry_run=False)
        assert res.status == "failed"
        assert "Missing LINKEDIN_ACCESS_TOKEN" in res.error_message


@pytest.mark.anyio
async def test_facebook_dry_run_mode():
    adapter = FacebookAdapter()
    res = await adapter.publish_post(content="Community engagement post!", dry_run=True)
    assert res.status == "published"
    assert res.is_mock is True
    assert "mock_fb_" in res.remote_post_id
    assert "facebook.com" in res.remote_post_url


@pytest.mark.anyio
async def test_facebook_length_validation():
    adapter = FacebookAdapter()
    excessive_text = "F" * 63210
    res = await adapter.publish_post(content=excessive_text, dry_run=False)
    assert res.status == "failed"
    assert "63,206 characters" in res.error_message


@pytest.mark.anyio
async def test_instagram_dry_run_mode():
    adapter = InstagramAdapter()
    res = await adapter.publish_post(content="Aesthetic visual caption.", dry_run=True)
    assert res.status == "published"
    assert res.is_mock is True
    assert "mock_ig_" in res.remote_post_id
    assert "instagram.com/p/" in res.remote_post_url


@pytest.mark.anyio
async def test_instagram_requires_media_in_live_mode():
    adapter = InstagramAdapter()
    with patch.object(settings, "INSTAGRAM_BUSINESS_ACCOUNT_ID", "178414000"), patch.object(settings, "META_USER_TOKEN", "token123"):
        res = await adapter.publish_post(content="Text only without media", media_url=None, dry_run=False)
        assert res.status == "failed"
        assert "requires an image or video URL" in res.error_message
