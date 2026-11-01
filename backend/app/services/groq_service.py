import json
import logging
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.platform_constraints import (
    PLATFORM_CONSTRAINTS,
    count_graphemes,
    get_content_length,
    get_platform_rule,
    validate_platform_content,
)
from app.schemas.generation import PlatformContentVariant

logger = logging.getLogger(__name__)


class GroqService:
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY.strip() if settings.GROQ_API_KEY else ""
        self.model = settings.GROQ_MODEL
        self._client = None

        if self.api_key and not self.api_key.startswith("gsk_your"):
            try:
                from groq import Groq
                self._client = Groq(api_key=self.api_key)
                logger.info(f"Groq client initialized with default model {self.model}")
            except Exception as e:
                logger.warning(f"Could not initialize Groq client: {e}")

    def _build_system_prompt(
        self,
        platforms: List[str],
        content_type: str,
        tone: str,
        language: str,
        include_hashtags: bool,
        audience: Optional[str] = None,
        campaign_objective: Optional[str] = None,
        additional_instructions: Optional[str] = None,
    ) -> str:
        """
        Builds a comprehensive, centralized system prompt informing Groq of all
        selected platforms and their authoritative publishing constraints.
        """
        platform_instructions = []
        for p in platforms:
            rule = get_platform_rule(p)
            if not rule:
                continue
            guidance = (
                f"- {rule.name.upper()} ({rule.id}):\n"
                f"  * Maximum length: {rule.max_length} {rule.length_unit}.\n"
                f"  * Title supported: {'YES (separate title required/optional)' if rule.supports_title else 'NO (do NOT provide a separate title)'}.\n"
                f"  * Formatting instructions: {rule.formatting_guidance}\n"
            )
            platform_instructions.append(guidance)

        platform_specs = "\n".join(platform_instructions)

        return (
            "You are an expert multi-platform social media copywriter and growth strategist.\n\n"
            "CRITICAL ARCHITECTURAL RULES:\n"
            "1. The user's input topic/prompt is SOURCE INSTRUCTION / SUBJECT MATTER, NEVER a pre-made title or finished caption.\n"
            "   You must interpret the topic and author original, tailored content based on it.\n"
            "   NEVER copy the user prompt verbatim as the post title or body.\n"
            "2. Generate INDEPENDENT, platform-adapted variants for ONLY the requested platforms.\n"
            "   Do not copy an identical caption across all platforms when their conventions and limits differ.\n"
            "3. Platform limits are HARD CONSTRAINTS:\n"
            f"{platform_specs}\n"
            "4. For platforms where 'Title supported: NO' (such as Bluesky and Instagram), set 'title': null.\n"
            "5. For platforms where 'Title supported: YES' (such as YouTube, Pinterest, and LinkedIn), provide a compelling, high-converting 'title'.\n"
            f"6. Tone: {tone}. Language: {language}. Content Type: {content_type}.\n"
            f"{f'Target Audience: {audience}. ' if audience else ''}"
            f"{f'Campaign Objective: {campaign_objective}. ' if campaign_objective else ''}"
            f"{f'Additional Instructions: {additional_instructions}. ' if additional_instructions else ''}"
            f"{'Include 3-5 relevant, high-traffic hashtags.' if include_hashtags else 'Do NOT include hashtags.'}\n\n"
            "STRUCTURED OUTPUT CONTRACT:\n"
            "You must return ONLY a single valid JSON object matching this schema exactly, with NO markdown code blocks, backticks, or commentary:\n"
            "{\n"
            '  "topic_prompt": "<the user topic>",\n'
            '  "content_type": "<the content type>",\n'
            '  "platform_content": {\n'
            '    "<platform_id>": {\n'
            '      "title": "<string or null>",\n'
            '      "text": "<platform tailored content>",\n'
            '      "hashtags": ["#tag1", "#tag2"]\n'
            "    }\n"
            "  }\n"
            "}"
        )

    async def generate_post(
        self,
        topic: str,
        tone: str = "Professional",
        content_type: str = "General Post",
        language: str = "English",
        include_hashtags: bool = True,
        platforms: Optional[List[str]] = None,
        audience: Optional[str] = None,
        campaign_objective: Optional[str] = None,
        additional_instructions: Optional[str] = None,
        current_content: Optional[str] = None,
        target_single_platform: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate social post copy using Groq LLM API with structured JSON output.
        Adapts original content for each requested platform following authoritative constraints.
        """
        clean_topic = topic.strip() or "AI in Social Media Marketing"
        active_platforms = [p.lower().strip() for p in (platforms or ["linkedin"])]
        if not active_platforms:
            active_platforms = ["linkedin"]

        # If user requested regeneration for a specific single platform
        if target_single_platform and target_single_platform.lower() in active_platforms:
            platforms_to_generate = [target_single_platform.lower()]
        else:
            platforms_to_generate = active_platforms

        # 1. Attempt live Groq generation if client is available
        if self._client:
            candidate_models = [
                "openai/gpt-oss-120b",
                "qwen/qwen3.8-27b",
                "openai/gpt-oss-20b",
                self.model,
            ]
            seen = set()
            models_to_try = [m for m in candidate_models if m and not (m in seen or seen.add(m))]

            system_prompt = self._build_system_prompt(
                platforms=platforms_to_generate,
                content_type=content_type,
                tone=tone,
                language=language,
                include_hashtags=include_hashtags,
                audience=audience,
                campaign_objective=campaign_objective,
                additional_instructions=additional_instructions,
            )

            user_prompt = f"Topic / Instructions: {clean_topic}"
            if current_content:
                user_prompt += f"\nExisting draft context for reference/adaptation:\n{current_content}"

            for candidate in models_to_try:
                try:
                    logger.info(f"Calling Groq with model '{candidate}' for platforms: {platforms_to_generate}")
                    chat_completion = self._client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        model=candidate,
                        temperature=0.7,
                        max_tokens=1500,
                        response_format={"type": "json_object"},
                        timeout=20.0,
                    )

                    raw_content = chat_completion.choices[0].message.content.strip()
                    logger.debug(f"Groq raw structured output: {raw_content[:200]}...")

                    cleaned_content = self._clean_json_text(raw_content)
                    parsed_json = json.loads(cleaned_content)
                    validated_variants = self._validate_and_normalize_output(
                        parsed_json=parsed_json,
                        requested_platforms=platforms_to_generate,
                        clean_topic=clean_topic,
                    )

                    if validated_variants:
                        primary_text = next(iter(validated_variants.values())).text
                        return {
                            "topic_prompt": clean_topic,
                            "content_type": content_type,
                            "platform_content": validated_variants,
                            "provider": f"Groq ({candidate})",
                            "model": candidate,
                            "generated_text": primary_text,
                            "tone": tone,
                            "language": language,
                            "variants": {k: v.text for k, v in validated_variants.items()},
                        }
                except Exception as e:
                    logger.warning(f"Groq generation attempt with '{candidate}' failed: {e}")

            logger.error("All Groq model attempts failed. Engaging intelligent offline generator.")

        # 2. Intelligent offline fallback generator producing full structured output
        offline_variants = self._synthesize_offline_variants(
            topic=clean_topic,
            platforms=platforms_to_generate,
            tone=tone,
            content_type=content_type,
            language=language,
            include_hashtags=include_hashtags,
        )

        primary_text = next(iter(offline_variants.values())).text if offline_variants else ""
        return {
            "topic_prompt": clean_topic,
            "content_type": content_type,
            "platform_content": offline_variants,
            "provider": "OmniPulse Engine (Offline Synthesizer)",
            "model": "offline-synthesizer",
            "generated_text": primary_text,
            "tone": tone,
            "language": language,
            "variants": {k: v.text for k, v in offline_variants.items()},
        }

    @staticmethod
    def _clean_json_text(raw_text: str) -> str:
        """Strips markdown code fences and cleans json response text."""
        cleaned = raw_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[len("```json"):].strip()
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:].strip()
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()
        return cleaned

    def _validate_and_normalize_output(
        self,
        parsed_json: Dict[str, Any],
        requested_platforms: List[str],
        clean_topic: str,
    ) -> Dict[str, PlatformContentVariant]:
        """
        Validates JSON structure returned by the LLM, extracts platform content,
        enforces character & grapheme limits, and guarantees no topic-as-title pollution.
        """
        platform_dict = parsed_json.get("platform_content")
        if not isinstance(platform_dict, dict):
            # Attempt alternative root keys if model wrapped it
            if "platforms" in parsed_json and isinstance(parsed_json["platforms"], dict):
                platform_dict = parsed_json["platforms"]
            else:
                platform_dict = {}

        result: Dict[str, PlatformContentVariant] = {}

        for p in requested_platforms:
            rule = get_platform_rule(p)
            raw_item = platform_dict.get(p) or platform_dict.get(p.capitalize()) or {}

            if isinstance(raw_item, str):
                text_val = raw_item.strip()
                title_val = None
                hashtags_val = []
            elif isinstance(raw_item, dict):
                text_val = str(raw_item.get("text") or raw_item.get("content") or "").strip()
                title_val = raw_item.get("title")
                if title_val is not None:
                    title_val = str(title_val).strip()
                    if not title_val or title_val.lower() == "none" or title_val.lower() == "null":
                        title_val = None
                hashtags_val = raw_item.get("hashtags")
                if not isinstance(hashtags_val, list):
                    hashtags_val = []
                hashtags_val = [str(h) for h in hashtags_val if str(h).strip()]
            else:
                text_val = ""
                title_val = None
                hashtags_val = []

            # If model returned empty text for this platform, synthesize platform adaptation
            if not text_val:
                text_val = self._generate_single_platform_text(clean_topic, p, "Professional", "English", True)

            # Prevent user prompt from becoming the title or caption verbatim
            if text_val == clean_topic:
                text_val = self._generate_single_platform_text(clean_topic, p, "Professional", "English", True)

            # Disallow title for platforms that don't support titles
            if rule and not rule.supports_title:
                title_val = None
            elif rule and rule.supports_title and not title_val:
                title_val = self._generate_fallback_title(clean_topic, p)

            # Strictly enforce Bluesky 300-grapheme ceiling with intelligent preservation
            if p == "bluesky":
                graphemes = count_graphemes(text_val)
                if graphemes > 300:
                    logger.warning(f"Groq Bluesky post exceeded 300 graphemes ({graphemes}). Trimming intelligently.")
                    text_val = self._trim_to_grapheme_limit(text_val, 295)

            # Enforce Pinterest description limit (500 chars)
            if p == "pinterest" and len(text_val) > 500:
                text_val = text_val[:490].rsplit(" ", 1)[0] + "..."

            # Enforce YouTube title limit (100 chars)
            if title_val and len(title_val) > 100:
                title_val = title_val[:97].rsplit(" ", 1)[0] + "..."

            char_count = get_content_length(p, text_val)

            result[p] = PlatformContentVariant(
                text=text_val,
                title=title_val,
                hashtags=hashtags_val,
                character_count=char_count,
            )

        return result

    def _trim_to_grapheme_limit(self, text: str, max_graphemes: int = 295) -> str:
        """Trims text to strictly fit within max_graphemes, preserving complete words and ellipses."""
        try:
            import grapheme
            grapheme_list = list(grapheme.graphemes(text))
            if len(grapheme_list) <= max_graphemes:
                return text
            truncated = "".join(grapheme_list[: max_graphemes - 3]).rstrip() + "..."
            return truncated
        except Exception:
            # Fallback character slice
            if len(text) <= max_graphemes:
                return text
            return text[: max_graphemes - 3].rsplit(" ", 1)[0] + "..."

    def _generate_fallback_title(self, topic: str, platform: str) -> str:
        """Generates a professional platform title based on the topic without literal duplication."""
        clean = topic.strip().capitalize()
        if platform == "youtube":
            return f"How {clean}: Complete Strategy & Guide"[:95]
        elif platform == "pinterest":
            return f"Guide to {clean}"[:95]
        elif platform == "linkedin":
            return f"Key Insights on {clean}"[:115]
        return clean[:95]

    def _generate_single_platform_text(
        self,
        topic: str,
        platform: str,
        tone: str,
        language: str,
        include_hashtags: bool,
    ) -> str:
        """Generates an authentic, platform-tailored post for a specific platform."""
        p = platform.lower().strip()
        subject = topic.strip()

        if p == "bluesky":
            # Must strictly be under 300 grapheme clusters
            hook = f"The landscape of {subject.lower()} is moving fast."
            body = "Creators and brands building repeatable workflows today will lead tomorrow's audience retention."
            tags = " #Strategy #Growth" if include_hashtags else ""
            res = f"{hook}\n\n{body}{tags}"
            if count_graphemes(res) > 295:
                res = self._trim_to_grapheme_limit(res, 290)
            return res

        elif p == "linkedin":
            lines = [
                f"How is {subject.lower()} redefining industry standards?",
                "",
                "Three decisive factors distinguish top-performing operators in this space:",
                "• Accelerated production velocity with zero compromise on quality",
                "• Precision targeting fueled by real-time audience engagement signals",
                "• Scalable workflows that turn one core idea into multi-channel momentum",
                "",
                "The shift isn't coming—it's already here.",
                "",
                "What has been your biggest observation in this area? Let's connect in the comments.",
            ]
            tags = "\n\n#Leadership #Innovation #Strategy #Growth" if include_hashtags else ""
            return "\n".join(lines) + tags

        elif p == "instagram":
            lines = [
                f"✨ The game-changer: {subject}",
                "",
                "Why high-growth creators are doubling down right now:",
                "1️⃣ 10x faster execution without creative burnout",
                "2️⃣ Deeper audience connection through personalized touchpoints",
                "3️⃣ Smarter distribution across your entire content ecosystem",
                "",
                "Double-tap if you're building for the future! 📌 Save this post for later.",
            ]
            tags = "\n\n#ContentCreator #DigitalGrowth #Strategy #Inspiration" if include_hashtags else ""
            return "\n".join(lines) + tags

        elif p == "facebook":
            lines = [
                f"Big discussion today around {subject.lower()}! 💬",
                "",
                "We are seeing a major evolution in how creators, founders, and teams build their community presence. The ability to streamline execution while staying authentic is the ultimate competitive advantage.",
                "",
                "Have you explored this in your own journey? Drop your thoughts or questions below—let's share insights!",
            ]
            tags = "\n\n#Community #Discussion #Growth" if include_hashtags else ""
            return "\n".join(lines) + tags

        elif p == "pinterest":
            lines = [
                f"Actionable strategies for {subject.lower()}.",
                "Discover key frameworks, step-by-step tactics, and workflow optimizations designed to accelerate your growth.",
                "Click the link to explore the full breakdown and save to your boards!",
            ]
            tags = " #GrowthTips #Inspiration" if include_hashtags else ""
            return "\n\n".join(lines) + tags

        elif p == "youtube":
            lines = [
                f"In this deep dive, we explore {subject.lower()} and break down the actionable strategies you need to know.",
                "",
                "📌 Key Takeaways:",
                "00:00 - Introduction & Strategic Overview",
                "01:30 - Core Frameworks & Real-world Implementation",
                "03:45 - Key Optimization Techniques",
                "06:00 - Summary & Next Steps",
                "",
                "Subscribe for actionable breakdowns every week! Leave your questions in the comments.",
            ]
            tags = "\n\n#YouTubeCreators #Strategy #Growth" if include_hashtags else ""
            return "\n".join(lines) + tags

        else:
            return (
                f"{subject} is creating unprecedented leverage for modern operators.\n\n"
                f"By streamlining production and personalizing distribution, you operate with exponential momentum."
            )

    def _synthesize_offline_variants(
        self,
        topic: str,
        platforms: List[str],
        tone: str,
        content_type: str,
        language: str,
        include_hashtags: bool,
    ) -> Dict[str, PlatformContentVariant]:
        """
        Creates full structured output offline when Groq is unavailable,
        guaranteeing strict platform-aware adaptation and constraint compliance.
        """
        variants: Dict[str, PlatformContentVariant] = {}

        for p in platforms:
            rule = get_platform_rule(p)
            text = self._generate_single_platform_text(topic, p, tone, language, include_hashtags)
            title = self._generate_fallback_title(topic, p) if (rule and rule.supports_title) else None

            # Extract hashtags
            hashtags = [w for w in text.split() if w.startswith("#") and len(w) > 1]
            char_count = get_content_length(p, text)

            variants[p] = PlatformContentVariant(
                text=text,
                title=title,
                hashtags=hashtags,
                character_count=char_count,
            )

        return variants


groq_service = GroqService()
