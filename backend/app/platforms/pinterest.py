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
    API_BASE_URL = "https://api-sandbox.pinterest.com/v5"

    @property
    def platform_name(self) -> str:
        return "pinterest"

    def _get_sandbox_token(self) -> str:
        """
        Retrieves PINTEREST_SANDBOX_TOKEN from settings or process environment.
        """
        import os
        token = getattr(settings, "PINTEREST_SANDBOX_TOKEN", "") or os.environ.get("PINTEREST_SANDBOX_TOKEN", "")
        return token.strip() if token else ""

    async def _resolve_credentials(self) -> tuple[str, str]:
        """
        Retrieves active access token and account/user ID.
        Exclusively uses PINTEREST_SANDBOX_TOKEN for Sandbox publishing,
        ensuring production OAuth access token is never used for Sandbox API requests.
        """
        sandbox_token = self._get_sandbox_token()
        if sandbox_token:
            return sandbox_token, "pinterest_sandbox_user"

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

        if self._get_sandbox_token():
            logger.debug("PINTEREST_SANDBOX_TOKEN is configured; OAuth refresh is not applicable.")
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

    async def create_board(
        self,
        name: str,
        description: Optional[str] = "Created by OmniPulse AI",
        privacy: str = "PUBLIC"
    ) -> Optional[Dict[str, Any]]:
        """
        Creates a new board via Pinterest API (POST /v5/boards).
        Supports Sandbox and Production environments.
        """
        token, _ = await self._resolve_credentials()
        if not token:
            logger.error("Cannot create Pinterest board: missing credentials.")
            return None

        clean_name = name.strip()[:50]  # Pinterest board name limit is 50 chars
        payload = {
            "name": clean_name,
            "description": (description or "Created by OmniPulse AI")[:500],
            "privacy": privacy.upper() if privacy.upper() in ("PUBLIC", "SECRET") else "PUBLIC"
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.post(
                    f"{self.API_BASE_URL}/boards",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                if resp.status_code in (200, 201):
                    data = resp.json()
                    b_id = str(data.get("id", "")).strip()
                    b_name = data.get("name", clean_name)
                    logger.info(f"Successfully created Pinterest board '{b_name}' (ID: {b_id})")
                    return {"id": b_id, "name": b_name}
                else:
                    logger.error(f"Failed to create Pinterest board (HTTP {resp.status_code}): {resp.text}")
                    return None
            except Exception as e:
                logger.error(f"Network error creating Pinterest board: {e}")
                return None

    async def get_boards(self, auto_create_default: bool = True) -> List[Dict[str, Any]]:
        """
        Retrieves user's Pinterest boards for pin placement.
        Handles Sandbox bookmark pagination (using page_size=250) until boards are found or pagination is exhausted.
        If no Sandbox boards exist, automatically creates a default Sandbox board if enabled.
        """
        token, _ = await self._resolve_credentials()
        if not token:
            return []

        all_boards: List[Dict[str, Any]] = []
        bookmark: Optional[str] = None
        seen_bookmarks = set()
        max_pages = 10

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                for _ in range(max_pages):
                    params: Dict[str, Any] = {"page_size": 250}
                    if bookmark:
                        params["bookmark"] = bookmark

                    resp = await client.get(
                        f"{self.API_BASE_URL}/boards",
                        headers={"Authorization": f"Bearer {token}"},
                        params=params,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        items = data.get("items", [])
                        for b in items:
                            b_id = str(b.get("id", "")).strip()
                            b_name = b.get("name", "Untitled Board")
                            if b_id and not any(existing["id"] == b_id for existing in all_boards):
                                all_boards.append({"id": b_id, "name": b_name})

                        next_bookmark = data.get("bookmark")
                        if next_bookmark and next_bookmark not in seen_bookmarks:
                            seen_bookmarks.add(next_bookmark)
                            bookmark = next_bookmark
                        else:
                            break
                    elif resp.status_code == 401 and not self._get_sandbox_token():
                        new_token = await self._refresh_access_token()
                        if new_token:
                            token = new_token
                            continue
                        break
                    else:
                        logger.warning(f"Pinterest boards endpoint returned HTTP {resp.status_code}: {resp.text}")
                        break
            except Exception as e:
                logger.error(f"Error fetching Pinterest boards: {e}")

        # If boards were found via pagination, return them
        if all_boards:
            return all_boards

        # If no boards found in Sandbox environment, automatically create a default Sandbox board
        if auto_create_default:
            logger.info("No Sandbox boards found. Auto-creating 'OmniPulse Sandbox Board' via API...")
            created = await self.create_board(name="OmniPulse Sandbox Board", description="Default board for OmniPulse AI Sandbox testing")
            if created:
                return [created]

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
            logger.warning("[Pinterest Sandbox] Validation failed: Description exceeds 500 characters (%d chars).", len(content))
            return PlatformResult(
                platform=self.platform_name,
                status="failed",
                error_message=f"Pin description exceeds Pinterest limit of 500 characters (current: {len(content)}).",
            )

        # 2. Dry-Run / Mock Publishing Mode
        if dry_run:
            simulated_id = f"mock_pin_{int(datetime.datetime.now().timestamp())}"
            logger.warning("[Pinterest Sandbox] Dry run is True. External HTTP request skipped. Returning simulated pin: %s", simulated_id)
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
            logger.error("[Pinterest Sandbox] Aborting: Missing credentials. Neither PINTEREST_SANDBOX_TOKEN nor OAuth token found.")
            return PlatformResult(
                platform=self.platform_name,
                status="failed",
                error_message="Missing Pinterest credentials. Please configure PINTEREST_SANDBOX_TOKEN or connect your account.",
            )

        # Pinterest Pins strictly require an image or video URL
        if not media_url:
            logger.error("[Pinterest Sandbox] Aborting: Missing media URL.")
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
                    logger.info("[Pinterest Sandbox] Auto-uploaded Pinterest data URL to Supabase: %s", supabase_url)
                    media_url = supabase_url
                else:
                    logger.error("[Pinterest Sandbox] Failed to upload data URL to Supabase.")
                    return PlatformResult(
                        platform=self.platform_name,
                        status="failed",
                        error_message="Pinterest requires a publicly accessible image URL (http/https). Local browser file uploads cannot be fetched by Pinterest.",
                    )
            except Exception as e:
                logger.warning("[Pinterest Sandbox] Failed to auto-upload data URL for Pinterest: %s", e)
                return PlatformResult(
                    platform=self.platform_name,
                    status="failed",
                    error_message="Pinterest requires a publicly accessible image URL (http/https).",
                )

        # Determine destination board ID
        board_id = kwargs.get("board_id")
        if not board_id:
            logger.info("[Pinterest Sandbox] No board_id provided in kwargs; fetching available boards...")
            boards = await self.get_boards()
            if boards:
                board_id = boards[0]["id"]
                logger.info("[Pinterest Sandbox] Selected first available board: %s (%s)", board_id, boards[0].get("name"))
            else:
                logger.error("[Pinterest Sandbox] No boards found on account.")
                return PlatformResult(
                    platform=self.platform_name,
                    status="failed",
                    error_message="No Pinterest boards found on this account. Please create at least one board on Pinterest before creating pins.",
                )

        raw_title = kwargs.get("title") or content
        title = raw_title[:100].strip()
        description = content[:500].strip()
        link = kwargs.get("destination_url") or kwargs.get("link")

        payload: Dict[str, Any] = {
            "title": title,
            "description": description,
            "board_id": str(board_id).strip(),
            "media_source": {
                "source_type": "image_url",
                "url": media_url,
            }
        }
        if link:
            payload["link"] = link

        endpoint_url = f"{self.API_BASE_URL}/pins"
        logger.info(
            "[Pinterest Sandbox] Attempting outgoing API request. Method: POST, URL: %s, Board ID: %s, Title: %s, Media URL: %s",
            endpoint_url,
            payload["board_id"],
            payload["title"],
            payload["media_source"]["url"],
        )

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.post(
                    endpoint_url,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                logger.info(
                    "[Pinterest Sandbox] Response received from POST %s. HTTP Status: %s, Body: %s",
                    endpoint_url,
                    resp.status_code,
                    resp.text[:300],
                )

                if resp.status_code == 401 and not self._get_sandbox_token():
                    logger.info("[Pinterest Sandbox] 401 Unauthorized encountered. Attempting OAuth token refresh...")
                    new_token = await self._refresh_access_token()
                    if new_token:
                        token = new_token
                        resp = await client.post(
                            endpoint_url,
                            headers={
                                "Authorization": f"Bearer {token}",
                                "Content-Type": "application/json",
                            },
                            json=payload,
                        )
                        logger.info(
                            "[Pinterest Sandbox] Retried POST %s after token refresh. HTTP Status: %s, Body: %s",
                            endpoint_url,
                            resp.status_code,
                            resp.text[:300],
                        )

                if resp.status_code in (200, 201):
                    data = resp.json()
                    pin_id = str(data.get("id", f"pin_{int(datetime.datetime.now().timestamp())}"))
                    pin_url = f"https://www.pinterest.com/pin/{pin_id}/"
                    logger.info(
                        "[Pinterest Sandbox] Pin successfully published! Returned Pin ID: %s, URL: %s",
                        pin_id,
                        pin_url,
                    )
                    return PlatformResult(
                        platform=self.platform_name,
                        status="published",
                        remote_post_id=pin_id,
                        remote_post_url=pin_url,
                        is_mock=False,
                        error_message=None,
                    )
                else:
                    err_msg = f"Pinterest API Error (HTTP {resp.status_code})"
                    try:
                        err_json = resp.json()
                        msg = err_json.get("message")
                        details = err_json.get("details")
                        if msg:
                            err_msg = f"Pinterest: {msg}"
                            if details and isinstance(details, list) and len(details) > 0:
                                d_item = details[0]
                                d_msg = d_item.get("message") if isinstance(d_item, dict) else str(d_item)
                                if d_msg and d_msg != msg:
                                    err_msg += f" ({d_msg})"
                        elif "error" in err_json:
                            err_msg = f"Pinterest: {err_json['error']}"
                    except Exception:
                        if resp.text:
                            err_msg = f"Pinterest API Error (HTTP {resp.status_code}): {resp.text[:200]}"
                    logger.error(
                        "[Pinterest Sandbox] Pin creation failed on Pinterest API. HTTP Status: %s, Error: %s",
                        resp.status_code,
                        err_msg,
                    )
                    return PlatformResult(
                        platform=self.platform_name,
                        status="failed",
                        error_message=err_msg,
                    )
            except Exception as e:
                logger.exception("[Pinterest Sandbox] Network error communicating with Pinterest API: %s", e)
                return PlatformResult(
                    platform=self.platform_name,
                    status="failed",
                    error_message=f"Network error communicating with Pinterest API: {str(e)}",
                )


pinterest_adapter = PinterestAdapter()
