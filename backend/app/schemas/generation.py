from typing import List, Optional
from pydantic import BaseModel, Field


class GeneratePreviewRequest(BaseModel):
    topic: str = Field(..., description="Topic or prompt for social post generation")
    tone: Optional[str] = Field("Professional", description="Tone (Professional, Casual, Witty, Inspiring)")
    content_type: Optional[str] = Field("General Post", description="Content type (General Post, Thought Leadership, Product Launch, Tips & Advice)")
    audience: Optional[str] = Field(None, description="Target audience description")
    campaign_objective: Optional[str] = Field(None, description="Campaign objective (Growth, Awareness, Engagement, Lead Gen)")
    language: Optional[str] = Field("English", description="Target language")
    include_hashtags: bool = Field(True, description="Whether to include hashtags")
    platforms: Optional[List[str]] = Field(default_factory=lambda: ["linkedin"], description="Target platforms")


class GeneratePreviewResponse(BaseModel):
    generated_text: str
    tone: str
    language: str
    provider: str
    model: str
    variants: Optional[dict[str, str]] = None
