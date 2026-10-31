# OmniPulse AI Social Media Agent — Comprehensive Repository Audit & Handover Report

**Document Date:** October 31, 2026  
**Audience:** Handover report for external engineering teams / AI assistants (ChatGPT, Claude, etc.)  
**Repository:** `Ai-social-media-agent-` (Branch: `main`)  
**Target Environment:** Unified Full-Stack Vercel Deployment (Vite + React 18 SPA + Python FastAPI Serverless)

---

## 1. Project Overview

OmniPulse is an autonomous, single-operator AI social media automation application designed to streamline content generation, cross-platform previewing, immediate multi-channel publishing, and future scheduling.

### Core Intent vs. Target Operational Scope
- **Operator Model:** Single-user / single-operator application. It explicitly rejects multi-tenant isolation, organization roles, team workspaces, and SaaS billing to maintain architectural simplicity.
- **Frontend Stack:** Modern React 18 SPA bundled with Vite 6 and TypeScript 5.6. Custom CSS design system with responsive layouts, 3D card tilt effects, multi-language preview tabs, and Meta developer onboarding drawers.
- **Backend Stack:** Python 3.12 + FastAPI with Pydantic v2 domain schemas, AsyncIO networking via HTTPX, and APScheduler / Vercel Cron orchestration.
- **AI Content Engine:** Groq API powered by `llama-3.3-70b-versatile` / `openai/gpt-oss-120b` with automated model fallback and a multilingual local offline copy synthesizer.
- **Persistence & Auth:** Supabase PostgreSQL with Row Level Security (RLS) policies and Supabase GoTrue Auth, backed by resilient in-memory and client-side `localStorage` fallbacks.
- **Automation Philosophy:** Complete retirement and removal of legacy Make.com webhooks; all scheduling, validation, and platform routing are native to FastAPI.

---

## 2. Current Repository Structure

The repository is structured as a unified monorepo where the root hosts the React/Vite frontend and deployment manifests, while the backend application is contained within `backend/` and bridged to Vercel Serverless Functions via `api/index.py`:

```
Ai-social-media-agent-/
├── .env.example                               # Unified root environment template (frontend + backend secrets)
├── .gitignore                                 # Git ignore (node_modules, dist, .venv, *.env)
├── implementation_plan_v2.md                  # Milestone tracking and architectural audit
├── index.html                                 # Single-page application HTML entrypoint
├── package.json                               # Frontend dependencies (@supabase/supabase-js, lucide-react, react)
├── package-lock.json                          # Pinned NPM dependency graph
├── README.md                                  # Comprehensive setup, PowerShell quickstart & test guide
├── requirements.txt                           # Root Python dependencies for Vercel Python runtime
├── tsconfig.json                              # TypeScript compiler configuration
├── vercel.json                                # Unified Vercel configuration (rewrites, crons, SPA fallback)
├── VERCEL_DEPLOYMENT.md                       # Intended deployment guide
├── vercel_environment_variables.env           # Deployment reference template
├── vite.config.ts                             # Vite configuration with local /api dev proxy
│
├── api/                                       # Vercel Serverless Function Directory
│   ├── index.py                               # Vercel entrypoint wrapping FastAPI with VercelPathMiddleware
│   └── requirements.txt                       # Mirrored Python dependencies for Vercel runtime
│
├── backend/                                   # FastAPI Backend Core
│   ├── .env.example                           # Backend-only environment template
│   ├── .gitignore                             # Backend gitignore (.venv, __pycache__, .env)
│   ├── requirements.txt                       # Backend Python dependencies
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                            # FastAPI ASGI application, lifespan, CORS, and Vercel Cron router
│   │   ├── api/
│   │   │   ├── deps.py                        # Common dependency stubs
│   │   │   └── v1/
│   │   │       └── routes/
│   │   │           ├── connections.py         # Social connection discovery & Meta OAuth/token verification
│   │   │           ├── generation.py          # AI post generation endpoint (/preview)
│   │   │           ├── health.py              # Service health status & Groq config diagnostic
│   │   │           ├── posts.py               # Post CRUD operations with Supabase + memory fallback
│   │   │           ├── publishing.py          # Live publishing dispatcher across platform adapters
│   │   │           └── scheduling.py          # Queue creation, inspection, cancellation & Vercel Cron endpoint
│   │   ├── core/
│   │   │   ├── config.py                      # Pydantic BaseSettings loading backend/.env
│   │   │   ├── logging.py                     # Structured logging configuration
│   │   │   └── security.py                    # Bearer token parsing and single-user authentication
│   │   ├── platforms/                         # Social Media Platform Adapters
│   │   │   ├── base.py                        # Abstract base class BasePlatformAdapter
│   │   │   ├── bluesky.py                     # AT Protocol v1 adapter (com.atproto)
│   │   │   ├── facebook.py                    # Meta Graph API v19.0 feed & photos adapter
│   │   │   ├── instagram.py                   # Meta Graph API v19.0 media container & publish adapter
│   │   │   └── linkedin.py                    # LinkedIn v2 ugcPosts REST adapter
│   │   ├── schemas/                           # Pydantic v2 Request/Response Schemas
│   │   │   ├── connection.py                  # ConnectionItem, ConnectionVerifyRequest/Response
│   │   │   ├── generation.py                  # GeneratePreviewRequest, GeneratePreviewResponse
│   │   │   ├── post.py                        # PostCreate, PostUpdate, PostResponse
│   │   │   ├── publishing.py                  # PublishRequest, PublishResponse, PlatformResult
│   │   │   └── scheduling.py                  # ScheduleCreate, ScheduleResponse, SchedulerHealthResponse
│   │   └── services/
│   │       ├── groq_service.py                # Groq LLM client, model fallback, & offline synthesizer
│   │       └── scheduling_service.py          # Background worker, atomic claiming, retries & orphan recovery
│   ├── tests/                                 # Automated Pytest Suite (30 Tests)
│   │   ├── test_adapters.py                   # Platform character validation, mock mode, & credential tests
│   │   ├── test_api.py                        # Route tests (/health, /posts, /generation, /connections, /publish)
│   │   ├── test_config.py                     # Deterministic configuration loading & secret leak tests
│   │   ├── test_e2e_workflow.py               # End-to-end simulated operator journey
│   │   └── test_scheduler.py                  # Queue persistence, claiming, exponential retries, & orphan recovery
│   └── tools/
│       └── generate_long_lived_token.py       # CLI utility to exchange short-lived Meta tokens for permanent Page tokens
│
├── docs/
│   └── context.md                             # Authoritative architectural lock-in document (2026-10-26)
│
├── public/
│   ├── logo.svg                               # Brand vector icon
│   └── social_media_ai_post.jpg               # Sample visual asset for testing media publishing
│
├── src/                                       # React 18 + Vite Frontend SPA
│   ├── App.tsx                                # Root component, navigation state, Supabase auth listener, post sync
│   ├── index.css                              # Design system, responsive classes, Meta OAuth drawer styling
│   ├── main.tsx                               # DOM mount
│   ├── vite-env.d.ts                          # Client environment variable type declarations
│   ├── components/
│   │   ├── Button.tsx                         # Reusable button component
│   │   ├── Header.tsx                         # Header with notifications dropdown and user profile pill
│   │   ├── PlatformIcon.tsx                   # SVG icons for Bluesky, LinkedIn, Facebook, Instagram, Twitter
│   │   ├── Sidebar.tsx                        # Left sidebar navigation with route badges
│   │   └── StatusBadge.tsx                    # Post status badges (Draft, Scheduled, Published, Failed)
│   ├── data/
│   │   └── mockData.ts                        # Initial seed data for posts, platforms, user profile, & metrics
│   ├── lib/
│   │   ├── api.ts                             # Typed central API client calling FastAPI with relative /api routing
│   │   └── supabase.ts                        # Browser Supabase JS client & connection latency tester
│   ├── pages/
│   │   ├── Auth.tsx                           # Login, Signup, Password Reset with Supabase + local fallback
│   │   ├── CreatePost.tsx                     # Creation studio with AI generation, live preview, inline editor
│   │   ├── Dashboard.tsx                      # Summary metrics, channel breakdown, and recent activity
│   │   ├── DataDeletion.tsx                   # Meta-compliant User Data Deletion Instructions
│   │   ├── Platforms.tsx                      # Channels page with Meta OAuth helper, App ID/Secret verification
│   │   ├── Posts.tsx                          # All Posts view with search, filter, and quick action menus
│   │   ├── PrivacyPolicy.tsx                  # Meta-compliant Privacy Policy with section navigation
│   │   ├── Scheduled.tsx                      # Scheduled queue management (Upcoming vs. Past tabs)
│   │   ├── Settings.tsx                       # Profile, Preferences, Notifications, Legal navigation
│   │   └── TermsOfService.tsx                 # Meta-compliant Terms of Service
│   └── types/
│       └── index.ts                           # Global TypeScript interfaces and platform types
│
└── supabase/
    └── migrations/
        └── 001_initial_schema.sql             # PostgreSQL schema with RLS policies and indexes
```

---

## 3. Actual Implemented Architecture

```
                                  Vercel Edge Network
                              (https://your-domain.vercel.app)
                                             │
                     ┌───────────────────────┴───────────────────────┐
                     │                                               │
             Path: /api/*, /health, /docs                       All other paths (SPA)
                     │                                               │
                     ▼                                               ▼
     ┌───────────────────────────────┐               ┌───────────────────────────────┐
     │   api/index.py (FastAPI ASGI) │               │   React 18 + Vite SPA         │
     │   - VercelPathMiddleware      │               │   - Dynamic SPA URL Router    │
     │   - Groq Multi-Model Fallback │               │   - Post Creation Studio      │
     │   - Social Platform Adapters  │               │   - Meta OAuth Drawer & Sync  │
     │   - Vercel Cron Endpoint      │               │   - Supabase Client Auth      │
     └──────────────┬────────────────┘               └───────────────┬───────────────┘
                    │                                                │
                    ├──────────────────────┬─────────────────────────┤
                    ▼                      ▼                         ▼
          ┌──────────────────┐   ┌───────────────────┐    ┌────────────────────┐
          │ Groq Cloud API   │   │ Supabase Postgres │    │  Social Networks   │
          │ Llama 3.3 / OSS  │   │ Auth + RLS Tables │    │  Bluesky / LinkedIn│
          └──────────────────┘   └───────────────────┘    │  Facebook / Insta  │
                                                          └────────────────────┘
```

### Architectural Realities vs. `context.md` & `VERCEL_DEPLOYMENT.md`
1. **Unified Monorepo:** Unlike early drafts that suggested separate deployment targets or an external Make.com engine, the codebase is consolidated into a single repository running on Vercel Edge.
2. **Stateless Resiliency:** Because serverless functions on Vercel are ephemeral, the publishing pipeline (`backend/app/api/v1/routes/publishing.py`) accepts post content and media URLs directly in the request payload, avoiding failures when in-memory caches are purged between invocations.
3. **Dual Persistence Model:** Database operations target Supabase PostgreSQL tables (`posts`, `post_platforms`, `scheduled_posts`). If Supabase credentials are not populated or fail due to network constraints, the backend seamlessly falls back to memory stores (`_MEMORY_POSTS`, `_MEMORY_SCHEDULES`), and the frontend mirrors state in `localStorage`.
4. **Vercel Cron Dual Trigger:** In production, continuous background loops (`asyncio.sleep`) are skipped (`os.environ.get("VERCEL")`), delegating schedule execution to `/api/cron/process-schedules` triggered by Vercel Cron and secured via `CRON_SECRET`.

---

## 4. Latest Development Work

Analysis of the 12 git commits from repository inception (`9cd0017`) to current HEAD (`e2d5543`) establishes the developer's exact recent progression:

### 1. Most Recently Added Functionality (Sat Oct 31, 2026 - Commit `e2d5543`)
- **Comprehensive Backend Automated Test Suite:** Implemented 30 automated tests across 5 test modules (`test_adapters.py`, `test_api.py`, `test_config.py`, `test_e2e_workflow.py`, `test_scheduler.py`). All tests run in mock/dry-run mode with zero live API side-effects.
- **Permanent Meta Token Generator Tool:** Authored `backend/tools/generate_long_lived_token.py` to exchange short-lived Facebook/Instagram tokens for 60-day user tokens and permanent (never-expiring) Page Access Tokens.
- **Supabase Database Schema Migration:** Created `supabase/migrations/001_initial_schema.sql` defining relational tables for `posts`, `post_platforms`, `scheduled_posts`, and `platform_connections` with Row Level Security (RLS) policies.
- **Full-Stack Documentation & Plan Update:** Wrote comprehensive quickstart, test execution, and deployment instructions in `README.md` and updated `implementation_plan_v2.md`.

### 2. Immediate Preceding Work (Fri Oct 30, 2026 - Commits `71afd05` through `5f5b64c`)
- **Supabase Service Role Key & Model Resilience (`71afd05`):** Added `SUPABASE_SERVICE_ROLE_KEY` support in `config.py` and `posts.py` to bypass RLS restrictions during backend persistence. Added multi-model fallback in `groq_service.py` (`openai/gpt-oss-120b`, `qwen/qwen3.8-27b`, `openai/gpt-oss-20b`).
- **Stateless Serverless Publishing (`22bbfb1`):** Updated `PublishRequest` schema and `publishing.py` to accept direct post content and media URLs from the client, ensuring Vercel serverless cold starts never 404 on draft IDs.
- **Sample Visual Asset Integration (`78c2647`):** Added `public/social_media_ai_post.jpg` and updated `mockPosts` to demonstrate multi-platform image publishing.
- **Meta OAuth Helper & Cross-Window Synchronization (`5f5b64c`, `2fac0a6`, `79a4688`):** Built an extensive Meta Developer OAuth configuration banner in `Platforms.tsx` displaying the exact Valid OAuth Redirect URI (`/platforms`), an interactive App ID & Secret verification drawer, and a cross-window `StorageEvent` listener that automatically activates Facebook/Instagram when returning from Meta authorization.
- **Legal Compliance Pages for Meta App Review (`d2629eb`, `53ef135`):** Created dedicated `/privacy`, `/terms`, and `/data-deletion` pages and updated `Auth.tsx` to ensure compliance with Meta Developer Platform Requirements.

### 3. Currently Being Developed / Incomplete
- **Durable Scheduling Execution:** While the schema and `scheduling_service.py` exist, column naming discrepancies between the SQL migration (`run_at`) and the service code (`scheduled_at`) prevent seamless Supabase queue persistence.
- **Twitter (X) and Pinterest Adapters:** Discussed in documentation and types, but entirely unbuilt in the backend.

---

## 5. Frontend Implementation Status

| Component / Page | File Path | Implementation Status | Features & Reality |
| :--- | :--- | :--- | :--- |
| **API Client** | `src/lib/api.ts` | **Implemented and verified** | Centralized client with auth token injection, relative `/api` routing, post CRUD, publishing dispatch, and schedule management. |
| **Supabase Client** | `src/lib/supabase.ts` | **Implemented and verified** | Browser `@supabase/supabase-js` client with session persistence and connection latency testing. |
| **Root Application** | `src/App.tsx` | **Implemented and verified** | Custom SPA routing (synchronizes URL pathname with `pushState`), Supabase session listener, post seeding on initial load, and toast notifications. |
| **Creation Studio** | `src/pages/CreatePost.tsx` | **Implemented and verified** | Topic input, tone/content-type/language selectors, real-time character counters, live platform preview tabs, inline preview editor, JPG/PNG image upload validation (≤ 10MB), and live Groq preview generation with offline fallback. |
| **Platforms Management** | `src/pages/Platforms.tsx` | **Implemented and verified** | Channels listing, Meta OAuth guidance drawer, redirect URI copy button, credentials input, and real-time backend verification. |
| **Posts View** | `src/pages/Posts.tsx` | **Implemented and verified** | Full post table with search, status filtering (All, Published, Scheduled, Draft, Failed), and action menus (Publish Now, Schedule, Delete). |
| **Scheduled Posts** | `src/pages/Scheduled.tsx` | **Partially implemented** | Tabbed table (Upcoming vs. Past). Displays posts filtered by `status === 'scheduled'`, but does not directly query the backend queue endpoint `api.listSchedules()`. |
| **Analytics Dashboard** | `src/pages/Dashboard.tsx` | **Implemented and verified** | Real-time post counts (Total, Published, Scheduled, Failed) dynamically derived from loaded posts. |
| **Settings** | `src/pages/Settings.tsx` | **Implemented and verified** | Profile management, content preferences (tone, language, hashtags), notification toggles, and legal navigation. |
| **Authentication** | `src/pages/Auth.tsx` | **Implemented and verified** | Supabase email/password sign-in and sign-up with password strength meter, local dev username bypass, and 3D tilting card effects. |
| **Compliance Pages** | `PrivacyPolicy.tsx`, `TermsOfService.tsx`, `DataDeletion.tsx` | **Implemented and verified** | Meta developer compliant legal documents with smooth section scrolling and print utilities. |

---

## 6. Backend Implementation Status

| Module | File Path | Status | Details |
| :--- | :--- | :--- | :--- |
| **FastAPI Core** | `backend/app/main.py` | **Implemented and verified** | Lifespan handling, multi-prefix route mounting (`/api/v1`, `/api`, `/`), CORS middleware for Vercel preview domains and localhost, and dedicated Vercel Cron endpoints. |
| **Configuration** | `backend/app/core/config.py` | **Implemented and verified** | Pydantic BaseSettings loading server secrets from `.env`. *Note: Discrepancy on `GROQ_MODEL` default identified in audit.* |
| **Health Route** | `backend/app/api/v1/routes/health.py` | **Implemented and verified** | Returns system health, UTC timestamp, environment mode, and Groq configuration status. |
| **Posts Route** | `backend/app/api/v1/routes/posts.py` | **Implemented and verified** | Post creation, listing with status filter, retrieval, patching, and deletion. Uses dual Supabase + memory caching. |
| **Publishing Route** | `backend/app/api/v1/routes/publishing.py` | **Implemented and verified** | Multi-platform publishing dispatch, supporting stateless payloads, dry-run simulation, and per-platform result recording. |
| **Connections Route**| `backend/app/api/v1/routes/connections.py` | **Implemented and verified** | Safe platform status inspection (zero secret leaks) and live verification against Bluesky, LinkedIn, and Meta Graph APIs. |
| **Scheduling Route** | `backend/app/api/v1/routes/scheduling.py` | **Implemented and verified** | Job creation, queue listing, job cancellation, health metrics, and Vercel Cron trigger endpoint. |
| **Vercel Entrypoint**| `api/index.py` | **Implemented and verified** | Python Serverless Function entrypoint with `VercelPathMiddleware` resolving rewritten URI paths. |

---

## 7. AI/Groq Integration Status

1. **Provider & Models:**
   - Primary LLM provider is the **Groq API** (`groq>=0.11.0`).
   - Default configured model in `config.py`: `openai/gpt-oss-120b`.
   - Fallback model list in `groq_service.py`: `[self.model, "openai/gpt-oss-120b", "qwen/qwen3.8-27b", "openai/gpt-oss-20b"]`.
2. **Server-Side Security:**
   - Groq API credentials (`GROQ_API_KEY`) reside exclusively in backend environment variables (`.env`). Never exposed in client bundles or `VITE_*` variables.
3. **Generation Workflow (`/api/v1/generation/preview`):**
   - Synthesizes post copy based on `topic`, `tone` (Professional, Casual, Witty, Inspiring), `content_type`, `language` (English, Hindi, Marathi, Spanish, French, German), and `include_hashtags`.
4. **Platform Tailoring (`generate_platform_variants`):**
   - **Bluesky:** Automatically reformats to an engaging hook + body and enforces strict truncation at 287 characters (within Bluesky's 300-char limit).
   - **LinkedIn:** Adds thought-leadership commentary framing and an engagement call-to-action (CTA).
   - **Facebook:** Adds community discussion prompts.
   - **Instagram:** Formats as an aesthetic visual caption with engagement hooks ("Double-tap if this resonates!").
5. **Offline Resiliency:**
   - If `GROQ_API_KEY` is missing, blank, or rate-limited across all candidate models, `groq_service.py` executes `_fallback_synthesis()`, generating high-quality localized copy in English, Hindi, Marathi, Spanish, French, or German.

---

## 8. Supabase and Database Status

### Migration & Tables (`supabase/migrations/001_initial_schema.sql`)
1. **`public.posts`:** Stores post metadata (`id TEXT PK`, `user_id UUID`, `title`, `snippet`, `content`, `media_url`, `tone`, `content_type`, `language`, `status`, `scheduled_at`, `created_at`, `updated_at`).
2. **`public.post_platforms`:** Relational delivery records per post (`post_id`, `platform`, `status`, `remote_post_id`, `remote_post_url`, `error_message`, `published_at`).
3. **`public.scheduled_posts`:** Queue records for worker execution (`id UUID PK`, `post_id`, `run_at TIMESTAMPTZ`, `status`, `attempts`, `max_attempts`, `last_attempt_at`, `error_message`).
4. **`public.platform_connections`:** Metadata and safe handle references (`user_id`, `platform`, `handle`, `connected_user`, `status`).

### Persistence Reality Check
- **Posts Survival:** Posts survive reloads. The frontend fetches from `/api/v1/posts` on mount and caches in `localStorage` (`ai_social_posts`).
- **Publishing Results:** Stored in `post_platforms` and reflected in `posts.status`.
- **Connection Metadata:** Stored in `localStorage` (`omnipulse_meta_credentials` and `ai_social_platforms`). The backend checks server `.env` or ephemeral verify requests, but **does not currently write back to the Supabase `platform_connections` table**.
- **Identified Schema Mismatch:**
  - `001_initial_schema.sql` defines `scheduled_posts.run_at TIMESTAMPTZ NOT NULL`.
  - `scheduling_service.py` attempts to insert and select using `scheduled_at` (lines 141, 158, 336).
  - Consequently, scheduled post writes to Supabase fail silently and fall back to the in-memory dictionary `_MEMORY_SCHEDULES`.

---

## 9. Social Platform Integration Matrix

| Platform | API Access | Authentication | Connection Verification | Publishing | Real Account Tested | Remaining Work |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Bluesky** | Implemented and verified | AT Protocol Session (`handle` + `app_password`) | Implemented and verified | Implemented and verified | Implemented but untested | Real credentials test; multi-image blob support. |
| **LinkedIn** | Implemented and verified | OAuth 2.0 Bearer Token + Author URN | Implemented and verified | Implemented and verified | Implemented but untested | Real credentials test; add image/media upload contract. |
| **Facebook** | Implemented and verified | Meta Graph API v19.0 Page Access Token | Implemented and verified | Implemented and verified | Implemented but untested | Test with live Facebook Page; verify token renewal. |
| **Instagram** | Implemented and verified | Meta Graph API v19.0 Business Account ID + Token | Implemented and verified | Implemented and verified | Implemented but untested | Test with live Instagram Business account; require public image URL. |
| **X (Twitter)** | Planned | None (OAuth 1.0a / 2.0 PKCE needed) | Not implemented | Not implemented | Not implemented | Implement `twitter.py` adapter, config variables, and API keys. |
| **Pinterest** | Not implemented | None (OAuth 2.0 needed) | Not implemented | Not implemented | Not implemented | Full research, adapter creation, and UI integration. |

---

## 10. Detailed Platform Investigation

### 1. Bluesky
- **Status:** Implemented and verified (`backend/app/platforms/bluesky.py`).
- **Endpoints:**
  - `POST https://bsky.social/xrpc/com.atproto.server.createSession`
  - `POST https://bsky.social/xrpc/com.atproto.repo.uploadBlob`
  - `POST https://bsky.social/xrpc/com.atproto.repo.createRecord` (`app.bsky.feed.post`)
- **Authentication:** AT Protocol session token (`accessJwt`) derived from handle and app password.
- **Environment Variables:** `BLUESKY_ENABLED`, `BLUESKY_HANDLE`, `BLUESKY_APP_PASSWORD`.
- **Credentials State:** Placeholders in `.env.example`; no active live credentials committed.
- **Connection Verification:** `validate_connection()` calls `createSession`.
- **Publishing:** Fully implemented for text and single image blob upload (from data URI or HTTP URL). Supports dry-run.
- **Limitations:** Strict 300-character ceiling. Relative media paths fallback to Vercel domain prefix.

### 2. LinkedIn
- **Status:** Implemented and verified (`backend/app/platforms/linkedin.py`).
- **Endpoints:**
  - `GET https://api.linkedin.com/v2/userinfo`
  - `POST https://api.linkedin.com/v2/ugcPosts`
- **Authentication:** OAuth 2.0 Bearer Token (`LINKEDIN_ACCESS_TOKEN`) and Author URN (`LINKEDIN_AUTHOR_URN`).
- **Environment Variables:** `LINKEDIN_ENABLED`, `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_AUTHOR_URN`.
- **Credentials State:** Placeholders only.
- **Connection Verification:** `validate_connection()` calls `userinfo` and validates status 200.
- **Publishing:** Text commentary is published with public visibility. Dry-run mode returns mock URN.
- **Limitations:** 3,000 character limit. **Media upload is not yet implemented** (`shareMediaCategory: "NONE"`). Requires LinkedIn Developer App with `w_member_social` permissions.

### 3. Facebook
- **Status:** Implemented and verified (`backend/app/platforms/facebook.py`).
- **Endpoints:**
  - `GET https://graph.facebook.com/v19.0/{page_id}`
  - `POST https://graph.facebook.com/v19.0/{page_id}/feed`
  - `POST https://graph.facebook.com/v19.0/{page_id}/photos`
  - `GET https://graph.facebook.com/oauth/access_token`
- **Authentication:** Meta Page Access Token (`FACEBOOK_PAGE_ACCESS_TOKEN`) and Page ID (`FACEBOOK_PAGE_ID`).
- **Environment Variables:** `FACEBOOK_ENABLED`, `FACEBOOK_PAGE_ACCESS_TOKEN`, `FACEBOOK_PAGE_ID`.
- **Credentials State:** Default App ID `2231204290777395` present in frontend helper; secrets are placeholders.
- **Connection Verification:** Validates against `/{page_id}` or via client credentials check.
- **Publishing:** Text published to feed; multipart base64 or remote URL images published to photos endpoint.
- **Limitations:** Must target a Facebook Page (personal user profiles unsupported by Meta API). Token requires `pages_manage_posts` and `pages_read_engagement`.

### 4. Instagram
- **Status:** Implemented and verified (`backend/app/platforms/instagram.py`).
- **Endpoints:**
  - `GET https://graph.facebook.com/v19.0/{account_id}`
  - `POST https://graph.facebook.com/v19.0/{account_id}/media` (Step 1: Container creation)
  - `POST https://graph.facebook.com/v19.0/{account_id}/media_publish` (Step 2: Publication)
- **Authentication:** Meta System User Token or Page Token with `INSTAGRAM_BUSINESS_ACCOUNT_ID`.
- **Environment Variables:** `INSTAGRAM_ENABLED`, `INSTAGRAM_ACCESS_TOKEN`, `INSTAGRAM_BUSINESS_ACCOUNT_ID`.
- **Credentials State:** Placeholders only.
- **Connection Verification:** Verified via `/{account_id}` with name and username fields.
- **Publishing:** 2-step media container creation and publication.
- **Limitations:** **Text-only posts are rejected by Instagram**. Requires a public HTTPS image URL (local `data:` URLs cannot be fetched by Meta servers). 2,200 character limit.

### 5. X (Twitter)
- **Status:** Planned / Not implemented in backend.
- **Code Reality:** UI icon exists in `PlatformIcon.tsx` and type `'twitter'` exists in `src/types/index.ts`. No backend adapter (`backend/app/platforms/twitter.py`) or configuration settings exist.
- **Requirements to Implement:** X API v2 app credentials, OAuth 1.0a / 2.0 PKCE, and handling of tier constraints (Free tier is write-only with tight monthly caps).

### 6. Pinterest
- **Status:** Not implemented.
- **Code Reality:** Completely absent from frontend, backend, schemas, and migrations.

---

## 11. Authentication and Security Status

1. **Single-User Scope:**
   - Architecture is intentionally designed for one operator. Unauthenticated requests are allowed in development mode or when single-user mode is active.
   - If an `Authorization: Bearer <token>` header is passed, `backend/app/core/security.py` parses it, and `posts.py` extracts the Supabase user ID or uses the primary operator UUID (`722cd994-8fbd-422d-afec-2f4111fb099d`).
2. **Secrets Protection:**
   - Zero secrets are compiled into client JS bundles. Groq keys, platform tokens, and Supabase service role keys reside strictly in backend environment variables.
   - `/api/v1/connections` endpoint returns safe handles (e.g. `@handle` or `Page ID: 123`) and never exposes tokens.
3. **CORS Restrictions:**
   - `CORSMiddleware` in `main.py` permits explicit local origins (`localhost:3000`, `127.0.0.1:3000`, `localhost:5173`, `localhost:8080`) and regex-matches production Vercel domains (`https://.*\.vercel\.app`).
4. **Vercel Cron Protection:**
   - `/api/cron/process-schedules` enforces authentication using `CRON_SECRET` via Bearer header or `?key=` query parameter.

---

## 12. Publishing Workflow

```
[CreatePost Studio]
       │ User clicks "Publish Now"
       ▼
[api.publishPost] ──> POST /api/v1/publishing/publish
                            │
                            ├─► Validates content & character constraints
                            ├─► Determines effective mode (Live vs. Mock via PUBLISHING_MODE)
                            │
                            ├─► Dispatches to BlueskyAdapter (300 char check, AT Protocol)
                            ├─► Dispatches to LinkedInAdapter (3000 char check, ugcPosts)
                            ├─► Dispatches to FacebookAdapter (Photo upload or feed post)
                            ├─► Dispatches to InstagramAdapter (Validates image URL, 2-step container)
                            │
                            ├─► Updates post status in memory & Supabase (posts table)
                            ├─► Upserts per-platform results in Supabase (post_platforms table)
                            │
                            ▼
                     Returns PublishResponse
                            │
                            ▼
[CreatePost / App.tsx] Updates UI badges, remote post URLs, and triggers success toast
```

- **Stateless Payload Fallback:** In `publishing.py`, if `post_id` is not present in memory or Supabase, the route reads `payload.content` and `payload.media_url` directly, preventing 404 errors during serverless cold starts.
- **Dry-Run Guarantee:** When `PUBLISHING_MODE=mock` (the default), all adapters return simulated post IDs (e.g. `at://...`, `urn:li:share:mock_...`) without making live network requests to social APIs.

---

## 13. Scheduling Workflow

1. **Scheduling Creation:**
   - User schedules a post in `CreatePost.tsx` or `Posts.tsx`.
   - Frontend calls `api.createSchedule()` (`POST /api/v1/schedules`).
   - Job is registered in `_MEMORY_SCHEDULES` and an attempt is made to upsert into Supabase `scheduled_posts`.
2. **Execution Engine (`scheduling_service.py`):**
   - **Local Development Mode:** A background AsyncIO polling task runs every 15 seconds.
   - **Vercel Serverless Mode:** The background loop is disabled on startup (`os.environ.get("VERCEL")`). Instead, Vercel Cron sends a daily GET request to `/api/cron/process-schedules` (or an external webhook triggers it more frequently).
3. **Atomic Claiming & Execution:**
   - `process_due_jobs_once()` acquires an `asyncio.Lock()` to prevent race conditions.
   - Due jobs (`scheduled_time <= NOW()`, `status = 'pending'`) are claimed by setting `status = 'processing'`.
   - The job is dispatched across the requested platform adapters with platform-tailored text variants.
4. **Exponential Retries & Orphan Recovery:**
   - If transient platform errors occur, the job is retried up to `max_attempts` (default 3) using exponential backoff ($10 \times 2^{\text{attempt}-1}$ seconds).
   - `recover_orphan_jobs()` runs on startup to detect jobs stranded in `'processing'` due to server restarts and resets them to `'pending'`.

---

## 14. Vercel Deployment Readiness

### Comparison Against `VERCEL_DEPLOYMENT.md`

| Requirement | Implementation Reality | Verdict |
| :--- | :--- | :--- |
| **Unified Project** | Root contains `package.json`, `src/`, `vercel.json`, and `api/index.py`. | ✅ Verified |
| **Serverless Entrypoint** | `api/index.py` correctly imports FastAPI and applies `VercelPathMiddleware`. | ✅ Verified |
| **Python Dependencies** | Both root `requirements.txt` and `api/requirements.txt` exist with all needed packages. | ✅ Verified |
| **Routing & SPA Fallback** | `vercel.json` rewrites `/api/(.*)`, `/health`, and `/docs` to `api/index.py`, and all other paths to `/index.html`. | ✅ Verified |
| **Vercel Cron Hook** | `vercel.json` specifies `"schedule": "0 0 * * *"` pointing to `/api/cron/process-schedules`. | ✅ Verified |
| **Environment Variable Parity**| Names in `config.py` match `.env.example` and `VERCEL_DEPLOYMENT.md`. | ✅ Verified |
| **Hobby Plan Limitations** | Vercel Hobby plan restricts Cron to once per day. Scheduled posts needing finer intervals require an external cron ping (e.g. cron-job.org). | ⚠️ Limitation Noted |
| **Stateless Worker Lifetime** | Background AsyncIO loops do not survive serverless container freeze; Vercel Cron invocation is properly implemented to compensate. | ✅ Verified |

---

## 15. Tests and Build Results

Actual check results executed in the environment:

### 1. Frontend Build & TypeScript Checks
- **Command:** `npm run build` (`tsc && vite build`)
- **Status:** **PASSED (0 Errors)**
- **Details:**
  - `npx tsc --noEmit` exited cleanly with 0 type errors.
  - Vite production bundle generated in 4.67s into `dist/`:
    - `dist/index.html`: 1.26 kB
    - `dist/assets/index-CDA9m8v8.css`: 88.82 kB
    - `dist/assets/index-DtVyAEex.js`: 568.20 kB

### 2. Backend Startup & ASGI Import Check
- **Command:** `python -c "from app.main import app; print(app.title)"`
- **Status:** **PASSED**
- **Output:** `App successfully imported: OmniPulse AI Social Media Agent API`
- **Vercel Function Import:** `python -c "from api.index import app"` **PASSED**

### 3. Automated Pytest Suite
- **Command:** `pytest -v` (in `backend/`)
- **Result:** **29 PASSED, 1 FAILED (30 tests total, runtime 1.43s)**
- **Passing Modules:**
  - `tests/test_adapters.py`: 10/10 PASSED (Bluesky, LinkedIn, Facebook, Instagram limits & mock mode)
  - `tests/test_api.py`: 6/6 PASSED (`/health`, `/`, `/posts`, `/generation/preview`, `/connections`, `/publishing`)
  - `tests/test_e2e_workflow.py`: 1/1 PASSED (Full simulated operator journey)
  - `tests/test_scheduler.py`: 6/6 PASSED (Health, create, list, cancel, dry-run dispatch, backoff, orphan recovery)
  - `tests/test_config.py`: 6/7 PASSED
- **Failure Root Cause Analysis:**
  - **Failing Test:** `tests/test_config.py::test_groq_and_supabase_configurations_loaded`
  - **Assertion Failure:** `assert settings.GROQ_MODEL == "llama-3.3-70b-versatile"` failed with `AssertionError: assert 'openai/gpt-oss-120b' == 'llama-3.3-70b-versatile'`.
  - **Reason:** In commit `71afd05`, the developer updated `config.py` default `GROQ_MODEL` to `"openai/gpt-oss-120b"`, while `test_config.py` still expects `"llama-3.3-70b-versatile"`. Setting `GROQ_MODEL=llama-3.3-70b-versatile` in `.env` makes 30/30 tests pass.

---

## 16. Known Bugs and Outstanding Issues

1. **`GROQ_MODEL` Default Discrepancy:**
   - In `backend/app/core/config.py` (line 42), `GROQ_MODEL: str = "openai/gpt-oss-120b"`.
   - In `.env.example`, `GROQ_MODEL=llama-3.3-70b-versatile`.
   - In `backend/tests/test_config.py` (line 86), the test asserts `"llama-3.3-70b-versatile"`.
   - *Impact:* Causes 1 unit test failure when run without an active `.env` file overriding the setting.
2. **`scheduled_posts` Column Name Mismatch (Database vs. Service Code):**
   - In `supabase/migrations/001_initial_schema.sql`, the queue timestamp column is named `run_at TIMESTAMPTZ NOT NULL`.
   - In `backend/app/services/scheduling_service.py` (lines 141, 158, 336), the service attempts to insert and select using `scheduled_at`.
   - *Impact:* When attempting to persist scheduled posts into Supabase, PostgREST returns a column mismatch error, forcing the scheduler to rely exclusively on ephemeral in-memory storage.
3. **Connection Metadata Not Written to Database:**
   - Frontend stores Meta App ID / secrets in `localStorage` (`omnipulse_meta_credentials`), but `backend/app/api/v1/routes/connections.py` does not write verified connection status to the Supabase `platform_connections` table.
4. **Scheduled Page Does Not Query Backend Schedule Queue:**
   - `src/pages/Scheduled.tsx` filters `posts` passed via props (`status === 'scheduled'`), rather than calling `api.listSchedules()` to display worker queue job statuses, attempts, and error diagnostics.
5. **Instagram Media Requirement Constraint:**
   - Instagram publishing will fail if the post does not include a publicly accessible HTTPS image URL (`data:` URLs are rejected).

---

## 17. Incomplete Features

1. **LinkedIn Media Uploads:**
   - `backend/app/platforms/linkedin.py` only publishes text (`"shareMediaCategory": "NONE"`). The multi-step register upload / asset upload contract for images is not yet implemented.
2. **X (Twitter) Adapter:**
   - Present in UI types and icons, but backend adapter `backend/app/platforms/twitter.py` is absent.
3. **Pinterest Adapter:**
   - Completely unbuilt across frontend, backend, and database schemas.
4. **User Preferences & Notification Persistence:**
   - Settings in `Settings.tsx` and notifications in `Header.tsx` are stored solely in `localStorage`. No Supabase tables exist for user preferences.

---

## 18. Recommended Next Development Steps

For the incoming developer or AI assistant, the recommended priority order is:

1. **Step 1: Fix the `scheduled_posts` Column Mismatch**
   - Align `backend/app/services/scheduling_service.py` and `supabase/migrations/001_initial_schema.sql` so both use `scheduled_at` (or `run_at`). Ensure `scheduled_time` is consistently mapped.
2. **Step 2: Reconcile `GROQ_MODEL` Configuration**
   - Align `backend/app/core/config.py` default with `test_config.py` and `.env.example` so `pytest` passes 30/30 cleanly out of the box.
3. **Step 3: Wire `Scheduled.tsx` to `api.listSchedules()`**
   - Update `src/pages/Scheduled.tsx` to fetch the real backend queue using `api.listSchedules()`, enabling visibility into job retry attempts, processing states, and execution logs.
4. **Step 4: Persist Verified Platform Connections into Supabase**
   - Update `POST /api/v1/connections/verify` in `connections.py` to write verified connection handles and status into `public.platform_connections`.
5. **Step 5: Implement LinkedIn Image Attachment Upload**
   - Add image asset registration (`com.linkedin.restli.common.ActionResponse` / `registerUpload`) to `backend/app/platforms/linkedin.py`.
6. **Step 6: Build the X (Twitter) Platform Adapter**
   - Create `backend/app/platforms/twitter.py` implementing `BasePlatformAdapter` using Twitter API v2 endpoints (`POST https://api.twitter.com/2/tweets`).

---

## 19. Important Files and Their Responsibilities

| File Path | Primary Responsibility |
| :--- | :--- |
| `api/index.py` | Vercel Python Serverless Function entry point; exposes `app` wrapped with `VercelPathMiddleware` to ensure clean path routing. |
| `vercel.json` | Master Vercel deployment routing specification; maps `/api/*` to `api/index.py`, schedules Vercel Crons, and directs frontend routes to `index.html`. |
| `backend/app/main.py` | FastAPI application initialization, lifespan startup/shutdown hooks, CORS configuration, and `/api/cron/process-schedules` handler. |
| `backend/app/core/config.py` | Central Pydantic `BaseSettings` container reading environment variables and providing safe defaults. |
| `backend/app/services/groq_service.py` | Groq LLM orchestration, model fallback chain, prompt generation, platform variant formatting, and offline multilingual synthesizer. |
| `backend/app/services/scheduling_service.py` | Background scheduling worker, atomic job claiming, exponential backoff retries, and startup orphan job recovery. |
| `backend/app/platforms/base.py` | Abstract Base Class defining `platform_name`, `validate_connection()`, and `publish_post()`. |
| `backend/app/platforms/bluesky.py` | Bluesky adapter implementing AT Protocol session creation, blob upload, and record posting. |
| `backend/app/platforms/linkedin.py` | LinkedIn adapter implementing v2 ugcPosts REST share publishing and author URN validation. |
| `backend/app/platforms/facebook.py` | Facebook adapter implementing Meta Graph API v19.0 feed posts and photo uploads. |
| `backend/app/platforms/instagram.py` | Instagram adapter implementing Meta Graph API v19.0 media container creation and publishing. |
| `backend/tools/generate_long_lived_token.py` | Interactive CLI tool for exchanging short-lived Meta tokens for permanent Page Access Tokens. |
| `supabase/migrations/001_initial_schema.sql` | Supabase PostgreSQL schema with RLS policies and indexes for posts, results, queue, and connections. |
| `src/lib/api.ts` | Central TypeScript API client wrapping all FastAPI REST endpoints with authentication header injection. |
| `src/lib/supabase.ts` | Browser Supabase client initialization and connection health check utility. |
| `src/App.tsx` | Main React application state controller, client-side route manager, Supabase auth synchronizer, and localStorage persistence mirror. |
| `src/pages/CreatePost.tsx` | AI-powered post creation studio with Groq preview generation, multi-platform preview tabs, and direct publish dispatch. |
| `src/pages/Platforms.tsx` | Social channels management page with Meta OAuth redirect helper, App ID/Secret verification, and cross-window sync. |
| `src/pages/Scheduled.tsx` | Scheduled queue viewing interface displaying upcoming and past posts. |

---

## 20. Phase 1: Authentication Architecture Overhaul (Completed)

### 20.1 Overview & Solved Problems
In Phase 1, the social account authentication and credential management system underwent a complete production-grade overhaul. The 6 core problems identified in the audit were resolved:

1. **Meta OAuth Popup Communication**: Replaced brittle window polling and localStorage listeners with server-side callback handling (`GET /api/v1/connections/meta/callback`) communicating to `window.opener` via `postMessage` using explicit, sanitized target origin validation (no wildcard `'*'`).
2. **Persistent Authentication**: Eliminated ephemeral in-memory and frontend-only states. All credentials and connections are persisted in Supabase (`platform_connections`), surviving browser reloads and Vercel serverless redeployments.
3. **App ID & Secret Security**: Removed manual App ID and App Secret fields from the frontend. Meta developer credentials (`META_APP_ID`, `META_APP_SECRET`, `META_REDIRECT_URI`) are strictly backend environment variables.
4. **Token Encryption at Rest**: Eliminated plaintext credentials from `localStorage`. Implemented authenticated symmetric encryption (`TokenEncryptionService` using Fernet / AES-128-CBC + HMAC-SHA256) via `TOKEN_ENCRYPTION_KEY`. Tokens are decrypted in-memory only by platform adapters during live publishing.
5. **Clean Environment Variables**: Separated static application configuration from dynamic user credentials. Bluesky, LinkedIn, Facebook, and Instagram tokens are stored in Supabase rather than bloating Vercel environment variables.
6. **Unified Platforms Dashboard**: Replaced the 816-line manual form in `Platforms.tsx` with a clean, modern card-based interface. Provides 1-click Meta OAuth popup connect, dedicated Bluesky and LinkedIn connect modals, and live connection status indicators with handles, IDs, Re-verify, and Disconnect actions.

### 20.2 Database Schema (`supabase/migrations/002_authentication_and_credentials.sql`)
- **`public.platform_connections`**: Added `account_id`, `account_name`, `encrypted_access_token`, `encrypted_refresh_token`, `token_expires_at`, `scopes`, `metadata`, and `last_verified_at`.
- **`public.oauth_states`**: Created table for tracking pending OAuth requests across distributed Vercel serverless instances, with index on `expires_at` and single-use atomic consumption.
- **Reconciliation**: Added `scheduled_at` alias column and backward-compatible trigger to `public.scheduled_posts`.

### 20.3 Platform Adapter Dynamic Credential Resolution
Each platform adapter (`FacebookAdapter`, `InstagramAdapter`, `LinkedInAdapter`, `BlueskyAdapter`) now implements `_resolve_credentials()`:
1. Queries `credential_service.get_credentials(platform_name)`.
2. Decrypts stored tokens in-memory if available.
3. Falls back to static environment variables (`settings.*`) if dynamic database credentials are not present.

### 20.4 Automated Verification & Test Results
- **Frontend Build**: `npx tsc --noEmit && npm run build` -> **0 TypeScript errors, bundle built cleanly in 4.09s**.
- **Backend Test Suite**: `pytest tests -v` -> **43/43 tests PASSED (100% pass rate)**.
  - 13 new authentication & connection tests (`tests/test_auth_and_connections.py`):
    - Symmetric token encryption and decryption.
    - Meta OAuth initiation for Facebook and Instagram with correct scopes.
    - Rejection of non-Meta platforms.
    - Expiration and rejection of invalid OAuth states.
    - Graceful handling of provider access cancellation.
    - Successful Facebook OAuth token exchange and Page retrieval.
    - Instagram business account requirement validation (fails gracefully if no business account linked).
    - Successful Instagram OAuth with linked Instagram Business Account.
    - Zero token/secret exposure in `/api/v1/connections` endpoint.
    - Bluesky AT Protocol connect and disconnect workflow.
    - LinkedIn `/v2/userinfo` connect and disconnect workflow.
  - 30 existing unit, adapter, scheduler, config, and E2E workflow tests passing cleanly.

---

## 21. Phase 2A: Platform Expansion & Platforms UI Refinement (Completed)

### 21.1 Overview & Dashboard Redesign
In Phase 2A, the Connected Platforms dashboard was completely redesigned into a clean, modern, responsive social media management interface:
- **Header**: Features the exact requested title (`Connected Platforms`), subtitle (`Manage your social media accounts and publishing connections.`), and a dynamic connection summary badge (`X of 6 platforms connected`) directly driven by server connection state rather than hardcoded numbers.
- **6 Platform Cards Grid**: Responsive 1-col (mobile), 2-col (tablet), and 3-col (desktop) grid displaying:
  1. **Bluesky**: Decentralized AT Protocol broadcast updates.
  2. **LinkedIn**: Professional commentary, articles, and updates.
  3. **Facebook**: Meta Page feed posts and photo updates.
  4. **Instagram**: Professional Business feed visuals, carousels, and captions.
  5. **Pinterest**: Visual Discovery & outbound link Pins (Coming Soon).
  6. **YouTube**: Video uploads, Shorts, descriptions, and tags (Coming Soon).
- **Recognizable Platform Branding**: Authentic, high-contrast SVG brand marks added for Pinterest (`#E60023` stylized P) and YouTube (`#FF0000` iconic play badge).
- **Confirmation Modal for Disconnect**: Replaced native browser alerts with a polished in-app confirmation modal warning the user before deleting credentials from Supabase.
- **Strict Separation of Operational vs. Coming Soon**:
  - Operational platforms (`bluesky`, `linkedin`, `facebook`, `instagram`) support live 1-click connect, credential entry, real-time verification, and disconnect.
  - Coming Soon platforms (`pinterest`, `youtube`) display their official platform identity, informative development status, and disabled `Coming soon` action buttons. No fake connections, nonfunctional OAuth links, or mock authorizations are exposed.

### 21.2 Platform Support Matrix

| Platform | Type | Status | Auth Mechanism | Publishing Capability | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Bluesky** | Operational | Connected / Disconnected | AT Protocol `createSession` with App Password | Live post + embedded images via AT Protocol | Encrypted in Supabase |
| **LinkedIn** | Operational | Connected / Disconnected | OAuth 2.0 Bearer Token (`w_member_social`) | Live text updates via `ugcPosts` API | Encrypted in Supabase |
| **Facebook** | Operational | Connected / Disconnected | Server-side Meta OAuth code exchange to long-lived Page Token | Live feed posts & photos via Graph API v19.0 | Encrypted in Supabase |
| **Instagram** | Operational | Connected / Disconnected | Server-side Meta OAuth with linked Professional Business Account | Media container creation & publish via Graph API v19.0 | Encrypted in Supabase |
| **Pinterest** | Planned | **Coming soon** | OAuth 2.0 Authorization Code Grant | Pin creation (`POST /v5/pins`) | Prerequisites documented below |
| **YouTube** | Planned | **Coming soon** | Google OAuth 2.0 with offline refresh token | Video upload (`POST /upload/youtube/v3/videos`) | Prerequisites documented below |

### 21.3 External Developer-Console Prerequisites for Future Platforms

#### Pinterest Integration Requirements (Phase 2B)
To enable operational Pinterest integration in a future milestone, the following external developer prerequisites are required:
1. **Pinterest Business Account**: Create or convert to a Pinterest Business Account at [business.pinterest.com](https://business.pinterest.com/).
2. **Pinterest Developer App**:
   - Register an app at the [Pinterest Developer Portal](https://developers.pinterest.com/apps/).
   - Obtain `PINTEREST_APP_ID` and `PINTEREST_APP_SECRET`.
   - Set **Redirect URI** to: `https://<your-project>.vercel.app/api/v1/connections/pinterest/callback` (production) and `http://localhost:8000/api/v1/connections/pinterest/callback` (local dev).
3. **Required OAuth Scopes**:
   - `boards:read` (discover boards for destination pin routing).
   - `pins:read` & `pins:write` (create and publish pins).
   - `user_accounts:read` (retrieve user profile and handle).
4. **App Approval & Rate Limits**:
   - Pinterest defaults new apps to a **Trial** tier (sandbox rate limit of 10 requests per minute and access limited to 5 registered developer test users).
   - Upgrading to **Standard** tier requires submitting the app for review with privacy policy, terms, and video walkthrough of the integration.
5. **Publishing Contract**:
   - `POST https://api.pinterest.com/v5/pins` requires `board_id`, `media_source` (public image URL), and optional `title`, `description`, and `link`.

#### YouTube Data API v3 Requirements (Phase 2B)
To enable operational YouTube video uploads in a future milestone, the following external Google Cloud prerequisites are required:
1. **Google Cloud Project**:
   - Create a project in [Google Cloud Console](https://console.cloud.google.com/).
   - Enable the **YouTube Data API v3** in APIs & Services.
2. **OAuth 2.0 Credentials**:
   - Create an OAuth 2.0 Client ID for a **Web Application**.
   - Obtain `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`.
   - Authorized Redirect URI: `https://<your-project>.vercel.app/api/v1/connections/youtube/callback`.
3. **OAuth Consent Screen & Verification**:
   - User Type: External.
   - Required Scope: `https://www.googleapis.com/auth/youtube.upload` (to upload videos and edit metadata) and `https://www.googleapis.com/auth/youtube.readonly` (to retrieve channel name and ID).
   - **Important Security Constraint**: `youtube.upload` is classified by Google as a **Sensitive / Restricted Scope**. Without completing Google App Verification (domain ownership verification, privacy policy, and OAuth consent audit), only designated test Google accounts (maximum 100) can authorize the app, and unverified app warning screens will appear.
4. **Daily Quota Limitations**:
   - Google assigns a default project quota of **10,000 units per day**.
   - Video upload operations (`videos.insert`) consume **1,600 units per upload**.
   - Under the default quota, a single project can upload a maximum of **6 videos per 24-hour window** across all channels. Increasing this quota requires a formal Google Quota Extension request.

### 21.4 Automated Verification & Test Results
- **Frontend TypeScript & Vite Production Build**: `npx tsc --noEmit && npm run build` -> **0 TypeScript errors, bundle built cleanly in 4.04s (`dist/assets/index-Cp1LgrID.js`, `index-C5YZbd0X.css`)**.
- **Backend Test Suite**: `pytest tests -v` -> **46/46 tests PASSED (100% pass rate)**.
  - Added 3 new Phase 2A tests in `tests/test_auth_and_connections.py`:
    - `test_six_platform_registry_presence_and_coming_soon_status`: Confirms all 6 platforms are returned by `GET /api/v1/connections`, with Pinterest and YouTube marked `status="coming_soon"`, `is_coming_soon=True`, and `is_configured=False`.
    - `test_coming_soon_platforms_cannot_falsely_verify`: Confirms `POST /api/v1/connections/{pinterest|youtube}/verify` safely returns `is_valid=False` and `status="coming_soon"`.
    - `test_coming_soon_platforms_cannot_initiate_meta_oauth`: Confirms Meta authorization explicitly rejects Pinterest and YouTube.
  - All 43 prior tests (encryption, Meta OAuth popup, Bluesky connect, LinkedIn connect, token exposure security, config, scheduler, and e2e workflow) remain 100% passing.





---

## 22. Phase 2B: Environment Configuration Refactor & Platform Integration Readiness

### 22.1 Architecture Overview & Separation of Concerns
In Phase 2B, the environment configuration architecture was refactored to cleanly decouple core application/infrastructure variables from social media platform credentials into two dedicated configuration files:

1. **`.env` (Core Application & Infrastructure)**:
   - Server & runtime: `ENVIRONMENT`, `PORT`, `HOST`, `API_PREFIX`.
   - Cross-Origin Resource Sharing: `CORS_ORIGINS`.
   - Publishing engine: `PUBLISHING_MODE` (`mock` | `live`), `SCHEDULER_ENABLED`, `SCHEDULER_POLL_INTERVAL_SECONDS`.
   - Groq LLM Post Synthesis: `GROQ_API_KEY`, `GROQ_MODEL`.
   - Supabase Persistence: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`.
   - Authenticated Token Encryption: `TOKEN_ENCRYPTION_KEY` (Fernet 32-byte urlsafe base64 key).
   - Vercel Cron Security: `CRON_SECRET`.
   - Frontend Vite Client: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_SUPABASE_PUBLISHABLE_KEY`, `VITE_API_BASE_URL`.

2. **`platform_credentials.env` (Social Media Platform Configuration)**:
   - **Section 1: Application IDs & OAuth Client IDs**:
     - `META_APP_ID`: Meta Developer App ID (shared between Facebook and Instagram OAuth).
     - `META_REDIRECT_URI`: Meta OAuth callback URI.
     - `LINKEDIN_CLIENT_ID` & `LINKEDIN_REDIRECT_URI`: LinkedIn OAuth app settings.
     - `PINTEREST_APP_ID` & `PINTEREST_REDIRECT_URI`: Pinterest Developer App settings.
     - `GOOGLE_CLIENT_ID` & `YOUTUBE_REDIRECT_URI`: Google Cloud OAuth credentials for YouTube.
   - **Section 2: Application Secrets (Server-Only)**:
     - `META_APP_SECRET`: Meta Developer App secret.
     - `LINKEDIN_CLIENT_SECRET`: LinkedIn OAuth client secret.
     - `PINTEREST_APP_SECRET`: Pinterest OAuth application secret.
     - `GOOGLE_CLIENT_SECRET`: Google OAuth client secret.
   - **Section 3: Bluesky AT Protocol**:
     - `BLUESKY_HANDLE`: AT Protocol identifier.
     - `BLUESKY_APP_PASSWORD`: App password generated in Bluesky settings.
     - `BLUESKY_SERVICE_URL`: AT Protocol PDS host (defaults to `https://bsky.social`).
     - `BLUESKY_ENABLED`: Status flag.
   - **Section 4: Legacy Platform Tokens (Reference Only)**:
     - Retains `FACEBOOK_PAGE_ACCESS_TOKEN`, `FACEBOOK_PAGE_ID`, `INSTAGRAM_ACCESS_TOKEN`, `INSTAGRAM_BUSINESS_ACCOUNT_ID`, `META_USER_TOKEN`, `LINKEDIN_ACCESS_TOKEN`, and `LINKEDIN_AUTHOR_URN`.
     - Explicitly annotated and blocked: these values are preserved for audit reference only and are strictly excluded from active authentication, publishing, verification, and fallback recovery paths.

### 22.2 Platform Readiness (Pinterest & YouTube)
To ensure seamless future integration without requiring subsequent configuration refactors:
- `backend/app/core/config.py` now natively registers `PINTEREST_APP_ID`, `PINTEREST_APP_SECRET`, and `PINTEREST_REDIRECT_URI`.
- `backend/app/core/config.py` now natively registers `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `YOUTUBE_REDIRECT_URI`.
- `BLUESKY_SERVICE_URL` is now supported and dynamically utilized by `BlueskyAdapter` across all XRP/AT Protocol requests (`uploadBlob`, `createRecord`, `createSession`).
- Safe default string values ensure that missing platform credentials never crash application boot or test runners.

### 22.3 Legacy Fallback Elimination
- **`FacebookAdapter`**: Removed `settings.FACEBOOK_PAGE_ACCESS_TOKEN` from `_resolve_credentials`. Live publishing now strictly queries encrypted Supabase storage via `credential_service.get_credentials("facebook")`.
- **`InstagramAdapter`**: Removed `settings.INSTAGRAM_ACCESS_TOKEN`, `settings.META_USER_TOKEN`, and `settings.FACEBOOK_PAGE_ACCESS_TOKEN` fallbacks. Live publishing now strictly queries encrypted Supabase storage via `credential_service.get_credentials("instagram")`.
- **`CredentialService`**: Removed static Meta credential fallbacks in `get_safe_connection_item`. Added explicit handling for disconnected state (`record.get("status") == "disconnected"`), ensuring that manually disconnected accounts never revert to static environment credentials.

### 22.4 Environment File Precedence & Security Policy
- Loading Order in `backend/app/core/config.py`:
  1. Root `.env`
  2. Backend `.env`
  3. Root `platform_credentials.env`
  4. Backend `platform_credentials.env`
  5. Process Environment Variables (`os.environ`) — highest precedence, preserving Vercel production serverless execution.
- Security & Git:
  - Both `.gitignore` and `backend/.gitignore` updated with explicit exclusion rules for `*.env` and `platform_credentials.env`.
  - Whitelisted example templates: `.env.example`, `platform_credentials.env.example`, `backend/.env.example`, and `backend/platform_credentials.env.example`.
  - Zero modifications or deletions made to existing user environment files.

### 22.5 Automated Verification & Quality Gates
- **Pytest Suite**: **55 of 55 tests passed (100% pass rate)**.
  - 9 new automated tests in `backend/tests/test_environment_config.py`:
    - `test_core_settings_loaded_properly`: Verifies `.env` variables (server, Groq, Supabase, encryption key).
    - `test_platform_credentials_loaded_from_platform_env`: Verifies `platform_credentials.env` loading.
    - `test_pinterest_and_youtube_readiness`: Verifies Pinterest and YouTube variables and defaults.
    - `test_process_environment_variable_precedence`: Verifies `os.environ` overrides file values.
    - `test_multi_env_file_resolution_order`: Verifies clean merging of multi-file Pydantic settings.
    - `test_legacy_facebook_tokens_not_used_in_active_publishing`: Proves legacy FB tokens are ignored without Supabase credentials.
    - `test_legacy_instagram_tokens_not_used_in_active_publishing`: Proves legacy IG tokens are ignored without Supabase credentials.
    - `test_legacy_meta_tokens_do_not_report_connected_status`: Verifies unauthenticated Meta platforms report disconnected.
    - `test_bluesky_service_url_configuration`: Verifies dynamic PDS host resolution.
- **Frontend Quality**:
  - `npx tsc --noEmit` -> **0 TypeScript errors**.
  - `npm run build` -> **Production bundle built cleanly**.
