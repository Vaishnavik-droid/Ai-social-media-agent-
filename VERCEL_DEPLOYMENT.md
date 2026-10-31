# OmniPulse — Vercel Full-Stack Single-Project Deployment Guide

This guide describes how to deploy **OmniPulse AI Social Media Agent** (both the React + Vite frontend and Python FastAPI backend) to **Vercel** in **one unified project**, on **one repository**, and under **one domain**.

---

## 🏗 Architecture & Routing Overview

In this unified architecture, Vercel hosts both your static SPA assets and your FastAPI backend using Vercel Python Serverless Functions:

```
                                  Vercel Edge Network
                              (https://your-domain.vercel.app)
                                             │
                     ┌───────────────────────┴───────────────────────┐
                     │                                               │
               Path matches /api/*                             All other paths
                     │                                               │
                     ▼                                               ▼
     ┌───────────────────────────────┐               ┌───────────────────────────────┐
     │  Vercel Python Function       │               │  Vite React 18 SPA            │
     │  (api/index.py -> FastAPI)   │               │  (dist/index.html + assets)   │
     │  - Groq LLM post synthesizer  │               │  - Dashboard, Studio, Queue   │
     │  - Meta OAuth & Token Security│               │  - Clean Platforms Cards UI   │
     │  - Bluesky / Meta / LinkedIn  │               │  - Supabase client auth       │
     │  - Vercel Cron scheduled jobs │               │  - Multi-platform preview     │
     └───────────────────────────────┘               └───────────────────────────────┘
```

### URL Map

| Route Pattern | Handled By | Description |
| :--- | :--- | :--- |
| `https://your-domain.vercel.app/` | Vite Frontend | Main web dashboard |
| `https://your-domain.vercel.app/platforms` | Vite Frontend | Platform connection manager |
| `https://your-domain.vercel.app/posts` | Vite Frontend | Client-side React Router (SPA fallback) |
| `https://your-domain.vercel.app/api/health` | FastAPI (`health_router`) | Backend health check & provider status |
| `https://your-domain.vercel.app/api/v1/generation/preview` | FastAPI (`generation_router`)| AI post generation powered by Groq |
| `https://your-domain.vercel.app/api/v1/posts` | FastAPI (`posts_router`) | Post CRUD operations |
| `https://your-domain.vercel.app/api/v1/publishing/publish`| FastAPI (`publishing_router`)| Live social publishing dispatch |
| `https://your-domain.vercel.app/api/v1/connections` | FastAPI (`connections_router`) | Public token-free connection statuses |
| `https://your-domain.vercel.app/api/v1/connections/meta/authorize` | FastAPI (`connections_router`) | Initiates Meta OAuth flow & creates state |
| `https://your-domain.vercel.app/api/v1/connections/meta/callback` | FastAPI (`connections_router`) | Server-side Meta OAuth code exchange & popup postMessage |
| `https://your-domain.vercel.app/api/v1/connections/bluesky/connect` | FastAPI (`connections_router`) | Connects Bluesky via AT Protocol session |
| `https://your-domain.vercel.app/api/v1/connections/linkedin/connect` | FastAPI (`connections_router`) | Connects LinkedIn via bearer token |
| `https://your-domain.vercel.app/api/v1/connections/{platform}/verify` | FastAPI (`connections_router`) | Re-verifies active credentials |
| `https://your-domain.vercel.app/api/v1/connections/{platform}` | FastAPI (`connections_router`) | Disconnects platform & purges credentials |
| `https://your-domain.vercel.app/api/cron/process-schedules`| FastAPI (`scheduling_router`) | Vercel Cron worker endpoint |
| `https://your-domain.vercel.app/docs` | FastAPI Swagger | Interactive OpenAPI Swagger UI |

---

## 🔐 Authentication & Credential Architecture (Phase 1)

OmniPulse implements centralized, secure credential management:
- **Zero Frontend Secrets**: The frontend never receives, stores, or transmits App Secrets, raw OAuth tokens, or passwords. Plaintext credentials are never saved in `localStorage`.
- **Authenticated Encryption at Rest**: All access tokens, refresh tokens, and passwords are encrypted using Fernet (AES-128-CBC + HMAC-SHA256 authenticated encryption) via `TOKEN_ENCRYPTION_KEY`.
- **Durable Persistence**: Platform credentials are encrypted and persisted in Supabase PostgreSQL (`platform_connections`), surviving browser restarts and Vercel serverless re-deployments.
- **Single-Use OAuth State Verification**: OAuth states are stored in Supabase (`oauth_states`) with a 10-minute expiration and atomic single-use consumption to prevent replay attacks across distributed serverless instances.
- **Reliable Popup Handshake**: Meta OAuth opens a standard browser popup. Upon successful authorization, the backend callback transmits `OMNIPULSE_OAUTH_SUCCESS` to `window.opener` using explicit target origin validation (no wildcard `*`), then auto-closes.

---

## 📂 Project Structure

```
├── api/
│   └── index.py               # Vercel Serverless Function entry point (exports FastAPI `app`)
├── backend/
│   ├── app/
│   │   ├── api/v1/routes/     # FastAPI routers (health, generation, posts, publishing, scheduling, connections)
│   │   ├── core/config.py     # Pydantic Settings & environment variables
│   │   ├── core/encryption.py # Fernet token encryption at rest
│   │   ├── platforms/         # Social network adapters (Bluesky, LinkedIn, Facebook, Instagram)
│   │   ├── schemas/           # Pydantic v2 domain schemas
│   │   ├── services/          # CredentialService, SchedulerService
│   │   └── main.py            # FastAPI ASGI application initialization
│   ├── tests/                 # 43 Automated unit, e2e, and OAuth tests
│   └── requirements.txt       # Backend dependencies
├── src/
│   ├── components/            # Reusable React components & layout
│   ├── pages/                 # Clean Platform Cards UI, Studio, Queue, Dashboard
│   ├── lib/api.ts             # Typed API client (relative `/api` routing)
│   ├── lib/supabase.ts        # Browser Supabase client
│   └── index.css              # Global styling & design system
├── supabase/
│   └── migrations/
│       ├── 001_initial_schema.sql
│       └── 002_authentication_and_credentials.sql # Credentials encryption & OAuth states schema
├── public/                    # Static assets & favicon
├── .env.example               # Template with clean separation of frontend vs. backend secrets
├── index.html                 # HTML entrypoint
├── package.json               # Frontend dependencies & build script
├── requirements.txt           # Python dependencies for Vercel Python runtime
├── tsconfig.json              # TypeScript compiler configuration
├── vercel.json                # Vercel unified routing, crons, and SPA fallback
└── vite.config.ts             # Vite configuration with local `/api` dev proxy
```

---

## 🛠 Meta Developer App Configuration

Before deploying Meta OAuth (Facebook & Instagram), configure your Meta Developer Application:

1. Go to [Meta for Developers](https://developers.facebook.com/apps/) and select your App (`2231204290777395`).
2. Under **App Settings -> Basic**:
   - **App Domains**: Add `localhost` and `your-project.vercel.app`.
   - **Privacy Policy URL**: Provide a valid URL.
   - Click **Add Platform** -> **Website** -> Site URL: `https://your-project.vercel.app` (or `http://localhost:3000`).
3. Under **Use cases** or **Products** -> **Facebook Login for Business** -> **Settings**:
   - Enable **Client OAuth Login** and **Web OAuth Login**.
   - Under **Valid OAuth Redirect URIs**, add:
     - `http://localhost:8000/api/v1/connections/meta/callback` (for local dev)
     - `https://your-project.vercel.app/api/v1/connections/meta/callback` (for production)
4. Verify App Permissions:
   - For Facebook: `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`, `public_profile`.
   - For Instagram: `instagram_basic`, `instagram_content_publish`.

---

## 🚀 Step-by-Step Vercel Deployment Instructions

### Step 1: Run Database Migration in Supabase
In your [Supabase Dashboard](https://supabase.com/dashboard) -> **SQL Editor**, execute:
`supabase/migrations/002_authentication_and_credentials.sql`

This creates:
- Columns in `public.platform_connections`: `account_id`, `account_name`, `encrypted_access_token`, `encrypted_refresh_token`, `token_expires_at`, `scopes`, `metadata`, `last_verified_at`.
- Table `public.oauth_states` for serverless state validation with index on `expires_at`.
- Reconciles `scheduled_posts.scheduled_at` vs `run_at`.

### Step 2: Push Code to GitHub
```powershell
git add .
git commit -m "feat(auth): overhaul social authentication architecture with token encryption and 1-click Meta OAuth"
git push origin main
```

### Step 3: Configure Environment Variables in Vercel
In Vercel **Project Settings -> Environment Variables**, configure:

#### 1. Public Frontend Variables (Browser)
| Variable Name | Value Description |
| :--- | :--- |
| `VITE_SUPABASE_URL` | `https://tuhgbmuwtlyuhwennfes.supabase.co` |
| `VITE_SUPABASE_ANON_KEY` | Your Supabase publishable / anon key |
| `VITE_SUPABASE_PUBLISHABLE_KEY` | Your Supabase publishable / anon key |
| `VITE_API_BASE_URL` | *Leave empty / omit* (defaults to relative `/api`) |

#### 2. Backend Core Infrastructure Secrets
| Variable Name | Value Description |
| :--- | :--- |
| `ENVIRONMENT` | `production` |
| `PUBLISHING_MODE` | `live` (or `mock` for safe dry-run testing) |
| `GROQ_API_KEY` | Your Groq API key (`gsk_...`) |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` |
| `SUPABASE_URL` | `https://tuhgbmuwtlyuhwennfes.supabase.co` |
| `SUPABASE_ANON_KEY` | Your Supabase anon key |
| `SUPABASE_SERVICE_ROLE_KEY`| Your Supabase service role secret key |
| `CRON_SECRET` | 32-character random string (e.g. `132d14401cfe27925b83398115eecdd8`) |

#### 3. Token Encryption & Meta OAuth Secrets
| Variable Name | Value Description |
| :--- | :--- |
| `TOKEN_ENCRYPTION_KEY` | 32-byte urlsafe base64 Fernet key (`xG_D9wKkKk8vJ3_p6qT5u8wL2mY4rZ1x9cB7dE0fA2s=`) |
| `META_APP_ID` | `2231204290777395` |
| `META_APP_SECRET` | Your Meta Developer App Secret |
| `META_REDIRECT_URI` | `https://your-project.vercel.app/api/v1/connections/meta/callback` |

#### 4. Optional Static Platform Overrides
*(Only used as fallback if dynamic DB connection is not present)*
`BLUESKY_HANDLE`, `BLUESKY_APP_PASSWORD`, `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_AUTHOR_URN`, `FACEBOOK_PAGE_ACCESS_TOKEN`, `FACEBOOK_PAGE_ID`, `INSTAGRAM_ACCESS_TOKEN`, `INSTAGRAM_BUSINESS_ACCOUNT_ID`.

### Step 4: Click Deploy
Vercel builds the static React bundle, provisions the FastAPI Python Serverless Function for `/api/*`, and sets up the Cron schedule.

---

## ⏰ Scheduled Automation via Vercel Cron

OmniPulse uses **Vercel Cron** to execute due scheduled jobs:
* **Configured Path**: `GET /api/cron/process-schedules`
* **Schedule in `vercel.json`**: `"0 0 * * *"` (Daily UTC on Hobby plan; can be changed to `"*/10 * * * *"` on Pro).
* **Security**: Verified using `Authorization: Bearer <CRON_SECRET>`.

---

## 💻 Local Development Workflow

Run frontend and backend locally with live reloading:

### Terminal 1: Backend
```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Terminal 2: Frontend
```powershell
npm run dev
```
Open [http://localhost:3000](http://localhost:3000). The Vite development proxy forwards all `/api` requests to `http://127.0.0.1:8000`.

---

## 🔍 Troubleshooting & Verification

1. **Meta OAuth Popup Issues**:
   - Ensure `META_REDIRECT_URI` matches the exact URL configured in the Meta App Dashboard under *Valid OAuth Redirect URIs*.
   - Verify that your browser did not block popups for the site.
2. **Instagram Connection "No linked Instagram Professional Account"**:
   - The Instagram account must be converted to a **Professional / Business or Creator** account and connected to your Facebook Page in Page Settings.
3. **Token Decryption Failures**:
   - If `TOKEN_ENCRYPTION_KEY` changes, existing encrypted tokens will fail to decrypt. Keep this key constant across deployments.
