import datetime
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.scheduling_service import scheduling_service, _MEMORY_SCHEDULES
from app.api.v1.routes.posts import _MEMORY_POSTS

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_environment():
    _MEMORY_SCHEDULES.clear()
    _MEMORY_POSTS.clear()
    yield
    _MEMORY_SCHEDULES.clear()
    _MEMORY_POSTS.clear()


@pytest.mark.anyio
async def test_complete_end_to_end_simulated_workflow():
    """
    Simulates the complete operator journey from prompt generation to scheduling
    and multi-platform mock execution with zero external network side-effects.
    """

    # ---------------------------------------------------------
    # Step 1: Health & System Readiness
    # ---------------------------------------------------------
    health_resp = client.get("/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["status"] in ["ok", "healthy"]

    # ---------------------------------------------------------
    # Step 2: Connections & Platform Registry Verification
    # ---------------------------------------------------------
    conn_resp = client.get("/api/v1/connections")
    assert conn_resp.status_code == 200
    conn_data = conn_resp.json()
    connections = conn_data.get("connections", [])
    platform_map = {c["id"]: c for c in connections}

    assert "bluesky" in platform_map
    assert "linkedin" in platform_map
    assert "facebook" in platform_map
    assert "instagram" in platform_map
    assert "whatsapp" not in platform_map

    # ---------------------------------------------------------
    # Step 3: LLM Content & Variant Generation
    # ---------------------------------------------------------
    gen_payload = {
        "topic": "Announcing the launch of OmniPulse AI social automation system!",
        "platforms": ["bluesky", "linkedin", "facebook", "instagram"],
        "tone": "Excited",
        "audience": "Tech founders, Creators & Growth teams",
        "campaign_objective": "Drive beta user signups",
        "include_hashtags": True,
    }

    gen_resp = client.post("/api/v1/generation/preview", json=gen_payload)
    assert gen_resp.status_code == 200
    gen_data = gen_resp.json()
    assert "generated_text" in gen_data
    assert len(gen_data["generated_text"]) > 10
    content_text = gen_data["generated_text"]
    assert "variants" in gen_data
    variants = gen_data["variants"] or {}
    assert "bluesky" in variants
    assert "linkedin" in variants
    assert "facebook" in variants
    assert "instagram" in variants

    # Bluesky length constraint check
    assert len(variants["bluesky"]) <= 300

    # ---------------------------------------------------------
    # Step 4: Persist Post in Post Library
    # ---------------------------------------------------------
    post_payload = {
        "title": "OmniPulse Public Beta Announcement",
        "snippet": content_text[:60] + "...",
        "content": content_text,
        "media_url": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1200",
        "tone": "Excited",
        "content_type": "Announcement",
        "language": "English",
        "platforms": ["bluesky", "linkedin", "facebook", "instagram"],
        "status": "scheduled",
    }

    post_resp = client.post("/api/v1/posts", json=post_payload)
    assert post_resp.status_code == 201
    created_post = post_resp.json()
    post_id = created_post["id"]
    assert post_id is not None
    assert created_post["status"] == "scheduled"

    # ---------------------------------------------------------
    # Step 5: Queue Multi-Platform Schedule (dry_run=True)
    # ---------------------------------------------------------
    # Target execution time: 1 minute in the past so it is immediately due
    due_time = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=1)).isoformat()
    sched_payload = {
        "post_id": post_id,
        "platforms": ["bluesky", "linkedin", "facebook", "instagram"],
        "scheduled_time": due_time,
        "dry_run": True,
        "max_attempts": 3,
        "variants": variants,
    }

    sched_resp = client.post("/api/v1/schedules", json=sched_payload)
    assert sched_resp.status_code == 201
    sched_job = sched_resp.json()
    sched_id = sched_job["id"]
    assert sched_job["status"] == "pending"
    assert sched_job["dry_run"] is True

    # ---------------------------------------------------------
    # Step 6: Atomic Claim & Background Processing Cycle
    # ---------------------------------------------------------
    processed_count = await scheduling_service.process_due_jobs_once()
    assert processed_count >= 1

    # ---------------------------------------------------------
    # Step 7: Post-Dispatch Verification
    # ---------------------------------------------------------
    check_sched_resp = client.get(f"/api/v1/schedules/{sched_id}")
    assert check_sched_resp.status_code == 200
    final_job = check_sched_resp.json()
    assert final_job["status"] == "completed"
    assert final_job["attempts"] == 1
    assert final_job["last_error"] is None

    # Check each platform result was safely mocked and published
    results = final_job["platform_results"]
    assert len(results) == 4
    for res in results:
        assert res["status"] == "published"
        assert res["is_mock"] is True
        assert res["remote_post_id"] is not None
        assert res["remote_post_url"] is not None

    # Check that Post Library post status was updated to published
    check_post_resp = client.get(f"/api/v1/posts/{post_id}")
    assert check_post_resp.status_code == 200
    assert check_post_resp.json()["status"] == "published"

    # ---------------------------------------------------------
    # Step 8: Unsupported Platform Graceful Rejection Verification
    # ---------------------------------------------------------
    unsupported_publish_resp = client.post("/api/v1/publishing/publish", json={
        "post_id": post_id,
        "platforms": ["unsupported_channel"],
        "dry_run": True,
    })
    assert unsupported_publish_resp.status_code == 200
    unsupported_result = unsupported_publish_resp.json()
    assert unsupported_result["success"] is False
    assert len(unsupported_result["results"]) == 1
    assert unsupported_result["results"][0]["platform"] == "unsupported_channel"
    assert unsupported_result["results"][0]["status"] == "failed"
    assert "requires API credentials" in unsupported_result["results"][0]["error_message"]
