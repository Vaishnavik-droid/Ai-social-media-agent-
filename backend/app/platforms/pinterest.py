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

    async def validate_connection(self) -> bool:
        """
        Validates Pinterest connection by querying authenticated user account.
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
                return resp.status_code == 200
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
                error_message="Pinterest Pins require an image or video URL. Please upload or provide a media URL.",
            )

        # Determine destination board ID
        board_id = kwargs.get("board_id")
        if not board_id:
            boards = await self.get_boards()
            if boards:
                board_id = boards[0]["id"]
            else:
                board_id = "default"

        title = kwargs.get("title") or content[:100].strip()
        link = kwargs.get("destination_url") or kwargs.get("link")

        # Resolve relative public URLs into fully qualified public HTTPS URLs
        if media_url.startswith("/"):
            media_url = f"https://ai-social-media-agent-phi.vercel.app{media_url}"

        # Construct payload according to Pinterest v5 API
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

        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
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
                    err_text = resp.text
                    logger.error(f"Pinterest Pin creation failed: {resp.status_code} - {err_text}")
                    return PlatformResult(
                        platform=self.platform_name,
                        status="failed",
                        error_message=f"Pinterest API Error ({resp.status_code}): {err_text}",
                    )
            except Exception as e:
                logger.exception(f"Error publishing Pin to Pinterest: {e}")
                return PlatformResult(
                    platform=self.platform_name,
                    status="failed",
                    error_message=f"Network error communicating with Pinterest API: {str(e)}",
                )


pinterest_adapter = PinterestAdapter()
