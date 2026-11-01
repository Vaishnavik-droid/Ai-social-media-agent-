import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.main import app
from app.platforms.youtube import YouTubeAdapter
from app.schemas.publishing import PlatformResult

client = TestClient(app)


def test_missing_youtube_post_type_rejected():
    """When YouTube is targeted without youtube_post_type, it must return a 400 validation error."""
    # Create draft
    post_res = client.post("/api/v1/posts", json={
        "title": "YouTube Test Post",
        "content": "Test video description",
        "platforms": ["youtube"],
        "status": "draft"
    })
    assert post_res.status_code == 201
    post_id = post_res.json()["id"]

    # Publish without youtube_post_type
    pub_res = client.post("/api/v1/publishing/publish", json={
        "post_id": post_id,
        "platforms": ["youtube"],
        "media_url": "https://example.com/video.mp4"
    })
    assert pub_res.status_code == 400
    detail = pub_res.json().get("detail", "")
    assert "youtube_post_type is required" in detail


def test_unsupported_community_post_rejected():
    """When an unsupported youtube_post_type like 'community_post' is passed, it must be rejected with 400."""
    post_res = client.post("/api/v1/posts", json={
        "title": "Community Post Reject Test",
        "content": "Test text only",
        "platforms": ["youtube"],
        "status": "draft"
    })
    post_id = post_res.json()["id"]

    pub_res = client.post("/api/v1/publishing/publish", json={
        "post_id": post_id,
        "platforms": ["youtube"],
        "youtube_post_type": "community_post"
    })
    assert pub_res.status_code == 400
    detail = pub_res.json().get("detail", "")
    assert "Unsupported youtube_post_type" in detail


def test_short_post_type_received_by_backend():
    """When 'short' is selected, backend passes it to YouTube adapter in dry_run mode."""
    post_res = client.post("/api/v1/posts", json={
        "title": "YouTube Shorts Test",
        "content": "Testing shorts publish #Shorts",
        "platforms": ["youtube"],
        "status": "draft"
    })
    post_id = post_res.json()["id"]

    pub_res = client.post("/api/v1/publishing/publish", json={
        "post_id": post_id,
        "platforms": ["youtube"],
        "youtube_post_type": "short",
        "media_url": "https://example.com/vertical_clip.mp4",
        "dry_run": True
    })
    assert pub_res.status_code == 200
    data = pub_res.json()
    assert data["success"] is True
    assert len(data["results"]) == 1
    assert data["results"][0]["platform"] == "youtube"
    assert data["results"][0]["status"] == "published"


def test_long_form_post_type_received_by_backend():
    """When 'long_form' is selected, backend passes it to YouTube adapter in dry_run mode."""
    post_res = client.post("/api/v1/posts", json={
        "title": "YouTube Long-form Test",
        "content": "Testing long form video publish",
        "platforms": ["youtube"],
        "status": "draft"
    })
    post_id = post_res.json()["id"]

    pub_res = client.post("/api/v1/publishing/publish", json={
        "post_id": post_id,
        "platforms": ["youtube"],
        "youtube_post_type": "long_form",
        "media_url": "https://example.com/episode.mp4",
        "dry_run": True
    })
    assert pub_res.status_code == 200
    data = pub_res.json()
    assert data["success"] is True
    assert len(data["results"]) == 1
    assert data["results"][0]["platform"] == "youtube"
    assert data["results"][0]["status"] == "published"


def test_multi_platform_publishing_preserves_independence():
    """When YouTube and Bluesky are selected together, youtube_post_type applies only to YouTube."""
    post_res = client.post("/api/v1/posts", json={
        "title": "Multi-platform Test",
        "content": "Cross-platform post content",
        "platforms": ["bluesky", "youtube"],
        "status": "draft"
    })
    post_id = post_res.json()["id"]

    pub_res = client.post("/api/v1/publishing/publish", json={
        "post_id": post_id,
        "platforms": ["bluesky", "youtube"],
        "youtube_post_type": "short",
        "media_url": "https://example.com/short.mp4",
        "dry_run": True
    })
    assert pub_res.status_code == 200
    data = pub_res.json()
    assert data["success"] is True
    assert len(data["results"]) == 2
    platforms_responded = [r["platform"] for r in data["results"]]
    assert "bluesky" in platforms_responded
    assert "youtube" in platforms_responded
    for r in data["results"]:
        assert r["status"] == "published"


@pytest.mark.anyio
async def test_youtube_adapter_requires_video():
    """YouTubeAdapter.publish_post requires video media and rejects static images or text-only."""
    adapter = YouTubeAdapter()

    # 1. No media
    res_no_media = await adapter.publish_post(
        content="No video upload",
        media_url=None,
        dry_run=False,
        youtube_post_type="short"
    )
    assert res_no_media.status == "failed"
    assert "requires a video file" in res_no_media.error_message

    # 2. Image media
    res_image = await adapter.publish_post(
        content="Image upload attempt",
        media_url="https://example.com/photo.jpg",
        dry_run=False,
        youtube_post_type="short"
    )
    assert res_image.status == "failed"
    assert "Static images are not supported" in res_image.error_message


@pytest.mark.anyio
async def test_youtube_adapter_rejects_unsupported_type():
    """YouTubeAdapter.publish_post rejects invalid post types."""
    adapter = YouTubeAdapter()
    res = await adapter.publish_post(
        content="Bad type",
        media_url="https://example.com/video.mp4",
        dry_run=False,
        youtube_post_type="community_post"
    )
    assert res.status == "failed"
    assert "Unsupported YouTube post type" in res.error_message
