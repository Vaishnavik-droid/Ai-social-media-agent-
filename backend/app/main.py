import datetime
import logging
import os
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.generation import router as generation_router
from app.api.v1.routes.posts import router as posts_router
from app.api.v1.routes.publishing import router as publishing_router
from app.api.v1.routes.connections import router as connections_router
from app.api.v1.routes.scheduling import router as scheduling_router
from app.api.v1.routes.media import router as media_router
from app.api.v1.routes.auth import router as auth_router
from app.services.scheduling_service import scheduling_service
from app.core.logging_redactor import SensitiveDataFilter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
for handler in logging.root.handlers:
    handler.addFilter(SensitiveDataFilter())

logger = logging.getLogger("omnipulse.backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 OmniPulse FastAPI Backend starting up...")
    logger.info(f"Target Environment: {settings.ENVIRONMENT}")
    logger.info(f"LLM Engine: Groq ({settings.GROQ_MODEL})")
    
    # In Vercel serverless functions, background infinite polling tasks are disabled.
    # Scheduled jobs are triggered by Vercel Cron via /api/cron/process-schedules.
    if os.environ.get("VERCEL"):
        logger.info("⚡ Vercel Serverless environment detected. Background polling loop skipped in favor of Vercel Cron.")
    else:
        await scheduling_service.start()
    
    yield
    
    logger.info("🛑 OmniPulse FastAPI Backend shutting down...")
    if not os.environ.get("VERCEL"):
        await scheduling_service.stop()


app = FastAPI(
    title="OmniPulse AI Social Media Agent API",
    description="Backend orchestration, Groq LLM service, Supabase persistence, and social publishing adapters.",
    version="1.0.0",
    lifespan=lifespan,
    redirect_slashes=False,
)

# CORS Configuration
origins = list(settings.CORS_ORIGINS) if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS]
for dev_origin in ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8080", "http://127.0.0.1:8080"]:
    if dev_origin not in origins:
        origins.append(dev_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root Health & Documentation Checks
for h_prefix in ["", "/api", "/api/v1", "/v1"]:
    app.include_router(health_router, prefix=h_prefix)

# Vercel Cron hooks (accessible with and without /api prefix)
@app.get("/api/cron/process-schedules")
@app.post("/api/cron/process-schedules")
@app.get("/cron/process-schedules")
@app.post("/cron/process-schedules")
async def vercel_cron_endpoint(
    authorization: Optional[str] = Header(None),
    cron_token: Optional[str] = Query(None, alias="key"),
):
    """
    Dedicated Vercel Cron execution endpoint.
    Invoked by Vercel Cron on production schedule, secured with CRON_SECRET.
    """
    expected_secret = settings.CRON_SECRET.strip() if settings.CRON_SECRET else ""
    if expected_secret:
        auth_token = ""
        if authorization:
            auth_token = authorization.replace("Bearer ", "").strip() if authorization.startswith("Bearer ") else authorization.strip()
        
        if auth_token != expected_secret and cron_token != expected_secret:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized: Invalid or missing CRON_SECRET.",
            )

    processed_count = await scheduling_service.process_due_jobs_once()
    return {
        "status": "success",
        "processed_jobs": processed_count,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

# API Endpoints (mounted under /api/v1, /api, /v1, and root for unified zero-404 routing)
for api_prefix in ["/api/v1", "/api", "/v1", ""]:
    app.include_router(generation_router, prefix=api_prefix)
    app.include_router(posts_router, prefix=api_prefix)
    app.include_router(publishing_router, prefix=api_prefix)
    app.include_router(connections_router, prefix=api_prefix)
    app.include_router(scheduling_router, prefix=api_prefix)
    app.include_router(media_router, prefix=api_prefix)
    app.include_router(auth_router, prefix=api_prefix)


@app.get("/")
async def root():
    return {
        "app": "OmniPulse AI Social Media Agent API",
        "docs": "/docs",
        "health": "/health",
        "api_health": "/api/health",
    }
