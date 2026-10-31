import asyncio
import base64
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

    async def _resolve_credentials(self) -> tuple[str, str]:
        from app.services.credential_service import credential_service
        creds = await credential_service.get_credentials("instagram")
        if creds and creds.get("access_token") and creds.get("account_id"):
            return creds["access_token"], creds["account_id"]
        # Legacy static tokens are eliminated from active auth/publishing paths
        return "", ""

    async def validate_connection(self) -> bool:
        token, account_id = await self._resolve_credentials()

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
        dry_run: bool = False,
        **kwargs
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
        token, account_id = await self._resolve_credentials()

        if not account_id:
            return PlatformResult(
                platform=self.platform_name,
                status="failed",
                error_message="Missing Instagram Business Account ID. Please connect your Instagram Business Account in Platforms.",
            )

        if not token:
            return PlatformResult(
                platform=self.platform_name,
                status="failed",
                error_message="Missing Instagram access token. Please connect your Instagram Account in Platforms.",
            )

        # Resolve relative public URLs into fully qualified public HTTPS URLs
        if media_url and media_url.startswith("/"):
            media_url = f"https://ai-social-media-agent-phi.vercel.app{media_url}"

        # Instagram Content Publishing API requires a public media URL
        if not media_url:
            return PlatformResult(
                platform=self.platform_name,
                status="failed",
                error_message="Instagram requires an image or video URL. Text-only posts are not supported by Instagram.",
            )

        if media_url.startswith("data:"):
            # Attempt resilient automatic upload to Supabase Storage
            try:
                from app.api.v1.routes.media import _upload_to_supabase
                header, encoded = media_url.split(",", 1)
                mime = header.split(";")[0].replace("data:", "").strip() or "image/jpeg"
                ext = "jpg" if "jpeg" in mime or "jpg" in mime else ("png" if "png" in mime else "mp4")
                file_bytes = base64.b64decode(encoded)
                supabase_url = _upload_to_supabase(file_bytes, f"ig_upload.{ext}", mime)
                if supabase_url:
                    logger.info(f"Auto-uploaded Instagram data URL to Supabase: {supabase_url}")
                    media_url = supabase_url
                else:
                    return PlatformResult(
                        platform=self.platform_name,
                        status="failed",
                        error_message="Instagram Graph API requires a publicly accessible image URL (http/https). Local browser file uploads (data: URLs) cannot be downloaded by Meta's servers.",
                    )
            except Exception as e:
                logger.warning(f"Failed to auto-upload data URL for Instagram: {e}")
                return PlatformResult(
                    platform=self.platform_name,
                    status="failed",
                    error_message="Instagram Graph API requires a publicly accessible image URL (http/https). Local browser file uploads (data: URLs) cannot be downloaded by Meta's servers.",
                )

        async with httpx.AsyncClient(timeout=30.0) as client:
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

                # Step 2: Poll Container Status until FINISHED
                # Meta processes media asynchronously; publishing immediately causes 2207027
                max_polls = 10
                poll_interval = 2.0
                container_ready = False
                for attempt in range(max_polls):
                    try:
                        status_resp = await client.get(
                            f"{self.GRAPH_BASE_URL}/{container_id}",
                            params={"fields": "status_code,status", "access_token": token}
                        )
                        if status_resp.status_code == 200:
                            s_data = status_resp.json()
                            s_code = s_data.get("status_code")
                            logger.info(f"Instagram container {container_id} status poll {attempt + 1}: {s_code}")
                            if s_code == "FINISHED":
                                container_ready = True
                                break
                            elif s_code in ("ERROR", "EXPIRED"):
                                err_detail = s_data.get("status", "Unknown processing error")
                                return PlatformResult(
                                    platform=self.platform_name,
                                    status="failed",
                                    error_message=f"Instagram media processing failed: {err_detail}",
                                )
                    except Exception as poll_err:
                        logger.warning(f"Instagram status poll attempt {attempt + 1} notice: {poll_err}")
                    await asyncio.sleep(poll_interval)

                # Step 3: Publish Media Container
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
