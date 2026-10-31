import base64
import logging
import mimetypes
import uuid
from typing import Optional
from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.api.v1.routes.posts import _get_supabase_client
from app.core.config import settings

logger = logging.getLogger("omnipulse.routes.media")
router = APIRouter(prefix="/media", tags=["Media"])

STORAGE_BUCKET = "post-media"
FALLBACK_BUCKET = "media"


class MediaUploadJson(BaseModel):
    data: str  # Base64 string or data: URL
    filename: Optional[str] = "upload.jpg"
    content_type: Optional[str] = None


class MediaUploadResponse(BaseModel):
    url: str
    filename: str
    content_type: str
    size: int
    storage: str  # 'supabase' or 'inline'


def _ensure_bucket(client, bucket_name: str) -> bool:
    """Attempts to check or create a public storage bucket if needed."""
    try:
        buckets = client.storage.list_buckets()
        bucket_names = [b.name if hasattr(b, 'name') else b.get('name') for b in buckets]
        if bucket_name not in bucket_names:
            client.storage.create_bucket(bucket_name, options={"public": True})
            logger.info(f"Created public Supabase storage bucket: {bucket_name}")
        return True
    except Exception as e:
        logger.debug(f"Bucket verification/creation for {bucket_name}: {e}")
        return False


def _upload_to_supabase(file_bytes: bytes, filename: str, content_type: str) -> Optional[str]:
    client = _get_supabase_client()
    if not client:
        return None

    # Pick bucket
    bucket = STORAGE_BUCKET
    _ensure_bucket(client, bucket)

    clean_name = filename.replace(" ", "_").replace("/", "_").replace("\\", "_")
    unique_path = f"uploads/{uuid.uuid4().hex[:12]}_{clean_name}"

    try:
        # Upload binary
        client.storage.from_(bucket).upload(
            path=unique_path,
            file=file_bytes,
            file_options={"content-type": content_type, "upsert": "true"},
        )
        public_url = client.storage.from_(bucket).get_public_url(unique_path)
        return public_url
    except Exception as e:
        logger.warning(f"Failed to upload to Supabase bucket '{bucket}': {e}. Trying fallback bucket '{FALLBACK_BUCKET}'...")
        try:
            _ensure_bucket(client, FALLBACK_BUCKET)
            client.storage.from_(FALLBACK_BUCKET).upload(
                path=unique_path,
                file=file_bytes,
                file_options={"content-type": content_type, "upsert": "true"},
            )
            return client.storage.from_(FALLBACK_BUCKET).get_public_url(unique_path)
        except Exception as e2:
            logger.error(f"Fallback bucket upload also failed: {e2}")
            return None


@router.post("/upload", response_model=MediaUploadResponse)
async def upload_media_file(file: UploadFile = File(...)):
    """
    Accepts multipart/form-data media upload (images/videos) and uploads to
    public Supabase Storage. Returns a persistent, public HTTPS URL suitable
    for Instagram Graph API, Pinterest Pins, YouTube, and LinkedIn.
    """
    try:
        content_bytes = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {str(e)}",
        )

    if not content_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    filename = file.filename or "media_upload.jpg"
    content_type = file.content_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"

    # Attempt Supabase Storage
    public_url = _upload_to_supabase(content_bytes, filename, content_type)

    if public_url:
        return MediaUploadResponse(
            url=public_url,
            filename=filename,
            content_type=content_type,
            size=len(content_bytes),
            storage="supabase",
        )

    # If Supabase storage is not available and file is <= 10MB, provide encoded data URL
    if len(content_bytes) <= 10 * 1024 * 1024:
        encoded = base64.b64encode(content_bytes).decode("ascii")
        data_url = f"data:{content_type};base64,{encoded}"
        return MediaUploadResponse(
            url=data_url,
            filename=filename,
            content_type=content_type,
            size=len(content_bytes),
            storage="inline",
        )

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Supabase Storage upload failed and file exceeds inline storage limit.",
    )


@router.post("/upload-json", response_model=MediaUploadResponse)
async def upload_media_json(payload: MediaUploadJson):
    """
    Accepts base64 / data URL JSON and uploads to public Supabase Storage.
    """
    raw_data = payload.data.strip()
    content_type = payload.content_type or "image/jpeg"

    if raw_data.startswith("data:"):
        header, encoded = raw_data.split(",", 1)
        mime = header.split(";")[0].replace("data:", "").strip()
        if mime:
            content_type = mime
    else:
        encoded = raw_data

    try:
        file_bytes = base64.b64decode(encoded)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid base64 media payload: {str(e)}",
        )

    filename = payload.filename or f"upload_{uuid.uuid4().hex[:8]}.jpg"
    public_url = _upload_to_supabase(file_bytes, filename, content_type)

    if public_url:
        return MediaUploadResponse(
            url=public_url,
            filename=filename,
            content_type=content_type,
            size=len(file_bytes),
            storage="supabase",
        )

    return MediaUploadResponse(
        url=raw_data if raw_data.startswith("data:") else f"data:{content_type};base64,{encoded}",
        filename=filename,
        content_type=content_type,
        size=len(file_bytes),
        storage="inline",
    )

