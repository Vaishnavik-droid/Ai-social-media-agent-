from typing import List, Optional
from pydantic import BaseModel, Field


class PlatformResult(BaseModel):
    platform: str
    status: str = Field("pending", pattern="^(pending|processing|published|scheduled|failed|cancelled)$")
    remote_post_id: Optional[str] = None
    remote_post_url: Optional[str] = None
    error_message: Optional[str] = None
    is_mock: bool = Field(False, description="True if published via dry-run or mock mode")


class PublishRequest(BaseModel):
    post_id: str
    platforms: List[str]
    publish_now: bool = True
    scheduled_at: Optional[str] = None
    dry_run: bool = Field(False, description="If True, performs validation and simulated publish without external dispatch")


class PublishResponse(BaseModel):
    post_id: str
    success: bool
    message: str
    results: List[PlatformResult]
    is_mock: bool = Field(False, description="True if any platform was executed in mock/dry-run mode")
