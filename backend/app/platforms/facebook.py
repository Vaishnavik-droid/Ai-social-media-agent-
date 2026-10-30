import datetime
import logging
from typing import Optional
import httpx

from app.core.config import settings
from app.platforms.base import BasePlatformAdapter
from app.schemas.publishing import PlatformResult

logger = logging.getLogger(__name__)


class FacebookAdapter(BasePlatformAdapter):
    GRAPH_API_VERSION = "v19.0"
    GRAPH_BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

    @property
    def platform_name(self) -> str:
        return "facebook"

    async def validate_connection(self) -> bool:
        token = settings.FACEBOOK_PAGE_ACCESS_TOKEN.strip()
        page_id = settings.FACEBOOK_PAGE_ID.strip()

        if not token or not page_id:
            return False

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(
                    f"{self.GRAPH_BASE_URL}/{page_id}",
                    params={"access_token": token, "fields": "id,name"}
                )
                return resp.status_code == 200
            except Exception as e:
                logger.error(f"Facebook connection validation failed: {e}")
                return False

    async def publish_post(
        self,
        content: str,
        media_url: Optional[str] = None,
        dry_run: bool = False
    ) -> PlatformResult:
        # 1. Validation
        if len(content) > 63206:
            return PlatformResult(
                platform=self.platform_name,
                status="failed",
                error_message=f"Post text exceeds Facebook limit of 63,206 characters (current: {len(content)}).",
            )

        # 2. Dry-Run / Mock Publishing Mode
        if dry_run:
            simulated_id = f"mock_fb_{int(datetime.datetime.now().timestamp())}"
            page_id = settings.FACEBOOK_PAGE_ID.strip() or "mockpage"
            return PlatformResult(
                platform=self.platform_name,
                status="published",
                remote_post_id=f"{page_id}_{simulated_id}",
                remote_post_url=f"https://www.facebook.com/{page_id}/posts/{simulated_id}",
                is_mock=True,
                error_message=None,
            )

        # 3. Live Facebook Graph API Dispatch
        token = settings.FACEBOOK_PAGE_ACCESS_TOKEN.strip()
        page_id = settings.FACEBOOK_PAGE_ID.strip()

        if not token:
            return PlatformResult(
                platform=self.platform_name,
                status="failed",
                error_message="Missing FACEBOOK_PAGE_ACCESS_TOKEN in backend/.env",
            )

        if not page_id:
            return PlatformResult(
                platform=self.platform_name,
                status="failed",
                error_message="Missing FACEBOOK_PAGE_ID in backend/.env",
            )

        # Resolve relative public URLs into fully qualified public HTTPS URLs
        if media_url and media_url.startswith("/"):
            media_url = f"https://ai-social-media-agent-phi.vercel.app{media_url}"

        import base64

        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                # 1. Image upload handling
                if media_url and media_url.startswith("data:image/"):
                    try:
                        header, encoded = media_url.split(",", 1)
                        mime_type = header.split(";")[0].replace("data:", "")
                        image_bytes = base64.b64decode(encoded)
                        ext = mime_type.split("/")[-1] if "/" in mime_type else "png"
                        
                        files = {
                            "source": (f"upload.{ext}", image_bytes, mime_type)
                        }
                        data = {
                            "caption": content,
                            "access_token": token
                        }
                        resp = await client.post(
                            f"{self.GRAPH_BASE_URL}/{page_id}/photos",
                            data=data,
                            files=files
                        )
                    except Exception as e:
                        logger.error(f"Error parsing base64 image for Facebook: {e}")
                        resp = await client.post(
                            f"{self.GRAPH_BASE_URL}/{page_id}/feed",
                            data={"message": content, "access_token": token}
                        )
                elif media_url and any(media_url.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]):
                    # Public image URL -> /{page_id}/photos
                    resp = await client.post(
                        f"{self.GRAPH_BASE_URL}/{page_id}/photos",
                        data={"caption": content, "url": media_url, "access_token": token}
                    )
                elif media_url and (media_url.startswith("http://") or media_url.startswith("https://")):
                    # Web link -> /{page_id}/feed
                    resp = await client.post(
                        f"{self.GRAPH_BASE_URL}/{page_id}/feed",
                        data={"message": content, "link": media_url, "access_token": token}
                    )
                else:
                    # Text-only post -> /{page_id}/feed
                    resp = await client.post(
                        f"{self.GRAPH_BASE_URL}/{page_id}/feed",
                        data={"message": content, "access_token": token}
                    )

                if resp.status_code == 200:
                    resp_data = resp.json()
                    post_id = resp_data.get("id") or resp_data.get("post_id")
                    return PlatformResult(
                        platform=self.platform_name,
                        status="published",
                        remote_post_id=post_id,
                        remote_post_url=f"https://www.facebook.com/{post_id}" if post_id else None,
                        is_mock=False,
                    )
                elif resp.status_code == 401:
                    return PlatformResult(
                        platform=self.platform_name,
                        status="failed",
                        error_message="Facebook Page Access Token expired or invalid (HTTP 401). Please re-generate token in Meta for Developers.",
                    )
                elif resp.status_code == 403:
                    err_json = {}
                    try:
                        err_json = resp.json().get("error", {})
                    except Exception:
                        pass
                    msg = err_json.get("message", "")
                    if "admin with sufficient administrative permission" in msg or "posting to a page" in msg:
                        return PlatformResult(
                            platform=self.platform_name,
                            status="failed",
                            error_message="Facebook error: FACEBOOK_PAGE_ID must be a Facebook Page ID (not a personal profile), and the token must have Page admin permissions.",
                        )
                    return PlatformResult(
                        platform=self.platform_name,
                        status="failed",
                        error_message="Insufficient Facebook Page permissions (HTTP 403). Requires 'pages_manage_posts' and 'pages_read_engagement'.",
                    )
                elif resp.status_code == 429:
                    return PlatformResult(
                        platform=self.platform_name,
                        status="failed",
                        error_message="Facebook Graph API rate limit reached (HTTP 429).",
                    )
                else:
                    err_msg = f"Facebook returned HTTP {resp.status_code}"
                    try:
                        err_json = resp.json().get("error", {})
                        code = err_json.get("code")
                        subcode = err_json.get("error_subcode")
                        msg = err_json.get("message", "")
                        if code == 190 or subcode in (463, 467) or "expired" in msg.lower():
                            err_msg = "Facebook Page Access Token expired. Please refresh your token."
                        elif "admin with sufficient administrative permission" in msg or "posting to a page" in msg:
                            err_msg = "Facebook error: FACEBOOK_PAGE_ID must be a Facebook Page ID (not a personal profile), and the token must have Page admin permissions."
                        elif msg:
                            err_msg = f"Facebook: {msg}"
                    except Exception:
                        pass
                    return PlatformResult(
                        platform=self.platform_name,
                        status="failed",
                        error_message=err_msg,
                    )
            except Exception as e:
                return PlatformResult(
                    platform=self.platform_name,
                    status="failed",
                    error_message=f"Error publishing to Facebook: {str(e)}",
                )


facebook_adapter = FacebookAdapter()
