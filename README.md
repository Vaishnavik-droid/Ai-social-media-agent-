# OmniPulse AI Social Media Agent

OmniPulse is an AI-powered social media workspace for creating, scheduling, and publishing content across multiple platforms from one dashboard.

## Features

- Generate post copy with Groq-powered AI.
- Create, preview, schedule, and publish posts.
- Connect and publish to Bluesky, LinkedIn, Facebook, Instagram, Pinterest, and YouTube.
- Upload media through Supabase Storage for platforms that require public HTTPS assets.
- Validate platform-specific requirements, including Instagram/Pinterest images and YouTube videos.
- Securely persist encrypted access and refresh tokens in Supabase.
- Use OAuth flows for Meta, Pinterest, and YouTube integrations.
- Run as a unified Vite/React frontend and FastAPI backend on Vercel.

## Architecture

- **Frontend:** React 18, TypeScript, Vite, and `lucide-react`
- **Backend:** Python FastAPI serverless API
- **Database and storage:** Supabase
- **AI provider:** Groq
- **Deployment:** Vercel

```text
Browser
  ├── React + Vite dashboard
  └── /api requests
        └── FastAPI routes
              ├── AI generation
              ├── authentication and connections
              ├── media uploads
              ├── scheduling
              └── publishing adapters
```

## Supported Platforms

| Platform | Authentication | Media publishing |
| --- | --- | --- |
| Bluesky | AT Protocol app password | Images and text |
| LinkedIn | OAuth/access token | Images and text |
| Facebook | Meta OAuth | Images and text |
| Instagram | Meta OAuth | Images and videos |
| Pinterest | OAuth 2.0 | Images and videos |
| YouTube | Google OAuth 2.0 | Videos |

## Project Structure

```text
api/                 Vercel FastAPI entry point
backend/app/         FastAPI application, routes, services, and adapters
backend/tests/       Backend tests
docs/                Project documentation
src/                 React pages, components, and API client
supabase/migrations/ Database schema migrations
public/              Static frontend assets
```

## Prerequisites

- Node.js 18 or newer
- Python 3.11 or newer
- A Supabase project
- A Groq API key for AI generation
- Provider credentials for any social platforms you want to connect

## Local Development

Install frontend dependencies:

```bash
npm install
```

Create local environment files from the provided templates:

```bash
cp .env.example .env
cp platform_credentials.env.example platform_credentials.env
```

Start the backend:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

In a second terminal, start the frontend:

```bash
npm run dev
```

Open the local Vite URL shown in the terminal. The Vite configuration proxies `/api` requests to the local FastAPI server.

## Environment Variables

Configure the values documented in `.env.example` and `platform_credentials.env.example`. Important settings include:

- `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` for the browser client
- `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and `SUPABASE_SERVICE_ROLE_KEY` for the backend
- `GROQ_API_KEY` and `GROQ_MODEL` for AI generation
- `TOKEN_ENCRYPTION_KEY` for encrypting stored credentials
- OAuth settings for Meta, Pinterest, and Google/YouTube
- `PUBLISHING_MODE=mock` for safe local dry runs, or `live` for real publishing

Never commit real API keys, OAuth secrets, access tokens, or refresh tokens.

## Database Setup

Apply the SQL migrations in `supabase/migrations/` to your Supabase project. The migrations create the application tables for users, posts, schedules, platform connections, OAuth state, and media-related data.

The platform expansion migration also enables Pinterest and YouTube records in platform connection and publishing tables.

## Useful Commands

```bash
npm run dev       # Start the Vite development server
npm run build     # Type-check and create a production frontend build
npm run preview   # Preview the production frontend build
pytest backend/tests
```

## Deployment

The project is designed for a unified Vercel deployment:

1. Apply the Supabase migrations.
2. Import the repository into Vercel.
3. Add the required frontend and backend environment variables in Vercel.
4. Configure OAuth redirect URLs using the deployed Vercel domain.
5. Set `PUBLISHING_MODE=mock` while validating the deployment, then switch to `live` when provider credentials are ready.

See [VERCEL_DEPLOYMENT.md](VERCEL_DEPLOYMENT.md) for the complete routing, environment-variable, OAuth, and cron configuration guide.

## Security Notes

- Keep backend secrets server-side; only public Supabase client settings belong in `VITE_*` variables.
- Keep `TOKEN_ENCRYPTION_KEY` stable after credentials are stored, or previously encrypted credentials cannot be decrypted.
- Use HTTPS callback URLs in production.
- Do not expose Supabase service-role keys or social platform tokens in frontend code.

## License

This project is distributed under the license in [LICENSE](LICENSE).

<img width="1600" height="810" alt="WhatsApp Image 2026-11-01 at 10 40 20 AM (1)" src="https://github.com/user-attachments/assets/da296532-a763-484f-8e55-c16761b82053" />

