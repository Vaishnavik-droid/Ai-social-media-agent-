import logging
from typing import Dict, List
from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.platforms.base import BasePlatformAdapter
from app.platforms.bluesky import bluesky_adapter
from app.platforms.linkedin import linkedin_adapter
from app.platforms.facebook import facebook_adapter
from app.platforms.instagram import instagram_adapter
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
}


@router.post("/publish", response_model=PublishResponse)
async def publish_post_endpoint(payload: PublishRequest):
    """
    Publish a post to selected social platforms.
    Routes to real adapters (Bluesky, LinkedIn, Facebook, Instagram) and records per-platform results.
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

    content = payload.content if payload.content is not None else post_data.get("content", "")
    media_url = payload.media_url if payload.media_url is not None else post_data.get("media_url")

    results: List[PlatformResult] = []
    any_success = False

    effective_dry_run = payload.dry_run or (settings.PUBLISHING_MODE.lower() == "mock")

    # 2. Iterate requested platforms
    for platform in payload.platforms:
        p_clean = platform.lower().strip()
        adapter = ADAPTERS.get(p_clean)
        if adapter:
            result = await adapter.publish_post(content=content, media_url=media_url, dry_run=effective_dry_run)
            results.append(result)
            if result.status == "published":
                any_success = True
        else:
            results.append(
                PlatformResult(
                    platform=platform,
                    status="failed",
                    error_message=f"Platform adapter for '{platform}' requires API credentials in backend/.env",
                )
            )

    # 3. Update status in memory & Supabase
    overall_status = "published" if any_success else "failed"
    if post_data:
        post_data["status"] = overall_status

    client = _get_supabase_client()
    if client:
        try:
            client.table("posts").update({"status": overall_status}).eq("id", db_id).execute()
            for r in results:
                client.table("post_platforms").upsert({
                    "post_id": db_id,
                    "platform": r.platform,
                    "status": r.status,
                    "remote_post_id": r.remote_post_id,
                    "remote_post_url": r.remote_post_url,
                    "error_message": r.error_message,
                }).execute()
        except Exception as e:
            logger.warning(f"Could not persist publish status in Supabase: {e}")

    is_any_mock = any(r.is_mock for r in results) or effective_dry_run
    mode_text = " [MOCK / DRY-RUN MODE]" if is_any_mock else ""

    return PublishResponse(
        post_id=payload.post_id,
        success=any_success,
        message=f"Publish job completed{mode_text}." if any_success else f"One or more platforms failed to publish{mode_text}.",
        results=results,
        is_mock=is_any_mock,
    )
