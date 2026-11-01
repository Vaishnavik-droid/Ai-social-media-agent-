import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "omnipulse-backend"
    assert "llm_provider" in data
    assert "groq_configured" in data


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "app" in data
    assert "docs" in data


def test_posts_lifecycle():
    # 1. Create a post
    payload = {
        "title": "Automated Test Post",
        "content": "This is a test post content for automated test suite.",
        "platforms": ["bluesky", "linkedin"],
        "tone": "Casual",
        "content_type": "Announcement",
        "language": "English",
        "status": "draft"
    }
    create_res = client.post("/api/v1/posts", json=payload)
    assert create_res.status_code == 201
    created_data = create_res.json()
    assert created_data["title"] == payload["title"]
    assert created_data["tone"] == "Casual"
    assert "id" in created_data
    post_id = created_data["id"]

    # 2. Retrieve post by ID
    get_res = client.get(f"/api/v1/posts/{post_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == post_id
    assert get_res.json()["title"] == payload["title"]

    # 3. Update the post (PATCH)
    patch_payload = {
        "title": "Updated Test Post Title",
        "tone": "Professional"
    }
    patch_res = client.patch(f"/api/v1/posts/{post_id}", json=patch_payload)
    assert patch_res.status_code == 200
    assert patch_res.json()["title"] == "Updated Test Post Title"
    assert patch_res.json()["tone"] == "Professional"

    # 4. List posts and verify inclusion
    list_res = client.get("/api/v1/posts")
    assert list_res.status_code == 200
    posts = list_res.json()
    assert any(p["id"] == post_id for p in posts)

    # 5. Status filter
    filter_res = client.get("/api/v1/posts?status_filter=draft")
    assert filter_res.status_code == 200
    for p in filter_res.json():
        assert p["status"] == "draft"

    # 6. Delete post
    del_res = client.delete(f"/api/v1/posts/{post_id}")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # 7. Confirm 404 after deletion
    not_found_res = client.get(f"/api/v1/posts/{post_id}")
    assert not_found_res.status_code == 404


def test_generation_preview():
    req = {
        "topic": "Future of artificial intelligence in social management",
        "tone": "Inspirational",
        "content_type": "Thought Leadership",
        "language": "English",
        "include_hashtags": True,
        "platforms": ["linkedin"]
    }
    res = client.post("/api/v1/generation/preview", json=req)
    assert res.status_code == 200
    data = res.json()
    assert "generated_text" in data
    assert len(data["generated_text"]) > 20
    assert data["tone"] == "Inspirational"
    assert "Groq" in data["provider"] or "Synthesizer" in data["provider"]


def test_generation_preview_five_platforms_no_youtube():
    """
    Exact production failure scenario:
    User selects all platforms EXCEPT YouTube (Bluesky, LinkedIn, Instagram, Facebook, Pinterest).
    Verifies that the API response contains valid variants for all 5 platforms,
    both 'text' and 'content' fields are populated, and YouTube is not included.
    """
    req = {
        "topic": "AI is changing social media marketing",
        "tone": "Professional",
        "content_type": "General Post",
        "language": "English",
        "include_hashtags": True,
        "platforms": ["bluesky", "linkedin", "instagram", "facebook", "pinterest"]
    }
    res = client.post("/api/v1/generation/preview", json=req)
    assert res.status_code == 200
    data = res.json()
    assert "platform_content" in data
    plat_content = data["platform_content"]
    assert len(plat_content) == 5
    for p in ["bluesky", "linkedin", "instagram", "facebook", "pinterest"]:
        assert p in plat_content
        variant = plat_content[p]
        assert "text" in variant and variant["text"]
        assert "content" in variant and variant["content"]
        assert variant["text"] == variant["content"]
        # Split safety on frontend
        lines = variant["content"].split("\n")
        assert len(lines) >= 1

    assert "youtube" not in plat_content


def test_connections_endpoints():
    # 1. List connections
    list_res = client.get("/api/v1/connections")
    assert list_res.status_code == 200
    data = list_res.json()
    assert "connections" in data
    assert len(data["connections"]) >= 2
    platform_ids = [c["id"] for c in data["connections"]]
    assert "bluesky" in platform_ids
    assert "linkedin" in platform_ids

    # 2. Verify platform connection
    verify_res = client.post("/api/v1/connections/verify", json={"platform": "bluesky"})
    assert verify_res.status_code == 200
    verify_data = verify_res.json()
    assert verify_data["platform"] == "bluesky"
    assert "is_valid" in verify_data
    assert "status" in verify_data


def test_publishing_pipeline():
    # Create a draft post to publish
    payload = {
        "title": "Publish Verification Test",
        "content": "Real publish pipeline verification content.",
        "platforms": ["bluesky"],
        "status": "draft"
    }
    create_res = client.post("/api/v1/posts", json=payload)
    post_id = create_res.json()["id"]

    # Dispatch publish
    pub_res = client.post(
        "/api/v1/publishing/publish",
        json={"post_id": post_id, "platforms": ["bluesky"], "publish_now": True}
    )
    assert pub_res.status_code == 200
    pub_data = pub_res.json()
    assert pub_data["post_id"] == post_id
    assert "results" in pub_data
    assert len(pub_data["results"]) == 1
    assert pub_data["results"][0]["platform"] == "bluesky"

    # Publishing non-existent post should return 404
    missing_res = client.post(
        "/api/v1/publishing/publish",
        json={"post_id": "non-existent-id-99999", "platforms": ["bluesky"]}
    )
    assert missing_res.status_code == 404
