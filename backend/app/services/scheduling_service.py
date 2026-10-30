import asyncio
import datetime
import logging
from typing import Any, Dict, List, Optional
import uuid

from app.core.config import settings
from app.platforms.bluesky import bluesky_adapter
from app.platforms.linkedin import linkedin_adapter
from app.platforms.facebook import facebook_adapter
from app.platforms.instagram import instagram_adapter
from app.schemas.publishing import PlatformResult
from app.schemas.scheduling import ScheduleCreate, ScheduleResponse, SchedulerHealthResponse
from app.api.v1.routes.posts import _MEMORY_POSTS, _get_supabase_client, to_uuid

logger = logging.getLogger("omnipulse.scheduler")

# In-memory storage fallback for scheduled jobs
_MEMORY_SCHEDULES: Dict[str, Dict[str, Any]] = {}

ADAPTERS = {
    "bluesky": bluesky_adapter,
    "linkedin": linkedin_adapter,
    "facebook": facebook_adapter,
    "instagram": instagram_adapter,
}


def _now_utc() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def _iso_now() -> str:
    return _now_utc().isoformat()


class SchedulingService:
    def __init__(self, poll_interval_seconds: int = 15):
        self.poll_interval_seconds = poll_interval_seconds
        self._running: bool = False
        self._worker_task: Optional[asyncio.Task] = None
        self._start_time: Optional[datetime.datetime] = None
        self._lock = asyncio.Lock()

    async def start(self):
        """Starts the background polling worker task (disabled in Vercel Serverless)."""
        import os
        if os.environ.get("VERCEL"):
            logger.info("⚡ Vercel Serverless environment detected. Persistent background worker loop disabled in favor of Vercel Cron.")
            return

        if not settings.SCHEDULER_ENABLED:
            logger.info("SchedulingService is disabled (SCHEDULER_ENABLED=false). Background worker loop not started.")
            return

        if self._running:
            logger.info("SchedulingService is already running.")
            return

        self._running = True
        self._start_time = _now_utc()
        self.poll_interval_seconds = settings.SCHEDULER_POLL_INTERVAL_SECONDS
        logger.info(f"⏰ SchedulingService starting (poll interval: {self.poll_interval_seconds}s)...")

        # Startup recovery: recover any jobs left orphaned in 'processing'
        await self.recover_orphan_jobs()

        self._worker_task = asyncio.create_task(self._worker_loop())
        logger.info("✅ SchedulingService background worker task initiated.")

    async def stop(self):
        """Gracefully cancels the background polling worker."""
        if not self._running:
            return

        logger.info("🛑 SchedulingService stopping background worker...")
        self._running = False
        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        self._worker_task = None
        logger.info("SchedulingService stopped.")

    async def _worker_loop(self):
        """Continuous polling loop."""
        while self._running:
            try:
                await self.process_due_jobs_once()
            except Exception as e:
                logger.error(f"Error in scheduler worker cycle: {e}", exc_info=True)

            try:
                await asyncio.sleep(self.poll_interval_seconds)
            except asyncio.CancelledError:
                break

    async def schedule_post(self, payload: ScheduleCreate) -> ScheduleResponse:
        """Create and queue a new scheduled post."""
        job_id = f"sched-{int(_now_utc().timestamp() * 1000)}-{uuid.uuid4().hex[:6]}"
        now_str = _iso_now()
        sched_time_iso = (
            payload.scheduled_time.astimezone(datetime.timezone.utc).isoformat()
            if payload.scheduled_time.tzinfo
            else payload.scheduled_time.replace(tzinfo=datetime.timezone.utc).isoformat()
        )

        job_data: Dict[str, Any] = {
            "id": job_id,
            "post_id": payload.post_id,
            "content": payload.content,
            "media_url": payload.media_url,
            "platforms": payload.platforms,
            "scheduled_time": sched_time_iso,
            "status": "pending",
            "attempts": 0,
            "max_attempts": payload.max_attempts,
            "last_error": None,
            "platform_results": [],
            "dry_run": payload.dry_run,
            "variants": payload.variants,
            "created_at": now_str,
            "updated_at": now_str,
        }

        # 1. In-memory store
        _MEMORY_SCHEDULES[job_id] = job_data

        # 2. Supabase persistence attempt
        client = _get_supabase_client()
        if client:
            try:
                db_id = to_uuid(job_id)
                post_db_id = to_uuid(payload.post_id) if payload.post_id else None
                client.table("scheduled_posts").upsert({
                    "id": db_id,
                    "post_id": post_db_id,
                    "status": "pending",
                    "scheduled_at": sched_time_iso,
                    "created_at": now_str,
                    "updated_at": now_str,
                }).execute()
            except Exception as e:
                logger.warning(f"Could not persist scheduled post to Supabase: {e}. Fallback to memory store active.")

        logger.info(f"Queued scheduled post {job_id} for {sched_time_iso} across {payload.platforms} (dry_run={payload.dry_run})")
        return ScheduleResponse(**job_data)

    async def list_schedules(self, status_filter: Optional[str] = None) -> List[ScheduleResponse]:
        """List all scheduled jobs, optionally filtered by status."""
        items: List[Dict[str, Any]] = []

        client = _get_supabase_client()
        if client:
            try:
                q = client.table("scheduled_posts").select("*").order("scheduled_at", desc=False)
                if status_filter and status_filter != "all":
                    q = q.eq("status", status_filter)
                res = q.execute()
                if res.data:
                    for row in res.data:
                        items.append({
                            "id": str(row["id"]),
                            "post_id": str(row.get("post_id")) if row.get("post_id") else None,
                            "content": row.get("content"),
                            "media_url": row.get("media_url"),
                            "platforms": row.get("platforms") or [],
                            "scheduled_time": str(row.get("scheduled_at") or row.get("scheduled_time") or ""),
                            "status": row.get("status", "pending"),
                            "attempts": row.get("attempts", 0),
                            "max_attempts": row.get("max_attempts", 3),
                            "last_error": row.get("last_error"),
                            "platform_results": row.get("platform_results") or [],
                            "dry_run": row.get("dry_run", False),
                            "created_at": str(row.get("created_at")),
                            "updated_at": str(row.get("updated_at")),
                        })
            except Exception as e:
                logger.warning(f"Could not read scheduled_posts from Supabase: {e}")

        if not items:
            # Fallback to in-memory store
            for job in _MEMORY_SCHEDULES.values():
                if status_filter and status_filter != "all" and job.get("status") != status_filter:
                    continue
                items.append(job)

        return [ScheduleResponse(**it) for it in items]

    async def get_schedule(self, schedule_id: str) -> Optional[ScheduleResponse]:
        """Fetch single scheduled job by ID."""
        if schedule_id in _MEMORY_SCHEDULES:
            return ScheduleResponse(**_MEMORY_SCHEDULES[schedule_id])

        db_id = to_uuid(schedule_id)
        if db_id in _MEMORY_SCHEDULES:
            return ScheduleResponse(**_MEMORY_SCHEDULES[db_id])

        client = _get_supabase_client()
        if client:
            try:
                res = client.table("scheduled_posts").select("*").eq("id", db_id).single().execute()
                if res.data:
                    row = res.data
                    return ScheduleResponse(
                        id=str(row["id"]),
                        post_id=str(row.get("post_id")) if row.get("post_id") else None,
                        content=row.get("content"),
                        media_url=row.get("media_url"),
                        platforms=row.get("platforms") or [],
                        scheduled_time=str(row.get("scheduled_at") or row.get("scheduled_time") or ""),
                        status=row.get("status", "pending"),
                        attempts=row.get("attempts", 0),
                        max_attempts=row.get("max_attempts", 3),
                        last_error=row.get("last_error"),
                        platform_results=row.get("platform_results") or [],
                        dry_run=row.get("dry_run", False),
                        created_at=str(row.get("created_at")),
                        updated_at=str(row.get("updated_at")),
                    )
            except Exception as e:
                logger.warning(f"Could not fetch schedule from Supabase: {e}")

        return None

    async def cancel_schedule(self, schedule_id: str) -> Optional[ScheduleResponse]:
        """Cancel a pending scheduled job."""
        job = await self.get_schedule(schedule_id)
        if not job:
            return None

        now_str = _iso_now()
        updated_dict = job.model_dump()
        updated_dict["status"] = "cancelled"
        updated_dict["updated_at"] = now_str

        # Update in-memory
        if schedule_id in _MEMORY_SCHEDULES:
            _MEMORY_SCHEDULES[schedule_id].update(updated_dict)
        db_id = to_uuid(schedule_id)
        if db_id in _MEMORY_SCHEDULES:
            _MEMORY_SCHEDULES[db_id].update(updated_dict)

        # Update Supabase
        client = _get_supabase_client()
        if client:
            try:
                client.table("scheduled_posts").update({
                    "status": "cancelled",
                    "updated_at": now_str,
                }).eq("id", db_id).execute()
            except Exception as e:
                logger.warning(f"Failed to cancel schedule in Supabase: {e}")

        return ScheduleResponse(**updated_dict)

    async def recover_orphan_jobs(self):
        """
        Startup recovery loop: checks for jobs left stuck in 'processing'
        state caused by an unexpected application kill or crash.
        """
        now = _now_utc()
        now_str = now.isoformat()
        recovered_count = 0

        # Check in-memory store
        for job_id, job in list(_MEMORY_SCHEDULES.items()):
            if job.get("status") == "processing":
                attempts = job.get("attempts", 1)
                max_attempts = job.get("max_attempts", 3)
                if attempts < max_attempts:
                    job["status"] = "pending"
                    job["updated_at"] = now_str
                    logger.warning(f"Recovered orphan job {job_id} back to 'pending' (attempt {attempts}/{max_attempts})")
                else:
                    job["status"] = "failed"
                    job["last_error"] = "Orphaned job exceeded max retries across restarts"
                    job["updated_at"] = now_str
                    logger.warning(f"Marked orphan job {job_id} as 'failed'")
                recovered_count += 1

        # Check Supabase
        client = _get_supabase_client()
        if client:
            try:
                res = client.table("scheduled_posts").select("*").eq("status", "processing").execute()
                for row in res.data or []:
                    attempts = row.get("attempts", 1)
                    max_attempts = row.get("max_attempts", 3)
                    new_status = "pending" if attempts < max_attempts else "failed"
                    client.table("scheduled_posts").update({
                        "status": new_status,
                        "updated_at": now_str,
                    }).eq("id", row["id"]).execute()
                    recovered_count += 1
            except Exception as e:
                logger.debug(f"Supabase orphan recovery skipped: {e}")

        if recovered_count > 0:
            logger.info(f"🔄 Recovered {recovered_count} orphan jobs from previous session.")

    async def process_due_jobs_once(self) -> int:
        """
        Atomic claiming and execution pass for due jobs.
        Returns the number of jobs processed.
        """
        async with self._lock:
            now = _now_utc()
            now_iso = now.isoformat()

            due_jobs: List[Dict[str, Any]] = []

            # 1. Find due jobs in memory store
            for job_id, job in _MEMORY_SCHEDULES.items():
                if job.get("status") == "pending":
                    sched_time_str = job.get("scheduled_time")
                    try:
                        sched_time = datetime.datetime.fromisoformat(sched_time_str.replace("Z", "+00:00"))
                        if sched_time.tzinfo is None:
                            sched_time = sched_time.replace(tzinfo=datetime.timezone.utc)
                        if sched_time <= now:
                            # Atomic claim in memory
                            job["status"] = "processing"
                            job["attempts"] = job.get("attempts", 0) + 1
                            job["updated_at"] = now_iso
                            due_jobs.append(job)
                    except Exception as parse_err:
                        logger.error(f"Error parsing scheduled_time for job {job_id}: {parse_err}")

            # 2. Check Supabase for any additional due jobs
            client = _get_supabase_client()
            if client:
                try:
                    res = client.table("scheduled_posts").select("*").eq("status", "pending").lte("scheduled_at", now_iso).execute()
                    for row in res.data or []:
                        rid = str(row["id"])
                        if rid not in [j["id"] for j in due_jobs]:
                            # Atomic claim
                            client.table("scheduled_posts").update({
                                "status": "processing",
                                "updated_at": now_iso,
                            }).eq("id", rid).execute()
                            due_jobs.append(row)
                except Exception as e:
                    logger.debug(f"Supabase due jobs query: {e}")

            if not due_jobs:
                return 0

            logger.info(f"Processing {len(due_jobs)} due scheduled posts...")

            # 3. Execute each claimed job
            for job in due_jobs:
                await self._execute_job(job)

            return len(due_jobs)

    async def _execute_job(self, job: Dict[str, Any]):
        """Executes a single claimed job across all specified platforms."""
        job_id = job["id"]
        post_id = job.get("post_id")
        content = job.get("content")
        media_url = job.get("media_url")
        platforms = job.get("platforms") or []
        dry_run = job.get("dry_run", False)
        effective_dry_run = dry_run or (settings.PUBLISHING_MODE.lower() == "mock")
        attempts = job.get("attempts", 1)
        max_attempts = job.get("max_attempts", 3)

        variants = job.get("variants") or {}
        # Resolve content if not explicitly in job
        if not content and post_id:
            # Check in-memory posts
            p_data = _MEMORY_POSTS.get(post_id) or _MEMORY_POSTS.get(to_uuid(post_id))
            if not p_data:
                client = _get_supabase_client()
                if client:
                    try:
                        res = client.table("posts").select("*").eq("id", to_uuid(post_id)).single().execute()
                        if res.data:
                            p_data = res.data
                    except Exception as e:
                        logger.warning(f"Could not load post {post_id} from Supabase: {e}")

            if p_data:
                content = p_data.get("content", "")
                if not media_url:
                    media_url = p_data.get("media_url")
                if not variants and p_data.get("variants"):
                    variants = p_data.get("variants")

        if not content:
            content = f"Automated scheduled post from OmniPulse Agent ({job_id})"

        platform_results: List[Dict[str, Any]] = []
        any_failed = False
        error_messages: List[str] = []

        # Dispatch each platform
        for plat in platforms:
            plat_clean = plat.lower().strip()
            # Select platform-specific variant if available
            plat_content = variants.get(plat_clean) if (variants and variants.get(plat_clean)) else content
            # Auto-trim if generic content exceeds platform hard limits
            if plat_clean == "bluesky" and len(plat_content) > 300:
                plat_content = plat_content[:297] + "..."
            elif plat_clean == "linkedin" and len(plat_content) > 3000:
                plat_content = plat_content[:2997] + "..."

            adapter = ADAPTERS.get(plat_clean)
            if adapter:
                try:
                    res: PlatformResult = await adapter.publish_post(
                        content=plat_content,
                        media_url=media_url,
                        dry_run=effective_dry_run,
                    )
                    platform_results.append(res.model_dump())
                    if res.status != "published":
                        any_failed = True
                        if res.error_message:
                            error_messages.append(f"{plat_clean}: {res.error_message}")
                except Exception as ex:
                    any_failed = True
                    error_msg = f"{plat_clean} exception: {str(ex)}"
                    error_messages.append(error_msg)
                    platform_results.append({
                        "platform": plat_clean,
                        "status": "failed",
                        "error_message": error_msg,
                        "remote_post_id": None,
                        "remote_post_url": None,
                        "is_mock": dry_run,
                    })
            else:
                any_failed = True
                msg = f"Unsupported platform: {plat}"
                error_messages.append(msg)
                platform_results.append({
                    "platform": plat,
                    "status": "failed",
                    "error_message": msg,
                    "remote_post_id": None,
                    "remote_post_url": None,
                    "is_mock": dry_run,
                })

        now_str = _iso_now()

        # Determine outcome & retry logic
        if not any_failed and platform_results:
            final_status = "completed"
            last_error = None
        else:
            if attempts < max_attempts:
                # Exponential backoff retry: 10s, 20s, 40s...
                backoff_seconds = 10 * (2 ** (attempts - 1))
                next_sched = _now_utc() + datetime.timedelta(seconds=backoff_seconds)
                final_status = "pending"
                job["scheduled_time"] = next_sched.isoformat()
                last_error = f"Attempt {attempts}/{max_attempts} failed: {'; '.join(error_messages)}. Next retry in {backoff_seconds}s"
                logger.warning(f"Job {job_id} failed on some platforms. Scheduling retry {attempts + 1}/{max_attempts} for {next_sched.isoformat()}")
            else:
                final_status = "failed"
                last_error = f"Max attempts ({max_attempts}) reached. Failures: {'; '.join(error_messages)}"
                logger.error(f"Job {job_id} permanently failed: {last_error}")

        # Update job record in memory
        job["status"] = final_status
        job["last_error"] = last_error
        job["platform_results"] = platform_results
        job["updated_at"] = now_str
        _MEMORY_SCHEDULES[job_id] = job

        # Update Supabase if available
        client = _get_supabase_client()
        if client:
            try:
                db_id = to_uuid(job_id)
                client.table("scheduled_posts").update({
                    "status": final_status,
                    "updated_at": now_str,
                }).eq("id", db_id).execute()

                # If post succeeded, update post status in posts table
                if final_status == "completed" and post_id:
                    post_db_id = to_uuid(post_id)
                    client.table("posts").update({"status": "published"}).eq("id", post_db_id).execute()
            except Exception as e:
                logger.debug(f"Supabase update error for job {job_id}: {e}")

        # Update memory post if associated
        if final_status == "completed" and post_id and post_id in _MEMORY_POSTS:
            _MEMORY_POSTS[post_id]["status"] = "published"

    def get_health(self) -> SchedulerHealthResponse:
        """Calculate scheduler health and queue breakdown."""
        total = len(_MEMORY_SCHEDULES)
        pending = sum(1 for j in _MEMORY_SCHEDULES.values() if j.get("status") == "pending")
        processing = sum(1 for j in _MEMORY_SCHEDULES.values() if j.get("status") == "processing")
        completed = sum(1 for j in _MEMORY_SCHEDULES.values() if j.get("status") == "completed")
        failed = sum(1 for j in _MEMORY_SCHEDULES.values() if j.get("status") == "failed")
        cancelled = sum(1 for j in _MEMORY_SCHEDULES.values() if j.get("status") == "cancelled")

        uptime = (_now_utc() - self._start_time).total_seconds() if self._start_time else 0.0

        return SchedulerHealthResponse(
            status="running" if self._running else "stopped",
            running=self._running,
            poll_interval_seconds=self.poll_interval_seconds,
            uptime_seconds=round(uptime, 2),
            total_jobs=total,
            pending_jobs=pending,
            processing_jobs=processing,
            completed_jobs=completed,
            failed_jobs=failed,
            cancelled_jobs=cancelled,
        )


# Global singleton instance
scheduling_service = SchedulingService(poll_interval_seconds=15)
