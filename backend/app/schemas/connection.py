from typing import List, Optional
from pydantic import BaseModel, Field


class ConnectionItem(BaseModel):
    id: str
    name: str
    handle: str
    status: str  # 'connected' | 'disconnected' | 'error' | 'expired' | 'reauth_required' | 'temp_unavailable' | 'coming_soon'
    status_reason: Optional[str] = None
    connected_user: Optional[str] = None
    connectedUser: Optional[str] = None
    account_id: Optional[str] = None
    accountId: Optional[str] = None
    account_name: Optional[str] = None
    accountName: Optional[str] = None
    last_verified_at: Optional[str] = None
    lastVerifiedAt: Optional[str] = None
    is_configured: Optional[bool] = False
    isConfigured: Optional[bool] = False
    is_coming_soon: Optional[bool] = False
    isComingSoon: Optional[bool] = False


class ConnectionListResponse(BaseModel):
    connections: List[ConnectionItem]


class MetaAuthorizeRequest(BaseModel):
    platform: str = Field(default="facebook", description="'facebook' or 'instagram'")
    redirect_origin: Optional[str] = Field(default=None, description="Frontend origin for popup postMessage handshake")


class MetaAuthorizeResponse(BaseModel):
    auth_url: str
    state: str
    platform: str


class OAuthAuthorizeRequest(BaseModel):
    platform: str = Field(..., description="'pinterest', 'youtube', 'facebook', or 'instagram'")
    redirect_origin: Optional[str] = Field(default=None, description="Frontend origin for popup postMessage handshake")


class OAuthAuthorizeResponse(BaseModel):
    auth_url: str
    state: str
    platform: str


class BlueskyConnectRequest(BaseModel):
    handle: str = Field(..., description="Bluesky handle, e.g. user.bsky.social")
    app_password: str = Field(..., description="Bluesky App Password from account settings")


class LinkedInConnectRequest(BaseModel):
    access_token: str = Field(..., description="LinkedIn OAuth 2.0 Bearer access token")
    author_urn: Optional[str] = Field(default=None, description="Optional LinkedIn Author URN (urn:li:person:... or urn:li:organization:...)")


class ConnectionVerifyRequest(BaseModel):
    platform: str
    access_token: Optional[str] = None
    page_id: Optional[str] = None
    account_id: Optional[str] = None


class ConnectionVerifyResponse(BaseModel):
    platform: str
    is_valid: bool
    status: str  # 'connected' | 'disconnected' | 'error' | 'expired' | 'reauth_required' | 'temp_unavailable'
    message: str
    account_name: Optional[str] = None
    status_reason: Optional[str] = None


class ConnectionDisconnectResponse(BaseModel):
    success: bool
    platform: str
    status: str
    message: str


class CreatePinterestBoardRequest(BaseModel):
    name: str = Field(..., description="Board name (max 50 chars)")
    description: Optional[str] = Field(default="Created by OmniPulse AI", description="Board description")
    privacy: Optional[str] = Field(default="PUBLIC", description="'PUBLIC' or 'SECRET'")
