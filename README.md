# OmniPulse — Autonomous AI Social Media Agent

OmniPulse is an autonomous, single-operator AI social media management system. It combines state-of-the-art LLM content orchestration via Groq (`llama-3.3-70b-versatile`), a durable database-backed scheduling engine with atomic claiming, and real social platform publishing adapters (Bluesky, LinkedIn, Facebook, Instagram).

---

## 🏗 Architecture Overview

```
                        ┌──────────────────────────────────────────────┐
                        │       React + Vite Frontend (Port 3000)      │
                        │   - Analytics, Calendar & Post Studio        │
                        │   - Dedicated Platform Pages                 │
                        │   - Direct API Integration                   │
                        └──────────────────────┬───────────────────────┘
                                               │ HTTP / REST
                                               ▼
                        ┌──────────────────────────────────────────────┐
                        │        FastAPI Backend (Port 8000)           │
                        │   - Groq Multi-Platform Variant Synthesizer  │
                        │   - Atomic-Claim Scheduling Engine           │
                        │   - Social Platform Adapters                 │
                        │   - Supabase Persistence + In-Memory Fallback│
                        └───────┬──────────────┬──────────────┬────────┘
                                │              │              │
           ┌────────────────────┴──┐    ┌──────┴──────┐    ┌──┴───────────────┐
           ▼                       ▼    ▼             ▼    ▼                  ▼
   [Bluesky Adapter]     [LinkedIn Adapter]   [Facebook]       [Instagram]
   AT Protocol v1        v2 ugcPosts / Shares Graph v19.0      Graph Media API
```

### Core Components
1. **Frontend (`ai social media agent mp2/`)**:
   - Modern, high-performance Vite + React 18 + TypeScript SPA.
   - Dedicated Channel Pages: `/platforms/bluesky`, `/platforms/linkedin`, `/platforms/facebook`, `/platforms/instagram`.
   - Real-time creation studio with AI variant generation, platform character counter, media previews, and calendar scheduling.

2. **Backend Engine (`backend/`)**:
   - **FastAPI Framework** with Pydantic v2 validation and AsyncIO concurrency.
   - **Groq LLM Engine**: Powered by `llama-3.3-70b-versatile` producing platform-tailored post variants respecting character limitations (Bluesky ≤ 300 chars, LinkedIn professional narrative ≤ 3,000 chars, Meta hashtags/engagements).
   - **Durable Scheduling Engine**:
     - Background async worker with 15s polling cycle.
     - Atomic task claiming (`status='processing'`) preventing duplicate dispatches.
     - Exponential backoff retry loop on transient platform failure.
     - Startup crash recovery loop restoring orphaned in-flight jobs.
     - Database persistence in Supabase `scheduled_posts` with zero-downtime memory store fallback.
   - **Social Adapters with Safe `dry_run` Mode**:
     - **Bluesky**: AT Protocol `com.atproto.repo.createRecord`, 300-char validation.
     - **LinkedIn**: LinkedIn v2 REST API share contract with author URN validation.
     - **Facebook**: Meta Graph API v19.0 feed publishing.
     - **Instagram**: Meta Graph API media container creation & publishing (enforces required image/video URL).

---

## 🚀 Quickstart Guide (Windows PowerShell)

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- (Optional) Groq API Key and Supabase account

---

### 1. Backend Setup & Run

Open a Windows PowerShell terminal:

```powershell
# Navigate to backend directory
cd "d:\ai social media agent mp23\backend"

# Activate the virtual environment
.\.venv\Scripts\Activate.ps1

# (Optional) Verify environment variables
# Copy .env.example to .env if not already present
if (-not (Test-Path .env)) { Copy-Item .env.example .env }

# Launch FastAPI development server
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The backend will be available at:
- **Interactive Swagger Docs**: `http://127.0.0.1:8000/docs`
- **Health Check**: `http://127.0.0.1:8000/health`
- **Scheduler Health**: `http://127.0.0.1:8000/api/v1/schedules/health`

---

### 2. Frontend Setup & Run

Open a second Windows PowerShell terminal:

```powershell
# Navigate to frontend directory
cd "d:\ai social media agent mp23\ai social media agent mp2"

# Install dependencies (if not installed)
npm.cmd install

# Start Vite dev server
npm.cmd run dev
```

The frontend will be accessible at `http://localhost:5173`.

---

## 🧪 Automated Test Suite

All automated tests execute in safe mock / `dry_run` mode with **zero live social media side-effects**.

### Run Backend Unit & Integration Tests (23/23 Passing)
```powershell
cd "d:\ai social media agent mp23\backend"
.\.venv\Scripts\python.exe -m pytest -v
```

**Test Coverage Summary (30 / 30 Tests Passing):**
- `tests/test_adapters.py` (10 tests): Validates character limits, missing credentials diagnostics, and mock dispatch for Bluesky, LinkedIn, Facebook, and Instagram.
- `tests/test_api.py` (6 tests): Validates `/health`, `/posts` CRUD, `/generation/preview`, `/connections`, and `/publishing`.
- `tests/test_config.py` (7 tests): Validates deterministic backend settings loading, unconfigured blank value safety, zero secret leaks, mock publishing defaults, and active platform registry.
- `tests/test_scheduler.py` (6 tests): Validates queue persistence, atomic claiming, job execution, cancellation, exponential retry backoff, and startup orphan recovery.
- `tests/test_e2e_workflow.py` (1 test): Validates complete operator journey (`Preview -> Persist -> Schedule -> Claim -> Dispatch -> Mock Publish -> Verify -> Unsupported Platform Rejection`).

### Run Frontend Typecheck & Build
```powershell
cd "d:\ai social media agent mp23\ai social media agent mp2"
npm.cmd run build
```
*(Compiles cleanly with 0 TypeScript and 0 Vite errors).*

---

## 🔒 Security & Minimal Environment Configuration

The application strictly separates browser-safe public variables from server-side secrets.

### 1. Frontend Environment (`ai social media agent mp2/.env.local`)
Only browser-safe variables prefixed with `VITE_` belong here. No API keys or tokens are ever exposed to the client bundle.
```dotenv
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key_here
VITE_SUPABASE_PUBLISHABLE_KEY=your_supabase_anon_key_here
VITE_API_BASE_URL=http://127.0.0.1:8000
```

### 2. Backend Environment (`backend/.env`)
The single source of truth for all server-side credentials and adapter keys:

```dotenv
# Server & Environment
ENVIRONMENT=development
PORT=8000
HOST=127.0.0.1
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"]

# Publishing Mode & Scheduling (Defaults to safe mock mode)
PUBLISHING_MODE=mock
SCHEDULER_ENABLED=true
SCHEDULER_POLL_INTERVAL_SECONDS=15

# Groq LLM Configuration
GROQ_API_KEY=
GROQ_MODEL=llama-3.3-70b-versatile

# Supabase Persistence
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=

# Platform 1: Bluesky (AT Protocol)
BLUESKY_ENABLED=false
BLUESKY_HANDLE=
BLUESKY_APP_PASSWORD=

# Platform 2: LinkedIn
LINKEDIN_ENABLED=false
LINKEDIN_ACCESS_TOKEN=
LINKEDIN_AUTHOR_URN=

# Platform 3: Facebook (Page Feed)
FACEBOOK_ENABLED=false
FACEBOOK_PAGE_ACCESS_TOKEN=
FACEBOOK_PAGE_ID=

# Platform 4: Instagram (Professional/Business)
INSTAGRAM_ENABLED=false
INSTAGRAM_ACCESS_TOKEN=
INSTAGRAM_BUSINESS_ACCOUNT_ID=
```

> **Safe Mock Guarantee**: With `PUBLISHING_MODE=mock`, all dispatches and scheduler cycles simulate realistic execution and produce mock remote IDs without calling live social network APIs. Set `PUBLISHING_MODE=live` only when you are ready to publish real posts.

---

## 📄 License
MIT License. Single-operator autonomous automation.
