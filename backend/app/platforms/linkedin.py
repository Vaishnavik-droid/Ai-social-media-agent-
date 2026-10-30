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

    async def validate_connection(self) -> bool:
        token = settings.LINKEDIN_ACCESS_TOKEN.strip()
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

    async def publish_post(
        self,
        content: str,
        media_url: Optional[str] = None,
        dry_run: bool = False
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
        token = settings.LINKEDIN_ACCESS_TOKEN.strip()
        author_urn = settings.LINKEDIN_AUTHOR_URN.strip()

        if not token:
            return PlatformResult(
                platform=self.platform_name,
                status="failed",
                error_message="Missing LINKEDIN_ACCESS_TOKEN in backend/.env",
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
                error_message="Missing valid LINKEDIN_AUTHOR_URN (e.g. urn:li:person:... or urn:li:organization:...) in backend/.env",
            )

        payload = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": content
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
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
                        error_message="LinkedIn access token expired or invalid (HTTP 401). Please update LINKEDIN_ACCESS_TOKEN.",
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
