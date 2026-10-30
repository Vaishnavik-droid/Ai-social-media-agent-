import datetime
import logging
from typing import Optional
import httpx

from app.core.config import settings
from app.platforms.base import BasePlatformAdapter
from app.schemas.publishing import PlatformResult

logger = logging.getLogger(__name__)


class InstagramAdapter(BasePlatformAdapter):
    GRAPH_API_VERSION = "v19.0"
    GRAPH_BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

    @property
    def platform_name(self) -> str:
        return "instagram"

    async def validate_connection(self) -> bool:
        account_id = settings.INSTAGRAM_BUSINESS_ACCOUNT_ID.strip()
        token = settings.INSTAGRAM_ACCESS_TOKEN.strip() or settings.META_USER_TOKEN.strip() or settings.FACEBOOK_PAGE_ACCESS_TOKEN.strip()

        if not account_id or not token:
            return False

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(
                    f"{self.GRAPH_BASE_URL}/{account_id}",
                    params={"access_token": token, "fields": "id,username,name"}
                )
                return resp.status_code == 200
            except Exception as e:
                logger.error(f"Instagram connection validation failed: {e}")
                return False

    async def publish_post(
        self,
        content: str,
        media_url: Optional[str] = None,
        dry_run: bool = False
    ) -> PlatformResult:
        # 1. Validation
        if len(content) > 2200:
            return PlatformResult(
                platform=self.platform_name,
                status="failed",
                error_message=f"Post caption exceeds Instagram limit of 2,200 characters (current: {len(content)}).",
            )

        # 2. Dry-Run / Mock Publishing Mode
        if dry_run:
            simulated_id = f"mock_ig_{int(datetime.datetime.now().timestamp())}"
            return PlatformResult(
                platform=self.platform_name,
                status="published",
                remote_post_id=simulated_id,
                remote_post_url=f"https://www.instagram.com/p/{simulated_id}/",
                is_mock=True,
                error_message=None,
            )

        # 3. Live Instagram Graph API Dispatch
        account_id = settings.INSTAGRAM_BUSINESS_ACCOUNT_ID.strip()
        token = settings.INSTAGRAM_ACCESS_TOKEN.strip() or settings.META_USER_TOKEN.strip() or settings.FACEBOOK_PAGE_ACCESS_TOKEN.strip()

        if not account_id:
            return PlatformResult(
                platform=self.platform_name,
                status="failed",
                error_message="Missing INSTAGRAM_BUSINESS_ACCOUNT_ID in backend/.env",
            )

        if not token:
            return PlatformResult(
                platform=self.platform_name,
                status="failed",
                error_message="Missing META_USER_TOKEN or FACEBOOK_PAGE_ACCESS_TOKEN in backend/.env",
            )

        # Instagram Content Publishing API requires a public media URL
        if not media_url:
            return PlatformResult(
                platform=self.platform_name,
                status="failed",
                error_message="Instagram requires an image or video URL. Text-only posts are not supported by Instagram.",
            )

        if media_url.startswith("data:"):
            return PlatformResult(
                platform=self.platform_name,
                status="failed",
                error_message="Instagram Graph API requires a publicly accessible image URL (http/https). Local browser file uploads (data: URLs) cannot be downloaded by Meta's servers.",
            )

        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                # Step 1: Create Media Container
                create_resp = await client.post(
                    f"{self.GRAPH_BASE_URL}/{account_id}/media",
                    data={
                        "image_url": media_url,
                        "caption": content,
                        "access_token": token,
                    }
                )

                if create_resp.status_code != 200:
                    err_msg = f"Instagram container creation failed (HTTP {create_resp.status_code})"
                    try:
                        err_json = create_resp.json().get("error", {})
                        msg = err_json.get("message", "")
                        if "Only photo or video can be accepted" in msg:
                            err_msg = "Instagram requires a valid public image or video URL."
                        elif msg:
                            err_msg = f"Instagram: {msg}"
                    except Exception:
                        pass
                    return PlatformResult(
                        platform=self.platform_name,
                        status="failed",
                        error_message=err_msg,
                    )

                container_id = create_resp.json().get("id")

                # Step 2: Publish Media Container
                pub_resp = await client.post(
                    f"{self.GRAPH_BASE_URL}/{account_id}/media_publish",
                    data={
                        "creation_id": container_id,
                        "access_token": token,
                    }
                )

                if pub_resp.status_code == 200:
                    media_id = pub_resp.json().get("id")
                    return PlatformResult(
                        platform=self.platform_name,
                        status="published",
                        remote_post_id=media_id,
                        remote_post_url=f"https://www.instagram.com/p/{media_id}/",
                        is_mock=False,
                    )
                else:
                    err_msg = f"Instagram publish failed (HTTP {pub_resp.status_code})"
                    try:
                        err_json = pub_resp.json().get("error", {})
                        msg = err_json.get("message", "")
                        if msg:
                            err_msg = f"Instagram: {msg}"
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
                    error_message=f"Error publishing to Instagram: {str(e)}",
                )


instagram_adapter = InstagramAdapter()
