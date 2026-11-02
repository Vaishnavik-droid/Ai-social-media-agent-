# OmniPulse AI Social Media Agent

OmniPulse is a full-stack AI social media workspace for generating, managing, scheduling, and publishing content across multiple social platforms from one dashboard.

The project combines a React 18 + Vite frontend, a Python FastAPI backend, Supabase authentication and persistence, Groq-powered content generation, encrypted platform credentials, and Vercel deployment with scheduled publishing.

> **Important:** This repository contains application code and configuration templates. Never commit real API keys, OAuth secrets, access tokens, app passwords, service-role keys, or encryption keys.

## Features

- AI-assisted post generation through Groq
- Platform-aware content variants, character limits, tones, languages, hashtags, and campaign objectives
- Draft creation, editing, deletion, publishing, and scheduling
- Multi-platform publishing from one post
- OAuth connection flows for Meta, Pinterest, and YouTube
- Direct credential verification for Bluesky and LinkedIn
- Connection status, refresh, disconnect, and account metadata
- Image and video upload to public Supabase Storage for providers that require HTTPS media URLs
- Pinterest board listing and board creation
- YouTube title and short/long-form publishing options
- Vercel Cron processing for scheduled posts
- Supabase-backed encrypted credential persistence
- FastAPI Swagger/OpenAPI documentation
- Automated backend tests and a TypeScript production build

## Supported platforms

| Platform | Connection | Publishing notes |
| --- | --- | --- |
| Bluesky | AT Protocol handle and app password | Text and media posts |
| LinkedIn | OAuth access token and author URN | Text and image posts |
| Facebook | Meta OAuth | Page text and media posts |
| Instagram | Meta OAuth | Requires a connected Professional account and media |
| Pinterest | Pinterest OAuth 2.0 | Requires a destination board and media |
| YouTube | Google OAuth 2.0 | Requires a video; supports title and description |

Availability of live publishing depends on the platform developer application, scopes, account type, review status, and environment configuration.

## Architecture

```text
Browser
  │
  ├── React + Vite SPA
  │     ├── Supabase browser client for authentication
  │     └── Typed API client
  │
  └── FastAPI backend
        ├── Groq content generation
        ├── Supabase persistence and storage
        ├── OAuth and credential services
        ├── Platform adapters
        └── Scheduler / Vercel Cron endpoint
```

### Local development

Vite runs on port `3000` and proxies `/api` requests to FastAPI on `127.0.0.1:8000`.

### Vercel deployment

Vercel serves the Vite build and rewrites backend routes to the Python serverless entry point at [`api/index.py`](api/index.py). The scheduled job is configured in [`vercel.json`](vercel.json):

```text
GET or POST /api/cron/process-schedules
Schedule: 0 0 * * * (daily at midnight UTC)
```

In Vercel's serverless environment, the in-process scheduler is disabled and the Cron endpoint processes due jobs instead.

## Repository layout

```text
.
├── api/
│   ├── index.py                  # Vercel FastAPI serverless entry point
│   └── requirements.txt          # Vercel Python dependencies
├── backend/
│   ├── app/
│   │   ├── api/v1/routes/        # Auth, generation, posts, publishing, media, OAuth, scheduling
│   │   ├── core/                 # Settings, encryption, security, logging redaction
│   │   ├── platforms/            # Bluesky, LinkedIn, Facebook, Instagram, Pinterest, YouTube
│   │   ├── schemas/              # Pydantic request and response models
│   │   └── services/             # Groq, credentials, and scheduling services
│   ├── tests/                    # Backend unit, integration, OAuth, and workflow tests
│   ├── requirements.txt          # Backend dependencies, including pytest
│   └── platform_credentials.env.example
├── src/
│   ├── components/               # Shared UI components
│   ├── pages/                    # Auth, dashboard, posts, scheduling, platforms, settings, legal pages
│   ├── lib/api.ts               # Typed frontend API client
│   ├── lib/platformConstraints.ts
│   └── types/                    # Frontend domain types
├── supabase/migrations/          # Database schema migrations 001–006
├── public/                       # Static assets
├── .env.example                  # Combined frontend/backend configuration template
├── platform_credentials.env.example
├── package.json                  # Frontend scripts and dependencies
├── requirements.txt              # Root/Vercel Python dependencies
├── vercel.json                   # Rewrites and Cron configuration
├── VERCEL_DEPLOYMENT.md          # Extended deployment reference
├── implementation_plan_v2.md     # Historical implementation plan
└── LATEST_WORK_REPORT.md         # Stabilization and handover report
```

## Prerequisites

- Node.js 18+ and npm
- Python 3.11+ (Python 3.12 is recommended)
- A Supabase project
- A Groq API key
- Developer applications and OAuth credentials for each platform you intend to use
- A Vercel account for production deployment

## Local setup

### 1. Install frontend dependencies

```bash
npm install
```

### 2. Create a Python environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

### 3. Configure environment variables

Copy the templates:

```bash
cp .env.example .env
cp platform_credentials.env.example platform_credentials.env
```

For the backend-only workflow, the equivalent templates are available at:

```text
backend/.env.example
backend/platform_credentials.env.example
```

At minimum, configure:

| Variable | Purpose |
| --- | --- |
| `VITE_SUPABASE_URL` | Supabase project URL exposed to the browser |
| `VITE_SUPABASE_ANON_KEY` or `VITE_SUPABASE_PUBLISHABLE_KEY` | Browser-safe Supabase key |
| `SUPABASE_URL` | Backend Supabase project URL |
| `SUPABASE_ANON_KEY` | Backend Supabase anon key |
| `SUPABASE_SERVICE_ROLE_KEY` | Backend-only Supabase service-role key |
| `GROQ_API_KEY` | Backend-only Groq key |
| `TOKEN_ENCRYPTION_KEY` | Fernet key used to encrypt stored platform credentials |
| `CRON_SECRET` | Secret protecting scheduled-job execution |
| `PUBLISHING_MODE` | `mock` for safe testing or `live` for real publishing |
| `SCHEDULER_ENABLED` | Enables the local scheduler when not running on Vercel |

Generate the encryption key with:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Keep `TOKEN_ENCRYPTION_KEY` unchanged after storing credentials. Changing it makes existing encrypted credentials unreadable.

### 4. Apply Supabase migrations

Run all files in [`supabase/migrations`](supabase/migrations) in filename order using the Supabase SQL Editor or your preferred migration workflow:

```text
001_initial_schema.sql
002_authentication_and_credentials.sql
003_add_pinterest_youtube_platforms.sql
004_fix_post_platforms_remote_id.sql
005_add_partially_published_status.sql
006_ensure_user_profiles_and_oauth_state.sql
```

These migrations create the application schema, authentication support, encrypted platform connection storage, OAuth state persistence, publishing result fields, and Pinterest/YouTube platform support.

### 5. Start the backend

From the repository root:

```bash
source .venv/bin/activate
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

The backend is available at:

- Health: <http://127.0.0.1:8000/health>
- Swagger UI: <http://127.0.0.1:8000/docs>
- OpenAPI JSON: <http://127.0.0.1:8000/openapi.json>

### 6. Start the frontend

In a second terminal:

```bash
npm run dev
```

Open <http://localhost:3000>.

## Platform credentials and OAuth

Copy [`platform_credentials.env.example`](platform_credentials.env.example) to `platform_credentials.env` and configure only the platforms you need. The file contains placeholders for:

- Meta App ID, secret, and callback URL for Facebook and Instagram
- LinkedIn client ID, secret, and callback URL
- Pinterest client ID, secret, and callback URL
- Google client ID, secret, and YouTube callback URL
- Bluesky handle, app password, and service URL

Update each provider's developer console with the exact callback URL used by the environment. For local development, the default callbacks use port `8000`; in production they must use the deployed domain.

Dynamic access and refresh tokens are stored in Supabase in encrypted form. Static legacy token variables remain in the example file for reference only and should not be used as a substitute for the active connection flows.

### Platform-specific requirements

- **Facebook/Instagram:** Configure Meta OAuth and connect Instagram to a Facebook Page. Instagram requires a Professional (Business or Creator) account and media.
- **LinkedIn:** Use a token with the required social publishing scope and provide or resolve the member author URN.
- **Pinterest:** The connected account must have a board; select the board before publishing.
- **YouTube:** Grant upload and read scopes and provide a video file in a supported format such as `.mp4` or `.webm`.
- **Bluesky:** Use an app password rather than the primary account password.

## Common API endpoints

The backend registers the API routers under `/api/v1` (and compatible `/api`, `/v1`, and root aliases where applicable).

| Endpoint | Purpose |
| --- | --- |
| `GET /api/health` | Backend and provider health |
| `POST /api/v1/auth/login` | Authenticate a user |
| `GET /api/v1/auth/resolve-username` | Resolve a username to an email |
| `POST /api/v1/generation/preview` | Generate AI content |
| `GET /api/v1/posts` | List posts |
| `POST /api/v1/posts` | Create a draft |
| `PATCH /api/v1/posts/{post_id}` | Update a draft |
| `DELETE /api/v1/posts/{post_id}` | Delete a post |
| `POST /api/v1/publishing/publish` | Publish now or queue a post |
| `POST /api/v1/media/upload` | Upload media to Supabase Storage |
| `POST /api/v1/connections/meta/authorize` | Start Facebook/Instagram OAuth |
| `POST /api/v1/connections/pinterest/authorize` | Start Pinterest OAuth |
| `POST /api/v1/connections/youtube/authorize` | Start YouTube OAuth |
| `POST /api/v1/connections/bluesky/connect` | Connect Bluesky |
| `POST /api/v1/connections/linkedin/connect` | Connect LinkedIn |
| `GET /api/v1/connections` | List connection statuses |
| `POST /api/v1/connections/{platform}/refresh` | Re-verify a connection |
| `DELETE /api/v1/connections/{platform}` | Disconnect and remove credentials |
| `POST /api/v1/schedules` | Create a scheduled job |
| `GET /api/v1/schedules` | List scheduled jobs |
| `DELETE /api/v1/schedules/{schedule_id}` | Cancel a scheduled job |
| `GET /api/cron/process-schedules` | Process due jobs from Vercel Cron |

Interactive documentation is available at `/docs` when the backend is running.

## Testing and builds

Run the backend test suite from the repository root:

```bash
pytest backend/tests
```

Run the frontend type-check and production build:

```bash
npx tsc --noEmit
npm run build
```

The backend tests cover API behavior, adapters, authentication, environment configuration, OAuth persistence, scheduling, media handling, platform-aware generation, and end-to-end workflows.

## Production deployment on Vercel

1. Apply all Supabase migrations.
2. Push this repository to GitHub.
3. Import the repository into Vercel using the Vite framework preset.
4. Add the required `VITE_*` browser variables and backend secrets in Vercel Project Settings.
5. Configure production OAuth callback URLs in each provider's developer console.
6. Set `PUBLISHING_MODE=mock` while validating the deployment; switch to `live` only after connection and publishing checks pass.
7. Deploy and verify `/health`, `/docs`, authentication, connections, media upload, generation, and a test scheduled job.

See [`VERCEL_DEPLOYMENT.md`](VERCEL_DEPLOYMENT.md) for the extended Vercel routing, environment-variable, Meta configuration, Cron, and troubleshooting reference.

### Production security checklist

- Set `ENVIRONMENT=production`.
- Use a strong random `CRON_SECRET`.
- Keep `SUPABASE_SERVICE_ROLE_KEY`, `GROQ_API_KEY`, OAuth secrets, and `TOKEN_ENCRYPTION_KEY` server-side only.
- Do not expose secrets through `VITE_*` variables.
- Use HTTPS callback URLs in production.
- Restrict Supabase policies and storage access to the intended application behavior.
- Keep the token encryption key stable and back it up securely.
- Use `PUBLISHING_MODE=mock` for dry runs and never test live publishing with accounts or content you do not control.

## Troubleshooting

### The frontend cannot reach the backend

Confirm FastAPI is running on `127.0.0.1:8000`, the Vite dev server is running on port `3000`, and `VITE_API_BASE_URL` is empty or points to the intended backend.

### OAuth callback fails

The callback URL must match exactly in the provider dashboard and environment variables, including scheme, hostname, port, path, and trailing slash behavior.

### Instagram reports that media is not ready

The backend waits for the Instagram media container to reach `FINISHED`. Confirm the account is Professional, the media is valid, and the uploaded URL is public HTTPS media.

### Pinterest cannot publish

Confirm the account has a board, the selected board ID is valid, the account has write permissions, and the media URL is publicly reachable.

### YouTube token or upload failures

Confirm the OAuth flow includes offline access and upload scopes, the Google client credentials are configured, and the uploaded file is a supported video format. The backend refreshes expired access tokens when a refresh token is available.

### Existing credentials cannot be decrypted

Restore the original `TOKEN_ENCRYPTION_KEY`. Generating a new key invalidates previously encrypted credentials.

## Additional documentation

- [`VERCEL_DEPLOYMENT.md`](VERCEL_DEPLOYMENT.md) — unified Vercel deployment guide
- [`LATEST_WORK_REPORT.md`](LATEST_WORK_REPORT.md) — platform stabilization and handover report
- [`implementation_plan_v2.md`](implementation_plan_v2.md) — implementation history and milestones
- [`docs/context.md`](docs/context.md) — project context

## License

See [`LICENSE`](LICENSE).
