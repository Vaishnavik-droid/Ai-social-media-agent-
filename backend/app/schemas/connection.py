from typing import List, Optional
from pydantic import BaseModel


class ConnectionItem(BaseModel):
    id: str
    name: str
    handle: str
    status: str  # 'connected' | 'disconnected' | 'error'
    connected_user: Optional[str] = None


class ConnectionListResponse(BaseModel):
    connections: List[ConnectionItem]


class ConnectionVerifyRequest(BaseModel):
    platform: str
    app_id: Optional[str] = None
    app_secret: Optional[str] = None
    access_token: Optional[str] = None
    page_id: Optional[str] = None
    account_id: Optional[str] = None
    redirect_uri: Optional[str] = None
    code: Optional[str] = None


class ConnectionVerifyResponse(BaseModel):
    platform: str
    is_valid: bool
    status: str
    message: str
