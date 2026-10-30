import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class GroqService:
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY.strip()
        self.model = settings.GROQ_MODEL
        self._client = None

        if self.api_key and not self.api_key.startswith("gsk_your"):
            try:
                from groq import Groq
                self._client = Groq(api_key=self.api_key)
                logger.info(f"Groq client initialized with model {self.model}")
            except Exception as e:
                logger.warning(f"Could not initialize Groq client: {e}")

    async def generate_post(
        self,
        topic: str,
        tone: str = "Professional",
        content_type: str = "General Post",
        language: str = "English",
        include_hashtags: bool = True,
        platforms: Optional[list] = None,
        audience: Optional[str] = None,
        campaign_objective: Optional[str] = None,
    ) -> dict:
        """
        Generate social post copy using Groq LLM API.
        Generates base copy and platform-specific tailored variants.
        Falls back to structured offline generation if GROQ_API_KEY is not configured yet.
        """
        # If real Groq client is ready, call Groq API
        if self._client:
            candidate_models = [self.model, "openai/gpt-oss-120b", "qwen/qwen3.8-27b", "openai/gpt-oss-20b"]
            seen_models = set()
            models_to_try = [m for m in candidate_models if m and not (m in seen_models or seen_models.add(m))]

            for candidate in models_to_try:
                try:
                    platform_info = f"\nTarget Platforms: {', '.join(platforms)}." if platforms else ""
                    audience_info = f"\nAudience: {audience}." if audience else ""
                    objective_info = f"\nCampaign Objective: {campaign_objective}." if campaign_objective else ""

                    system_prompt = (
                        f"You are an expert social media strategist and copywriter. "
                        f"Write a high-converting, engaging social media post in {language}.\n"
                        f"Tone: {tone}.\n"
                        f"Content Type: {content_type}.{platform_info}{audience_info}{objective_info}\n"
                        f"{'Include 3-5 relevant, high-traffic hashtags at the end.' if include_hashtags else 'Do NOT include hashtags.'}\n"
                        f"Format cleanly with natural line breaks. Return ONLY the post text without conversational filler or quotation marks."
                    )

                    user_prompt = f"Topic / Concept: {topic}"

                    chat_completion = self._client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        model=candidate,
                        temperature=0.7,
                        max_tokens=600,
                        timeout=15.0,
                    )

                    content = chat_completion.choices[0].message.content.strip()

                    # Generate platform variants
                    variants = self.generate_platform_variants(content, platforms or ["linkedin", "bluesky"])

                    return {
                        "generated_text": content,
                        "tone": tone,
                        "language": language,
                        "provider": "Groq",
                        "model": candidate,
                        "variants": variants,
                    }
                except Exception as e:
                    logger.warning(f"Groq API call with model '{candidate}' failed: {e}")

            logger.error("All Groq candidate models failed. Activating fallback synthesizer.")

        # Fallback synthesizer if Groq API key is still pending in .env or failed
        fallback_text = self._fallback_synthesis(topic, tone, language, include_hashtags)
        variants = self.generate_platform_variants(fallback_text, platforms or ["linkedin", "bluesky"])
        return {
            "generated_text": fallback_text,
            "tone": tone,
            "language": language,
            "provider": "Local Synthesizer (Set GROQ_API_KEY in backend/.env for live Groq LLM)",
            "model": "offline-fallback",
            "variants": variants,
        }

    def generate_platform_variants(self, text: str, platforms: list) -> dict[str, str]:
        """
        Creates platform-tailored adaptations respecting character limits and formatting expectations.
        """
        variants = {}
        for plat in platforms:
            p = plat.lower()
            if p == "bluesky":
                # Bluesky 300-char strict limit with punchy hook
                lines = [l.strip() for l in text.split("\n") if l.strip()]
                hook = lines[0] if lines else text
                body = " ".join(lines[1:3]) if len(lines) > 1 else ""
                combined = f"{hook}\n\n{body}".strip()
                if len(combined) > 290:
                    combined = combined[:287] + "..."
                variants["bluesky"] = combined
            elif p == "linkedin":
                # LinkedIn: Thought leadership hook, clean spacing, clear CTA
                variants["linkedin"] = text + "\n\nWhat are your thoughts on this? Let's discuss in the comments below."
            elif p == "facebook":
                # Facebook: Conversational, community discussion
                variants["facebook"] = text + "\n\nDrop a comment and share your experience with our community!"
            elif p == "instagram":
                # Instagram: Visual caption with line breaks and engagement prompt
                variants["instagram"] = f"✨ Double-tap if this resonates!\n\n{text}\n\nSave this post for later 📌"
            else:
                variants[p] = text
        return variants

    def _fallback_synthesis(self, topic: str, tone: str, language: str, include_hashtags: bool) -> str:
        prompt = topic.strip() or "AI in Social Media Marketing"

        if language == "Hindi":
            text = (
                f"🚀 {prompt}\n\n"
                f"आर्टिफिशियल इंटेलिजेंस (AI) सोशल मीडिया मार्केटिंग और कंटेंट क्रिएशन को एक नए स्तर पर ले जा रहा है। "
                f"तेज गति, सटीक टार्गेटिंग और पर्सनलाइज्ड स्ट्रेटेजी से बिजनेस को बड़ा फायदा मिल रहा है।\n\n"
                f"भविष्य उन्हीं का है जो नई तकनीक को प्रभावी ढंग से अपनाते हैं!"
            )
            hashtags = "\n\n#आर्टिफिशियलइंटेलिजेंस #डिजिटलग्रोथ #सोशलमीडियामार्केटिंग #इनोवेशन"
        elif language == "Marathi":
            text = (
                f"🚀 {prompt}\n\n"
                f"आर्टिफिशियल इंटेलिजन्स (AI) मुळे सोशल मीडिया स्ट्रॅटेजी आणि बिझनेस ग्रोथला नवीन गती मिळत आहे। "
                f"कमी वेळात अचूक आणि प्रभावी कंटेंट पोहोचवणे आता सहज शक्य झाले आहे।\n\n"
                f"भविष्य तंत्रज्ञानासोबत पुढे जाणाऱ्यांचेच आहे!"
            )
            hashtags = "\n\n#डिजिटलमहाराष्ट्र #व्यवसायवाढ #सोशलमीडिया #इनोव्हेशन"
        elif language == "Spanish":
            text = (
                f"🚀 {prompt}\n\n"
                f"La inteligencia artificial está transformando radicalmente el marketing en redes sociales: "
                f"contenido más ágil, estratégico y personalizado.\n\n"
                f"¡El futuro pertenece a los creadores y marcas que aprovechan la IA de forma efectiva!"
            )
            hashtags = "\n\n#InteligenciaArtificial #MarketingDigital #Estrategia"
        elif language == "French":
            text = (
                f"📝 {prompt}\n\n"
                f"L'intelligence artificielle redéfinit la création de contenu sur les réseaux sociaux: "
                f"rapidité, pertinence et personnalisation accrue.\n\n"
                f"L'avenir appartient aux créateurs audacieux. Qu'en pensez-vous ?"
            )
            hashtags = "\n\n#IA #MarketingDigital #Innovation"
        elif language == "German":
            text = (
                f"💡 {prompt}\n\n"
                f"Künstliche Intelligenz revolutioniert das Social-Media-Marketing durch schnellere Workflows "
                f"und maßgeschneiderte Inhalte.\n\n"
                f"Die Zukunft gehört denjenigen, die KI gezielt einsetzen! Was ist Ihre Strategie?"
            )
            hashtags = "\n\n#KI #SocialMediaMarketing #Tech"
        else:
            if tone == "Casual":
                text = (
                    f"Quick thought on {prompt.lower()} 👋:\n\n"
                    f"Honestly, the productivity jump is wild. Instead of spending 3 hours on repetitive drafting, "
                    f"you spend 15 minutes refining high-impact hooks and visuals.\n\n"
                    f"The real secret? Using AI to brainstorm, then injecting your own authentic perspective."
                )
                hashtags = "\n\n#SocialMediaTips #AITools #CreatorEconomy"
            elif tone == "Witty":
                text = (
                    f"Hot take on {prompt.lower()} 🔥:\n\n"
                    f"AI won't replace human creators. But creators who use AI will certainly replace creators who don't.\n\n"
                    f"Work smarter, post sharper, and let the algorithm do the heavy lifting.\n\n"
                    f"Agree or disagree? Let's debate in the replies ⚡"
                )
                hashtags = "\n\n#MarketingHumor #TechTrends #Productivity"
            elif tone == "Inspiring":
                text = (
                    f"🌟 {prompt}\n\n"
                    f"We are witnessing the most significant democratisation of creative leverage in history.\n\n"
                    f"You no longer need a massive production studio to build a global audience—just a clear vision, "
                    f"relentless consistency, and intelligent tools to amplify your message.\n\n"
                    f"Build the future today."
                )
                hashtags = "\n\n#Inspiration #GrowthMindset #Leadership #FutureOfWork"
            else:
                text = (
                    f"{prompt} is changing the way high-growth creators build audiences.\n\n"
                    f"By streamlining production and personalizing distribution, creators can operate with the leverage "
                    f"of an entire media agency.\n\n"
                    f"The future belongs to operators who build repeatable, automated publishing workflows."
                )
                hashtags = "\n\n#AIMarketing #SocialMediaStrategy #ContentCreation #Growth"

        return text + (hashtags if include_hashtags else "")


groq_service = GroqService()
