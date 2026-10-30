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
     │  - Bluesky / Meta / LinkedIn  │               │  - Supabase client auth       │
     │  - Vercel Cron scheduled jobs │               │  - Multi-platform preview     │
     └───────────────────────────────┘               └───────────────────────────────┘
```

### URL Map

| Route Pattern | Handled By | Description |
| :--- | :--- | :--- |
| `https://your-domain.vercel.app/` | Vite Frontend | Main web dashboard |
| `https://your-domain.vercel.app/posts` | Vite Frontend | Client-side React Router (SPA fallback) |
| `https://your-domain.vercel.app/api/health` | FastAPI (`health_router`) | Backend health check & provider status |
| `https://your-domain.vercel.app/api/v1/generation/preview` | FastAPI (`generation_router`)| AI post generation powered by Groq |
| `https://your-domain.vercel.app/api/v1/posts` | FastAPI (`posts_router`) | Post CRUD operations |
| `https://your-domain.vercel.app/api/v1/publishing/publish`| FastAPI (`publishing_router`)| Live social publishing dispatch |
| `https://your-domain.vercel.app/api/v1/connections` | FastAPI (`connections_router`) | Social channel connection verification |
| `https://your-domain.vercel.app/api/cron/process-schedules`| FastAPI (`scheduling_router`) | Vercel Cron worker endpoint |
| `https://your-domain.vercel.app/docs` | FastAPI Swagger | Interactive OpenAPI Swagger UI |

---

## 📂 Project Structure

```
├── api/
│   └── index.py               # Vercel Serverless Function entry point (exports FastAPI `app`)
├── backend/
│   ├── app/
│   │   ├── api/v1/routes/     # FastAPI routers (health, generation, posts, publishing, scheduling)
│   │   ├── core/config.py     # Pydantic Settings & environment variables
│   │   ├── platforms/         # Social network adapters (Bluesky, LinkedIn, Facebook, Instagram)
│   │   ├── schemas/           # Pydantic v2 domain schemas
│   │   ├── services/          # Scheduling and orchestration services
│   │   └── main.py            # FastAPI ASGI application initialization
│   ├── tests/                 # 30 Automated unit & integration tests
│   └── requirements.txt       # Backend dependencies
├── src/
│   ├── components/            # Reusable React components & layout
│   ├── pages/                 # Pages (Dashboard, CreatePost, Scheduled, Platforms, Settings)
│   ├── lib/api.ts             # Typed API client (relative `/api` routing)
│   ├── lib/supabase.ts        # Browser Supabase client
│   └── index.css              # Global styling & design system
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

## 🚀 Step-by-Step Vercel Deployment Instructions

### Step 1: Push Code to GitHub
Ensure the latest code is committed and pushed to your GitHub repository:
```powershell
git add .
git commit -m "feat: configure full-stack Vercel deployment with Python FastAPI and React Vite"
git push origin main
```

### Step 2: Import Project in Vercel
1. Log in to [Vercel Dashboard](https://vercel.com/dashboard).
2. Click **Add New...** -> **Project**.
3. Select your GitHub repository: **`VaishnaviK-droid/Ai-social-media-agent-`**.
4. Configure Project Settings:
   - **Framework Preset**: `Vite` (Vercel will auto-detect this from `vercel.json`).
   - **Root Directory**: `./` (leave default).
   - **Build Command**: `npm run build` (or `tsc && vite build`).
   - **Output Directory**: `dist`.
   - **Install Command**: `npm install`.

### Step 3: Configure Environment Variables in Vercel
In the Vercel **Environment Variables** section during project creation (or under **Project Settings -> Environment Variables**), add the following:

#### 1. Public Frontend Variables
| Variable Name | Value Description |
| :--- | :--- |
| `VITE_SUPABASE_URL` | `https://tuhgbmuwtlyuhwennfes.supabase.co` |
| `VITE_SUPABASE_ANON_KEY` | Your Supabase publishable / anon key |
| `VITE_SUPABASE_PUBLISHABLE_KEY` | Your Supabase publishable / anon key |
| `VITE_API_BASE_URL` | *Leave empty / omit* (defaults to relative `/api` on same domain) |

#### 2. Backend Server-Side Secrets
| Variable Name | Value Description |
| :--- | :--- |
| `ENVIRONMENT` | `production` |
| `PUBLISHING_MODE` | `live` (or `mock` for safe dry-run testing) |
| `GROQ_API_KEY` | Your Groq API key (`gsk_...`) |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` |
| `SUPABASE_URL` | `https://tuhgbmuwtlyuhwennfes.supabase.co` |
| `SUPABASE_ANON_KEY` | Your Supabase anon key |
| `SUPABASE_SERVICE_ROLE_KEY`| Your Supabase service role secret key |
| `CRON_SECRET` | Generate a random 32-character secret string (e.g. `openssl rand -hex 16`) |

#### 3. Social Publishing Platform Secrets
| Variable Name | Value Description |
| :--- | :--- |
| `BLUESKY_ENABLED` | `true` |
| `BLUESKY_HANDLE` | `curator06.bsky.social` |
| `BLUESKY_APP_PASSWORD` | Your Bluesky app password |
| `LINKEDIN_ENABLED` | `true` |
| `LINKEDIN_ACCESS_TOKEN` | Your LinkedIn OAuth bearer token |
| `LINKEDIN_AUTHOR_URN` | `urn:li:person:rFwwulFIXG` |
| `FACEBOOK_ENABLED` | `true` |
| `FACEBOOK_PAGE_ACCESS_TOKEN` | Your Facebook Page access token |
| `FACEBOOK_PAGE_ID` | Your numeric Facebook Page ID (e.g. `122...`) |
| `INSTAGRAM_ENABLED` | `true` |
| `INSTAGRAM_ACCESS_TOKEN` | Your Meta System User permanent access token |
| `INSTAGRAM_BUSINESS_ACCOUNT_ID` | Your Instagram Business Account ID (`1784...`) |

### Step 4: Click Deploy
Click **Deploy**. Vercel will:
1. Run `npm install` and `npm run build` to generate the static frontend bundle into `dist/`.
2. Detect `api/index.py` and install Python dependencies from `requirements.txt`.
3. Provision the Python Serverless Function for `/api/*`.
4. Deploy the unified application to `https://<your-project>.vercel.app`.

---

## ⏰ Scheduled Automation via Vercel Cron

In serverless architectures, background worker threads (`asyncio.sleep`) cannot stay alive permanently. OmniPulse uses **Vercel Cron** to execute due scheduled jobs:

* **Configured Path**: `GET /api/cron/process-schedules`
* **Schedule in `vercel.json`**: `"0 0 * * *"` (Daily UTC on Hobby plan; can be changed to `"*/10 * * * *"` on Vercel Pro).
* **Security**:
  * Vercel automatically passes `Authorization: Bearer <CRON_SECRET>`.
  * The endpoint verifies this header. If unauthorized or missing, it responds with `HTTP 401`.
* **Execution Flow**:
  1. Vercel Cron sends a `GET` request to `/api/cron/process-schedules`.
  2. The function queries Supabase for pending jobs whose `scheduled_at <= now()`.
  3. It atomically claims each job (`status = 'processing'`).
  4. Posts are published to Bluesky, LinkedIn, Facebook, and Instagram.
  5. Status is updated in Supabase (`completed` or `failed`).

---

## 💻 Local Development Workflow

Run frontend and backend locally with live reloading:

### Terminal 1: Backend
```powershell
cd backend
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Terminal 2: Frontend
```powershell
npm run dev
```
Open [http://localhost:3000](http://localhost:3000). The Vite development proxy will forward all `/api` requests to `http://127.0.0.1:8000`.

---

## 🔍 Troubleshooting & Common Issues

### 1. `Function Payload Exceeded` or Timeout
* Ensure large images are uploaded using a public image URL (e.g. Unsplash, Supabase Storage) rather than massive base64 strings exceeding Vercel's 4.5MB serverless payload limit.

### 2. Cron Jobs Not Triggering
* On Vercel **Hobby** (free) plan, Vercel restricts cron frequency to once per day. If you specify a schedule like `*/10 * * * *` on a Hobby plan, Vercel build will warn or reject it. Use `"0 0 * * *"` for Hobby, or use an external ping service (such as [cron-job.org](https://cron-job.org/)) pointing to `https://<your-domain>.vercel.app/api/cron/process-schedules?key=<CRON_SECRET>`.

### 3. Facebook "Invalid parameter" or "Insufficient Permission"
* Verify `FACEBOOK_PAGE_ID` belongs to a **Facebook Page**, not a personal user profile.
* Ensure `FACEBOOK_PAGE_ACCESS_TOKEN` was generated with `pages_manage_posts` and `pages_read_engagement`.

### 4. Instagram "Requires publicly accessible image URL"
* Meta's Instagram Graph API requires media to be downloaded by Meta's servers from a publicly accessible HTTP/HTTPS URL. Local browser uploads (`data:` URLs) are not accepted by Meta.
