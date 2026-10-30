import datetime
import logging
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.config import settings
from app.core.security import get_current_user_token
from app.schemas.post import PostCreate, PostUpdate, PostResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/posts", tags=["Posts"])

# In-memory post store for resilient fallback when Supabase is disconnected
_MEMORY_POSTS: dict[str, dict] = {}


def to_uuid(val: str) -> str:
    """
    Deterministically converts any ID string to a valid UUID format
    to maintain PostgreSQL UUID column compatibility.
    """
    try:
        return str(uuid.UUID(str(val)))
    except (ValueError, AttributeError):
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, str(val)))


def extract_user_id(token: Optional[str] = None) -> str:
    """Extracts user ID from Supabase JWT or falls back to primary account."""
    if token:
        try:
            import base64
            import json
            payload_part = token.split(".")[1]
            padded = payload_part + "=" * ((4 - len(payload_part) % 4) % 4)
            data = json.loads(base64.urlsafe_b64decode(padded))
            sub = data.get("sub")
            if sub:
                return sub
        except Exception:
            pass
    return "722cd994-8fbd-422d-afec-2f4111fb099d"


def _get_supabase_client(token: Optional[str] = None):
    if not settings.SUPABASE_URL or not (settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY):
        return None
    try:
        from supabase import create_client
        key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY
        client = create_client(settings.SUPABASE_URL, key)
        if token and not settings.SUPABASE_SERVICE_ROLE_KEY:
            client.postgrest.auth(token)
        return client
    except Exception as e:
        logger.warning(f"Could not connect to Supabase: {e}")
        return None


@router.get("", response_model=List[PostResponse])
async def list_posts(
    status_filter: Optional[str] = None,
    token: Optional[str] = Depends(get_current_user_token),
):
    client = _get_supabase_client(token)
    if client:
        try:
            query = client.table("posts").select("*").order("created_at", desc=True)
            if status_filter and status_filter != "all":
                query = query.eq("status", status_filter)
            res = query.execute()
            posts = []
            for row in res.data:
                # fetch platforms for post
                plat_res = client.table("post_platforms").select("platform").eq("post_id", row["id"]).execute()
                platforms = [p["platform"] for p in plat_res.data] if plat_res.data else []
                posts.append(PostResponse(
                    id=str(row["id"]),
                    title=row["title"],
                    snippet=row.get("snippet"),
                    content=row["content"],
                    media_url=row.get("media_url"),
                    tone=row.get("tone"),
                    content_type=row.get("content_type"),
                    language=row.get("language"),
                    platforms=platforms,
                    status=row.get("status", "draft"),
                    scheduled_at=str(row.get("scheduled_at")) if row.get("scheduled_at") else None,
                    created_at=str(row.get("created_at")) if row.get("created_at") else None,
                ))
            if posts:
                return posts
        except Exception as e:
            logger.warning(f"Supabase list failed ({e}), using memory fallback")

    # Fallback to in-memory store
    seen_ids = set()
    posts = []
    for p in _MEMORY_POSTS.values():
        pid = p.get("id")
        if pid and pid not in seen_ids:
            seen_ids.add(pid)
            posts.append(p)

    if status_filter and status_filter != "all":
        posts = [p for p in posts if p.get("status") == status_filter]
    return [PostResponse(**p) for p in posts]


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    payload: PostCreate,
    token: Optional[str] = Depends(get_current_user_token),
):
    post_id = payload.id or f"post-{int(datetime.datetime.now().timestamp() * 1000)}"
    db_id = to_uuid(post_id)
    now_str = payload.created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()

    post_dict = {
        "id": post_id,
        "title": payload.title,
        "snippet": payload.snippet or (payload.content[:50].replace("\n", " ") + "..."),
        "content": payload.content,
        "media_url": payload.media_url,
        "tone": payload.tone or "Professional",
        "content_type": payload.content_type or "General Post",
        "language": payload.language or "English",
        "platforms": payload.platforms,
        "status": payload.status,
        "scheduled_at": payload.scheduled_at,
        "created_at": now_str,
    }

    client = _get_supabase_client(token)
    if client:
        try:
            client.table("posts").upsert({
                "id": db_id,
                "user_id": extract_user_id(token),
                "title": post_dict["title"],
                "snippet": post_dict["snippet"],
                "content": post_dict["content"],
                "media_url": post_dict["media_url"],
                "tone": post_dict["tone"],
                "content_type": post_dict["content_type"],
                "language": post_dict["language"],
                "status": post_dict["status"],
                "scheduled_at": post_dict["scheduled_at"],
            }).execute()

            # Insert target platforms
            for plat in payload.platforms:
                client.table("post_platforms").upsert({
                    "post_id": db_id,
                    "platform": plat,
                    "status": "scheduled" if payload.status == "scheduled" else "pending",
                }).execute()

            # If scheduled, also register in scheduled_posts queue
            if payload.status == "scheduled" and post_dict.get("scheduled_at"):
                try:
                    client.table("scheduled_posts").upsert({
                        "post_id": db_id,
                        "run_at": post_dict["scheduled_at"],
                        "status": "pending",
                    }).execute()
                except Exception as sched_err:
                    logger.warning(f"Could not record scheduled_post in Supabase: {sched_err}")
        except Exception as e:
            logger.warning(f"Supabase create post failed ({e}), stored in memory")

    _MEMORY_POSTS[post_id] = post_dict
    _MEMORY_POSTS[db_id] = post_dict
    return PostResponse(**post_dict)


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: str,
    token: Optional[str] = Depends(get_current_user_token),
):
    if post_id in _MEMORY_POSTS:
        return PostResponse(**_MEMORY_POSTS[post_id])

    db_id = to_uuid(post_id)
    if db_id in _MEMORY_POSTS:
        return PostResponse(**_MEMORY_POSTS[db_id])

    client = _get_supabase_client(token)
    if client:
        try:
            res = client.table("posts").select("*").eq("id", db_id).single().execute()
            if res.data:
                row = res.data
                plat_res = client.table("post_platforms").select("platform").eq("post_id", db_id).execute()
                platforms = [p["platform"] for p in plat_res.data] if plat_res.data else []
                return PostResponse(
                    id=post_id,
                    title=row["title"],
                    snippet=row.get("snippet"),
                    content=row["content"],
                    media_url=row.get("media_url"),
                    tone=row.get("tone"),
                    content_type=row.get("content_type"),
                    language=row.get("language"),
                    platforms=platforms,
                    status=row.get("status", "draft"),
                    scheduled_at=str(row.get("scheduled_at")) if row.get("scheduled_at") else None,
                    created_at=str(row.get("created_at")) if row.get("created_at") else None,
                )
        except Exception as e:
            logger.warning(f"Supabase get post failed: {e}")

    raise HTTPException(status_code=404, detail="Post not found")


@router.patch("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: str,
    payload: PostUpdate,
    token: Optional[str] = Depends(get_current_user_token),
):
    db_id = to_uuid(post_id)
    target = _MEMORY_POSTS.get(post_id) or _MEMORY_POSTS.get(db_id)

    client = _get_supabase_client(token)
    if not target and client:
        try:
            res = client.table("posts").select("*").eq("id", db_id).single().execute()
            if res.data:
                target = res.data
                target["id"] = post_id
        except Exception as e:
            logger.warning(f"Supabase fetch before update failed: {e}")

    if not target:
        raise HTTPException(status_code=404, detail="Post not found")

    update_dict = payload.model_dump(exclude_unset=True)
    for k, v in update_dict.items():
        if v is not None:
            target[k] = v

    if client:
        try:
            db_update = {k: v for k, v in update_dict.items() if k not in ("platforms", "contentType", "scheduledAt", "mediaUrl")}
            if payload.contentType:
                db_update["content_type"] = payload.contentType
            if payload.scheduledAt:
                db_update["scheduled_at"] = payload.scheduledAt
            if payload.mediaUrl:
                db_update["media_url"] = payload.mediaUrl
            if db_update:
                client.table("posts").update(db_update).eq("id", db_id).execute()
        except Exception as e:
            logger.warning(f"Supabase update post failed: {e}")

    _MEMORY_POSTS[post_id] = target
    _MEMORY_POSTS[db_id] = target
    return PostResponse(**target)


@router.delete("/{post_id}")
async def delete_post(
    post_id: str,
    token: Optional[str] = Depends(get_current_user_token),
):
    db_id = to_uuid(post_id)
    if post_id in _MEMORY_POSTS:
        del _MEMORY_POSTS[post_id]
    if db_id in _MEMORY_POSTS:
        del _MEMORY_POSTS[db_id]

    client = _get_supabase_client(token)
    if client:
        try:
            client.table("posts").delete().eq("id", db_id).execute()
        except Exception as e:
            logger.warning(f"Supabase delete post failed: {e}")

    return {"success": True, "message": f"Post {post_id} deleted"}
