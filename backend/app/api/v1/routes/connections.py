import datetime
import html
import logging
import secrets
from typing import Optional
from urllib.parse import quote, urlparse
from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse
import httpx

from app.core.config import settings
from app.platforms.bluesky import bluesky_adapter
from app.platforms.facebook import facebook_adapter
from app.platforms.instagram import instagram_adapter
from app.platforms.linkedin import linkedin_adapter
from app.platforms.pinterest import pinterest_adapter
from app.platforms.youtube import youtube_adapter
from app.schemas.connection import (
    BlueskyConnectRequest,
    ConnectionDisconnectResponse,
    ConnectionItem,
    ConnectionListResponse,
    ConnectionVerifyRequest,
    ConnectionVerifyResponse,
    LinkedInConnectRequest,
    MetaAuthorizeRequest,
    MetaAuthorizeResponse,
    OAuthAuthorizeRequest,
    OAuthAuthorizeResponse,
)
from app.services.credential_service import credential_service

logger = logging.getLogger("omnipulse.routes.connections")
router = APIRouter(prefix="/connections", tags=["Connections"])


def _sanitize_origin(origin: Optional[str]) -> str:
    """Validates and sanitizes the frontend origin for postMessage targetOrigin."""
    if not origin:
        return "http://localhost:3000"
    try:
        parsed = urlparse(origin)
        if parsed.scheme in ("http", "https") and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"
    except Exception:
        pass
    return "http://localhost:3000"


def _render_popup_html(
    success: bool,
    platform: str,
    target_origin: str,
    handle: Optional[str] = None,
    error_message: Optional[str] = None,
) -> HTMLResponse:
    """
    Renders an HTML response designed to execute inside an OAuth popup window.
    Sends a safe postMessage to window.opener with exact targetOrigin and closes.
    """
    safe_origin = _sanitize_origin(target_origin)
    safe_platform = html.escape(platform or "")
    safe_handle = html.escape(handle or "")
    safe_error = html.escape(error_message or "")

    if success:
        title = "Authorization Successful!"
        body_msg = f"Connecting {safe_platform.capitalize()} ({safe_handle})... Closing window."
        msg_payload = f"""{{
            type: "OMNIPULSE_OAUTH_SUCCESS",
            platform: "{safe_platform}",
            status: "connected",
            handle: "{safe_handle}"
        }}"""
    else:
        title = "Authorization Failed"
        body_msg = f"Could not connect {safe_platform.capitalize()}: {safe_error}"
        msg_payload = f"""{{
            type: "OMNIPULSE_OAUTH_ERROR",
            platform: "{safe_platform}",
            status: "error",
            error: "{safe_error}"
        }}"""

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{title} — OmniPulse</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: #0f172a;
      color: #f8fafc;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      margin: 0;
      padding: 20px;
      text-align: center;
    }}
    .card {{
      background: #1e293b;
      border: 1px solid #334155;
      border-radius: 12px;
      padding: 32px 24px;
      max-width: 420px;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
    }}
    .badge {{
      display: inline-block;
      padding: 6px 14px;
      border-radius: 9999px;
      font-size: 13px;
      font-weight: 600;
      margin-bottom: 16px;
      background: {"#065f46; color: #34d399;" if success else "#881337; color: #fb7185;"}
    }}
    h2 {{ margin: 0 0 10px; font-size: 20px; }}
    p {{ color: #94a3b8; font-size: 14px; line-height: 1.5; margin: 0 0 20px; }}
    .close-btn {{
      background: #3b82f6;
      color: white;
      border: none;
      padding: 8px 18px;
      border-radius: 6px;
      font-weight: 500;
      cursor: pointer;
    }}
  </style>
</head>
<body>
  <div class="card">
    <div class="badge">{"✓ Complete" if success else "✕ Error"}</div>
    <h2>{title}</h2>
    <p>{body_msg}</p>
    <button class="close-btn" onclick="window.close()">Close Window</button>
  </div>
  <script>
    (function() {{
      const targetOrigin = "{safe_origin}";
      const message = {msg_payload};
      if (window.opener && !window.opener.closed) {{
        window.opener.postMessage(message, targetOrigin);
        setTimeout(function() {{ window.close(); }}, 1000);
      }} else {{
        setTimeout(function() {{ window.location.href = targetOrigin + "/platforms"; }}, 1500);
      }}
    }})();
  </script>
</body>
</html>"""
    return HTMLResponse(content=html_content, status_code=200 if success else 400)


# =============================================================================
# 1. Platform Connections List (Safe & Token-Free)
# =============================================================================

@router.get("", response_model=ConnectionListResponse)
async def list_connections():
    """
    Returns platform connection statuses safely without ever exposing tokens or secrets.
    """
    connections_data = await credential_service.list_all_connections()
    return ConnectionListResponse(
        connections=[ConnectionItem(**c) for c in connections_data]
    )


# =============================================================================
# 2. Meta OAuth (Facebook & Instagram Centralized Handshake)
# =============================================================================

@router.post("/meta/authorize", response_model=MetaAuthorizeResponse)
async def initiate_meta_authorization(payload: MetaAuthorizeRequest, request: Request):
    """
    Initiates server-side Meta OAuth flow for Facebook or Instagram.
    Generates a cryptographically secure, signed state with expiration.
    Returns the official Facebook dialog authorization URL.
    """
    app_id = settings.META_APP_ID.strip()
    if not app_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Meta App ID is not configured on the backend. Please add META_APP_ID in platform_credentials.env.",
        )

    platform = payload.platform.lower().strip()
    if platform not in ("facebook", "instagram"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Platform must be either 'facebook' or 'instagram'.",
        )

    # Determine callback URI
    if settings.META_REDIRECT_URI:
        callback_uri = settings.META_REDIRECT_URI.strip()
    else:
        # Dynamic callback URL based on incoming request
        base_url = str(request.base_url).rstrip("/")
        callback_uri = f"{base_url}/api/v1/connections/meta/callback"

    # Determine frontend origin for popup postMessage
    origin = _sanitize_origin(payload.redirect_origin or request.headers.get("origin"))

    # Generate secure random state token
    state_id = f"meta_{secrets.token_urlsafe(24)}"
    await credential_service.save_oauth_state(
        state_id=state_id,
        platform=platform,
        redirect_origin=origin,
        expires_in_seconds=600,  # 10 minutes TTL
    )

    # Scopes
    if platform == "instagram":
        scopes = "pages_show_list,pages_read_engagement,instagram_basic,instagram_content_publish,public_profile"
    else:
        scopes = "pages_show_list,pages_read_engagement,pages_manage_posts,public_profile"

    auth_url = (
        f"https://www.facebook.com/v19.0/dialog/oauth"
        f"?client_id={app_id}"
        f"&redirect_uri={quote(callback_uri, safe='')}"
        f"&state={state_id}"
        f"&scope={scopes}"
        f"&response_type=code"
    )

    logger.info(f"Initiated Meta OAuth for '{platform}' with callback '{callback_uri}' and origin '{origin}'.")
    return MetaAuthorizeResponse(
        auth_url=auth_url,
        state=state_id,
        platform=platform,
    )


@router.get("/meta/callback", response_class=HTMLResponse)
async def handle_meta_oauth_callback(
    request: Request,
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None),
):
    """
    Dedicated server-side callback endpoint for Meta OAuth.
    Validates state, exchanges authorization code for long-lived Page/Instagram tokens,
    encrypts and persists credentials in Supabase, and communicates result to parent via postMessage.
    """
    origin = _sanitize_origin(request.headers.get("origin"))

    # 1. Handle error returned by Meta
    if error:
        err_msg = error_description or error
        logger.warning(f"Meta OAuth error returned: {err_msg}")
        return _render_popup_html(
            success=False,
            platform="meta",
            target_origin=origin,
            error_message=err_msg,
        )

    if not code or not state:
        return _render_popup_html(
            success=False,
            platform="meta",
            target_origin=origin,
            error_message="Missing code or state parameters from Meta authorization.",
        )

    # 2. Validate and consume OAuth state
    state_data = await credential_service.verify_and_consume_oauth_state(state)
    if not state_data:
        logger.warning(f"Rejected invalid or expired Meta OAuth state: {state}")
        return _render_popup_html(
            success=False,
            platform="meta",
            target_origin=origin,
            error_message="Invalid or expired OAuth state session. Please re-open the authorization window.",
        )

    platform = state_data.get("platform", "facebook")
    target_origin = state_data.get("redirect_origin") or origin

    app_id = settings.META_APP_ID.strip()
    app_secret = settings.META_APP_SECRET.strip()

    if not app_id or not app_secret:
        return _render_popup_html(
            success=False,
            platform=platform,
            target_origin=target_origin,
            error_message="Server is missing META_APP_ID or META_APP_SECRET in environment variables.",
        )

    # Callback URI must match the exact URI passed during authorization
    if settings.META_REDIRECT_URI:
        callback_uri = settings.META_REDIRECT_URI.strip()
    else:
        base_url = str(request.base_url).rstrip("/")
        callback_uri = f"{base_url}/api/v1/connections/meta/callback"

    graph_base = "https://graph.facebook.com/v19.0"

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            # 3. Exchange authorization code for short-lived User Access Token
            token_resp = await client.get(
                f"{graph_base}/oauth/access_token",
                params={
                    "client_id": app_id,
                    "client_secret": app_secret,
                    "redirect_uri": callback_uri,
                    "code": code,
                },
            )
            token_json = token_resp.json()

            if token_resp.status_code != 200 or "access_token" not in token_json:
                detail = token_json.get("error", {}).get("message", "Token exchange failed with Meta.")
                logger.error(f"Meta token exchange error: {token_json}")
                return _render_popup_html(
                    success=False,
                    platform=platform,
                    target_origin=target_origin,
                    error_message=f"Meta Token Exchange Error: {detail}",
                )

            short_token = token_json["access_token"]

            # 4. Exchange for Long-Lived User Access Token (~60 days)
            long_resp = await client.get(
                f"{graph_base}/oauth/access_token",
                params={
                    "grant_type": "fb_exchange_token",
                    "client_id": app_id,
                    "client_secret": app_secret,
                    "fb_exchange_token": short_token,
                },
            )
            long_json = long_resp.json()
            user_token = long_json.get("access_token") if long_resp.status_code == 200 else short_token

            # 5. Query user's Facebook Pages and connected Instagram Business accounts
            accounts_resp = await client.get(
                f"{graph_base}/me/accounts",
                params={
                    "access_token": user_token,
                    "fields": "id,name,access_token,category,instagram_business_account{id,username,name}",
                },
            )
            accounts_json = accounts_resp.json()
            pages = accounts_json.get("data", [])

            if accounts_resp.status_code != 200 or not pages:
                return _render_popup_html(
                    success=False,
                    platform=platform,
                    target_origin=target_origin,
                    error_message="No Facebook Pages found. You must be an administrator of at least one Facebook Page to publish.",
                )

            # 6. Branch: Facebook vs. Instagram
            if platform == "facebook":
                primary_page = pages[0]
                page_id = str(primary_page["id"])
                page_name = str(primary_page.get("name", f"Page {page_id}"))
                page_token = str(primary_page.get("access_token", user_token))

                await credential_service.save_connection(
                    platform="facebook",
                    handle=page_name,
                    access_token=page_token,
                    account_id=page_id,
                    account_name=page_name,
                    metadata={"page_id": page_id, "page_name": page_name, "category": primary_page.get("category")},
                    scopes="pages_show_list,pages_read_engagement,pages_manage_posts",
                )

                # Connection verification
                is_valid = await facebook_adapter.validate_connection()
                if not is_valid:
                    logger.warning("Facebook connection verification returned false after saving credentials.")

                return _render_popup_html(
                    success=True,
                    platform="facebook",
                    target_origin=target_origin,
                    handle=page_name,
                )

            elif platform == "instagram":
                # Find page with connected Instagram Business Account
                target_page = None
                ig_account = None

                for p in pages:
                    ig_data = p.get("instagram_business_account")
                    if ig_data and ig_data.get("id"):
                        target_page = p
                        ig_account = ig_data
                        break

                if not ig_account or not target_page:
                    return _render_popup_html(
                        success=False,
                        platform="instagram",
                        target_origin=target_origin,
                        error_message="No Instagram Business or Creator account found linked to your Facebook Pages. Please ensure your Instagram profile is a Professional account linked to your Facebook Page in Settings.",
                    )

                ig_id = str(ig_account["id"])
                ig_username = ig_account.get("username", "")
                ig_handle = f"@{ig_username}" if ig_username else f"IG {ig_id}"
                token_to_store = str(target_page.get("access_token", user_token))

                await credential_service.save_connection(
                    platform="instagram",
                    handle=ig_handle,
                    access_token=token_to_store,
                    account_id=ig_id,
                    account_name=ig_username or ig_handle,
                    metadata={
                        "instagram_id": ig_id,
                        "instagram_username": ig_username,
                        "facebook_page_id": target_page.get("id"),
                        "facebook_page_name": target_page.get("name"),
                    },
                    scopes="pages_show_list,pages_read_engagement,instagram_basic,instagram_content_publish",
                )

                # Connection verification
                is_valid = await instagram_adapter.validate_connection()
                if not is_valid:
                    logger.warning("Instagram connection verification returned false after saving credentials.")

                return _render_popup_html(
                    success=True,
                    platform="instagram",
                    target_origin=target_origin,
                    handle=ig_handle,
                )

    except Exception as e:
        logger.error(f"Error during Meta OAuth callback processing: {e}", exc_info=True)
        return _render_popup_html(
            success=False,
            platform=platform,
            target_origin=target_origin,
            error_message=f"Internal authentication error: {str(e)}",
        )



# =============================================================================
# 2B. Pinterest OAuth Endpoints
# =============================================================================

@router.post("/pinterest/authorize", response_model=OAuthAuthorizeResponse)
async def initiate_pinterest_oauth(request: Request, payload: Optional[OAuthAuthorizeRequest] = None):
    app_id = settings.PINTEREST_APP_ID.strip()
    if not app_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pinterest App ID is not configured on the backend. Please add PINTEREST_APP_ID in platform_credentials.env.",
        )

    if settings.PINTEREST_REDIRECT_URI:
        callback_uri = settings.PINTEREST_REDIRECT_URI.strip()
    else:
        base_url = str(request.base_url).rstrip("/")
        callback_uri = f"{base_url}/api/v1/connections/pinterest/callback"

    origin = _sanitize_origin((payload.redirect_origin if payload else None) or request.headers.get("origin"))

    state_id = f"pin_{secrets.token_urlsafe(24)}"
    await credential_service.save_oauth_state(
        state_id=state_id,
        platform="pinterest",
        redirect_origin=origin,
    )

    scopes = "boards:read,boards:write,pins:read,pins:write,user_accounts:read"
    auth_url = (
        f"https://www.pinterest.com/oauth/?"
        f"client_id={quote(app_id)}"
        f"&redirect_uri={quote(callback_uri)}"
        f"&response_type=code"
        f"&scope={quote(scopes)}"
        f"&state={quote(state_id)}"
    )

    return OAuthAuthorizeResponse(
        auth_url=auth_url,
        state=state_id,
        platform="pinterest",
    )


@router.get("/pinterest/callback", response_class=HTMLResponse)
async def pinterest_oauth_callback(
    request: Request,
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None),
):
    target_origin = "http://localhost:3000"
    if error or error_description:
        return _render_popup_html(
            success=False,
            platform="pinterest",
            target_origin=target_origin,
            error_message=error_description or error or "User cancelled Pinterest authorization.",
        )

    if not code or not state:
        return _render_popup_html(
            success=False,
            platform="pinterest",
            target_origin=target_origin,
            error_message="Missing authorization code or session state parameter.",
        )

    state_data = await credential_service.verify_and_consume_oauth_state(state)
    if not state_data:
        return _render_popup_html(
            success=False,
            platform="pinterest",
            target_origin=target_origin,
            error_message="Invalid or expired OAuth state session. Please initiate login again.",
        )

    target_origin = state_data.get("redirect_origin") or target_origin

    app_id = settings.PINTEREST_APP_ID.strip()
    app_secret = settings.PINTEREST_APP_SECRET.strip()
    if not app_id or not app_secret:
        return _render_popup_html(
            success=False,
            platform="pinterest",
            target_origin=target_origin,
            error_message="Pinterest App credentials are not configured on the backend.",
        )

    if settings.PINTEREST_REDIRECT_URI:
        callback_uri = settings.PINTEREST_REDIRECT_URI.strip()
    else:
        base_url = str(request.base_url).rstrip("/")
        callback_uri = f"{base_url}/api/v1/connections/pinterest/callback"

    try:
        import base64
        auth_header = base64.b64encode(f"{app_id}:{app_secret}".encode("utf-8")).decode("utf-8")

        async with httpx.AsyncClient(timeout=20.0) as client:
            token_resp = await client.post(
                "https://api.pinterest.com/v5/oauth/token",
                headers={
                    "Authorization": f"Basic {auth_header}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": callback_uri,
                },
            )

            if token_resp.status_code != 200:
                return _render_popup_html(
                    success=False,
                    platform="pinterest",
                    target_origin=target_origin,
                    error_message=f"Failed to exchange authorization code: {token_resp.text}",
                )

            token_data = token_resp.json()
            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")

            user_resp = await client.get(
                "https://api.pinterest.com/v5/user_account",
                headers={"Authorization": f"Bearer {access_token}"},
            )

            username = "Pinterest Account"
            account_id = None
            if user_resp.status_code == 200:
                user_data = user_resp.json()
                username = user_data.get("username") or user_data.get("id") or username
                account_id = str(user_data.get("id") or username)

            handle = f"@{username.lstrip('@')}"
            await credential_service.save_connection(
                platform="pinterest",
                access_token=access_token,
                refresh_token=refresh_token,
                account_id=account_id or username,
                account_name=handle,
                handle=handle,
                metadata={"token_type": token_data.get("token_type", "bearer")},
            )

            return _render_popup_html(
                success=True,
                platform="pinterest",
                target_origin=target_origin,
                handle=handle,
            )
    except Exception as e:
        logger.error(f"Error during Pinterest OAuth callback processing: {e}", exc_info=True)
        return _render_popup_html(
            success=False,
            platform="pinterest",
            target_origin=target_origin,
            error_message=f"Internal error connecting Pinterest: {str(e)}",
        )


# =============================================================================
# 2C. YouTube OAuth Endpoints
# =============================================================================

@router.post("/youtube/authorize", response_model=OAuthAuthorizeResponse)
async def initiate_youtube_oauth(request: Request, payload: Optional[OAuthAuthorizeRequest] = None):
    client_id = settings.GOOGLE_CLIENT_ID.strip()
    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google Client ID is not configured on the backend. Please add GOOGLE_CLIENT_ID in platform_credentials.env.",
        )

    if settings.YOUTUBE_REDIRECT_URI:
        callback_uri = settings.YOUTUBE_REDIRECT_URI.strip()
    else:
        base_url = str(request.base_url).rstrip("/")
        callback_uri = f"{base_url}/api/v1/connections/youtube/callback"

    origin = _sanitize_origin((payload.redirect_origin if payload else None) or request.headers.get("origin"))

    state_id = f"yt_{secrets.token_urlsafe(24)}"
    await credential_service.save_oauth_state(
        state_id=state_id,
        platform="youtube",
        redirect_origin=origin,
    )

    scopes = "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly"
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={quote(client_id)}"
        f"&redirect_uri={quote(callback_uri)}"
        f"&response_type=code"
        f"&scope={quote(scopes)}"
        f"&access_type=offline"
        f"&prompt=consent"
        f"&state={quote(state_id)}"
    )

    return OAuthAuthorizeResponse(
        auth_url=auth_url,
        state=state_id,
        platform="youtube",
    )


@router.get("/youtube/callback", response_class=HTMLResponse)
async def youtube_oauth_callback(
    request: Request,
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None),
):
    target_origin = "http://localhost:3000"
    if error or error_description:
        return _render_popup_html(
            success=False,
            platform="youtube",
            target_origin=target_origin,
            error_message=error_description or error or "User cancelled Google authorization.",
        )

    if not code or not state:
        return _render_popup_html(
            success=False,
            platform="youtube",
            target_origin=target_origin,
            error_message="Missing authorization code or session state parameter.",
        )

    state_data = await credential_service.get_and_consume_oauth_state(state)
    if not state_data:
        return _render_popup_html(
            success=False,
            platform="youtube",
            target_origin=target_origin,
            error_message="Invalid or expired OAuth state session. Please initiate login again.",
        )

    target_origin = state_data.get("redirect_origin") or target_origin

    client_id = settings.GOOGLE_CLIENT_ID.strip()
    client_secret = settings.GOOGLE_CLIENT_SECRET.strip()
    if not client_id or not client_secret:
        return _render_popup_html(
            success=False,
            platform="youtube",
            target_origin=target_origin,
            error_message="Google/YouTube client credentials are not configured on the backend.",
        )

    if settings.YOUTUBE_REDIRECT_URI:
        callback_uri = settings.YOUTUBE_REDIRECT_URI.strip()
    else:
        base_url = str(request.base_url).rstrip("/")
        callback_uri = f"{base_url}/api/v1/connections/youtube/callback"

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            token_resp = await client.post(
                "https://oauth2.googleapis.com/token",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": callback_uri,
                },
            )

            if token_resp.status_code != 200:
                return _render_popup_html(
                    success=False,
                    platform="youtube",
                    target_origin=target_origin,
                    error_message=f"Failed to exchange Google code: {token_resp.text}",
                )

            token_data = token_resp.json()
            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")

            chan_resp = await client.get(
                "https://www.googleapis.com/youtube/v3/channels",
                params={"part": "snippet", "mine": "true"},
                headers={"Authorization": f"Bearer {access_token}"},
            )

            channel_title = "YouTube Channel"
            channel_id = None
            if chan_resp.status_code == 200:
                items = chan_resp.json().get("items", [])
                if items:
                    snippet = items[0].get("snippet", {})
                    channel_title = snippet.get("title") or channel_title
                    channel_id = items[0].get("id")

            handle = channel_title
            await credential_service.save_connection(
                platform="youtube",
                access_token=access_token,
                refresh_token=refresh_token,
                account_id=channel_id or channel_title,
                account_name=channel_title,
                handle=handle,
                metadata={"token_type": "Bearer"},
            )

            return _render_popup_html(
                success=True,
                platform="youtube",
                target_origin=target_origin,
                handle=handle,
            )
    except Exception as e:
        logger.error(f"Error during YouTube OAuth callback processing: {e}", exc_info=True)
        return _render_popup_html(
            success=False,
            platform="youtube",
            target_origin=target_origin,
            error_message=f"Internal error connecting YouTube: {str(e)}",
        )


@router.get("/pinterest/boards")
async def get_pinterest_boards():
    boards = await pinterest_adapter.get_boards()
    return {"boards": boards}

# =============================================================================
# 3. Direct Platform Connect Endpoints (Bluesky & LinkedIn)
# =============================================================================

@router.post("/bluesky/connect", response_model=ConnectionVerifyResponse)
async def connect_bluesky(payload: BlueskyConnectRequest):
    """
    Connects Bluesky using an App Password. Validates credentials with AT Protocol,
    encrypts the password, and durably persists the connection.
    """
    handle = payload.handle.strip().lstrip("@")
    app_password = payload.app_password.strip()

    if not handle or not app_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bluesky handle and App Password are both required.",
        )

    # Authenticate with AT Protocol
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(
                f"{bluesky_adapter.BSKY_HOST}/xrpc/com.atproto.server.createSession",
                json={"identifier": handle, "password": app_password},
            )
            if resp.status_code != 200:
                return ConnectionVerifyResponse(
                    platform="bluesky",
                    is_valid=False,
                    status="disconnected",
                    message="Invalid Bluesky handle or App Password. Please check credentials in Bluesky Settings -> App Passwords.",
                )

            session = resp.json()
            did = session.get("did")
            user_handle = f"@{session.get('handle', handle)}"

            # Encrypt and persist
            await credential_service.save_connection(
                platform="bluesky",
                handle=user_handle,
                access_token=app_password,
                account_id=did,
                account_name=user_handle,
                metadata={"did": did},
            )

            # Invalidate session cache in adapter so new credentials take effect
            bluesky_adapter._cached_session = session

            return ConnectionVerifyResponse(
                platform="bluesky",
                is_valid=True,
                status="connected",
                message=f"Bluesky account '{user_handle}' connected and verified successfully!",
                account_name=user_handle,
            )

        except Exception as e:
            return ConnectionVerifyResponse(
                platform="bluesky",
                is_valid=False,
                status="disconnected",
                message=f"Network error connecting to Bluesky: {str(e)}",
            )


@router.post("/linkedin/connect", response_model=ConnectionVerifyResponse)
async def connect_linkedin(payload: LinkedInConnectRequest):
    """
    Connects LinkedIn using an OAuth 2.0 Bearer access token.
    Validates token with /v2/userinfo, extracts author URN, encrypts, and persists.
    """
    token = payload.access_token.strip()
    author_urn = (payload.author_urn or "").strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LinkedIn access token is required.",
        )

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(
                f"{linkedin_adapter.BASE_URL}/userinfo",
                headers={"Authorization": f"Bearer {token}"},
            )
            if resp.status_code != 200:
                return ConnectionVerifyResponse(
                    platform="linkedin",
                    is_valid=False,
                    status="disconnected",
                    message="Invalid or expired LinkedIn access token. Please re-generate token with 'w_member_social' permission.",
                )

            user_info = resp.json()
            sub = user_info.get("sub")
            name = user_info.get("name") or "LinkedIn Member"
            resolved_urn = author_urn if author_urn.startswith("urn:li:") else f"urn:li:person:{sub}"

            await credential_service.save_connection(
                platform="linkedin",
                handle=name,
                access_token=token,
                account_id=resolved_urn,
                account_name=name,
                metadata={"sub": sub, "author_urn": resolved_urn},
            )

            return ConnectionVerifyResponse(
                platform="linkedin",
                is_valid=True,
                status="connected",
                message=f"LinkedIn account '{name}' connected successfully!",
                account_name=name,
            )

        except Exception as e:
            return ConnectionVerifyResponse(
                platform="linkedin",
                is_valid=False,
                status="disconnected",
                message=f"Network error connecting to LinkedIn: {str(e)}",
            )


# =============================================================================
# 4. Connection Verification, Disconnection, and Refresh
# =============================================================================

@router.post("/verify", response_model=ConnectionVerifyResponse)
async def verify_connection_body(payload: ConnectionVerifyRequest):
    """
    Verifies a connection using request body parameters.
    Supports backward compatibility with POST /api/v1/connections/verify.
    """
    return await verify_platform_connection(payload.platform, payload)


@router.post("/{platform}/verify", response_model=ConnectionVerifyResponse)
async def verify_platform_connection(platform: str, payload: Optional[ConnectionVerifyRequest] = None):
    """
    Verifies an existing connection using stored credentials or environment variables.
    """
    p_clean = platform.lower().strip()

    if p_clean == "bluesky":
        is_valid = await bluesky_adapter.validate_connection()
        conn = credential_service.get_safe_connection_item("bluesky")
        status_val = "connected" if is_valid else ("error" if conn.get("status") in ("connected", "error") or conn.get("is_configured") else "disconnected")
        if status_val in ("connected", "error"):
            await credential_service.update_connection_status("bluesky", status_val)
        return ConnectionVerifyResponse(
            platform="bluesky",
            is_valid=is_valid,
            status=status_val,
            message="Bluesky AT Protocol session verified successfully!" if is_valid else "Bluesky session verification failed. Please reconnect.",
            account_name=conn.get("handle"),
        )
    elif p_clean == "linkedin":
        is_valid = await linkedin_adapter.validate_connection()
        conn = credential_service.get_safe_connection_item("linkedin")
        status_val = "connected" if is_valid else ("error" if conn.get("status") in ("connected", "error") or conn.get("is_configured") else "disconnected")
        if status_val in ("connected", "error"):
            await credential_service.update_connection_status("linkedin", status_val)
        return ConnectionVerifyResponse(
            platform="linkedin",
            is_valid=is_valid,
            status=status_val,
            message="LinkedIn token verified successfully!" if is_valid else "LinkedIn access token expired or invalid.",
            account_name=conn.get("handle"),
        )
    elif p_clean == "facebook":
        is_valid = await facebook_adapter.validate_connection()
        conn = credential_service.get_safe_connection_item("facebook")
        status_val = "connected" if is_valid else ("error" if conn.get("status") in ("connected", "error") or conn.get("is_configured") else "disconnected")
        if status_val in ("connected", "error"):
            await credential_service.update_connection_status("facebook", status_val)
        return ConnectionVerifyResponse(
            platform="facebook",
            is_valid=is_valid,
            status=status_val,
            message="Facebook Page verified successfully with Meta Graph API!" if is_valid else "Facebook connection verification failed. Please re-authorize.",
            account_name=conn.get("handle"),
        )
    elif p_clean == "instagram":
        is_valid = await instagram_adapter.validate_connection()
        conn = credential_service.get_safe_connection_item("instagram")
        status_val = "connected" if is_valid else ("error" if conn.get("status") in ("connected", "error") or conn.get("is_configured") else "disconnected")
        if status_val in ("connected", "error"):
            await credential_service.update_connection_status("instagram", status_val)
        return ConnectionVerifyResponse(
            platform="instagram",
            is_valid=is_valid,
            status=status_val,
            message="Instagram Business Account verified successfully!" if is_valid else "Instagram connection verification failed. Please re-authorize.",
            account_name=conn.get("handle"),
        )
    elif p_clean == "pinterest":
        is_valid = await pinterest_adapter.validate_connection()
        conn = credential_service.get_safe_connection_item("pinterest")
        status_val = "connected" if is_valid else ("error" if conn.get("status") in ("connected", "error") or conn.get("is_configured") else "disconnected")
        if status_val in ("connected", "error"):
            await credential_service.update_connection_status("pinterest", status_val)
        return ConnectionVerifyResponse(
            platform="pinterest",
            is_valid=is_valid,
            status=status_val,
            message="Pinterest account verified successfully!" if is_valid else "Pinterest connection verification failed. Please reconnect.",
            account_name=conn.get("handle"),
        )
    elif p_clean == "youtube":
        is_valid = await youtube_adapter.validate_connection()
        conn = credential_service.get_safe_connection_item("youtube")
        status_val = "connected" if is_valid else ("error" if conn.get("status") in ("connected", "error") or conn.get("is_configured") else "disconnected")
        if status_val in ("connected", "error"):
            await credential_service.update_connection_status("youtube", status_val)
        return ConnectionVerifyResponse(
            platform="youtube",
            is_valid=is_valid,
            status=status_val,
            message="YouTube channel verified successfully!" if is_valid else "YouTube connection verification failed. Please reconnect.",
            account_name=conn.get("handle"),
        )

    return ConnectionVerifyResponse(
        platform=platform,
        is_valid=False,
        status="disconnected",
        message=f"Platform '{platform}' is not currently supported.",
    )


@router.delete("/{platform}", response_model=ConnectionDisconnectResponse)
async def disconnect_platform(platform: str):
    """
    Disconnects a social media channel, deleting stored encrypted credentials.
    """
    p_clean = platform.lower().strip()
    await credential_service.delete_connection(p_clean)

    # Invalidate cached session if Bluesky
    if p_clean == "bluesky":
        bluesky_adapter._cached_session = None

    return ConnectionDisconnectResponse(
        success=True,
        platform=p_clean,
        status="disconnected",
        message=f"{p_clean.capitalize()} disconnected successfully.",
    )


@router.post("/{platform}/refresh", response_model=ConnectionVerifyResponse)
async def refresh_platform_connection(platform: str):
    """
    Refreshes credentials or re-verifies connection health for a platform.
    """
    return await verify_platform_connection(platform)
