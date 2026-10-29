OmniPulse AI Social Media Agent --- Project Context & Architecture Lock-in
Document status: Authoritative project context
Decision date: 2026-10-26
Audience: Anyone (human or AI coding agent) making future changes to
this repository
Purpose: Preserve the agreed architecture and prevent future work
from reintroducing rejected complexity.
Source-of-truth rule: Follow this document for architecture and
product decisions. If the existing code disagrees with it, treat the
code as legacy/current implementation to be migrated---not as proof
that the old design is still desired. If a requirement is genuinely
ambiguous, ask before making a major architectural change.

1. Project goal
Build a single-user AI social media automation application. The user
works through a web frontend to draft or generate social content, choose
supported social platforms, publish immediately, schedule posts, and
track outcomes.

The application should use:
- Existing frontend: React + Vite (based on the current project
  audit; verify exact versions from package.json).
- Backend: Python + FastAPI.
- LLM provider: Groq API.
- LLM orchestration: Direct Groq SDK/API calls by default. Use
  LangChain only where it clearly simplifies a real requirement; it is
  optional, not mandatory.
- Persistence/authentication: Existing Supabase project, subject
  to auditing the current schema and frontend integration.
- Automation: FastAPI backend code, not Make.com.
The project is for one user's own accounts. It does not require
multi-tenant isolation, tenant routing, or a generalized SaaS
account-management architecture. It still requires sensible
authentication, secrets protection, validation, and safe handling of
external API credentials.
2. Locked decisions
These are the decisions future contributors must preserve unless the
project owner explicitly changes them.
1. Remove Make.com from the target architecture. Do not build new
   Make.com scenarios, webhooks, blueprints, or dependencies. Migrate
   any existing src/lib/make.ts integration into calls to the FastAPI
   backend, then remove or clearly deprecate the old integration once
   unused.
2. FastAPI owns automation orchestration. It validates requests,
   calls the LLM when needed, routes work to platform adapters, handles
   publishing/scheduling, records status, and returns meaningful
   results.
3. Groq is the LLM provider. Store the Groq API key on the backend
   only. Never expose it in browser code or a VITE_* variable.
4. LangChain is optional. Start with the simplest maintainable
   implementation. Add LangChain only if it materially helps with
   prompt chains, structured output, tool orchestration, or other
   demonstrated complexity. Do not add it just because the project uses
   an LLM.
5. Single-user scope. Optimize for one operator and that operator's
   social accounts. Do not introduce tenant IDs, tenant isolation
   frameworks, organizations, roles, or billing unless specifically
   requested. Do not confuse "single user" with "no security."
6. Supabase remains the intended managed persistence/auth service,
   but audit the current implementation before assuming application
   data is already stored there. Browser localStorage is not a
   substitute for durable shared persistence.
7. Platform integration must be real and explicit. A platform is
   not "connected" merely because a button or UI state exists. Only
   show a connection as active after credentials/OAuth and a
   verification call succeed.
8. Never report successful publishing unless the platform API
   confirms success. Persist the platform response/reference and
   status where possible.
9. Build and test one platform end-to-end first, then generalize
   the adapter pattern to other platforms.
10. Do not rewrite the whole frontend without need. Preserve working
    UI and replace its integration layer incrementally.
3. Current project state --- reported, not independently verified
The project audit previously described the repository as having a
substantially built React/Vite frontend, Supabase Auth initialization,
local-storage/mock-data paths, and a frontend Make.com webhook sender.
The audit also reported that AI generation may be template-based and
platform connection controls may be UI-only.

Treat these as leads to verify in the repository, not guaranteed facts.
Before implementation:
- Inspect the actual repository tree and package.json.
- Read the existing Supabase client/configuration and
  schema/migrations.
- Inspect src/lib/make.ts, all callers, and environment-variable
  usage.
- Trace post creation, scheduling, deletion, platform connection, and
  status UI.
- Identify which data currently uses Supabase versus localStorage or
  mock data.
- Inspect current tests and run the existing checks.
Do not assume a previously discussed database table has already been
created. Tables previously proposed include profiles, posts,
post_platforms, scheduled_posts, platform_connections, and
media_assets; reconcile these with the actual Supabase schema before
writing migrations.
4. Target architecture
React + Vite frontend
    |
    | HTTPS JSON requests; Supabase session/token where auth is enabled
    v
FastAPI backend
    |
    +--> Request validation and application services
    |
    +--> Groq LLM service (generation, rewriting, platform-specific variants)
    |
    +--> Platform adapter interface
    |       +--> LinkedIn adapter (subject to API access and permissions)
    |       +--> Instagram adapter (subject to account type, permissions and media requirements)
    |       +--> Facebook adapter (subject to Page/app permissions)
    |       +--> Bluesky adapter (subject to current API/auth requirements)
    |
    +--> Scheduling service / worker
    |
    +--> Supabase persistence (posts, platform results, schedule and connection metadata)
    |
    +--> Structured logs, retries, and error reporting
Important: This diagram is the target design, not a statement that
these adapters or features already exist.
Responsibilities
Frontend - Collect post text, media, selected platforms, generation
preferences, and schedule time. - Call FastAPI endpoints rather than
Make.com webhooks. - Display loading, validation errors, per-platform
results, and scheduled/published states. - Never contain Groq secrets,
platform client secrets, or privileged Supabase service-role
credentials. - Keep the current design where practical; update the API
integration layer first.

FastAPI - Define typed request/response schemas with Pydantic. -
Validate inputs and platform-specific requirements. -
Authenticate/authorize requests as appropriate for the existing
single-user setup. - Call Groq for content generation and
transformations. - Route publish jobs through platform adapters. -
Persist job and per-platform statuses. - Handle schedule execution,
retries, rate limits, and errors. - Return a clear result for each
requested platform.

Groq - Generate or adapt copy from user instructions. - Produce
platform-specific variants and optional hashtags. - Use structured
outputs where helpful and validate model responses. - Do not let model
output directly execute arbitrary code or arbitrary external actions. -
Provide useful fallback errors for rate limits, unavailable models,
malformed output, or missing configuration.

Supabase - Use the existing project for durable application data
and, if already adopted, authentication. - Confirm schema and Row Level
Security policies before relying on them. - Store secrets only in an
appropriate server-side secret store/environment, not ordinary
client-readable tables. - Store connection metadata and token references
securely; do not return access tokens to the frontend. - Decide whether
FastAPI accesses Supabase using the user's session/JWT or a server
credential. If using a service-role key, keep it backend-only and
enforce the single-user access model deliberately.
5. Suggested repository structure
Adapt this structure to the actual repository rather than moving
everything blindly. The frontend and backend may live in a monorepo.
project-root/
├── PROJECT_CONTEXT.md          # This authoritative decision document
├── README.md                    # Setup and run instructions
├── .gitignore
├── .env.example                 # Placeholder names only; never real secrets
├── frontend/                    # Or existing root-level React/Vite app
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── lib/
│   │   │   ├── api.ts            # Central FastAPI client
│   │   │   └── supabase.ts       # Only if frontend Supabase use is retained
│   │   └── types/
│   └── package.json
├── backend/
│   ├── pyproject.toml            # Or requirements.txt; choose one primary approach
│   ├── app/
│   │   ├── main.py               # FastAPI app, middleware, routers
│   │   ├── core/
│   │   │   ├── config.py         # Environment-based settings
│   │   │   ├── security.py       # Authentication and secret handling
│   │   │   └── logging.py
│   │   ├── api/
│   │   │   ├── deps.py
│   │   │   └── routes/
│   │   │       ├── health.py
│   │   │       ├── posts.py
│   │   │       ├── generation.py
│   │   │       ├── publishing.py
│   │   │       ├── scheduling.py
│   │   │       └── connections.py
│   │   ├── schemas/              # Pydantic request/response models
│   │   ├── services/
│   │   │   ├── groq_service.py
│   │   │   ├── post_service.py
│   │   │   ├── publish_service.py
│   │   │   └── scheduling_service.py
│   │   ├── platforms/
│   │   │   ├── base.py           # Shared adapter protocol/interface
│   │   │   ├── linkedin.py
│   │   │   ├── instagram.py
│   │   │   ├── facebook.py
│   │   │   └── bluesky.py
│   │   ├── repositories/          # Database access boundary
│   │   ├── workers/               # Scheduled-job execution
│   │   └── tests/
│   └── README.md
├── supabase/
│   ├── migrations/
│   └── config.toml               # If Supabase CLI is used
└── docs/
    ├── API_CONTRACT.md
    └── PLATFORM_REQUIREMENTS.md
The platform list is the discussed target scope, not a guarantee that
every platform can be enabled immediately. Platform APIs have different
access, review, media, account-type, and permission requirements. Verify
current official documentation before implementing each adapter.
6. Backend API contract --- initial proposal
Use a versioned /api/v1 prefix. Exact fields should be finalized after
inspecting existing frontend types and forms.
  Method                  Endpoint                                  Purpose
  GET                   /health                                 Basic service health
                                                                    check

  POST                  /api/v1/generation/preview              Generate or rewrite
                                                                    post content with Groq

  POST                  /api/v1/posts                           Create/save a post
                                                                    draft

  GET                   /api/v1/posts                           List posts

  GET                   /api/v1/posts/{post_id}                 Retrieve one post

  PATCH                 /api/v1/posts/{post_id}                 Update a draft

  DELETE                /api/v1/posts/{post_id}                 Delete a draft/post
                                                                    record under defined
                                                                    rules

  POST                  /api/v1/publishing/publish              Publish a post to
                                                                    selected platforms

  POST                  /api/v1/schedules                       Schedule publication

  GET                   /api/v1/schedules                       List scheduled jobs

  DELETE                /api/v1/schedules/{schedule_id}         Cancel a scheduled job

  GET                   /api/v1/connections                     Show safe connection
                                                                    status, never tokens

  POST                  /api/v1/connections/{platform}/verify   Verify configured
                                                                    connection

  GET                   /api/v1/publishing/jobs/{job_id}        Inspect job and
                                                                per-platform status
These endpoints are a proposal, not an already implemented API. Do not
implement all endpoints before confirming the frontend flows. Use
Pydantic schemas, predictable HTTP status codes, and consistent error
responses.
Example publish request (illustrative)
{
  "post_id": "existing-or-new-post-id",
  "platforms": ["linkedin", "bluesky"],
  "publish_now": true
}
For a scheduled post, use a timezone-aware ISO 8601 timestamp and
validate that it is in the future. Do not silently interpret local times
without a timezone.
Per-platform result model
Represent outcomes independently, for example:
- pending
- processing
- published
- scheduled
- failed
- cancelled
A multi-platform request can partially succeed. Return and persist a
result for each platform rather than marking the entire job successful
when only one platform publishes.
7. Persistence and scheduling principles
- Audit current Supabase tables before creating migrations.
- Establish a canonical persisted post record and separate
  per-platform outcomes.
- Store timestamps in UTC; preserve the intended user timezone for
  schedule display and interpretation.
- Use a durable scheduler/worker approach for scheduled posts. A
  simple in-process background task is not sufficient for reliable
  schedules across restarts or deployments.
- For a small single-user application, begin with the least complex
  durable option compatible with the deployment environment. Examples
  to evaluate include a database-backed job table with a worker, or a
  lightweight scheduler that recovers pending jobs on startup.
- Make publishing idempotent where feasible to reduce duplicate posts
  after retries or network timeouts.
- Record attempt count, timestamps, platform response identifiers, and
  sanitized error messages.
- Do not store media only in temporary local paths if the publishing
  job needs the media later. Use durable object storage or a
  platform-compatible source URL.
- Define what deletion means: deleting a local record cannot
  necessarily delete a post already published on a third-party
  platform.
8. Credentials, authentication, and safety
Single-user scope removes the need for tenant isolation, but not for
basic security.
- Keep Groq keys, platform secrets, refresh tokens, and privileged
  Supabase credentials on the backend.
- Use .env locally and the hosting provider's secret manager in
  deployment.
- Commit only .env.example with blank or obvious placeholder values.
- Add .env, token files, local databases, logs containing secrets,
  and generated credentials to .gitignore.
- Never log raw authorization headers, access tokens, refresh tokens,
  or full secret-bearing environment values.
- Configure CORS to the actual frontend origin(s), not unrestricted
  wildcard origins with credentials.
- Protect the backend with the project's chosen single-user
  authentication mechanism. If the frontend uses Supabase Auth,
  validate the incoming JWT server-side; do not trust a user ID sent
  in the JSON body.
- Avoid returning platform tokens or privileged credentials from any
  API endpoint.
- Validate media types, file sizes, URLs, text lengths, timestamps,
  and platform selections.
- Handle provider rate limits and errors without leaking secrets.
- If a webhook is no longer needed, remove it from active code and
  configuration; rotate any exposed or shared webhook URL that was
  active.
9. Groq and LangChain implementation rule
Start with a small groq_service.py that provides a narrow interface
such as:
- generate_post(...)
- rewrite_for_platform(...)
- generate_platform_variants(...)
Use environment configuration for the API key and model name. Validate
the generated result before saving or publishing. Keep prompts in code
or versioned prompt files so they can be reviewed.

Add LangChain only when a concrete need is identified and its value
outweighs added dependencies and debugging surface. Direct API/SDK usage
is the default for straightforward generation and structured responses.
Do not add autonomous agents or open-ended tool execution for this
project unless a clearly scoped feature requires it.
10. Platform integration strategy
Implement one platform end-to-end first. The choice should be based on
the user's account access, API approval, content type, and simplest
valid test path---not assumptions that all platforms are equally
accessible.

For every adapter:
1. Document account and developer-app prerequisites.
2. Document required permissions/scopes and token lifecycle.
3. Implement a common interface such as validate_connection,
   publish_text, and, where supported, publish_media.
4. Respect platform-specific payload and media requirements.
5. Return a normalized result containing status, remote post ID/URL if
   available, and a sanitized error.
6. Test with a real account and a safe test post before exposing
   "connected" or "published" UI states.
7. Verify current official platform documentation before relying on
   endpoint names, access tiers, or permissions.
Do not assume that a single generic "publish" API works identically for
LinkedIn, Instagram, Facebook, and Bluesky.
11. Migration plan
Work in small, verifiable increments. Avoid building every feature at
once.
Phase 0 --- Repository audit
- Inspect the actual folder structure and package manifests.
- Identify current frontend flows, Supabase usage, localStorage mocks,
  and Make.com references.
- Capture current behavior and run existing tests/build.
Phase 1 --- FastAPI foundation
- Create the backend app, settings, health route, CORS, schemas, and
  test setup.
- Add .env.example and safe configuration loading.
- Confirm the frontend can call the backend locally.
Phase 2 --- Replace Make.com integration
- Create one centralized frontend API client.
- Replace calls to src/lib/make.ts with typed FastAPI calls.
- Add clear loading and error states.
- Remove old Make.com configuration only after all callers are
  migrated.
Phase 3 --- Data persistence
- Audit and reconcile Supabase schema.
- Define and migrate canonical posts, per-platform results, schedules,
  and connection metadata as needed.
- Replace localStorage/mock persistence for data that must survive
  reloads or be processed by the backend.
- Verify create, read, update, delete, and status refresh.
Phase 4 --- Groq generation
- Add server-side Groq integration.
- Implement generation and platform-specific rewriting.
- Validate output and handle API errors.
- Add tests using mocked provider responses.
Phase 5 --- One real platform
- Configure credentials securely.
- Implement and test connection verification and a real publishing
  path.
- Save the returned platform ID and status.
- Verify UI status reflects actual platform results.
Phase 6 --- Scheduling
- Add durable schedule records and worker execution.
- Handle cancellation, retries, idempotency, and per-platform
  failures.
- Test restart/recovery behavior and timezone correctness.
Phase 7 --- Additional platforms
- Add each remaining platform adapter separately.
- Confirm developer access and permissions before claiming support.
- Test platform-specific text/media constraints and partial failure.
Phase 8 --- End-to-end verification
- Draft → save → generate/rewrite → select platform → publish →
  persist result → refresh UI.
- Schedule → persist job → execute at due time → persist result → show
  final state.
- Test invalid credentials, rate limits, partial success, duplicate
  retries, and backend restart.
12. Definition of done
Do not describe the system as complete until these are demonstrated:
- [ ] Frontend uses FastAPI for application automation; no active
  Make.com dependency remains.
- [ ] Backend starts from documented instructions and /health
  succeeds.
- [ ] Secrets are backend-only and absent from browser bundles and
  Git.
- [ ] Post data that must persist is stored durably, not only in
  localStorage.
- [ ] Groq generation works with real configuration and handles
  errors.
- [ ] At least one social platform connection is verified against its
  real API.
- [ ] A real test post publishes and its remote result is saved.
- [ ] Scheduled jobs survive a backend restart and execute reliably.
- [ ] Per-platform partial success and failure are visible in the UI.
- [ ] Tests and frontend/backend build checks pass.
- [ ] README setup, environment variables, API endpoints, and platform
  prerequisites are documented.
13. Rules for future contributors and coding agents
Before changing architecture:
1. Read this document first.
2. Inspect actual source files and current behavior; do not assume this
   document proves implementation exists.
3. Keep the single-user FastAPI + Groq + Supabase direction.
4. Do not reintroduce Make.com, multi-tenant isolation, or a mandatory
   LangChain dependency.
5. Prefer small changes with tests over broad rewrites.
6. Do not invent credentials, claim API access is available, or mark
   mock functionality as complete.
7. Clearly distinguish implemented, tested, and planned features in
   summaries.
8. Update this document when the project owner explicitly changes a
   locked decision; explain the change and its reason in the document's
   decision history.
14. Decision history
  Date                                Decision
  2026-10-26                          Replace Make.com automation with a
                                      FastAPI backend.

  2026-10-26                          Use Groq API as the LLM provider.

  2026-10-26                          LangChain is optional and should be
                                      added only if it materially
                                      simplifies orchestration.

  2026-10-26                          Keep the project single-user; do
                                      not build multi-tenant isolation.

  2026-10-26                          Preserve the existing frontend
                                      where practical and migrate its
                                  integration incrementally.
Final authority: The project owner. This document is the default
source of architectural context for future work; only the project owner
can override its locked decisions.