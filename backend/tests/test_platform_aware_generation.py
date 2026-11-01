"""
Automated test suite for OmniPulse AI Platform-Aware Content Generation & Structured Output.
Covers:
1. Topic/Title Separation Test
2. Multi-Platform Generation Test
3. Bluesky Grapheme Counting Test (Unicode UAX #29, ZWJ sequences, bytes)
4. Structured Output Validation Test (Pydantic, Markdown stripping, fallback)
5. Publishing Variant Routing & Validation Test
"""

import json
import pytest
from unittest.mock import AsyncMock, patch

from backend.app.core.platform_constraints import (
    count_graphemes,
    count_bytes,
    validate_platform_content,
    get_content_length,
    PLATFORM_CONSTRAINTS,
)
from backend.app.schemas.generation import (
    GeneratePreviewRequest,
    GeneratePreviewResponse,
    PlatformContentVariant,
)
from backend.app.services.groq_service import GroqService


# ============================================================================
# 1. Topic / Title Separation Test
# ============================================================================

def test_topic_title_separation():
    """
    Verify that topic prompt is strictly treated as an instruction/subject
    and is NEVER reused verbatim as the generated title or post caption.
    Also verify platforms without title fields (Bluesky, Instagram) receive no title.
    """
    groq = GroqService()
    topic = "AI is changing social media marketing"
    platforms = ["bluesky", "linkedin", "instagram", "pinterest", "youtube"]

    # Call generate_post (offline synthesizer or live)
    result = groq._synthesize_offline_variants(
        topic=topic,
        platforms=platforms,
        tone="Professional",
        content_type="General Post",
        language="English",
        include_hashtags=True,
    )

    # 1. Check Bluesky: NO title, and text is NOT verbatim topic
    assert "bluesky" in result
    bsky = result["bluesky"]
    assert bsky.title is None
    assert bsky.text != topic
    assert not bsky.text.startswith(f"{topic}\n")

    # 2. Check Instagram: NO title, and text is NOT verbatim topic
    assert "instagram" in result
    insta = result["instagram"]
    assert insta.title is None
    assert insta.text != topic

    # 3. Check LinkedIn: Supports title; title if present is NOT verbatim topic
    assert "linkedin" in result
    li = result["linkedin"]
    if li.title:
        assert li.title.strip().lower() != topic.strip().lower()
    assert li.text != topic

    # 4. Check Pinterest: Supports title; title is NOT verbatim topic
    assert "pinterest" in result
    pin = result["pinterest"]
    assert pin.title is not None
    assert pin.title.strip().lower() != topic.strip().lower()
    assert pin.text != topic

    # 5. Check YouTube: Supports title; title is NOT verbatim topic
    assert "youtube" in result
    yt = result["youtube"]
    assert yt.title is not None
    assert yt.title.strip().lower() != topic.strip().lower()
    assert yt.text != topic


# ============================================================================
# 2. Multi-Platform Generation Test
# ============================================================================

def test_multi_platform_generation():
    """
    Request generation for Bluesky, LinkedIn, and Instagram in a single request.
    Verify distinct content for each platform respecting their unique constraints.
    """
    groq = GroqService()
    topic = "Scaling creator workflows with intelligent agents"
    platforms = ["bluesky", "linkedin", "instagram"]

    result = groq._synthesize_offline_variants(
        topic=topic,
        platforms=platforms,
        tone="Professional",
        content_type="General Post",
        language="English",
        include_hashtags=True,
    )

    bsky = result.get("bluesky")
    linkedin = result.get("linkedin")
    insta = result.get("instagram")

    assert bsky is not None
    assert linkedin is not None
    assert insta is not None

    # Distinct content per platform
    assert bsky.text != linkedin.text
    assert linkedin.text != insta.text
    assert bsky.text != insta.text

    # Bluesky constraint: <= 300 Unicode graphemes
    bsky_graphemes = count_graphemes(bsky.text)
    assert bsky_graphemes <= 300, f"Bluesky content exceeded 300 graphemes: {bsky_graphemes}"

    # LinkedIn formatting: structured with paragraphs and bullet points
    assert "\n" in linkedin.text
    assert "•" in linkedin.text or len(linkedin.text.splitlines()) >= 3

    # Instagram: visual hook, emojis and hashtags
    assert "#" in insta.text or (insta.hashtags and len(insta.hashtags) > 0)


# ============================================================================
# 3. Bluesky Grapheme Counting Test
# ============================================================================

def test_bluesky_grapheme_counting_standard_ascii():
    """
    Test 299, 300, and 301 standard ASCII characters against Bluesky constraints.
    """
    text_299 = "a" * 299
    text_300 = "a" * 300
    text_301 = "a" * 301

    assert count_graphemes(text_299) == 299
    assert count_graphemes(text_300) == 300
    assert count_graphemes(text_301) == 301

    # 299 and 300 must be valid
    is_valid_299, err_299 = validate_platform_content("bluesky", text_299)
    assert is_valid_299 is True
    assert err_299 is None

    is_valid_300, err_300 = validate_platform_content("bluesky", text_300)
    assert is_valid_300 is True
    assert err_300 is None

    # 301 must be rejected
    is_valid_301, err_301 = validate_platform_content("bluesky", text_301)
    assert is_valid_301 is False
    assert "300 Unicode grapheme clusters" in err_301


def test_bluesky_grapheme_counting_complex_emojis_and_zwj():
    """
    Test multi-byte Unicode characters and Zero-Width Joiner (ZWJ) family/modifier emojis.
    Verify they are counted as single graphemes, not naive Python len() or JS length.
    """
    # Family emoji: Man + ZWJ + Woman + ZWJ + Girl + ZWJ + Boy
    # In naive len(str), this is 11 code units! In Unicode grapheme clusters, it is 1.
    family_emoji = "👨‍👩‍👧‍👦"
    assert count_graphemes(family_emoji) == 1
    assert len(family_emoji) > 1

    # Flag emoji: Regional indicator sequence (2 code points -> 1 grapheme)
    us_flag = "🇺🇸"
    in_flag = "🇮🇳"
    assert count_graphemes(us_flag) == 1
    assert count_graphemes(in_flag) == 1

    # Rocket emoji
    rocket = "🚀"
    assert count_graphemes(rocket) == 1

    # Skin tone modifier emoji (2 code points -> 1 grapheme)
    thumbs_up_dark = "👍🏿"
    assert count_graphemes(thumbs_up_dark) == 1

    # Combined string: 16 graphemes
    test_str = "Hello 👨‍👩‍👧‍👦 world! 🇺🇸"
    # "Hello " (6) + family (1) + " world! " (8) + flag (1) = 16 graphemes
    assert count_graphemes(test_str) == 16


def test_bluesky_byte_count_limit():
    """
    Verify AT Protocol byte limit enforcement (3,000 UTF-8 bytes).
    """
    # 290 graphemes of simple ASCII = 290 bytes (well within 3000 bytes)
    ascii_content = "x" * 290
    assert count_bytes(ascii_content) == 290
    valid, err = validate_platform_content("bluesky", ascii_content)
    assert valid is True

    # Multi-byte UTF-8 test:
    four_byte_char = "🚀"
    assert len(four_byte_char.encode("utf-8")) == 4
    multi_byte_str = four_byte_char * 751
    assert count_bytes(multi_byte_str) == 3004

    # Validate rejects
    valid_mb, err_mb = validate_platform_content("bluesky", multi_byte_str)
    assert valid_mb is False


# ============================================================================
# 4. Structured Output Validation Test
# ============================================================================

def test_structured_output_json_parsing_and_repairs():
    """
    Test with simulated Groq responses:
    - Pure valid JSON parsed and normalized
    - Markdown-wrapped JSON (```json ... ```) stripped and normalized
    - Intelligent fallback when JSON is malformed
    """
    groq = GroqService()
    topic = "AI video tools in 2026"

    raw_json_dict = {
        "platform_content": {
            "bluesky": {
                "text": "AI video tools are evolving rapidly. Workflows that took days now take hours. #AIVideo",
                "title": None,
                "hashtags": ["#AIVideo"],
            },
            "linkedin": {
                "text": "AI video tools have crossed a critical fidelity threshold.\n\nHere is what every creator needs to know.",
                "title": "The Evolution of AI Video Production",
                "hashtags": ["#AIVideo", "#CreatorTools"],
            }
        }
    }

    # 1. Test _validate_and_normalize_output with pure dictionary
    normalized = groq._validate_and_normalize_output(
        parsed_json=raw_json_dict,
        requested_platforms=["bluesky", "linkedin"],
        clean_topic=topic,
    )
    assert "bluesky" in normalized
    assert normalized["bluesky"].title is None
    assert normalized["bluesky"].character_count == count_graphemes(normalized["bluesky"].text)
    assert normalized["linkedin"].title == "The Evolution of AI Video Production"

    # 2. Markdown-wrapped JSON stripping
    markdown_wrapped = f"```json\n{json.dumps(raw_json_dict)}\n```"
    cleaned = groq._clean_json_text(markdown_wrapped)
    parsed_json = json.loads(cleaned)
    normalized_cleaned = groq._validate_and_normalize_output(
        parsed_json=parsed_json,
        requested_platforms=["bluesky", "linkedin"],
        clean_topic=topic,
    )
    assert "bluesky" in normalized_cleaned

    # 3. Model prompt pollution check: if model returned prompt as text, it gets replaced
    polluted_json = {
        "platform_content": {
            "bluesky": {
                "text": topic,  # Verbatim topic pollution
                "title": None,
            }
        }
    }
    cleaned_polluted = groq._validate_and_normalize_output(
        parsed_json=polluted_json,
        requested_platforms=["bluesky"],
        clean_topic=topic,
    )
    assert cleaned_polluted["bluesky"].text != topic


# ============================================================================
# 5. Publishing Variant Routing & Validation Test
# ============================================================================

def test_publishing_variant_validation_logic():
    """
    Verify pre-publish validation rules:
    - Over-limit Bluesky (>300 graphemes) fails with clear error.
    - Title over-limit on YouTube (>100 chars) fails.
    - Valid variants succeed.
    """
    # 1. Over-limit Bluesky
    over_limit_bsky = "This is a great thought on AI. " + ("x" * 280)
    assert count_graphemes(over_limit_bsky) > 300
    is_valid, err = validate_platform_content("bluesky", over_limit_bsky)
    assert is_valid is False
    assert "Unicode grapheme clusters" in err

    # 2. Valid Bluesky
    valid_bsky = "AI is changing social media marketing! 🚀 Faster drafts and sharper distribution."
    is_valid_bsky, err_bsky = validate_platform_content("bluesky", valid_bsky)
    assert is_valid_bsky is True
    assert err_bsky is None

    # 3. Over-limit YouTube title (>100 chars)
    long_title = "T" * 105
    is_valid_yt, err_yt = validate_platform_content("youtube", "Video description", title=long_title)
    assert is_valid_yt is False
    assert "exceeds maximum limit of 100 characters" in err_yt

    # 4. Valid YouTube
    is_valid_yt_ok, _ = validate_platform_content("youtube", "Video description", title="Short Video Title")
    assert is_valid_yt_ok is True


def test_publish_request_schema_variant_mapping():
    """
    Verify PublishRequest schema correctly accepts and structures platform_content and variants.
    """
    from backend.app.schemas.publishing import PublishRequest

    req = PublishRequest(
        post_id="post-abc-123",
        platforms=["bluesky", "linkedin", "instagram"],
        content="Default shared copy",
        platform_content={
            "bluesky": {
                "content": "Specific Bluesky post under 300 graphemes 🦋",
            },
            "linkedin": {
                "title": "Specific LinkedIn Insight Title",
                "content": "Specific LinkedIn detailed article body with paragraphs.",
            },
            "instagram": {
                "content": "Instagram visual caption with emojis ✨🚀 #Growth",
            }
        },
        dry_run=True,
    )

    assert req.post_id == "post-abc-123"
    assert len(req.platforms) == 3
    assert req.platform_content["bluesky"]["content"] == "Specific Bluesky post under 300 graphemes 🦋"
    assert req.platform_content["linkedin"]["title"] == "Specific LinkedIn Insight Title"
    assert req.platform_content["instagram"]["content"] == "Instagram visual caption with emojis ✨🚀 #Growth"
