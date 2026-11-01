"""
Centralized Platform Constraints, Character/Grapheme Rules, and Content Validation.
Single source of truth for all social platform limits across OmniPulse AI.
"""

from dataclasses import dataclass, field
import logging
from typing import Dict, List, Optional, Tuple
import unicodedata

logger = logging.getLogger(__name__)

# Grapheme counting with graceful fallback
try:
    import grapheme
    def count_graphemes(text: str) -> int:
        """
        Count Unicode grapheme clusters per Unicode UAX #29 standard.
        Correctly groups complex emojis, ZWJ sequences, skin-tone modifiers, and combining characters.
        """
        if not text:
            return 0
        return grapheme.length(text)
except ImportError:
    def count_graphemes(text: str) -> int:
        """Fallback grapheme counter using unicodedata combining character filtering."""
        if not text:
            return 0
        return sum(1 for ch in text if not unicodedata.combining(ch))


def count_bytes(text: str) -> int:
    """Returns exact UTF-8 byte count of string."""
    if not text:
        return 0
    return len(text.encode("utf-8"))


@dataclass(frozen=True)
class PlatformRule:
    id: str
    name: str
    max_length: int
    length_unit: str  # "graphemes" | "characters"
    max_bytes: Optional[int] = None
    supports_title: bool = False
    max_title_length: Optional[int] = None
    supports_media: bool = True
    media_required: bool = False
    allowed_media_types: List[str] = field(default_factory=lambda: ["image", "video"])
    max_hashtags: Optional[int] = None
    formatting_guidance: str = ""


# Authoritative constraint catalog for all 6 supported platforms
PLATFORM_CONSTRAINTS: Dict[str, PlatformRule] = {
    "bluesky": PlatformRule(
        id="bluesky",
        name="Bluesky",
        max_length=300,
        length_unit="graphemes",
        max_bytes=3000,
        supports_title=False,
        supports_media=True,
        media_required=False,
        allowed_media_types=["image", "video"],
        max_hashtags=5,
        formatting_guidance=(
            "Strict limit of 300 Unicode grapheme clusters. Punchy hook, concise idea, "
            "no fluff. Fit everything within the 300-grapheme ceiling with a safety margin."
        ),
    ),
    "linkedin": PlatformRule(
        id="linkedin",
        name="LinkedIn",
        max_length=3000,
        length_unit="characters",
        supports_title=True,
        max_title_length=120,
        supports_media=True,
        media_required=False,
        allowed_media_types=["image", "video"],
        max_hashtags=5,
        formatting_guidance=(
            "Professional, informative, structured paragraphs with clean line breaks. "
            "Includes actionable insight or thought leadership takeaway and a discussion question."
        ),
    ),
    "instagram": PlatformRule(
        id="instagram",
        name="Instagram",
        max_length=2200,
        length_unit="characters",
        supports_title=False,
        supports_media=True,
        media_required=True,
        allowed_media_types=["image", "video"],
        max_hashtags=30,
        formatting_guidance=(
            "Visual-first caption with an engaging hook in the first line. "
            "Clean line breaks, conversational tone, clear CTA, and 3-5 targeted hashtags."
        ),
    ),
    "facebook": PlatformRule(
        id="facebook",
        name="Facebook",
        max_length=5000,
        length_unit="characters",
        supports_title=False,
        supports_media=True,
        media_required=False,
        allowed_media_types=["image", "video"],
        max_hashtags=5,
        formatting_guidance=(
            "Conversational, community-focused discussion prompt. "
            "Encourages feedback, comments, and community sharing."
        ),
    ),
    "pinterest": PlatformRule(
        id="pinterest",
        name="Pinterest",
        max_length=500,
        length_unit="characters",
        supports_title=True,
        max_title_length=100,
        supports_media=True,
        media_required=True,
        allowed_media_types=["image", "video"],
        max_hashtags=10,
        formatting_guidance=(
            "Keyword-rich, inspiring Pin title (under 100 characters). "
            "Clear, actionable description highlighting steps, benefits, or inspiration (under 500 characters)."
        ),
    ),
    "youtube": PlatformRule(
        id="youtube",
        name="YouTube",
        max_length=5000,
        length_unit="characters",
        supports_title=True,
        max_title_length=100,
        supports_media=True,
        media_required=True,
        allowed_media_types=["video"],
        max_hashtags=15,
        formatting_guidance=(
            "High-CTR, curiosity-driven video title under 100 characters. "
            "Comprehensive description with key takeaways, timestamps/topics, and context under 5,000 characters."
        ),
    ),
}


def get_platform_rule(platform: str) -> Optional[PlatformRule]:
    """Retrieves authoritative platform rule by clean platform identifier."""
    return PLATFORM_CONSTRAINTS.get(platform.lower().strip())


def get_content_length(platform: str, text: str) -> int:
    """Calculates content length using the platform's native measurement unit."""
    rule = get_platform_rule(platform)
    if rule and rule.length_unit == "graphemes":
        return count_graphemes(text)
    return len(text) if text else 0


def validate_platform_content(
    platform: str,
    text: str,
    title: Optional[str] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Validates post content and optional title against platform constraints.
    Returns (is_valid, error_message).
    """
    p_clean = platform.lower().strip()
    rule = get_platform_rule(p_clean)
    if not rule:
        return True, None

    if not text or not text.strip():
        return False, f"Post content for {rule.name} cannot be empty."

    # Title validation
    if title and rule.supports_title and rule.max_title_length:
        if len(title) > rule.max_title_length:
            return False, (
                f"{rule.name} title exceeds maximum limit of {rule.max_title_length} characters "
                f"(current: {len(title)})."
            )

    # Content length validation
    if rule.length_unit == "graphemes":
        grapheme_count = count_graphemes(text)
        if grapheme_count > rule.max_length:
            return False, (
                f"{rule.name} content exceeds limit of {rule.max_length} Unicode grapheme clusters "
                f"(current count: {grapheme_count})."
            )

        if rule.max_bytes:
            byte_count = count_bytes(text)
            if byte_count > rule.max_bytes:
                return False, (
                    f"{rule.name} record exceeds AT Protocol limit of {rule.max_bytes} UTF-8 bytes "
                    f"(current: {byte_count} bytes)."
                )
    else:
        char_count = len(text)
        if char_count > rule.max_length:
            return False, (
                f"{rule.name} content exceeds limit of {rule.max_length} characters "
                f"(current length: {char_count})."
            )

    return True, None

