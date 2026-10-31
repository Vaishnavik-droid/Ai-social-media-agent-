import base64
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

    async def _refresh_access_token(self) -> Optional[str]:
        """
        Uses stored refresh token to obtain a fresh Google OAuth access token.
        Updates persistent storage via CredentialService.
        """
        from app.services.credential_service import credential_service
        creds = await credential_service.get_credentials("youtube")
        if not creds or not creds.get("refresh_token"):
            logger.warning("No refresh token available to refresh YouTube access token.")
            return None

        client_id = settings.GOOGLE_CLIENT_ID.strip()
        client_secret = settings.GOOGLE_CLIENT_SECRET.strip()
        if not client_id or not client_secret:
            logger.error("Missing GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET for YouTube token refresh.")
            return None

        refresh_token = creds["refresh_token"]
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    "https://oauth2.googleapis.com/token",
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    data={
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "refresh_token": refresh_token,
                        "grant_type": "refresh_token",
                    },
                )
                if resp.status_code == 200:
                    token_data = resp.json()
                    new_token = token_data.get("access_token")
                    expires_in = token_data.get("expires_in", 3600)
                    expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=expires_in)

                    await credential_service.save_connection(
                        platform="youtube",
                        handle=creds.get("handle") or creds.get("account_name") or "YouTube Channel",
                        access_token=new_token,
                        refresh_token=refresh_token,
                        account_id=creds.get("account_id"),
                        account_name=creds.get("account_name"),
                        token_expires_at=expires_at,
                        metadata=creds.get("metadata") or {},
                    )
                    logger.info("Successfully refreshed and persisted new YouTube OAuth access token.")
                    return new_token
                else:
                    logger.error(f"Failed to refresh YouTube token (HTTP {resp.status_code}): {resp.text}")
        except Exception as e:
            logger.error(f"Error refreshing YouTube access token: {e}")
        return None

    async def validate_connection(self) -> bool:
        """
        Validates YouTube connection by querying the authenticated channel.
        Auto-refreshes token if expired.
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
                if resp.status_code == 200:
                    return True
                elif resp.status_code == 401:
                    # Token expired; attempt automatic refresh
                    new_token = await self._refresh_access_token()
                    if new_token:
                        retry_resp = await client.get(
                            f"{self.API_BASE_URL}/channels",
                            params={"part": "snippet", "mine": "true"},
                            headers={"Authorization": f"Bearer {new_token}"}
                        )
                        return retry_resp.status_code == 200
                return False
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
                error_message="YouTube publishing requires a video file (.mp4, .webm). Text-only and image-only uploads are not supported by YouTube.",
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

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                # Resolve video binary data & content type
                video_bytes: Optional[bytes] = None
                content_type = "video/mp4"

                if media_url.startswith("data:"):
                    header, encoded = media_url.split(",", 1)
                    mime = header.split(";")[0].replace("data:", "").strip()
                    if mime:
                        content_type = mime
                    video_bytes = base64.b64decode(encoded)
                elif media_url.startswith("http://") or media_url.startswith("https://"):
                    dl_resp = await client.get(media_url)
                    if dl_resp.status_code == 200:
                        video_bytes = dl_resp.content
                        ct = dl_resp.headers.get("content-type")
                        if ct:
                            content_type = ct.split(";")[0].strip()
                    else:
                        return PlatformResult(
                            platform=self.platform_name,
                            status="failed",
                            error_message=f"Failed to fetch video for YouTube from URL (HTTP {dl_resp.status_code}).",
                        )

                if not video_bytes:
                    return PlatformResult(
                        platform=self.platform_name,
                        status="failed",
                        error_message="Could not resolve video binary data for YouTube upload.",
                    )

                # Initiate Resumable Upload Session
                init_headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json; charset=UTF-8",
                    "X-Upload-Content-Type": content_type,
                }
                init_resp = await client.post(
                    self.UPLOAD_BASE_URL,
                    params={"uploadType": "resumable", "part": "snippet,status"},
                    headers=init_headers,
                    json=metadata,
                )

                # Check for 401 and attempt token refresh
                if init_resp.status_code == 401:
                    new_token = await self._refresh_access_token()
                    if new_token:
                        token = new_token
                        init_headers["Authorization"] = f"Bearer {token}"
                        init_resp = await client.post(
                            self.UPLOAD_BASE_URL,
                            params={"uploadType": "resumable", "part": "snippet,status"},
                            headers=init_headers,
                            json=metadata,
                        )

                if init_resp.status_code in (200, 201):
                    upload_url = init_resp.headers.get("Location")
                    if upload_url:
                        # Upload video bytes to resumable session URL
                        upload_finish_resp = await client.put(
                            upload_url,
                            headers={
                                "Content-Type": content_type,
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
                        else:
                            return PlatformResult(
                                platform=self.platform_name,
                                status="failed",
                                error_message=f"YouTube video payload upload failed (HTTP {upload_finish_resp.status_code}): {upload_finish_resp.text}",
                            )

                    # Direct completion without separate session
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
