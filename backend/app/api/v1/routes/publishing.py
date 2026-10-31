import datetime
import logging
import os
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.platforms.base import BasePlatformAdapter
from app.platforms.bluesky import bluesky_adapter
from app.platforms.linkedin import linkedin_adapter
from app.platforms.facebook import facebook_adapter
from app.platforms.instagram import instagram_adapter
from app.platforms.pinterest import pinterest_adapter
from app.platforms.youtube import youtube_adapter
from app.schemas.publishing import PlatformResult, PublishRequest, PublishResponse
from app.api.v1.routes.posts import _MEMORY_POSTS, _get_supabase_client, to_uuid

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/publishing", tags=["Publishing"])

# Registered platform adapters
ADAPTERS: Dict[str, BasePlatformAdapter] = {
    "bluesky": bluesky_adapter,
    "linkedin": linkedin_adapter,
    "facebook": facebook_adapter,
    "instagram": instagram_adapter,
    "pinterest": pinterest_adapter,
    "youtube": youtube_adapter,
}


@router.post("/publish", response_model=PublishResponse)
async def publish_post_endpoint(payload: PublishRequest):
    """
    Publish a post to selected social platforms.
    Routes to real adapters (Bluesky, LinkedIn, Facebook, Instagram, Pinterest, YouTube)
    and records per-platform results.
    Supports dry_run=True for safe testing and simulation.
    """
    db_id = to_uuid(payload.post_id)

    # 1. Fetch post content
    post_data = _MEMORY_POSTS.get(payload.post_id) or _MEMORY_POSTS.get(db_id)
    if not post_data:
        client = _get_supabase_client()
        if client:
            try:
                res = client.table("posts").select("*").eq("id", db_id).single().execute()
                if res.data:
                    post_data = res.data
            except Exception as e:
                logger.error(f"Failed to fetch post {payload.post_id}: {e}")

    # Fallback to direct payload content for stateless serverless resiliency
    if not post_data:
        if payload.content is not None:
            post_data = {
                "id": payload.post_id,
                "content": payload.content,
                "media_url": payload.media_url,
                "status": "pending",
            }
            _MEMORY_POSTS[payload.post_id] = post_data
            _MEMORY_POSTS[db_id] = post_data
        else:
            raise HTTPException(status_code=404, detail=f"Post with ID {payload.post_id} not found.")

    logger.info(
        "[Publishing] Received publish request: post_id=%s, platforms=%s, dry_run=%s, board_id=%s, title=%s, PUBLISHING_MODE=%s",
        payload.post_id,
        payload.platforms,
        payload.dry_run,
        payload.board_id,
        payload.title,
        settings.PUBLISHING_MODE,
    )

    content = payload.content if payload.content is not None else post_data.get("content", "")
    media_url = payload.media_url if payload.media_url is not None else post_data.get("media_url")

    results: List[PlatformResult] = []
    any_success = False

    global_dry_run = payload.dry_run or (settings.PUBLISHING_MODE.lower() == "mock")

    # 2. Iterate requested platforms
    for platform in payload.platforms:
        p_clean = platform.lower().strip()
        adapter = ADAPTERS.get(p_clean)
        if adapter:
            platform_dry_run = global_dry_run
            # Pinterest Sandbox Override: If PINTEREST_SANDBOX_TOKEN is configured and user did not explicitly request dry_run, enforce live execution
            if p_clean == "pinterest" and not payload.dry_run:
                sandbox_token = getattr(settings, "PINTEREST_SANDBOX_TOKEN", None) or os.environ.get("PINTEREST_SANDBOX_TOKEN")
                if sandbox_token:
                    platform_dry_run = False
                    logger.info("[Publishing] Pinterest sandbox token detected. Enforcing live API dispatch (dry_run=False).")

            result = await adapter.publish_post(
                content=content,
                media_url=media_url,
                dry_run=platform_dry_run,
                title=payload.title,
                board_id=payload.board_id,
            )
            results.append(result)
            logger.info(
                "[Publishing] Platform result for '%s': status=%s, remote_post_id=%s, remote_post_url=%s, is_mock=%s, error=%s",
                result.platform,
                result.status,
                result.remote_post_id,
                result.remote_post_url,
                result.is_mock,
                result.error_message,
            )
            if result.status == "published":
                any_success = True
        else:
            fail_result = PlatformResult(
                platform=platform,
                status="failed",
                error_message=f"Platform adapter for '{platform}' requires API credentials in platform_credentials.env",
            )
            results.append(fail_result)
            logger.warning("[Publishing] No adapter registered for platform: %s", platform)

    # 3. Update status in memory & Supabase
    overall_status = "published" if any_success else "failed"
    if post_data:
        post_data["status"] = overall_status

    client = _get_supabase_client()
    if client:
        try:
            client.table("posts").update({"status": overall_status}).eq("id", db_id).execute()
        except Exception as e:
            logger.error(f"Failed to update post status in Supabase: {e}")

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        for r in results:
            platform_row_id = to_uuid(f"{db_id}-{r.platform}")
            row_data: Dict[str, Any] = {
                "id": platform_row_id,
                "post_id": db_id,
                "platform": r.platform,
                "status": r.status,
                "published_url": r.remote_post_url,
                "remote_post_url": r.remote_post_url,
                "remote_post_id": r.remote_post_id,
                "error_message": r.error_message,
            }
            if r.status == "published":
                row_data["published_at"] = now_iso

            try:
                client.table("post_platforms").upsert(row_data, on_conflict="post_id,platform").execute()
                logger.info(
                    "[Publishing] DB persistence for '%s' (post_id: %s) succeeded: remote_post_id=%s, status=%s",
                    r.platform,
                    db_id,
                    r.remote_post_id,
                    r.status,
                )
            except Exception as e:
                err_str = str(e)
                if "remote_post_id" in err_str or "remote_post_url" in err_str or "schema cache" in err_str:
                    logger.warning(
                        f"Supabase post_platforms table missing remote_post_id column. "
                        f"Falling back to published_url. Please run migration 004_fix_post_platforms_remote_id.sql. Error: {e}"
                    )
                    fallback_data: Dict[str, Any] = {
                        "id": platform_row_id,
                        "post_id": db_id,
                        "platform": r.platform,
                        "status": r.status,
                        "published_url": r.remote_post_url,
                        "error_message": r.error_message,
                    }
                    if r.status == "published":
                        fallback_data["published_at"] = now_iso
                    try:
                        client.table("post_platforms").upsert(fallback_data, on_conflict="post_id,platform").execute()
                        logger.info(
                            "[Publishing] DB fallback persistence for '%s' (post_id: %s) succeeded: published_url=%s, status=%s",
                            r.platform,
                            db_id,
                            r.remote_post_url,
                            r.status,
                        )
                    except Exception as fallback_err:
                        logger.error(f"Failed to upsert post_platform fallback for {r.platform}: {fallback_err}")
                else:
                    logger.error(f"Failed to upsert post_platform for {r.platform}: {e}")

    return PublishResponse(
        post_id=payload.post_id,
        success=any_success,
        message=f"Post dispatched to {len(payload.platforms)} platform(s): {overall_status}",
        results=results,
        is_mock=any(r.is_mock for r in results) if results else global_dry_run,
    )
