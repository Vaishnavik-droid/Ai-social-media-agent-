import base64
import datetime
import logging
from typing import Optional, List, Dict, Any
import httpx

from app.core.config import settings
from app.platforms.base import BasePlatformAdapter
from app.schemas.publishing import PlatformResult

logger = logging.getLogger(__name__)


class PinterestAdapter(BasePlatformAdapter):
    API_BASE_URL = "https://api.pinterest.com/v5"

    @property
    def platform_name(self) -> str:
        return "pinterest"

    async def _resolve_credentials(self) -> tuple[str, str]:
        """
        Retrieves active access token and account/user ID from CredentialService.
        """
        from app.services.credential_service import credential_service
        creds = await credential_service.get_credentials("pinterest")
        if creds and creds.get("access_token"):
            return creds["access_token"], creds.get("account_id") or ""
        return "", ""

    async def _refresh_access_token(self) -> Optional[str]:
        """
        Refreshes Pinterest OAuth access token using refresh_token and basic auth.
        """
        from app.services.credential_service import credential_service
        creds = await credential_service.get_credentials("pinterest")
        if not creds or not creds.get("refresh_token"):
            logger.warning("No refresh token available to refresh Pinterest access token.")
            return None

        app_id = settings.PINTEREST_APP_ID.strip()
        app_secret = settings.PINTEREST_APP_SECRET.strip()
        if not app_id or not app_secret:
            logger.error("Missing PINTEREST_APP_ID or PINTEREST_APP_SECRET for Pinterest token refresh.")
            return None

        refresh_token = creds["refresh_token"]
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    f"{self.API_BASE_URL}/oauth/token",
                    auth=(app_id, app_secret),
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token,
                    },
                )
                if resp.status_code == 200:
                    token_data = resp.json()
                    new_token = token_data.get("access_token")
                    new_refresh = token_data.get("refresh_token") or refresh_token
                    expires_in = token_data.get("expires_in", 2592000)
                    expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=expires_in)

                    await credential_service.save_connection(
                        platform="pinterest",
                        handle=creds.get("handle") or creds.get("account_name") or "Pinterest Account",
                        access_token=new_token,
                        refresh_token=new_refresh,
                        account_id=creds.get("account_id"),
                        account_name=creds.get("account_name"),
                        token_expires_at=expires_at,
                        metadata=creds.get("metadata") or {},
                    )
                    logger.info("Successfully refreshed and persisted new Pinterest OAuth access token.")
                    return new_token
                else:
                    logger.error(f"Failed to refresh Pinterest token (HTTP {resp.status_code}): {resp.text}")
        except Exception as e:
            logger.error(f"Error refreshing Pinterest access token: {e}")
        return None

    async def validate_connection(self) -> bool:
        """
        Validates Pinterest connection by querying authenticated user account.
        Auto-refreshes token if expired.
        """
        token, _ = await self._resolve_credentials()
        if not token:
            return False

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(
                    f"{self.API_BASE_URL}/user_account",
                    headers={"Authorization": f"Bearer {token}"}
                )
                if resp.status_code == 200:
                    return True
                elif resp.status_code == 401:
                    new_token = await self._refresh_access_token()
                    if new_token:
                        retry_resp = await client.get(
                            f"{self.API_BASE_URL}/user_account",
                            headers={"Authorization": f"Bearer {new_token}"}
                        )
                        return retry_resp.status_code == 200
                return False
            except Exception as e:
                logger.error(f"Pinterest connection validation failed: {e}")
                return False

    async def get_boards(self) -> List[Dict[str, Any]]:
        """
        Retrieves user's Pinterest boards for pin placement.
        """
        token, _ = await self._resolve_credentials()
        if not token:
            return []

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(
                    f"{self.API_BASE_URL}/boards",
                    headers={"Authorization": f"Bearer {token}"}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    items = data.get("items", [])
                    return [{"id": b["id"], "name": b["name"]} for b in items]
                elif resp.status_code == 401:
                    new_token = await self._refresh_access_token()
                    if new_token:
                        retry_resp = await client.get(
                            f"{self.API_BASE_URL}/boards",
                            headers={"Authorization": f"Bearer {new_token}"}
                        )
                        if retry_resp.status_code == 200:
                            data = retry_resp.json()
                            items = data.get("items", [])
                            return [{"id": b["id"], "name": b["name"]} for b in items]
            except Exception as e:
                logger.error(f"Error fetching Pinterest boards: {e}")
        return []

    async def publish_post(
        self,
        content: str,
        media_url: Optional[str] = None,
        dry_run: bool = False,
        **kwargs
    ) -> PlatformResult:
        # 1. Validation: Pinterest description limit is 500 characters
        if len(content) > 500:
            return PlatformResult(
                platform=self.platform_name,
                status="failed",
                error_message=f"Pin description exceeds Pinterest limit of 500 characters (current: {len(content)}).",
            )

        # 2. Dry-Run / Mock Publishing Mode
        if dry_run:
            simulated_id = f"mock_pin_{int(datetime.datetime.now().timestamp())}"
            return PlatformResult(
                platform=self.platform_name,
                status="published",
                remote_post_id=simulated_id,
                remote_post_url=f"https://www.pinterest.com/pin/{simulated_id}/",
                is_mock=True,
                error_message=None,
            )

        # 3. Live Pinterest API Dispatch
        token, _ = await self._resolve_credentials()
        if not token:
            return PlatformResult(
                platform=self.platform_name,
                status="failed",
                error_message="Missing Pinterest credentials. Please connect your Pinterest account in Platforms.",
            )

        # Pinterest Pins strictly require an image or video URL
        if not media_url:
            return PlatformResult(
                platform=self.platform_name,
                status="failed",
                error_message="Pinterest Pins require an image or video URL. Please upload or provide an image.",
            )

        # Resolve relative public URLs into fully qualified public HTTPS URLs
        if media_url.startswith("/"):
            media_url = f"https://ai-social-media-agent-phi.vercel.app{media_url}"

        # Resilient handling of data: URLs by uploading to public Supabase Storage
        if media_url.startswith("data:"):
            try:
                from app.api.v1.routes.media import _upload_to_supabase
                header, encoded = media_url.split(",", 1)
                mime = header.split(";")[0].replace("data:", "").strip() or "image/jpeg"
                ext = "jpg" if "jpeg" in mime or "jpg" in mime else "png"
                file_bytes = base64.b64decode(encoded)
                supabase_url = _upload_to_supabase(file_bytes, f"pin_upload.{ext}", mime)
                if supabase_url:
                    logger.info(f"Auto-uploaded Pinterest data URL to Supabase: {supabase_url}")
                    media_url = supabase_url
                else:
                    return PlatformResult(
                        platform=self.platform_name,
                        status="failed",
                        error_message="Pinterest requires a publicly accessible image URL (http/https). Local browser file uploads cannot be fetched by Pinterest.",
                    )
            except Exception as e:
                logger.warning(f"Failed to auto-upload data URL for Pinterest: {e}")
                return PlatformResult(
                    platform=self.platform_name,
                    status="failed",
                    error_message="Pinterest requires a publicly accessible image URL (http/https).",
                )

        # Determine destination board ID
        board_id = kwargs.get("board_id")
        if not board_id:
            boards = await self.get_boards()
            if boards:
                board_id = boards[0]["id"]
            else:
                return PlatformResult(
                    platform=self.platform_name,
                    status="failed",
                    error_message="No Pinterest boards found on this account. Please create at least one board on Pinterest before creating pins.",
                )

        title = kwargs.get("title") or content[:100].strip()
        link = kwargs.get("destination_url") or kwargs.get("link")

        payload = {
            "title": title,
            "description": content,
            "board_id": board_id,
            "media_source": {
                "source_type": "image_url",
                "url": media_url,
            }
        }
        if link:
            payload["link"] = link

        async with httpx.AsyncClient(timeout=25.0) as client:
            try:
                resp = await client.post(
                    f"{self.API_BASE_URL}/pins",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )

                if resp.status_code == 401:
                    new_token = await self._refresh_access_token()
                    if new_token:
                        token = new_token
                        resp = await client.post(
                            f"{self.API_BASE_URL}/pins",
                            headers={
                                "Authorization": f"Bearer {token}",
                                "Content-Type": "application/json",
                            },
                            json=payload,
                        )

                if resp.status_code in (200, 201):
                    data = resp.json()
                    pin_id = data.get("id", f"pin_{int(datetime.datetime.now().timestamp())}")
                    return PlatformResult(
                        platform=self.platform_name,
                        status="published",
                        remote_post_id=pin_id,
                        remote_post_url=f"https://www.pinterest.com/pin/{pin_id}/",
                        is_mock=False,
                        error_message=None,
                    )
                else:
                    err_msg = f"Pinterest API Error (HTTP {resp.status_code})"
                    try:
                        err_json = resp.json()
                        msg = err_json.get("message")
                        if msg:
                            err_msg = f"Pinterest: {msg}"
                    except Exception:
                        pass
                    return PlatformResult(
                        platform=self.platform_name,
                        status="failed",
                        error_message=err_msg,
                    )
            except Exception as e:
                logger.exception(f"Error publishing Pin to Pinterest: {e}")
                return PlatformResult(
                    platform=self.platform_name,
                    status="failed",
                    error_message=f"Network error communicating with Pinterest API: {str(e)}",
                )


pinterest_adapter = PinterestAdapter()
