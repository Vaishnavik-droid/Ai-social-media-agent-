import base64
import datetime
import logging
from typing import Optional, Tuple
import httpx

from app.core.config import settings
from app.platforms.base import BasePlatformAdapter
from app.schemas.publishing import PlatformResult

logger = logging.getLogger(__name__)


class BlueskyAdapter(BasePlatformAdapter):
    @property
    def BSKY_HOST(self) -> str:
        return (settings.BLUESKY_SERVICE_URL or "https://bsky.social").rstrip("/")

    def __init__(self):
        self._cached_session: Optional[dict] = None

    @property
    def platform_name(self) -> str:
        return "bluesky"

    async def _resolve_media_bytes(self, media_url: Optional[str]) -> Tuple[Optional[bytes], Optional[str]]:
        """Downloads or decodes media into raw bytes and content type."""
        if not media_url:
            return None, None
        try:
            if media_url.startswith("/"):
                media_url = f"https://ai-social-media-agent-phi.vercel.app{media_url}"

            if media_url.startswith("data:"):
                # Handle base64 data URI (e.g., from browser image uploads)
                header, data = media_url.split(",", 1)
                mime = header.split(";")[0].replace("data:", "").strip()
                return base64.b64decode(data), mime or "image/jpeg"
            elif media_url.startswith("http://") or media_url.startswith("https://"):
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.get(media_url)
                    if resp.status_code == 200:
                        mime = resp.headers.get("content-type", "image/jpeg").split(";")[0].strip()
                        return resp.content, mime
        except Exception as e:
            logger.warning(f"Failed to fetch or decode media for Bluesky from {media_url[:60]}: {e}")
        return None, None

    async def _resolve_credentials(self) -> tuple[str, str]:
        from app.services.credential_service import credential_service
        creds = await credential_service.get_credentials("bluesky")
        if creds and creds.get("access_token") and creds.get("handle"):
            return creds["handle"].lstrip("@"), creds["access_token"]
        return settings.BLUESKY_HANDLE.strip(), settings.BLUESKY_APP_PASSWORD.strip()

    async def _create_session(self, force_refresh: bool = False) -> Optional[dict]:
        if self._cached_session and not force_refresh:
            return self._cached_session

        handle, app_password = await self._resolve_credentials()

        if not handle or not app_password:
            return None

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.post(
                    f"{self.BSKY_HOST}/xrpc/com.atproto.server.createSession",
                    json={"identifier": handle, "password": app_password},
                )
                if resp.status_code == 200:
                    self._cached_session = resp.json()
                    return self._cached_session
                logger.warning(f"Bluesky auth failed: {resp.text}")
                return None
            except Exception as e:
                logger.error(f"Error authenticating with Bluesky: {e}")
                return None

    async def validate_connection(self) -> bool:
        session = await self._create_session(force_refresh=True)
        return session is not None

    async def publish_post(
        self,
        content: str,
        media_url: Optional[str] = None,
        dry_run: bool = False,
        **kwargs
    ) -> PlatformResult:
        # 1. Validation & Auto-truncate for Bluesky 300-char limit
        if len(content) > 300:
            return PlatformResult(
                platform=self.platform_name,
                status="failed",
                error_message=f"Post text exceeds Bluesky limit of 300 characters (current: {len(content)}).",
            )


        # 2. Dry-Run / Mock Publishing Mode
        if dry_run:
            simulated_rkey = f"mock_{int(datetime.datetime.now().timestamp())}"
            handle = settings.BLUESKY_HANDLE.strip() or "mock.bsky.social"
            return PlatformResult(
                platform=self.platform_name,
                status="published",
                remote_post_id=f"at://did:plc:mocksimulateddid/app.bsky.feed.post/{simulated_rkey}",
                remote_post_url=f"https://bsky.app/profile/{handle}/post/{simulated_rkey}",
                is_mock=True,
                error_message=None,
            )

        # 3. Live AT Protocol Dispatch
        session = await self._create_session()
        if not session:
            handle, app_pwd = await self._resolve_credentials()
            if not handle or not app_pwd:
                return PlatformResult(
                    platform=self.platform_name,
                    status="failed",
                    error_message="Missing BLUESKY_HANDLE or BLUESKY_APP_PASSWORD. Please connect your Bluesky account.",
                )
            return PlatformResult(
                platform=self.platform_name,
                status="failed",
                error_message="Failed to authenticate session with Bluesky AT Protocol",
            )

        access_jwt = session.get("accessJwt")
        did = session.get("did")
        handle = session.get("handle")

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")

        record = {
            "$type": "app.bsky.feed.post",
            "text": content,
            "createdAt": now_iso,
        }

        async with httpx.AsyncClient(timeout=25.0) as client:
            try:
                # If media_url is provided, upload image blob and embed into the post
                if media_url:
                    img_bytes, mime_type = await self._resolve_media_bytes(media_url)
                    if img_bytes:
                        upload_resp = await client.post(
                            f"{self.BSKY_HOST}/xrpc/com.atproto.repo.uploadBlob",
                            headers={
                                "Authorization": f"Bearer {access_jwt}",
                                "Content-Type": mime_type or "image/jpeg",
                            },
                            content=img_bytes,
                            timeout=25.0,
                        )
                        if upload_resp.status_code == 200:
                            blob_data = upload_resp.json().get("blob")
                            if blob_data:
                                record["embed"] = {
                                    "$type": "app.bsky.embed.images",
                                    "images": [
                                        {
                                            "alt": content[:100] or "OmniPulse Post Image",
                                            "image": blob_data,
                                        }
                                    ],
                                }
                        else:
                            logger.warning(f"Bluesky blob upload returned {upload_resp.status_code}: {upload_resp.text}")

                resp = await client.post(
                    f"{self.BSKY_HOST}/xrpc/com.atproto.repo.createRecord",
                    headers={"Authorization": f"Bearer {access_jwt}"},
                    json={
                        "repo": did,
                        "collection": "app.bsky.feed.post",
                        "record": record,
                    },
                )

                if resp.status_code == 200:
                    data = resp.json()
                    rkey = data.get("uri", "").split("/")[-1]
                    web_url = f"https://bsky.app/profile/{handle}/post/{rkey}"
                    return PlatformResult(
                        platform=self.platform_name,
                        status="published",
                        remote_post_id=data.get("uri"),
                        remote_post_url=web_url,
                    )
                elif resp.status_code == 401:
                    # Clear session on expired token
                    self._cached_session = None
                    return PlatformResult(
                        platform=self.platform_name,
                        status="failed",
                        error_message="Bluesky AT Protocol session expired (HTTP 401). Please re-verify credentials.",
                    )
                else:
                    return PlatformResult(
                        platform=self.platform_name,
                        status="failed",
                        error_message=f"Bluesky returned HTTP {resp.status_code}: {resp.text}",
                    )
            except Exception as e:
                return PlatformResult(
                    platform=self.platform_name,
                    status="failed",
                    error_message=f"Network error publishing to Bluesky: {str(e)}",
                )


bluesky_adapter = BlueskyAdapter()
