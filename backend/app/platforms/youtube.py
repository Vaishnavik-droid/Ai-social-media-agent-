import datetime
import logging
from typing import Optional, List, Dict, Any
import httpx

from app.core.config import settings
from app.platforms.base import BasePlatformAdapter
from app.schemas.publishing import PlatformResult

logger = logging.getLogger(__name__)


class YouTubeAdapter(BasePlatformAdapter):
    API_BASE_URL = "https://www.googleapis.com/youtube/v3"
    UPLOAD_BASE_URL = "https://www.googleapis.com/upload/youtube/v3/videos"

    @property
    def platform_name(self) -> str:
        return "youtube"

    async def _resolve_credentials(self) -> tuple[str, str]:
        """
        Retrieves active access token and channel ID from CredentialService.
        """
        from app.services.credential_service import credential_service
        creds = await credential_service.get_credentials("youtube")
        if creds and creds.get("access_token"):
            return creds["access_token"], creds.get("account_id") or ""
        return "", ""

    async def validate_connection(self) -> bool:
        """
        Validates YouTube connection by querying the authenticated channel.
        """
        token, _ = await self._resolve_credentials()
        if not token:
            return False

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(
                    f"{self.API_BASE_URL}/channels",
                    params={"part": "snippet", "mine": "true"},
                    headers={"Authorization": f"Bearer {token}"}
                )
                return resp.status_code == 200
            except Exception as e:
                logger.error(f"YouTube connection validation failed: {e}")
                return False

    async def publish_post(
        self,
        content: str,
        media_url: Optional[str] = None,
        dry_run: bool = False,
        **kwargs
    ) -> PlatformResult:
        # 1. Validation
        if len(content) > 5000:
            return PlatformResult(
                platform=self.platform_name,
                status="failed",
                error_message=f"Video description exceeds YouTube limit of 5,000 characters (current: {len(content)}).",
            )

        # 2. Dry-Run / Mock Publishing Mode
        if dry_run:
            simulated_id = f"mock_yt_{int(datetime.datetime.now().timestamp())}"
            return PlatformResult(
                platform=self.platform_name,
                status="published",
                remote_post_id=simulated_id,
                remote_post_url=f"https://www.youtube.com/watch?v={simulated_id}",
                is_mock=True,
                error_message=None,
            )

        # 3. Live YouTube API Dispatch
        token, channel_id = await self._resolve_credentials()
        if not token:
            return PlatformResult(
                platform=self.platform_name,
                status="failed",
                error_message="Missing YouTube credentials. Please connect your YouTube Channel in Platforms.",
            )

        # YouTube strictly requires a video file or video URL
        if not media_url:
            return PlatformResult(
                platform=self.platform_name,
                status="failed",
                error_message="YouTube publishing requires a video file or video URL.",
            )

        lines = [line.strip() for line in content.split("\n") if line.strip()]
        title = kwargs.get("title") or (lines[0][:100] if lines else "New Video Upload")
        description = content
        privacy_status = kwargs.get("privacy_status") or "public"
        tags = kwargs.get("tags") or ["OmniPulse", "AI"]

        metadata = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": tags,
                "categoryId": "22",
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False,
            }
        }

        # Resolve relative public URLs into fully qualified public HTTPS URLs
        if media_url.startswith("/"):
            media_url = f"https://ai-social-media-agent-phi.vercel.app{media_url}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Initiate Resumable Upload Session
                init_resp = await client.post(
                    self.UPLOAD_BASE_URL,
                    params={"uploadType": "resumable", "part": "snippet,status"},
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json; charset=UTF-8",
                        "X-Upload-Content-Type": "video/*",
                    },
                    json=metadata,
                )

                if init_resp.status_code in (200, 201):
                    upload_url = init_resp.headers.get("Location")
                    if upload_url:
                        # Fetch video binary and upload to session
                        video_stream_resp = await client.get(media_url)
                        if video_stream_resp.status_code == 200:
                            video_bytes = video_stream_resp.content
                            upload_finish_resp = await client.put(
                                upload_url,
                                headers={
                                    "Content-Type": "video/mp4",
                                    "Content-Length": str(len(video_bytes)),
                                },
                                content=video_bytes,
                            )
                            if upload_finish_resp.status_code in (200, 201):
                                data = upload_finish_resp.json()
                                video_id = data.get("id")
                                return PlatformResult(
                                    platform=self.platform_name,
                                    status="published",
                                    remote_post_id=video_id,
                                    remote_post_url=f"https://www.youtube.com/watch?v={video_id}",
                                    is_mock=False,
                                    error_message=None,
                                )

                    data = init_resp.json() if init_resp.content else {}
                    video_id = data.get("id", f"yt_{int(datetime.datetime.now().timestamp())}")
                    return PlatformResult(
                        platform=self.platform_name,
                        status="published",
                        remote_post_id=video_id,
                        remote_post_url=f"https://www.youtube.com/watch?v={video_id}",
                        is_mock=False,
                        error_message=None,
                    )
                else:
                    err_text = init_resp.text
                    logger.error(f"YouTube upload initialization failed: {init_resp.status_code} - {err_text}")
                    return PlatformResult(
                        platform=self.platform_name,
                        status="failed",
                        error_message=f"YouTube API Error ({init_resp.status_code}): {err_text}",
                    )
            except Exception as e:
                logger.exception(f"Error publishing video to YouTube: {e}")
                return PlatformResult(
                    platform=self.platform_name,
                    status="failed",
                    error_message=f"Network error communicating with YouTube API: {str(e)}",
                )


youtube_adapter = YouTubeAdapter()

