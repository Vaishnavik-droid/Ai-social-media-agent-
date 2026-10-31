import datetime
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.scheduling_service import scheduling_service, _MEMORY_SCHEDULES


@pytest.fixture(autouse=True)
def clear_schedules():
    _MEMORY_SCHEDULES.clear()
    yield
    _MEMORY_SCHEDULES.clear()


client = TestClient(app)


def test_scheduler_health_endpoint():
    response = client.get("/api/v1/schedules/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "running" in data
    assert "poll_interval_seconds" in data
    assert "total_jobs" in data


def test_schedule_creation_and_listing():
    future_time = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)).isoformat()
    payload = {
        "content": "Exciting AI announcement tomorrow!",
        "platforms": ["bluesky", "linkedin"],
        "scheduled_time": future_time,
        "dry_run": True,
        "max_attempts": 3,
    }

    create_resp = client.post("/api/v1/schedules", json=payload)
    assert create_resp.status_code == 201
    job = create_resp.json()
    assert job["id"].startswith("sched-")
    assert job["status"] == "pending"
    assert job["dry_run"] is True
    assert job["platforms"] == ["bluesky", "linkedin"]

    # List schedules
    list_resp = client.get("/api/v1/schedules")
    assert list_resp.status_code == 200
    schedules = list_resp.json()
    assert len(schedules) >= 1
    assert any(s["id"] == job["id"] for s in schedules)


def test_schedule_cancellation():
    future_time = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=5)).isoformat()
    create_resp = client.post("/api/v1/schedules", json={
        "content": "Post to cancel",
        "platforms": ["bluesky"],
        "scheduled_time": future_time,
        "dry_run": True,
    })
    job_id = create_resp.json()["id"]

    # Cancel schedule
    del_resp = client.delete(f"/api/v1/schedules/{job_id}")
    assert del_resp.status_code == 200
    cancelled_job = del_resp.json()
    assert cancelled_job["status"] == "cancelled"

    # Verify status in get
    get_resp = client.get(f"/api/v1/schedules/{job_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["status"] == "cancelled"


@pytest.mark.anyio
async def test_due_job_execution_dry_run():
    # Schedule job in the past
    past_time = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=5)).isoformat()
    create_resp = client.post("/api/v1/schedules", json={
        "content": "Testing scheduled dispatch with mock mode",
        "platforms": ["bluesky", "linkedin", "facebook"],
        "scheduled_time": past_time,
        "dry_run": True,
        "max_attempts": 3,
    })
    job_id = create_resp.json()["id"]

    # Trigger execution pass
    processed = await scheduling_service.process_due_jobs_once()
    assert processed >= 1

    # Check updated job
    get_resp = client.get(f"/api/v1/schedules/{job_id}")
    assert get_resp.status_code == 200
    job = get_resp.json()
    assert job["status"] == "completed"
    assert job["attempts"] == 1
    assert len(job["platform_results"]) == 3
    for res in job["platform_results"]:
        assert res["status"] == "published"
        assert res["is_mock"] is True


@pytest.mark.anyio
async def test_scheduler_retry_backoff_and_permanent_failure():
    # Schedule a job with an unsupported platform to force failure
    past_time = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=10)).isoformat()
    create_resp = client.post("/api/v1/schedules", json={
        "content": "Failing schedule test",
        "platforms": ["unsupported_channel_xyz"],
        "scheduled_time": past_time,
        "dry_run": True,
        "max_attempts": 2,
    })
    job_id = create_resp.json()["id"]

    # 1st attempt: should retry (attempts=1, status='pending', scheduled_time pushed forward)
    processed = await scheduling_service.process_due_jobs_once()
    assert processed == 1

    job = (await scheduling_service.get_schedule(job_id)).model_dump()
    assert job["attempts"] == 1
    assert job["status"] == "pending"
    assert "Next retry in" in job["last_error"]

    # Force scheduled_time to past again to trigger 2nd and final attempt
    _MEMORY_SCHEDULES[job_id]["scheduled_time"] = (
        datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=5)
    ).isoformat()

    # 2nd attempt: max_attempts=2 reached, should permanently fail
    processed = await scheduling_service.process_due_jobs_once()
    assert processed == 1

    job = (await scheduling_service.get_schedule(job_id)).model_dump()
    assert job["attempts"] == 2
    assert job["status"] == "failed"
    assert "Max attempts (2) reached" in job["last_error"]


@pytest.mark.anyio
async def test_startup_orphan_recovery():
    # Simulate an orphan job stuck in 'processing' due to server crash
    orphan_id = "sched-orphan-test-999"
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
    _MEMORY_SCHEDULES[orphan_id] = {
        "id": orphan_id,
        "post_id": None,
        "content": "Crash recovery post",
        "media_url": None,
        "platforms": ["bluesky"],
        "scheduled_time": now_str,
        "status": "processing",
        "attempts": 1,
        "max_attempts": 3,
        "last_error": None,
        "platform_results": [],
        "dry_run": True,
        "created_at": now_str,
        "updated_at": now_str,
    }

    # Run recovery
    await scheduling_service.recover_orphan_jobs()

    recovered_job = _MEMORY_SCHEDULES[orphan_id]
    assert recovered_job["status"] == "pending"
    assert recovered_job["attempts"] == 1
