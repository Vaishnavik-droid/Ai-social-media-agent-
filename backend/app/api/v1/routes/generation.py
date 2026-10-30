from fastapi import APIRouter
from app.schemas.generation import GeneratePreviewRequest, GeneratePreviewResponse
from app.services.groq_service import groq_service

router = APIRouter(prefix="/generation", tags=["Generation"])


@router.post("/preview", response_model=GeneratePreviewResponse)
async def generate_post_preview(payload: GeneratePreviewRequest):
    result = await groq_service.generate_post(
        topic=payload.topic,
        tone=payload.tone or "Professional",
        content_type=payload.content_type or "General Post",
        language=payload.language or "English",
        include_hashtags=payload.include_hashtags,
        platforms=payload.platforms,
        audience=payload.audience,
        campaign_objective=payload.campaign_objective,
    )
    return GeneratePreviewResponse(**result)
