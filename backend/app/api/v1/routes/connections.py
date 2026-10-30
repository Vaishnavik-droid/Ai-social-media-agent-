from fastapi import APIRouter
from app.platforms.bluesky import bluesky_adapter
from app.platforms.linkedin import linkedin_adapter
from app.platforms.facebook import facebook_adapter
from app.platforms.instagram import instagram_adapter
from app.schemas.connection import (
    ConnectionItem,
    ConnectionListResponse,
    ConnectionVerifyRequest,
    ConnectionVerifyResponse,
)
from app.core.config import settings

router = APIRouter(prefix="/connections", tags=["Connections"])


@router.get("", response_model=ConnectionListResponse)
async def list_connections():
    """
    Returns platform connection statuses safely without ever exposing tokens or secrets.
    """
    bsky_configured = bool(settings.BLUESKY_HANDLE and settings.BLUESKY_APP_PASSWORD)
    linkedin_configured = bool(settings.LINKEDIN_ACCESS_TOKEN)
    fb_configured = bool(settings.FACEBOOK_PAGE_ACCESS_TOKEN and settings.FACEBOOK_PAGE_ID)
    ig_configured = bool(settings.INSTAGRAM_BUSINESS_ACCOUNT_ID and (settings.INSTAGRAM_ACCESS_TOKEN or settings.META_USER_TOKEN or settings.FACEBOOK_PAGE_ACCESS_TOKEN))

    connections = [
        ConnectionItem(
            id="bluesky",
            name="Bluesky",
            handle=settings.BLUESKY_HANDLE or "@yourhandle.bsky.social",
            status="connected" if bsky_configured else "disconnected",
            connectedUser=settings.BLUESKY_HANDLE or None,
        ),
        ConnectionItem(
            id="linkedin",
            name="LinkedIn",
            handle=settings.LINKEDIN_AUTHOR_URN or "LinkedIn Account",
            status="connected" if linkedin_configured else "disconnected",
            connectedUser=settings.LINKEDIN_AUTHOR_URN or None,
        ),
        ConnectionItem(
            id="facebook",
            name="Facebook",
            handle=f"Page ID: {settings.FACEBOOK_PAGE_ID}" if settings.FACEBOOK_PAGE_ID else "Facebook Page",
            status="connected" if fb_configured else "disconnected",
            connectedUser=settings.FACEBOOK_PAGE_ID or None,
        ),
        ConnectionItem(
            id="instagram",
            name="Instagram",
            handle=f"IG ID: {settings.INSTAGRAM_BUSINESS_ACCOUNT_ID}" if settings.INSTAGRAM_BUSINESS_ACCOUNT_ID else "@yourbrand",
            status="connected" if ig_configured else "disconnected",
            connectedUser=settings.INSTAGRAM_BUSINESS_ACCOUNT_ID or None,
        ),
    ]

    return ConnectionListResponse(connections=connections)


@router.post("/verify", response_model=ConnectionVerifyResponse)
async def verify_connection(payload: ConnectionVerifyRequest):
    platform = payload.platform.lower().strip()

    if platform == "bluesky":
        is_valid = await bluesky_adapter.validate_connection()
        return ConnectionVerifyResponse(
            platform="bluesky",
            is_valid=is_valid,
            status="connected" if is_valid else "disconnected",
            message="Bluesky AT Protocol session verified successfully!" if is_valid else "Invalid Bluesky handle or app password in backend/.env",
        )
    elif platform == "linkedin":
        is_valid = await linkedin_adapter.validate_connection()
        return ConnectionVerifyResponse(
            platform="linkedin",
            is_valid=is_valid,
            status="connected" if is_valid else "disconnected",
            message="LinkedIn token verified successfully!" if is_valid else "Invalid or expired LinkedIn access token in backend/.env",
        )
    elif platform == "facebook":
        is_valid = await facebook_adapter.validate_connection()
        return ConnectionVerifyResponse(
            platform="facebook",
            is_valid=is_valid,
            status="connected" if is_valid else "disconnected",
            message="Facebook Page Access Token verified successfully!" if is_valid else "Invalid Facebook Page Token or Page ID in backend/.env",
        )
    elif platform == "instagram":
        is_valid = await instagram_adapter.validate_connection()
        return ConnectionVerifyResponse(
            platform="instagram",
            is_valid=is_valid,
            status="connected" if is_valid else "disconnected",
            message="Instagram Business account verified successfully!" if is_valid else "Invalid Instagram Account ID or Meta User Token in backend/.env",
        )

    return ConnectionVerifyResponse(
        platform=platform,
        is_valid=False,
        status="disconnected",
        message=f"Platform '{platform}' requires OAuth 2.0 configuration in backend/.env",
    )
