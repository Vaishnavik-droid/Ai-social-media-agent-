import datetime
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "omnipulse-backend",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "environment": settings.ENVIRONMENT,
        "llm_provider": "Groq",
        "llm_model": settings.GROQ_MODEL,
        "groq_configured": bool(settings.GROQ_API_KEY and not settings.GROQ_API_KEY.startswith("gsk_your")),
    }
