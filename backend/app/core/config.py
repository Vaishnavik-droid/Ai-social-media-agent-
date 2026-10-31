import json
from pathlib import Path
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

# Collect env file paths from root and backend directories if they exist.
# Pydantic-settings reads files in sequence; later files take precedence.
# Process environment variables (os.environ) take highest precedence over all files.
_env_files: List[str] = []
for _p in [
    PROJECT_ROOT / ".env",
    BACKEND_DIR / ".env",
    PROJECT_ROOT / "platform_credentials.env",
    BACKEND_DIR / "platform_credentials.env",
]:
    if _p.is_file():
        _resolved = str(_p.resolve())
        if _resolved not in _env_files:
            _env_files.append(_resolved)


class Settings(BaseSettings):
    # =========================================================================
    # 1. Server & Application Environment
    # =========================================================================
    ENVIRONMENT: str = "development"
    APP_ENV: str = ""
    PORT: int = 8000
    HOST: str = "127.0.0.1"
    API_PREFIX: str = "/api/v1"

    # CORS Configuration
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # =========================================================================
    # 2. Publishing & Scheduler Engine
    # =========================================================================
    PUBLISHING_MODE: str = "mock"  # "mock" or "live"
    SCHEDULER_ENABLED: bool = True
    SCHEDULER_POLL_INTERVAL_SECONDS: int = 15
    CRON_SECRET: str = ""

    # =========================================================================
    # 3. Groq LLM Engine Configuration
    # =========================================================================
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # =========================================================================
    # 4. Supabase Persistence
    # =========================================================================
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_KEY: str = ""  # alias for SUPABASE_ANON_KEY

    # =========================================================================
    # 5. Authenticated Credential Encryption (At Rest)
    # =========================================================================
    TOKEN_ENCRYPTION_KEY: str = ""

    # =========================================================================
    # 6. Social Media Platforms (Configured via platform_credentials.env)
    # =========================================================================
    # --- SECTION 1: Application IDs & OAuth Client IDs ---
    # Meta Developer App (shared between Facebook and Instagram OAuth)
    META_APP_ID: str = "2231204290777395"
    META_REDIRECT_URI: str = ""

    # LinkedIn OAuth App
    LINKEDIN_CLIENT_ID: str = ""
    LINKEDIN_REDIRECT_URI: str = ""

    # Pinterest Developer App (Phase 2B readiness)
    PINTEREST_APP_ID: str = ""
    PINTEREST_REDIRECT_URI: str = ""
    PINTEREST_SANDBOX_TOKEN: str = ""

    # Google / YouTube OAuth App (Phase 2B readiness)
    GOOGLE_CLIENT_ID: str = ""
    YOUTUBE_REDIRECT_URI: str = ""

    # --- SECTION 2: Application Secrets ---
    META_APP_SECRET: str = ""
    LINKEDIN_CLIENT_SECRET: str = ""
    PINTEREST_APP_SECRET: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # --- SECTION 3: Bluesky AT Protocol ---
    BLUESKY_ENABLED: bool = False
    BLUESKY_HANDLE: str = ""
    BLUESKY_APP_PASSWORD: str = ""
    BLUESKY_SERVICE_URL: str = "https://bsky.social"

    # --- SECTION 4: Legacy Platform Reference Tokens ---
    # Kept for reference only; not used in active authentication, verification, or publishing.
    FACEBOOK_ENABLED: bool = False
    FACEBOOK_PAGE_ACCESS_TOKEN: str = ""
    FACEBOOK_PAGE_ID: str = ""

    INSTAGRAM_ENABLED: bool = False
    INSTAGRAM_ACCESS_TOKEN: str = ""
    INSTAGRAM_BUSINESS_ACCOUNT_ID: str = ""
    META_USER_TOKEN: str = ""

    LINKEDIN_ENABLED: bool = False
    LINKEDIN_ACCESS_TOKEN: str = ""
    LINKEDIN_AUTHOR_URN: str = ""

    model_config = SettingsConfigDict(
        env_file=tuple(_env_files) if _env_files else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
