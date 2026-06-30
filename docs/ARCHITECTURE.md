# MailCraft — Architecture & Technical Reference

> **Scope:** Complete technical reference for the MailCraft application, covering every layer from local development to production deployment. Intended audience: engineers onboarding to the project or performing architectural review.

---

## Table of Contents

1. [High-Level Overview](#1-high-level-overview)
2. [Repository Structure](#2-repository-structure)
3. [Technology Stack](#3-technology-stack)
4. [Configuration & Environment Variables](#4-configuration--environment-variables)
5. [Database Layer](#5-database-layer)
6. [Authentication & Session Management](#6-authentication--session-management)
7. [Middleware Stack](#7-middleware-stack)
8. [API Reference](#8-api-reference)
9. [Application Layer (Handlers & Services)](#9-application-layer-handlers--services)
10. [Generation Pipeline](#10-generation-pipeline)
11. [LLM Infrastructure](#11-llm-infrastructure)
12. [File Storage](#12-file-storage)
13. [Async Worker](#13-async-worker)
14. [Templates & Frontend](#14-templates--frontend)
15. [Prompt Engineering](#15-prompt-engineering)
16. [Rate Limiting](#16-rate-limiting)
17. [Security Controls](#17-security-controls)
18. [Health Checks](#18-health-checks)
19. [PDF Export](#19-pdf-export)
20. [Dev vs Production Differences](#20-dev-vs-production-differences)
21. [Docker & Deployment](#21-docker--deployment)
22. [CI Pipeline](#22-ci-pipeline)
23. [Data Flow — End to End](#23-data-flow--end-to-end)

---

## 1. High-Level Overview

MailCraft is a **FastAPI** web application that generates professional application documents (emails and cover letters) for job interviews, MS applications, and PhD applications. It uses Google Gemini LLMs with an 8-step generation pipeline that extracts CV text, builds grounded prompts, generates structured output, and optionally humanizes the result before persisting it.

```
Browser
  │
  ├─ HTML pages (Jinja2 + Tailwind CSS)
  │    ├─ Auth:  /auth/login, /auth/register
  │    ├─ Home:  /
  │    └─ Dashboard: /dashboard, /dashboard/generate,
  │                  /dashboard/scenarios, /dashboard/scenarios/:id/edit
  │
  └─ JSON API (/api/*)
       ├─ Auth       → cookies (HS256 JWT)
       ├─ Scenarios  → CRUD for editable system prompts
       ├─ Generations → create (sync / async), list, get, delete, export PDF
       ├─ Jobs        → poll async generation status
       └─ Health      → liveness + readiness

FastAPI App (main.py)
  │
  ├─ Middleware: SecurityHeaders → CSRF → RequestLogging
  ├─ Route handlers call ApplicationDocumentHandler
  └─ ApplicationDocumentHandler runs GenerationPipeline
       │
       └─ 8 steps: Validate → ExtractText → StoreFiles → GroundingResearch
                   → LLMGenerate → FormatOutput → Humanize → Persist

Database (SQLite dev / Postgres prod) — SQLAlchemy + Alembic
LLM: Google Gemini (google-genai SDK)
Storage: Local filesystem or S3/MinIO
Worker: ARQ (Redis-backed) for async generation
```

---

## 2. Repository Structure

```
MailCraft/
├── app/
│   ├── main.py                        # FastAPI app factory + lifespan + router mounting
│   ├── exceptions.py                  # Global exception handlers
│   ├── logging_config.py              # Re-export of core.logging.setup.configure_logging
│   │
│   ├── api/
│   │   ├── dependencies/
│   │   │   ├── authentication.py      # AuthenticatedUser, OptionalUser, Page redirects
│   │   │   ├── database.py            # DatabaseSession DI
│   │   │   ├── large_language_model.py# LLMClient + Settings DI
│   │   │   └── storage.py             # FileStorage DI
│   │   └── routes/
│   │       ├── api/
│   │       │   ├── auth_api.py        # POST /api/auth/register|login|refresh; GET /api/auth/me
│   │       │   ├── generations.py     # GET|POST /api/generations; GET|DELETE /{id}; GET /{id}/pdf
│   │       │   ├── scenarios.py       # CRUD + clone /api/scenarios
│   │       │   ├── jobs.py            # GET /api/jobs/{job_id}
│   │       │   └── health.py          # GET /api/health, /api/health/ready
│   │       ├── dashboard/
│   │       │   └── pages.py           # HTML dashboard pages (index, generate, scenarios, editor)
│   │       ├── auth_pages.py          # HTML login/register/logout form pages
│   │       └── pages.py               # GET / (home page)
│   │
│   ├── application/
│   │   ├── handlers/
│   │   │   └── application_document_handler.py
│   │   ├── pipelines/
│   │   │   ├── generation_context.py  # Shared mutable state for pipeline
│   │   │   ├── generation_pipeline.py # Pipeline runner
│   │   │   ├── pipeline_factory.py    # build_application_document_pipeline()
│   │   │   └── steps/
│   │   │       ├── validate_input_step.py
│   │   │       ├── extract_resume_text_step.py
│   │   │       ├── store_resume_files_step.py
│   │   │       ├── grounding_research_step.py
│   │   │       ├── language_model_generation_step.py
│   │   │       ├── format_output_step.py
│   │   │       ├── humanize_content_step.py
│   │   │       └── persist_generated_content_step.py
│   │   ├── serializers/
│   │   │   └── generated_content_serializer.py
│   │   └── services/
│   │       ├── authentication_service.py
│   │       ├── scenario_service.py
│   │       ├── generated_content_service.py
│   │       ├── generation_job_service.py
│   │       ├── content_humanization_service.py
│   │       ├── email_formatting_service.py
│   │       ├── fact_preservation_service.py
│   │       ├── resume_storage_service.py
│   │       └── default_scenario_templates.py
│   │
│   ├── core/
│   │   ├── configuration.py           # Pydantic Settings (all env vars)
│   │   ├── csrf.py                    # Token generation helpers
│   │   ├── exceptions.py              # LlmError, ServiceValidationError
│   │   ├── rate_limits.py             # slowapi Limiter instance
│   │   ├── startup_validation.py      # Prod secret + API key checks
│   │   └── logging/
│   │       ├── setup.py               # configure_logging()
│   │       ├── json_formatter.py      # Structured JSON log formatter
│   │       ├── filters.py             # RequestContextFilter (adds request_id)
│   │       └── context.py             # request_id ContextVar
│   │
│   ├── database/
│   │   ├── base.py                    # SQLAlchemy declarative Base
│   │   ├── engine_manager.py          # Singleton engine + session factory
│   │   ├── session.py                 # get_database_session() generator
│   │   ├── migrations.py              # run_migrations() using Alembic API
│   │   └── models/
│   │       ├── user.py
│   │       ├── refresh_token.py
│   │       ├── scenario.py
│   │       ├── generated_content.py
│   │       └── generation_job.py
│   │
│   ├── domain/enums/
│   │   ├── generation_kind.py         # LEGACY_EMAIL, APPLICATION_DOCUMENT
│   │   ├── application_purpose.py     # INTERVIEW, MS, PHD
│   │   ├── document_type.py           # EMAIL, COVER_LETTER
│   │   └── generation_job_status.py   # QUEUED, RUNNING, COMPLETED, FAILED
│   │
│   ├── infrastructure/
│   │   ├── large_language_model/
│   │   │   └── client.py              # Google GenAI wrapper
│   │   ├── document_processing/
│   │   │   └── pdf_text_extractor.py  # pypdf text extraction
│   │   ├── export/
│   │   │   └── document_pdf_exporter.py # ReportLab PDF builder
│   │   ├── health/
│   │   │   └── checks.py              # DB ping + optional LLM ping
│   │   └── storage/
│   │       ├── base.py                # FileStorage ABC
│   │       ├── factory.py             # build_file_storage(settings)
│   │       ├── local_file_storage.py
│   │       └── s3_file_storage.py
│   │
│   ├── middleware/
│   │   ├── csrf.py                    # Double-submit CSRF protection
│   │   ├── security_headers.py        # CSP, X-Frame-Options, etc.
│   │   └── request_logging.py         # Request ID + timing logs
│   │
│   ├── prompts/
│   │   ├── builders/
│   │   │   ├── __init__.py
│   │   │   ├── content_humanizer_prompt_builder.py
│   │   │   └── application_document_user_prompt_builder.py
│   │   └── templates/
│   │       ├── content_humanizer.py   # CONTENT_HUMANIZER_SYSTEM_RULES constant
│   │       └── parts/                 # (empty after quick-mail removal)
│   │
│   ├── schemas/                       # Pydantic v2 request/response models
│   │   ├── authentication.py
│   │   ├── scenario.py
│   │   ├── generated_content.py
│   │   ├── generation_job.py
│   │   ├── health.py
│   │   └── application_document.py    # StructuredApplicationDocumentOutput
│   │
│   ├── static/
│   │   └── js/
│   │       ├── dompurify.min.js       # Client-side HTML sanitizer (bundled)
│   │       └── safe-dom.js            # XSS-safe DOM helpers
│   │
│   ├── templates/                     # Jinja2 HTML templates
│   │   ├── base.html
│   │   ├── layouts/
│   │   │   └── dashboard.html
│   │   ├── pages/
│   │   │   ├── index.html
│   │   │   ├── auth/
│   │   │   │   ├── login.html
│   │   │   │   └── register.html
│   │   │   └── dashboard/
│   │   │       ├── index.html         # Document history
│   │   │       ├── generate.html      # Application document generator
│   │   │       ├── scenarios.html     # Scenario list
│   │   │       └── scenario_editor.html
│   │   └── components/
│   │       ├── navbar.html
│   │       ├── footer.html
│   │       ├── flash.html
│   │       └── ui.html                # Jinja2 macros (button, card, form_field)
│   │
│   └── worker/
│       └── main.py                    # ARQ worker + process_generation_job function
│
├── alembic/
│   ├── env.py
│   └── versions/
│       ├── 0001_initial.py
│       ├── 0002_unified_generated_content.py
│       ├── 0003_content_humanization.py
│       ├── 0004_humanizer_metadata.py
│       ├── 0005_upload_storage_keys.py
│       └── 0006_generation_jobs.py
│
├── data/                              # Runtime: SQLite DB + local uploads
├── tests/
│   ├── conftest.py                    # Shared fixtures (client, auth helpers)
│   ├── integration/                   # Full HTTP round-trip tests
│   └── unit/                          # Isolated unit tests per service/step
├── tools/
│   └── reporting/                     # Offline PDF report generators
├── scripts/
│   └── deploy.sh                      # Docker entrypoint: migrate + start
├── docs/                              # Architecture + design docs (this file)
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── pyproject.toml
├── alembic.ini
├── .env.example
└── .env.production.example
```

---

## 3. Technology Stack

| Layer | Library / Tool | Version |
|-------|---------------|---------|
| Web framework | FastAPI | ≥0.137 |
| Server | Uvicorn (standard) | ≥0.49 |
| ORM | SQLAlchemy | ≥2.0 |
| Migrations | Alembic | ≥1.14 |
| Validation | Pydantic v2 | via pydantic-settings ≥2.14 |
| LLM | google-genai | ≥2.8 |
| PDF text | pypdf | ≥5.1 |
| PDF export | ReportLab | ≥4.4 |
| Auth | PyJWT (HS256) | ≥2.10 |
| Hashing | bcrypt | ≥4.2 |
| Rate limiting | slowapi | ≥0.1.9 |
| Template engine | Jinja2 | ≥3.1 |
| DB driver | psycopg[binary] | ≥3.2 (Postgres prod) |
| Object storage | boto3 | ≥1.35 (S3/MinIO) |
| Async worker | ARQ | ≥0.26 |
| Queue | Redis | ≥5.0 |
| Dev: lint | Ruff | ≥0.15 |
| Dev: types | pyrefly | ≥1.1 |
| Dev: testing | pytest + pytest-asyncio + pytest-cov | ≥9.1 |
| Frontend CSS | Tailwind CSS (CDN) | v3 |
| Frontend JS | DOMPurify (bundled) + marked (CDN + SRI) | — |

---

## 4. Configuration & Environment Variables

All settings are loaded by `app/core/configuration.py` via Pydantic `BaseSettings`. The `.env` file is read automatically. A cached singleton is available via `get_settings()`.

### Core Application

| Env Var | Default | Required | Description |
|---------|---------|----------|-------------|
| `DEBUG` | `false` | No | Enables OpenAPI, reloader, relaxes security checks |
| `HOST` | `127.0.0.1` | No | Bind address for uvicorn |
| `PORT` | `8081` | No | Bind port |
| `APP_NAME` | `MailCraft` | No | Application display name |

### Google Gemini

| Env Var | Default | Required | Description |
|---------|---------|----------|-------------|
| `GOOGLE_API_KEY` | `""` | **Yes (prod)** | Google AI Studio / Vertex API key |
| `GOOGLE_MODEL_A` | — | **Yes** | Primary generation model (e.g. `gemini-2.5-flash`) |
| `GOOGLE_MODEL_B` | — | **Yes** | Secondary model (retained for config; not used in active pipeline) |
| `GOOGLE_JUDGE_MODEL` | — | **Yes** | Model for humanizer + health LLM check |
| `LLM_REQUEST_DELAY_SECONDS` | `0.0` | No | Post-call sleep to avoid rate-limit bursts |
| `LLM_MAX_RETRIES` | `3` | No | Max retry attempts on transient API errors |
| `LLM_RETRY_BASE_DELAY_SECONDS` | `1.0` | No | Exponential backoff base (seconds) |
| `LLM_RETRY_MAX_DELAY_SECONDS` | `30.0` | No | Backoff cap |

### Database

| Env Var | Default | Description |
|---------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./data/mailcraft.db` | SQLAlchemy URL; use `postgresql://...` in production |
| `RUN_MIGRATIONS_ON_STARTUP` | `true` | Set to `false` in Docker (deploy.sh runs Alembic) |

### Authentication

| Env Var | Default | Description |
|---------|---------|-------------|
| `JWT_SECRET_KEY` | `change-me-in-production` | HS256 signing secret; **must be ≥32 bytes in production** |
| `JWT_ACCESS_EXPIRE_MINUTES` | `15` | Access token TTL |
| `JWT_REFRESH_EXPIRE_DAYS` | `7` | Refresh token TTL |
| `CSRF_ENABLED` | `true` | Toggle double-submit CSRF protection |

### File Storage & Uploads

| Env Var | Default | Description |
|---------|---------|-------------|
| `UPLOAD_MAX_MB` | `10` | Max resume PDF size |
| `UPLOAD_DIR` | `./data/uploads` | Root directory for local storage |
| `STORAGE_BACKEND` | `local` | `local` or `s3` |
| `STORE_UPLOADED_RESUMES` | `false` | Persist raw PDF bytes after text extraction |
| `S3_BUCKET` | `""` | S3 bucket name (required when `STORAGE_BACKEND=s3`) |
| `AWS_REGION` | `""` | AWS region |
| `AWS_ACCESS_KEY_ID` | `""` | AWS credentials |
| `AWS_SECRET_ACCESS_KEY` | `""` | AWS credentials |
| `AWS_ENDPOINT_URL` | `""` | Custom endpoint (MinIO, LocalStack) |

### Humanization

| Env Var | Default | Description |
|---------|---------|-------------|
| `HUMANIZE_CONTENT_ENABLED` | `true` | Enable/disable humanization step |
| `HUMANIZE_MODEL` | `""` | Override model; falls back to `GOOGLE_MODEL_A` |
| `HUMANIZE_FACT_RECALL_THRESHOLD` | `0.75` | Min fraction of facts that must survive humanization |

### Async Worker

| Env Var | Default | Description |
|---------|---------|-------------|
| `GENERATION_ASYNC_ENABLED` | `false` | Allow `?async=true` on POST /api/generations |
| `REDIS_URL` | `redis://localhost:6379/0` | ARQ job queue |

### Rate Limiting

| Env Var | Default | Description |
|---------|---------|-------------|
| `RATE_LIMIT_ENABLED` | `true` | Toggle all rate limits (disable in CI) |

### Logging & Observability

| Env Var | Default | Description |
|---------|---------|-------------|
| `LOG_FORMAT` | `json` | `json` (structured) or `text` (human-readable) |
| `LOG_LEVEL` | `INFO` | Standard Python log level |
| `HEALTH_CHECK_LLM_ENABLED` | `false` | Include LLM ping in readiness check |
| `HEALTH_CHECK_LLM_TIMEOUT_SECONDS` | `2.0` | LLM health timeout |

---

## 5. Database Layer

### Models & Relationships

```
users ────────────┬──── refresh_tokens
     │            │
     ├──── scenarios ────────── generated_contents
     │                               │
     └──── generated_contents ───────┘
                                     │
     generation_jobs ─── result ──── generated_contents
```

### Table: `users`

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer PK | Auto-increment |
| `email` | String (unique) | Lowercased on registration |
| `hashed_password` | String | bcrypt |
| `is_active` | Boolean | Default `true` |
| `created_at` | DateTime (tz) | |

### Table: `refresh_tokens`

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer PK | |
| `jti` | String (unique) | JWT token ID |
| `token_hash` | String | SHA-256 of raw token |
| `user_id` | FK → users | |
| `expires_at` | DateTime (tz) | |
| `revoked_at` | DateTime (tz, nullable) | Set on logout/rotation |

### Table: `scenarios`

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer PK | |
| `user_id` | FK → users | |
| `name` | String | |
| `purpose` | String | `interview` / `ms` / `phd` |
| `document_type` | String | `email` / `cover_letter` |
| `system_prompt` | Text | Markdown prompt sent to LLM as system instruction |
| `is_default` | Boolean | Default `false`; set on seeded scenarios |
| `created_at`, `updated_at` | DateTime (tz) | |

### Table: `generated_contents`

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer PK | |
| `user_id` | FK → users | |
| `generation_kind` | String | `application_document` (or `legacy_email` for historical rows) |
| `subject` | String (nullable) | Email subject |
| `body` | Text | Final body (humanized or raw) |
| `raw_subject` | String (nullable) | Pre-humanization subject |
| `raw_body` | Text (nullable) | Pre-humanization body |
| `humanization_applied` | Boolean | |
| `humanizer_model_name` | String (nullable) | |
| `humanizer_prompt_version` | String (nullable) | |
| `created_at` | DateTime (tz) | |
| **Application doc fields** | | |
| `scenario_id` | FK → scenarios (nullable) | |
| `purpose` | String (nullable) | |
| `document_type` | String (nullable) | |
| `position_description` | Text (nullable) | |
| `cv_filenames_json` | Text (nullable) | JSON list of uploaded filenames |
| `cv_extracted_text` | Text (nullable) | Concatenated PDF text |
| `resume_storage_keys_json` | Text (nullable) | JSON list of `{filename, key}` |
| `grounding_links_json` | Text (nullable) | JSON list of URLs |
| `metadata_json` | Text (nullable) | Structured LLM metadata |
| `grounding_metadata_json` | Text (nullable) | Google Search result metadata |
| `model_name` | String (nullable) | LLM model used |
| **Legacy fields (historical)** | | |
| `intent` | Text (nullable) | Kept for old rows only |
| `key_facts_json` | Text (nullable) | |
| `tone` | String (nullable) | |
| `strategy` | String (nullable) | |
| `prompt_version` | String (nullable) | |

### Table: `generation_jobs`

| Column | Type | Notes |
|--------|------|-------|
| `id` | String PK | UUID |
| `user_id` | FK → users | |
| `status` | String | `queued` / `running` / `completed` / `failed` |
| `kind` | String | `application_document` |
| `payload_json` | Text | Serialized job inputs |
| `result_generation_id` | FK → generated_contents (nullable) | Set on completion |
| `error_message` | Text (nullable) | Set on failure |
| `created_at`, `updated_at` | DateTime (tz) | |

### Alembic Migrations

| Revision | Purpose |
|----------|---------|
| `0001_initial` | Create users, refresh_tokens, scenarios, generated_documents (original schema) |
| `0002_unified_generated_content` | Consolidate into `generated_contents` with generation_kind discriminator |
| `0003_content_humanization` | Add raw_subject, raw_body, humanization_applied |
| `0004_humanizer_metadata` | Add humanizer_model_name, humanizer_prompt_version |
| `0005_upload_storage_keys` | Add resume_storage_keys_json |
| `0006_generation_jobs` | Create generation_jobs table |

---

## 6. Authentication & Session Management

### JWT Cookie Flow

```
1. POST /auth/register  (HTML) or  POST /api/auth/register  (JSON)
   └─► register_user() → bcrypt hash → save user → seed 6 default scenarios
   └─► create_access_token(user_id) + create_refresh_token(user_id, db)
   └─► Set-Cookie: access_token (HttpOnly, 15 min)
   └─► Set-Cookie: refresh_token (HttpOnly, 7 days)

2. Subsequent requests:
   Browser sends both cookies → FastAPI reads access_token → verify HS256

3. Token refresh:
   POST /api/auth/refresh
   └─► Decode refresh_token JWT → verify jti + hash in DB → revoke old → issue new pair

4. Logout:
   POST /auth/logout (HTML only)
   └─► Revoke refresh token by jti → clear both cookies
```

### Cookie Properties

| Cookie | `httponly` | `samesite` | `secure` | TTL |
|--------|-----------|------------|---------|-----|
| `access_token` | Yes | lax | `not DEBUG` | 15 min |
| `refresh_token` | Yes | lax | `not DEBUG` | 7 days |

### Default Scenario Seeding

On first registration, 6 scenarios are seeded (`is_default=True`):

| Purpose | Document Type |
|---------|--------------|
| interview | email |
| interview | cover_letter |
| ms | email |
| ms | cover_letter |
| phd | email |
| phd | cover_letter |

These cannot be deleted (service enforces at least one per purpose+type combination).

---

## 7. Middleware Stack

Registration order in `main.py` (outer = first in request chain):

```
SecurityHeadersMiddleware  ← outermost (first to receive request)
  └─ CsrfMiddleware
       └─ RequestLoggingMiddleware
            └─ FastAPI routes
```

### RequestLoggingMiddleware

- Generates or propagates `X-Request-ID` header (UUID4)
- Stores request ID in `request_id` ContextVar (injected into all log records via `RequestContextFilter`)
- Logs at `INFO`: `method`, `path`, `status_code`, `duration_ms`
- Extracts `user_id` from access cookie when present (decoded without exception on failure)

### CsrfMiddleware

- **Exempt paths:** anything starting with `/api/` or `/static/`
- **GET/HEAD/OPTIONS:** sets `csrf_token` cookie if absent (32 random hex bytes via `secrets.token_hex(16)`)
- **POST/PUT/DELETE/PATCH:** reads form body, compares `cookie["csrf_token"]` == `form["csrf_token"]` via `secrets.compare_digest`; returns 403 on mismatch
- **Body replay:** buffers body bytes and replaces `request.receive` so FastAPI form parsers can still consume the body after CSRF has read it
- Skipped entirely when `CSRF_ENABLED=false`
- Cookie: `samesite=strict`, `secure=not debug`, `httponly=False` (must be readable by JS for AJAX — but application doc generation goes through `/api/` which is exempt)

### SecurityHeadersMiddleware

Sets on every response:

```
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
X-XSS-Protection: 0
Permissions-Policy: camera=(), microphone=(), geolocation=()
Content-Security-Policy:
  default-src 'self';
  script-src 'self' 'unsafe-inline' cdn.tailwindcss.com cdn.jsdelivr.net;
  style-src 'self' 'unsafe-inline' cdn.tailwindcss.com fonts.googleapis.com;
  font-src 'self' fonts.gstatic.com;
  img-src 'self' data:;
  connect-src 'self'
```

Removes: `X-Powered-By`, `Server`

---

## 8. API Reference

### Authentication Routes

| Method | Path | Auth | Rate Limit | Body / Params | Response |
|--------|------|------|------------|---------------|----------|
| GET | `/auth/login` | Optional | — | — | HTML login page |
| POST | `/auth/login` | No | 10/min | Form: `email`, `password`, `csrf_token` | Redirect → `/dashboard` |
| GET | `/auth/register` | Optional | — | — | HTML register page |
| POST | `/auth/register` | No | 10/min | Form: `email`, `password`, `csrf_token` | Redirect → `/dashboard` |
| POST | `/auth/logout` | No | — | Form: `csrf_token` | Redirect → `/auth/login` |
| POST | `/api/auth/register` | No | 10/min | `{email, password}` JSON | `{message}` + cookies |
| POST | `/api/auth/login` | No | 10/min | `{email, password}` JSON | `{message}` + cookies |
| GET | `/api/auth/me` | **Yes** | — | — | `{id, email}` |
| POST | `/api/auth/refresh` | Refresh cookie | 30/min | — | `{message}` + new cookies |

### Scenarios Routes

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/scenarios` | Yes | List user's scenarios; optional `?purpose=&document_type=` filters |
| POST | `/api/scenarios` | Yes | Create scenario |
| PATCH | `/api/scenarios/{id}` | Yes | Update name and/or system_prompt |
| POST | `/api/scenarios/{id}/clone` | Yes | Clone with optional `?name=` |
| DELETE | `/api/scenarios/{id}` | Yes | Delete (cannot delete last scenario for a purpose+type combo) |

### Generations Routes

| Method | Path | Auth | Rate Limit | Description |
|--------|------|------|------------|-------------|
| POST | `/api/generations` | Yes | **10/hour** | Generate and persist a document (see §10) |
| GET | `/api/generations` | Yes | — | List with filters: `generation_kind`, `purpose`, `document_type`, `scenario_id`, `q`, `limit`, `offset` |
| GET | `/api/generations/{id}` | Yes | — | Get single document |
| DELETE | `/api/generations/{id}` | Yes | — | Soft-delete record |
| GET | `/api/generations/{id}/pdf` | Yes | — | Export as PDF (ReportLab) |

**POST `/api/generations` (multipart form):**

```
purpose            string  required  interview | ms | phd
document_type      string  required  email | cover_letter
scenario_id        int     required  ID of scenario to use as system prompt
position_description string required Job/program description (max 10,000 chars)
grounding_links    string  optional  Repeatable; URLs for Google Search grounding
resume_files       file    required  Repeatable; PDF files (max UPLOAD_MAX_MB each)
```

When `?async=true` and `GENERATION_ASYNC_ENABLED=true`: returns 202 with `{job_id}` instead of 201.

### Jobs Routes

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/jobs/{job_id}` | Yes | Poll async job status |

### Health Routes

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/health` | No | Liveness: always `{status: "ok"}` |
| GET | `/api/health/ready` | No | Readiness: checks DB + optional LLM |

### Dashboard HTML Routes

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/dashboard` | Yes | Document history with filters and stats |
| GET | `/dashboard/generate` | Yes | Application document generator form |
| GET | `/dashboard/scenarios` | Yes | Scenario management list |
| GET | `/dashboard/scenarios/{id}/edit` | Yes | Scenario prompt editor |

### Public HTML Routes

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/` | No | Landing page |

---

## 9. Application Layer (Handlers & Services)

### ApplicationDocumentHandler

`app/application/handlers/application_document_handler.py`

Entry point for generation. Builds a `GenerationContext` from the caller's arguments, runs the 8-step pipeline, and serializes the persisted ORM record to a `GeneratedContentResponse`.

```python
async def generate(
    self, *, user_id, purpose, document_type, scenario_id,
    position_description, resume_file_payloads, grounding_links,
    database_session, settings, language_model_client, file_storage=None
) -> GeneratedContentResponse
```

### Services

| Service | Key Methods | Notes |
|---------|-------------|-------|
| `authentication_service` | `register_user()`, `login_user()`, `create_access_token()`, `create_refresh_token()`, `rotate_refresh_token()`, `revoke_refresh_token()` | Stateless helpers; DB session passed in |
| `scenario_service` | `list_for_user()`, `get_owned()`, `create()`, `update()`, `clone()`, `delete()` | Enforces minimum-one-per-type constraint on delete |
| `generated_content_service` | `list_for_user(filters, limit, offset)`, `get_owned()`, `delete_owned()`, `get_dashboard_stats()` | Filters: kind, purpose, doc type, scenario_id, query_text (LIKE) |
| `generation_job_service` | `create_job()`, `get_by_id()`, `get_owned()`, `mark_running()`, `mark_completed()`, `mark_failed()`, `enqueue()` | Serializes to Redis via ARQ |
| `content_humanization_service` | `parse_humanized_output()`, `resolve_content_type_label()` | Uses `parse_subject_body_output` from email_formatting_service |
| `email_formatting_service` | `format_document_body()`, `resolve_subject_and_body()`, `build_clipboard_text()`, `parse_subject_body_output()` | Used by format + humanize steps |
| `fact_preservation_service` | `verify_facts_preserved(facts, text, threshold)` | Fuzzy substring matching; returns score + missed list |
| `resume_storage_service` | `store_resume_files(payloads, user_id, file_storage)` | Returns list of `{filename, key}` |
| `default_scenario_templates` | `DEFAULT_SCENARIO_TEMPLATES` list | 6 seeded templates per user |

---

## 10. Generation Pipeline

### Step Sequence

```
POST /api/generations (multipart form)
         │
         ▼
ApplicationDocumentHandler.generate()
         │
         ▼
GenerationPipeline.run(context)
         │
         ├─ 1. ValidateInputStep
         │      Checks: purpose, document_type, position_description not empty,
         │      resume_file_payloads not empty, scenario_id set, scenario
         │      exists and owned by user. Sets context.system_instruction.
         │
         ├─ 2. ExtractResumeTextStep
         │      Extracts text from all uploaded PDFs using pypdf.
         │      Sets context.resume_text (concatenated), context.resume_filenames.
         │
         ├─ 3. StoreResumeFilesStep
         │      If STORE_UPLOADED_RESUMES=true: uploads raw PDFs to FileStorage.
         │      Sets context.resume_storage_keys.
         │
         ├─ 4. GroundingResearchStep
         │      Builds context.user_prompt via application_document_user_prompt_builder.
         │      Includes purpose, document_type, position_description, resume_text,
         │      and any grounding_links.
         │
         ├─ 5. LanguageModelGenerationStep
         │      Calls LLMClient.generate_structured_with_grounding():
         │        - If grounding_links present: two-pass (Search → JSON)
         │        - Else: single structured JSON pass
         │      Model: GOOGLE_MODEL_A. Sets context.structured_output,
         │      context.grounding_metadata, context.model_name.
         │
         ├─ 6. FormatOutputStep
         │      Validates StructuredApplicationDocumentOutput from structured_output.
         │      Extracts subject + body, formats paragraphs, builds clipboard_text.
         │      Raises LlmError if email has no subject.
         │
         ├─ 7. HumanizeContentStep
         │      (Skipped if HUMANIZE_CONTENT_ENABLED=false)
         │      Saves raw_subject / raw_body. Builds humanizer prompt with
         │      must_preserve_facts from metadata.key_highlights_used +
         │      metadata.matched_skills. Calls HUMANIZE_MODEL (or GOOGLE_MODEL_A).
         │      Verifies fact recall ≥ HUMANIZE_FACT_RECALL_THRESHOLD.
         │      Falls back to raw content if LLM fails or facts are dropped.
         │
         └─ 8. PersistGeneratedContentStep
                Inserts GeneratedContent ORM record with all output fields.
                Sets context.generated_content (refreshed from DB).
         │
         ▼
serialize_generated_content(record, include_raw_content=DEBUG)
         │
         ▼
GeneratedContentResponse (201)
```

### LLM Output Schema (`StructuredApplicationDocumentOutput`)

```json
{
  "subject": "string (null for cover letters)",
  "body": "string (multi-paragraph, formatted text)",
  "metadata": {
    "generation_reason": "string",
    "organization": "string",
    "position_title": "string",
    "recipient_name": "string",
    "matched_skills": ["string"],
    "key_highlights_used": ["string"],
    "tone_used": "string"
  }
}
```

---

## 11. LLM Infrastructure

`app/infrastructure/large_language_model/client.py`

### Client Initialization

Lazy-init: `google.genai.Client(api_key=settings.google_api_key)` created on first use.

### Methods

| Method | Model Used | Notes |
|--------|-----------|-------|
| `generate_content(prompt, model?)` | `google_judge_model` (default) | Plain text output |
| `generate_structured_with_grounding(system_instruction, user_prompt, response_schema, model, enable_google_search)` | `model` arg | Two-pass if search enabled |
| `_run_grounding_research(system_instruction, user_prompt, grounding_links, model)` | — | Appends search excerpts to context |
| `_run_structured_generation(system_instruction, user_prompt, schema, model)` | — | `response_mime_type=application/json` |

### Two-Pass Google Search Strategy

Gemini 2.5 does not support simultaneous tool use and structured JSON output. When `grounding_links` are provided:

```
Pass 1: Google Search grounding call (tool_config=AUTO)
        → returns freetext with search excerpts embedded
Pass 2: Structured JSON call with original prompt + search context appended
        → returns typed StructuredApplicationDocumentOutput
```

When no grounding links: single structured pass.

### Retry Logic

```python
for attempt in range(max_retries):
    try:
        return await _call()
    except google.APIError as e:
        if e.code in (429, 500, 503):
            delay = min(base * 2**attempt, max_delay)
            await asyncio.sleep(delay)
        else:
            raise LlmError(...)
raise LlmError("Max retries exceeded")
```

### Token Usage Logging

After every LLM call, `_log_token_usage()` logs at DEBUG:
```json
{"operation": "structured", "model": "...", "prompt_tokens": 1234,
 "candidates_tokens": 567, "total_tokens": 1801}
```

---

## 12. File Storage

### Abstraction

`FileStorage` ABC in `app/infrastructure/storage/base.py`:

```python
def put(key: str, data: bytes, content_type: str) -> str   # returns key
def get(key: str) -> bytes
def delete(key: str) -> None
def exists(key: str) -> bool
```

### Local Storage (`LocalFileStorage`)

Files stored at `{UPLOAD_DIR}/{key}`. Directories created automatically on put.

### S3 Storage (`S3FileStorage`)

Uses `boto3` `s3.put_object` / `s3.get_object`. Supports `AWS_ENDPOINT_URL` for MinIO compatibility. Raises `ServiceValidationError` if `S3_BUCKET` is empty.

### Factory

```python
def build_file_storage(settings) -> FileStorage:
    if settings.storage_backend == "s3":
        return S3FileStorage(settings)
    return LocalFileStorage(settings)
```

### Resume Key Pattern

```
resumes/{user_id}/{uuid4}/{original_filename}
```

Stored in DB as `resume_storage_keys_json`: `[{"filename": "cv.pdf", "key": "resumes/1/abc123/cv.pdf"}]`

---

## 13. Async Worker

### Overview

When `GENERATION_ASYNC_ENABLED=true`, the `POST /api/generations?async=true` path:
1. Serializes resume PDFs as base64 in `payload_json`
2. Creates a `GenerationJob` record (status=`queued`)
3. Enqueues the job via ARQ to Redis
4. Returns HTTP 202 with `{job_id}`

The client polls `GET /api/jobs/{job_id}` to track progress.

### Worker Process

```
mailcraft-worker
    └─ ARQ WorkerSettings
         ├─ functions: [process_generation_job]
         ├─ on_startup: initialize_database()
         └─ redis_settings: REDIS_URL
```

### process_generation_job Flow

```python
async def process_generation_job(ctx, job_id):
    job = job_service.get_by_id(job_id)

    # Idempotency guard: skip already-completed jobs on ARQ retry
    if job.status == COMPLETED:
        return {job_id, generation_id}

    job_service.mark_running(job)
    payload = json.loads(job.payload_json)

    # Decode resume PDFs from base64
    resume_payloads = [(filename, base64.b64decode(content_b64)) for ...]

    result = await ApplicationDocumentHandler().generate(...)
    job_service.mark_completed(job, generation_id=result.id)
    return {job_id, generation_id}
```

On any exception: `session.rollback()` → `mark_failed(job, error_message)` → re-raise.

### Payload JSON Structure

```json
{
  "purpose": "interview",
  "document_type": "email",
  "scenario_id": 42,
  "position_description": "Senior ML Engineer...",
  "grounding_links": ["https://company.example/about"],
  "resume_files": [
    {"filename": "cv.pdf", "content_base64": "JVBERi0x..."}
  ]
}
```

---

## 14. Templates & Frontend

### Template Hierarchy

```
base.html
  ├─ layouts/dashboard.html   ← extends base; adds sidebar + CSRF token
  │    ├─ pages/dashboard/index.html
  │    ├─ pages/dashboard/generate.html
  │    ├─ pages/dashboard/scenarios.html
  │    └─ pages/dashboard/scenario_editor.html
  └─ pages/
       ├─ index.html
       ├─ auth/login.html
       └─ auth/register.html
```

### Component Macros (`components/ui.html`)

| Macro | Signature | Renders |
|-------|-----------|---------|
| `button(text, type, variant, extra_class, id)` | `variant="primary"` or `"secondary"` | `<button>` with brand/stone colors |
| `card(title, extra_class)` | block macro | white rounded-2xl card |
| `form_field(label, name, field_type, value, placeholder, required, rows)` | `field_type="text"` or `"textarea"` | labeled input or textarea |

### Design System Tokens (Tailwind config in `base.html`)

```js
colors: {
  'brand': { 50–950: ... }   // Violet primary palette
  'surface': { 50–950: ... } // Warm white/grey backgrounds
  'stone': Tailwind default stone scale
}
```

### Dashboard: Client-Side Architecture

Dashboard pages (generate, scenarios, history) make `fetch()` calls to the JSON API (`/api/*`). Cookie auth is automatic (same-origin). CSRF is not required for `/api/*` routes (exempt by design).

The scenario editor auto-saves with a 2-second debounce via `PATCH /api/scenarios/{id}`.

Document history uses a view/copy/delete modal backed by `GET /api/generations/{id}` and `DELETE /api/generations/{id}`.

---

## 15. Prompt Engineering

### Application Document User Prompt

`app/prompts/builders/application_document_user_prompt_builder.py`

Builds the user-turn message from:
- **Purpose** and **document type** → document label
- **Position description** → pasted verbatim
- **Resume text** → extracted PDF content
- **Grounding links** → bulleted list (or "None provided")
- **BODY_FORMAT_INSTRUCTIONS** → paragraph structure rules

The prompt instructs the model to return a JSON object matching `StructuredApplicationDocumentOutput`.

### Content Humanizer

`app/prompts/templates/content_humanizer.py` — `CONTENT_HUMANIZER_SYSTEM_RULES`

Key rules enforced:
- Preserve all factual claims (names, dates, numbers, organizations)
- Do not invent new facts
- Remove AI telltale phrases (e.g., "I hope this email finds you well", "In conclusion")
- Maintain subject in `Subject:` format on first line
- Keep approximate length ±15%
- Match tone label (formal/casual/etc.)

**Builder** (`content_humanizer_prompt_builder.py`, version `1.1.0`):
- Accepts optional `must_preserve_facts` list (injected from `key_highlights_used` + `matched_skills` in document metadata)
- Returns full prompt combining system rules + subject/body + preservation checklist

**Fact guard:** `fact_preservation_service.verify_facts_preserved()` checks that each required fact appears as a substring (case-insensitive) in the humanized clipboard text. Falls back to raw content if score < threshold.

---

## 16. Rate Limiting

Implementation: `slowapi.Limiter(key_func=get_remote_address)` with a custom `authenticated_rate_limit_key` that returns `user_id` from the access JWT cookie (falls back to IP for unauthenticated requests).

| Endpoint | Limit | Key |
|----------|-------|-----|
| `POST /api/auth/register` | 10/minute | IP |
| `POST /api/auth/login` | 10/minute | IP |
| `POST /api/auth/refresh` | 30/minute | IP |
| `POST /auth/login` | 10/minute | IP |
| `POST /auth/register` | 10/minute | IP |
| `POST /api/generations` | **10/hour** | User ID (or IP) |

Rate limit exceeded returns HTTP 429. Disabled when `RATE_LIMIT_ENABLED=false` (CI, tests).

---

## 17. Security Controls

| Control | Details |
|---------|---------|
| **CSRF protection** | Double-submit cookie; all non-API form routes protected; `secrets.compare_digest` for timing safety |
| **Security headers** | CSP, X-Frame-Options: DENY, nosniff, Referrer-Policy, Permissions-Policy |
| **JWT validation** | `startup_validation.py` refuses weak default `JWT_SECRET_KEY` in production; requires ≥32 bytes |
| **API key validation** | `GOOGLE_API_KEY` required when `DEBUG=false` |
| **Cookie security** | `Secure`, `HttpOnly`, `SameSite=lax` in production |
| **Password hashing** | bcrypt |
| **Refresh token rotation** | Token hash stored in DB; old token revoked on rotation |
| **XSS prevention** | DOMPurify used in scenario editor; `textContent` instead of `innerHTML` in history modal |
| **SRI** | `marked.js` CDN script in scenario editor has SHA-384 integrity attribute |
| **Rate limiting** | Auth + generation endpoints rate-limited |
| **Input validation** | Pydantic models on all API endpoints; form length limits |

---

## 18. Health Checks

### `GET /api/health` (Liveness)

Always returns:
```json
{"status": "ok"}
```

Used by Docker HEALTHCHECK directive.

### `GET /api/health/ready` (Readiness)

Performs:
1. **Database check:** `SELECT 1` via SQLAlchemy
2. **LLM check** (if `HEALTH_CHECK_LLM_ENABLED=true`): small `generate_content` call with `HEALTH_CHECK_LLM_TIMEOUT_SECONDS` timeout

Response shape:
```json
{
  "status": "ok | degraded | fail",
  "checks": {
    "database": {"status": "ok", "response_ms": 4},
    "llm": {"status": "ok", "response_ms": 340}
  }
}
```

Returns HTTP 503 if `database.status == "fail"`. Returns 200 even when `llm.status == "degraded"`.

---

## 19. PDF Export

`app/infrastructure/export/document_pdf_exporter.py`

### Build Process

1. **`build_document_pdf(record)`** → `bytes`
2. Uses `reportlab.platypus.SimpleDocTemplate` (letter size, 72pt margins)
3. Layout:
   - MailCraft logo text + generation metadata (purpose, document type, organization, position)
   - Horizontal rule
   - Subject line (bold, if present)
   - Body paragraphs (each wrapped in `Paragraph` with indentation)
   - Footer: "MailCraft — Generated Document | {date} | Page N"
4. Styles: `getSampleStyleSheet()` extended with custom heading, normal, small styles

### Filename

```
mailcraft-{purpose}-{document_type}-{YYYYMMDD}.pdf
```

### Route

```
GET /api/generations/{id}/pdf
→ StreamingResponse(content=bytes, media_type="application/pdf",
                   headers={"Content-Disposition": "attachment; filename=..."})
```

---

## 20. Dev vs Production Differences

| Feature | `DEBUG=true` | `DEBUG=false` |
|---------|-------------|--------------|
| OpenAPI docs (`/docs`, `/redoc`, `/openapi.json`) | Enabled | **Disabled** |
| Uvicorn `--reload` | Yes | No |
| JWT secret validation | Skipped | **Enforced** (must be ≥32 bytes, not default) |
| Google API key requirement | Optional | **Required** |
| Cookie `Secure` flag | `False` | **`True`** |
| CSRF cookie `Secure` flag | `False` | **`True`** |
| Raw content in API response | Included (`raw_subject`, `raw_body`) | **Hidden** |
| Dashboard "Original AI vs Humanized" tabs | Shown (JS `DEBUG_MODE=true`) | **Hidden** |
| Log format | `text` (unless `LOG_FORMAT=json`) | `json` |
| Access log level | INFO | WARNING |
| `lifespan` startup validation | No-op | Full checks |

---

## 21. Docker & Deployment

### Dockerfile (Multi-Stage)

**Stage 1 — builder:**
```dockerfile
FROM python:3.12-slim-bookworm AS builder
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
```

**Stage 2 — runtime:**
```dockerfile
FROM python:3.12-slim-bookworm
WORKDIR /app
COPY --from=builder /app/.venv ./.venv
COPY app/ alembic/ alembic.ini scripts/ tools/ ./
RUN useradd -r mailcraft && chown -R mailcraft:mailcraft /app
USER mailcraft
EXPOSE 8081
HEALTHCHECK --interval=30s --timeout=10s CMD curl -f /api/health || exit 1
CMD ["./scripts/deploy.sh"]
```

### deploy.sh

```bash
#!/usr/bin/env bash
set -euo pipefail
.venv/bin/alembic upgrade head
exec .venv/bin/mailcraft
```

Ensures migrations run before server starts; uses `exec` so the process receives shutdown signals cleanly.

### docker-compose.yml Services

| Service | Profile | Image | Ports | Notes |
|---------|---------|-------|-------|-------|
| `db` | default | `postgres:16-alpine` | 5432 | Volume: `postgres_data`; `POSTGRES_DB/USER/PASSWORD=mailcraft` |
| `app` | default | Built locally | 8081:8081 | Env from `.env.production`; depends on `db`; `RUN_MIGRATIONS_ON_STARTUP=false` |
| `redis` | `scale` | `redis:7-alpine` | 6379 | ARQ job queue |
| `minio` | `scale` | `minio/minio` | 9000/9001 | S3-compatible storage |
| `worker` | `scale` | Built locally | — | Runs `mailcraft-worker`; depends on `db`, `redis` |

### Volume Mounts

| Volume | Purpose |
|--------|---------|
| `postgres_data` | Postgres data directory |
| `upload_data` | Local file uploads (app + worker share) |
| `minio_data` | MinIO object storage |

### Running with Async Generation (full stack)

```bash
docker compose --profile scale up
```

Adds Redis, MinIO, and the worker service. Set `GENERATION_ASYNC_ENABLED=true`, `STORAGE_BACKEND=s3`, `S3_BUCKET=mailcraft` in `.env.production`.

### Makefile Targets

```
make dev      → DEBUG=true uv run mailcraft
make run      → uv run mailcraft
make worker   → uv run mailcraft-worker
make migrate  → uv run alembic upgrade head
make test     → uv run pytest
make lint     → uv run ruff check && ruff format --check
make fmt      → uv run ruff check --fix && ruff format .
```

---

## 22. CI Pipeline

**File:** `.github/workflows/ci.yml`  
**Triggers:** push and pull request to `main` and `develop`

### Jobs

#### `lint`

```yaml
steps:
  - checkout
  - setup uv + Python 3.12
  - uv sync --all-groups
  - uv run ruff check .
  - uv run ruff format --check .
```

#### `type-check`

```yaml
steps:
  - checkout
  - setup uv + Python 3.12
  - uv sync --all-groups
  - uv run pyrefly check    # continue-on-error: true
```

#### `test`

```yaml
env:
  GOOGLE_API_KEY: test-api-key
  GOOGLE_MODEL_A: gemini-2.5-flash
  GOOGLE_MODEL_B: gemini-2.5-flash
  GOOGLE_JUDGE_MODEL: gemini-2.5-flash
  JWT_SECRET_KEY: ci-secret-key-32-bytes-minimum-ok
  DATABASE_URL: sqlite:///./data/test.db
  RATE_LIMIT_ENABLED: false
  LOG_FORMAT: text
  HUMANIZE_CONTENT_ENABLED: false
  CSRF_ENABLED: false

steps:
  - checkout
  - setup uv + Python 3.12
  - mkdir -p data
  - uv run pytest --cov=app --cov-report=xml --cov-fail-under=60
  - upload coverage to codecov
```

Coverage minimum: **60%** of `app/` source lines.

---

## 23. Data Flow — End to End

### Synchronous Document Generation

```
User (browser)
  │
  │  POST /api/generations  (multipart/form-data)
  │    - purpose=interview
  │    - document_type=email
  │    - scenario_id=3
  │    - position_description=...
  │    - grounding_links=https://company.com
  │    - resume_files=[cv.pdf]
  ▼
FastAPI Router (app/api/routes/api/generations.py)
  │ authenticate via access_token cookie
  │ check rate limit (10/hour per user)
  ▼
ApplicationDocumentHandler.generate()
  │ build GenerationContext
  ▼
GenerationPipeline.run(context)
  │
  ├─ ValidateInputStep
  │    → fetch scenario from DB; set system_instruction
  │
  ├─ ExtractResumeTextStep
  │    → pypdf → resume_text = "Jane Doe, Python 5 years..."
  │
  ├─ StoreResumeFilesStep
  │    → if STORE_UPLOADED_RESUMES: upload to FileStorage; store keys
  │
  ├─ GroundingResearchStep
  │    → assemble user_prompt with resume_text + position + grounding URLs
  │
  ├─ LanguageModelGenerationStep
  │    → Pass 1: Google Search grounding (if links present)
  │    → Pass 2: generate_structured(schema=StructuredApplicationDocumentOutput)
  │    → structured_output = {subject, body, metadata{...}}
  │
  ├─ FormatOutputStep
  │    → validate schema → format paragraphs → build clipboard_text
  │
  ├─ HumanizeContentStep
  │    → save raw_subject, raw_body
  │    → build humanizer prompt with key_highlights_used facts
  │    → call HUMANIZE_MODEL → parse output → verify facts ≥ threshold
  │    → if ok: update subject, body, clipboard_text
  │    → if fail: restore raw content
  │
  └─ PersistGeneratedContentStep
       → INSERT generated_contents → refresh → set context.generated_content
  │
  ▼
serialize_generated_content(record, include_raw_content=DEBUG)
  │
  ▼
HTTP 201 GeneratedContentResponse
{
  "id": 42,
  "generation_kind": "application_document",
  "purpose": "interview",
  "document_type": "email",
  "scenario_id": 3,
  "scenario_name": "Default Interview Email",
  "subject": "Application for Senior ML Engineer",
  "body": "Dear Dr. Smith,\n\n...",
  "clipboard_text": "Subject: Application...\n\nDear Dr. Smith...",
  "humanization_applied": true,
  "metadata_json": {...},
  "created_at": "2026-07-01T..."
}
```

### Async Generation (with Worker)

```
POST /api/generations?async=true
  │
  ├─ Serialize resume PDFs as base64
  ├─ INSERT generation_jobs (status=queued)
  ├─ Enqueue job to Redis
  └─ Return HTTP 202 {job_id: "uuid"}

  ... (client polls GET /api/jobs/{job_id}) ...

ARQ Worker picks up job
  ├─ mark_running(job)
  ├─ ApplicationDocumentHandler.generate() (same pipeline as sync)
  ├─ mark_completed(job, generation_id=result.id)
  └─ Client polls → status=completed, generation_id available
     └─ Client fetches GET /api/generations/{generation_id}
```

---

## Appendix A: Enums

| Enum | Values |
|------|--------|
| `GenerationKind` | `application_document`, `legacy_email` (historical only) |
| `ApplicationPurpose` | `interview`, `ms`, `phd` |
| `DocumentType` | `email`, `cover_letter` |
| `GenerationJobStatus` | `queued`, `running`, `completed`, `failed` |

## Appendix B: HTTP Error Codes

| Status | When |
|--------|------|
| 400 | Invalid input (Pydantic validation failure) |
| 401 | Missing or invalid access token |
| 403 | CSRF token mismatch |
| 404 | Resource not found or not owned by user |
| 422 | Request body schema error (FastAPI default) |
| 429 | Rate limit exceeded |
| 500 | Unhandled server error |
| 503 | Readiness check failed (DB down) |

## Appendix C: Known Limitations

1. **No API logout endpoint** — refresh token revocation only available via the HTML `POST /auth/logout` form.
2. **Single Postgres database** — no read replicas; no connection pooling configured beyond SQLAlchemy defaults.
3. **Humanizer two-call cost** — every generation makes at least two LLM calls when humanization is enabled.
4. **Base64 resume encoding in async jobs** — large PDFs increase Redis payload size; consider streaming or pre-upload for large files.
5. **Google Search grounding two-pass** — Gemini limitation requires two API calls when grounding links are provided.
6. **LEGACY_EMAIL enum value retained** — historical `legacy_email` rows remain in DB; filter UI shows them as "Legacy".
