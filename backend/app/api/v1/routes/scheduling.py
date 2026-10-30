import datetime
import logging
from typing import List, Optional
from fastapi import APIRouter, Header, HTTPException, Query, status

from app.core.config import settings
from app.schemas.scheduling import ScheduleCreate, ScheduleResponse, SchedulerHealthResponse
from app.services.scheduling_service import scheduling_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/schedules", tags=["Scheduling"])



@router.post("", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(payload: ScheduleCreate):
    """
    Queue a new scheduled post to one or more platforms at a specified future UTC time.
    Supports dry_run=True for safe simulation without touching live social APIs.
    """
    try:
        return await scheduling_service.schedule_post(payload)
    except Exception as e:
        logger.error(f"Failed to queue schedule: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to schedule post: {str(e)}",
        )


@router.get("", response_model=List[ScheduleResponse])
async def list_schedules(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: pending, processing, completed, failed, cancelled"),
):
    """
    Retrieve all scheduled queue jobs, ordered by execution time.
    """
    return await scheduling_service.list_schedules(status_filter=status_filter)


@router.get("/health", response_model=SchedulerHealthResponse)
async def get_scheduler_health():
    """
    Check the health, uptime, worker state, and queue depth of the scheduling engine.
    """
    return scheduling_service.get_health()


@router.post("/trigger")
async def trigger_scheduler_cycle():
    """
    Manually trigger an atomic claiming and execution cycle for due jobs.
    Useful for testing, synchronization, and admin inspection.
    """
    processed_count = await scheduling_service.process_due_jobs_once()
    return {
        "status": "success",
        "processed_jobs": processed_count,
    }


@router.get("/process-due-jobs")
@router.post("/process-due-jobs")
async def vercel_cron_process_due_jobs(
    authorization: Optional[str] = Header(None),
    cron_token: Optional[str] = Query(None, alias="key"),
):
    """
    Vercel Cron endpoint to claim and process due scheduled posts.
    Secured by CRON_SECRET if configured in Vercel environment variables.
    """
    expected_secret = settings.CRON_SECRET.strip() if settings.CRON_SECRET else ""
    if expected_secret:
        auth_token = ""
        if authorization:
            auth_token = authorization.replace("Bearer ", "").strip() if authorization.startswith("Bearer ") else authorization.strip()
        
        if auth_token != expected_secret and cron_token != expected_secret:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized: Invalid or missing CRON_SECRET.",
            )

    processed_count = await scheduling_service.process_due_jobs_once()
    return {
        "status": "success",
        "processed_jobs": processed_count,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }



@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(schedule_id: str):
    """
    Retrieve details and execution results of a specific scheduled post by ID.
    """
    job = await scheduling_service.get_schedule(schedule_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheduled job with ID '{schedule_id}' not found.",
        )
    return job


@router.delete("/{schedule_id}", response_model=ScheduleResponse)
async def cancel_schedule(schedule_id: str):
    """
    Cancel a pending scheduled job before its execution.
    """
    job = await scheduling_service.cancel_schedule(schedule_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheduled job with ID '{schedule_id}' not found.",
        )
    return job
