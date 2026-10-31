import base64
import datetime
import logging
from typing import Optional
import httpx

from app.core.config import settings
from app.platforms.base import BasePlatformAdapter
from app.schemas.publishing import PlatformResult

logger = logging.getLogger(__name__)


class LinkedInAdapter(BasePlatformAdapter):
    BASE_URL = "https://api.linkedin.com/v2"

    @property
    def platform_name(self) -> str:
        return "linkedin"

    async def _resolve_credentials(self) -> tuple[str, str]:
        from app.services.credential_service import credential_service
        creds = await credential_service.get_credentials("linkedin")
        if creds and creds.get("access_token"):
            return creds["access_token"], creds.get("account_id") or settings.LINKEDIN_AUTHOR_URN.strip()
        return settings.LINKEDIN_ACCESS_TOKEN.strip(), settings.LINKEDIN_AUTHOR_URN.strip()

    async def validate_connection(self) -> bool:
        token, _ = await self._resolve_credentials()
        if not token:
            return False

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(
                    f"{self.BASE_URL}/userinfo",
                    headers={"Authorization": f"Bearer {token}"},
                )
                return resp.status_code == 200
            except Exception as e:
                logger.error(f"LinkedIn connection validation failed: {e}")
                return False

    async def _upload_image_asset(self, client: httpx.AsyncClient, token: str, author_urn: str, media_url: str) -> Optional[str]:
        """
        Uploads image to LinkedIn Assets API and returns digitalmediaAsset URN.
        """
        try:
            # 1. Resolve image bytes
            image_bytes: Optional[bytes] = None
            if media_url.startswith("data:"):
                header, encoded = media_url.split(",", 1)
                image_bytes = base64.b64decode(encoded)
            elif media_url.startswith("http://") or media_url.startswith("https://"):
                dl_resp = await client.get(media_url)
                if dl_resp.status_code == 200:
                    image_bytes = dl_resp.content

            if not image_bytes:
                return None

            # 2. Register upload request
            register_payload = {
                "registerUploadRequest": {
                    "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                    "owner": author_urn,
                    "serviceRelationships": [
                        {
                            "relationshipType": "OWNER",
                            "identifier": "urn:li:userGeneratedContent"
                        }
                    ]
                }
            }

            reg_resp = await client.post(
                f"{self.BASE_URL}/assets?action=registerUpload",
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Restli-Protocol-Version": "2.0.0",
                    "Content-Type": "application/json",
                },
                json=register_payload,
            )

            if reg_resp.status_code not in (200, 201):
                logger.warning(f"LinkedIn asset registerUpload failed (HTTP {reg_resp.status_code}): {reg_resp.text}")
                return None

            reg_data = reg_resp.json().get("value", {})
            asset_urn = reg_data.get("asset")
            upload_mech = reg_data.get("uploadMechanism", {})
            http_mech = upload_mech.get("com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest", {})
            upload_url = http_mech.get("uploadUrl")

            if not asset_urn or not upload_url:
                return None

            # 3. Binary upload to upload_url
            upload_resp = await client.put(
                upload_url,
                headers={
                    "Authorization": f"Bearer {token}",
                },
                content=image_bytes,
            )

            if upload_resp.status_code in (200, 201):
                logger.info(f"Successfully uploaded image asset to LinkedIn: {asset_urn}")
                return asset_urn
            else:
                logger.warning(f"LinkedIn binary image upload failed: HTTP {upload_resp.status_code}")
                return None
        except Exception as e:
            logger.warning(f"Error uploading LinkedIn image asset: {e}")
            return None

    async def publish_post(
        self,
        content: str,
        media_url: Optional[str] = None,
        dry_run: bool = False,
        **kwargs
    ) -> PlatformResult:
        # 1. Validation
        if len(content) > 3000:
            return PlatformResult(
                platform=self.platform_name,
                status="failed",
                error_message=f"Post text exceeds LinkedIn limit of 3,000 characters (current length: {len(content)}).",
            )

        # 2. Dry-Run / Mock Publishing Mode
        if dry_run:
            simulated_urn = f"urn:li:share:mock_{int(datetime.datetime.now().timestamp())}"
            return PlatformResult(
                platform=self.platform_name,
                status="published",
                remote_post_id=simulated_urn,
                remote_post_url=f"https://www.linkedin.com/feed/update/{simulated_urn}",
                is_mock=True,
                error_message=None,
            )

        # 3. Live LinkedIn Dispatch
        token, author_urn = await self._resolve_credentials()

        if not token:
            return PlatformResult(
                platform=self.platform_name,
                status="failed",
                error_message="Missing LINKEDIN_ACCESS_TOKEN. Please connect your LinkedIn account in Platforms.",
            )

        # Auto-resolve author URN if missing urn:li prefix
        if token and (not author_urn or not author_urn.startswith("urn:li:")):
            try:
                async with httpx.AsyncClient(timeout=10.0) as uclient:
                    u_resp = await uclient.get(
                        f"{self.BASE_URL}/userinfo",
                        headers={"Authorization": f"Bearer {token}"}
                    )
                    if u_resp.status_code == 200:
                        sub = u_resp.json().get("sub")
                        if sub:
                            author_urn = f"urn:li:person:{sub}"
            except Exception as e:
                logger.warning(f"Failed to auto-resolve LinkedIn URN from /userinfo: {e}")

        if not author_urn or not author_urn.startswith("urn:li:"):
            return PlatformResult(
                platform=self.platform_name,
                status="failed",
                error_message="Missing valid LinkedIn author URN (e.g. urn:li:person:... or urn:li:organization:...). Please reconnect LinkedIn in Platforms.",
            )

        # Resolve relative public URLs into fully qualified public HTTPS URLs
        if media_url and media_url.startswith("/"):
            media_url = f"https://ai-social-media-agent-phi.vercel.app{media_url}"

        async with httpx.AsyncClient(timeout=25.0) as client:
            try:
                # Check for image asset upload
                share_category = "NONE"
                media_list = []
                if media_url:
                    asset_urn = await self._upload_image_asset(client, token, author_urn, media_url)
                    if asset_urn:
                        share_category = "IMAGE"
                        media_list = [
                            {
                                "status": "READY",
                                "description": {"text": content[:100].strip() or "OmniPulse Post"},
                                "media": asset_urn,
                                "title": {"text": "OmniPulse Image"}
                            }
                        ]

                share_content = {
                    "shareCommentary": {
                        "text": content
                    },
                    "shareMediaCategory": share_category
                }
                if media_list:
                    share_content["media"] = media_list

                payload = {
                    "author": author_urn,
                    "lifecycleState": "PUBLISHED",
                    "specificContent": {
                        "com.linkedin.ugc.ShareContent": share_content
                    },
                    "visibility": {
                        "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                    }
                }

                resp = await client.post(
                    f"{self.BASE_URL}/ugcPosts",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "X-Restli-Protocol-Version": "2.0.0",
                        "Content-Type": "application/json"
                    },
                    json=payload
                )

                if resp.status_code in (200, 201):
                    data = resp.json()
                    post_urn = data.get("id")
                    return PlatformResult(
                        platform=self.platform_name,
                        status="published",
                        remote_post_id=post_urn,
                        remote_post_url=f"https://www.linkedin.com/feed/update/{post_urn}" if post_urn else None,
                        is_mock=False,
                    )
                elif resp.status_code == 401:
                    return PlatformResult(
                        platform=self.platform_name,
                        status="failed",
                        error_message="LinkedIn access token expired or invalid (HTTP 401). Please reconnect LinkedIn in Platforms.",
                    )
                elif resp.status_code == 403:
                    return PlatformResult(
                        platform=self.platform_name,
                        status="failed",
                        error_message="Insufficient LinkedIn permissions (HTTP 403). Requires 'w_member_social' or 'w_organization_social'.",
                    )
                elif resp.status_code == 429:
                    return PlatformResult(
                        platform=self.platform_name,
                        status="failed",
                        error_message="LinkedIn API rate limit reached (HTTP 429). Please wait before publishing again.",
                    )
                else:
                    return PlatformResult(
                        platform=self.platform_name,
                        status="failed",
                        error_message=f"LinkedIn returned HTTP {resp.status_code}: {resp.text}",
                    )
            except Exception as e:
                return PlatformResult(
                    platform=self.platform_name,
                    status="failed",
                    error_message=f"Error publishing to LinkedIn: {str(e)}",
                )


linkedin_adapter = LinkedInAdapter()
