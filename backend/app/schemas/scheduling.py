import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ScheduleCreate(BaseModel):
    post_id: Optional[str] = Field(None, description="ID of existing post in post library")
    content: Optional[str] = Field(None, description="Direct post content if not referencing an existing post")
    media_url: Optional[str] = Field(None, description="Optional media or image URL")
    platforms: List[str] = Field(..., min_length=1, description="List of target platforms (e.g. bluesky, linkedin, facebook, instagram)")
    scheduled_time: datetime.datetime = Field(..., description="Target execution timestamp (ISO 8601 UTC)")
    dry_run: bool = Field(False, description="Whether to publish in safe mock/dry_run mode")
    max_attempts: int = Field(3, ge=1, le=10, description="Maximum retry attempts on failure")
    variants: Optional[Dict[str, str]] = Field(None, description="Platform-tailored content variants")


class ScheduleUpdate(BaseModel):
    scheduled_time: Optional[datetime.datetime] = Field(None, description="New scheduled time")
    platforms: Optional[List[str]] = Field(None, description="Updated target platforms")
    content: Optional[str] = Field(None, description="Updated content")
    dry_run: Optional[bool] = Field(None, description="Updated dry_run flag")
    variants: Optional[Dict[str, str]] = Field(None, description="Platform-tailored content variants")


class ScheduleResponse(BaseModel):
    id: str
    post_id: Optional[str] = None
    content: Optional[str] = None
    media_url: Optional[str] = None
    platforms: List[str]
    scheduled_time: str
    status: str  # pending, processing, completed, failed, cancelled
    attempts: int = 0
    max_attempts: int = 3
    last_error: Optional[str] = None
    platform_results: Optional[List[Dict[str, Any]]] = None
    dry_run: bool = False
    variants: Optional[Dict[str, str]] = None
    created_at: str
    updated_at: str


class SchedulerHealthResponse(BaseModel):
    status: str
    running: bool
    poll_interval_seconds: int
    uptime_seconds: float
    total_jobs: int
    pending_jobs: int
    processing_jobs: int
    completed_jobs: int
    failed_jobs: int
    cancelled_jobs: int
