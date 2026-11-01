from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator


class PostCreate(BaseModel):
    id: Optional[str] = None
    title: str
    snippet: Optional[str] = None
    content: str
    media_url: Optional[str] = None
    mediaUrl: Optional[str] = None
    tone: Optional[str] = "Professional"
    content_type: Optional[str] = "General Post"
    contentType: Optional[str] = None
    language: Optional[str] = "English"
    platforms: List[str] = Field(default_factory=list)
    status: str = Field("draft", pattern="^(draft|published|partially_published|scheduled|failed)$")
    scheduled_at: Optional[str] = None
    scheduledAt: Optional[str] = None
    created_at: Optional[str] = None
    createdAt: Optional[str] = None
    topic_prompt: Optional[str] = None
    topicPrompt: Optional[str] = None
    platform_content: Optional[Dict[str, Any]] = None
    platformContent: Optional[Dict[str, Any]] = None
    variants: Optional[Dict[str, str]] = None
    youtube_post_type: Optional[str] = None
    youtubePostType: Optional[str] = None
    pinterest_board_id: Optional[str] = None
    pinterestBoardId: Optional[str] = None

    @model_validator(mode="after")
    def unify_aliases(self):
        if not self.media_url and self.mediaUrl:
            self.media_url = self.mediaUrl
        if not self.content_type and self.contentType:
            self.content_type = self.contentType
        if not self.scheduled_at and self.scheduledAt:
            self.scheduled_at = self.scheduledAt
        if not self.created_at and self.createdAt:
            self.created_at = self.createdAt
        if not self.topic_prompt and self.topicPrompt:
            self.topic_prompt = self.topicPrompt
        if not self.platform_content and self.platformContent:
            self.platform_content = self.platformContent
        if not self.youtube_post_type and self.youtubePostType:
            self.youtube_post_type = self.youtubePostType
        if not self.pinterest_board_id and self.pinterestBoardId:
            self.pinterest_board_id = self.pinterestBoardId
        return self


class PostUpdate(BaseModel):
    title: Optional[str] = None
    snippet: Optional[str] = None
    content: Optional[str] = None
    media_url: Optional[str] = None
    mediaUrl: Optional[str] = None
    tone: Optional[str] = None
    content_type: Optional[str] = None
    contentType: Optional[str] = None
    language: Optional[str] = None
    platforms: Optional[List[str]] = None
    status: Optional[str] = None
    scheduled_at: Optional[str] = None
    scheduledAt: Optional[str] = None
    topic_prompt: Optional[str] = None
    topicPrompt: Optional[str] = None
    platform_content: Optional[Dict[str, Any]] = None
    platformContent: Optional[Dict[str, Any]] = None
    variants: Optional[Dict[str, str]] = None
    youtube_post_type: Optional[str] = None
    youtubePostType: Optional[str] = None
    pinterest_board_id: Optional[str] = None
    pinterestBoardId: Optional[str] = None


class PostResponse(BaseModel):
    id: str
    title: str
    snippet: Optional[str] = None
    content: str
    media_url: Optional[str] = None
    mediaUrl: Optional[str] = None
    tone: Optional[str] = "Professional"
    content_type: Optional[str] = "General Post"
    contentType: Optional[str] = None
    language: Optional[str] = "English"
    platforms: List[str] = Field(default_factory=list)
    status: str
    scheduled_at: Optional[str] = None
    scheduledAt: Optional[str] = None
    created_at: Optional[str] = None
    createdAt: Optional[str] = None
    topic_prompt: Optional[str] = None
    topicPrompt: Optional[str] = None
    platform_content: Optional[Dict[str, Any]] = None
    platformContent: Optional[Dict[str, Any]] = None
    variants: Optional[Dict[str, str]] = None
    youtube_post_type: Optional[str] = None
    youtubePostType: Optional[str] = None
    pinterest_board_id: Optional[str] = None
    pinterestBoardId: Optional[str] = None

    @model_validator(mode="after")
    def populate_camel_and_snake(self):
        if self.media_url and not self.mediaUrl:
            self.mediaUrl = self.media_url
        elif self.mediaUrl and not self.media_url:
            self.media_url = self.mediaUrl

        if self.content_type and not self.contentType:
            self.contentType = self.content_type
        elif self.contentType and not self.content_type:
            self.content_type = self.contentType

        if self.scheduled_at and not self.scheduledAt:
            self.scheduledAt = self.scheduled_at
        elif self.scheduledAt and not self.scheduled_at:
            self.scheduled_at = self.scheduledAt

        if self.created_at and not self.createdAt:
            self.createdAt = self.created_at
        elif self.createdAt and not self.created_at:
            self.created_at = self.createdAt

        if self.topic_prompt and not self.topicPrompt:
            self.topicPrompt = self.topic_prompt
        elif self.topicPrompt and not self.topic_prompt:
            self.topic_prompt = self.topicPrompt

        if self.platform_content and not self.platformContent:
            self.platformContent = self.platform_content
        elif self.platformContent and not self.platform_content:
            self.platform_content = self.platformContent

        if self.youtube_post_type and not self.youtubePostType:
            self.youtubePostType = self.youtube_post_type
        elif self.youtubePostType and not self.youtube_post_type:
            self.youtube_post_type = self.youtubePostType

        if self.pinterest_board_id and not self.pinterestBoardId:
            self.pinterestBoardId = self.pinterest_board_id
        elif self.pinterestBoardId and not self.pinterest_board_id:
            self.pinterest_board_id = self.pinterestBoardId

        return self
