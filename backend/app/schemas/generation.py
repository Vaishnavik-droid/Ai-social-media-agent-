from typing import Dict, List, Optional
from pydantic import BaseModel, Field, model_validator


class PlatformContentVariant(BaseModel):
    text: Optional[str] = Field(None, description="Platform-tailored post content or caption")
    content: Optional[str] = Field(None, description="Platform-tailored post content (alias/mirror of text for frontend compatibility)")
    title: Optional[str] = Field(None, description="Optional title if supported by the platform (e.g. YouTube, Pinterest, LinkedIn)")
    hashtags: List[str] = Field(default_factory=list, description="Extracted or generated hashtags")
    character_count: int = Field(0, description="Length measured in the platform's native unit (e.g. graphemes for Bluesky)")

    @model_validator(mode="after")
    def sync_text_and_content(self) -> "PlatformContentVariant":
        if not self.content and self.text:
            self.content = self.text
        elif not self.text and self.content:
            self.text = self.content
        if not self.text:
            self.text = ""
            self.content = ""
        return self


class GeneratePreviewRequest(BaseModel):
    topic: str = Field(..., description="Topic or prompt for social post generation (instruction/concept, not final post title)")
    tone: Optional[str] = Field("Professional", description="Tone (Professional, Casual, Witty, Inspiring)")
    content_type: Optional[str] = Field("General Post", description="Content type (General Post, Thought Leadership, Product Launch, Tips & Advice)")
    audience: Optional[str] = Field(None, description="Target audience description")
    campaign_objective: Optional[str] = Field(None, description="Campaign objective (Growth, Awareness, Engagement, Lead Gen)")
    language: Optional[str] = Field("English", description="Target language")
    include_hashtags: bool = Field(True, description="Whether to include hashtags")
    platforms: List[str] = Field(default_factory=lambda: ["linkedin"], description="Target platforms")
    additional_instructions: Optional[str] = Field(None, description="Additional custom instructions")
    current_content: Optional[str] = Field(None, description="Existing draft context when regenerating")
    target_single_platform: Optional[str] = Field(None, description="If specified, only regenerates the variant for this platform")


class GeneratePreviewResponse(BaseModel):
    topic_prompt: str = Field(..., description="Original user topic/prompt")
    content_type: str = Field(..., description="Content type used for generation")
    platform_content: Dict[str, PlatformContentVariant] = Field(
        default_factory=dict,
        description="Structured dictionary of platform-specific content variants"
    )
    provider: str
    model: str
    # Backwards compatibility fields
    generated_text: str = Field("", description="Primary or fallback post text representation")
    tone: str = "Professional"
    language: str = "English"
    variants: Optional[Dict[str, str]] = Field(None, description="Simple mapping of platform -> text for backward compatibility")
