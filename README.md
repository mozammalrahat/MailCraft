# MailCraft

AI-powered application document generator. Uploads your CV, applies a scenario-driven system prompt, and produces polished interview emails and cover letters grounded in your real experience. Built with FastAPI, Jinja2, SQLAlchemy, and Google Gemini.

---

## Stack

| Layer | Technology |
|-------|------------|
| Web framework | FastAPI + Uvicorn |
| Templates | Jinja2 + Tailwind CSS |
| ORM / migrations | SQLAlchemy 2.0 + Alembic |
| Validation | Pydantic v2 |
| LLM | Google GenAI SDK (`google-genai`) |
| Auth | HS256 JWT (HttpOnly cookies) |
| Async worker | ARQ + Redis |
| Object storage | Local filesystem or S3 / MinIO |
| PDF export | ReportLab |
| Package manager | uv |
| Lint / format | Ruff |
| Type checking | pyrefly |
| Tests | pytest + pytest-asyncio |

---

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Google AI Studio API key with Gemini access

---

## Quick Start (local dev)

```bash
# Install dependencies
uv sync

# Copy and fill in your environment
cp .env.example .env
# Required: set GOOGLE_API_KEY, GOOGLE_MODEL_A, GOOGLE_MODEL_B,
#           GOOGLE_JUDGE_MODEL, and JWT_SECRET_KEY

# Run migrations and start the server
uv run mailcraft
```

Open http://127.0.0.1:8081 — register an account and start generating.

Alternatively, run migrations explicitly before starting:

```bash
uv run alembic upgrade head
uv run mailcraft
```

---

## Makefile shortcuts

```bash
make dev       # DEBUG=true, auto-reload
make run       # production-like local run
make migrate   # alembic upgrade head
make test      # pytest with coverage
make lint      # ruff check
make fmt       # ruff --fix + format
make worker    # start ARQ async worker
```

---

## Routes

| Route | Auth | Description |
|-------|------|-------------|
| `/` | Public | Landing page |
| `/auth/register` | Public | Create account |
| `/auth/login` | Public | Sign in |
| `/dashboard` | Required | Document history + stats |
| `/dashboard/generate` | Required | Generate email or cover letter |
| `/dashboard/scenarios` | Required | Manage system-prompt scenarios |
| `/dashboard/scenarios/:id/edit` | Required | Edit scenario prompt |

---

## API

> All JSON API routes are under `/api/`. Cookie auth (`access_token`) is required on protected routes. Rate limits apply per user.

### Auth

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/auth/register` | No | Create account + set cookies |
| POST | `/api/auth/login` | No | Sign in + set cookies |
| GET | `/api/auth/me` | Yes | Current user info |
| POST | `/api/auth/refresh` | Refresh cookie | Rotate access token |

### Generations

| Method | Path | Auth | Rate limit | Description |
|--------|------|------|------------|-------------|
| POST | `/api/generations` | Yes | 10/hour | Generate and persist a document |
| GET | `/api/generations` | Yes | — | List with filters |
| GET | `/api/generations/{id}` | Yes | — | Get single document |
| DELETE | `/api/generations/{id}` | Yes | — | Delete record |
| GET | `/api/generations/{id}/pdf` | Yes | — | Export PDF |

**POST `/api/generations`** accepts `multipart/form-data`:

```
purpose              interview | ms | phd
document_type        email | cover_letter
scenario_id          int
position_description string
grounding_links      string (repeatable, optional)
resume_files         PDF file (repeatable)
?async=true          enqueue as background job (requires worker + Redis)
```

### Scenarios

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/scenarios` | Yes | List user's scenarios |
| POST | `/api/scenarios` | Yes | Create scenario |
| PATCH | `/api/scenarios/{id}` | Yes | Update name / system prompt |
| POST | `/api/scenarios/{id}/clone` | Yes | Clone scenario |
| DELETE | `/api/scenarios/{id}` | Yes | Delete (keeps at least one per type) |

### Jobs (async)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/jobs/{job_id}` | Yes | Poll async job status |

### Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Liveness — always `{status: "ok"}` |
| GET | `/api/health/ready` | Readiness — DB ping + optional LLM ping |

---

## Example: generate a document

```bash
# 1. Register
curl -c cookies.txt -X POST http://127.0.0.1:8081/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "password": "yourpassword"}'

# 2. List available scenarios to find scenario_id
curl -b cookies.txt http://127.0.0.1:8081/api/scenarios

# 3. Generate an interview email with your CV
curl -b cookies.txt -X POST http://127.0.0.1:8081/api/generations \
  -F "purpose=interview" \
  -F "document_type=email" \
  -F "scenario_id=1" \
  -F "position_description=Senior ML Engineer at Acme — 5 years Python required" \
  -F "grounding_links=https://acme.example/about" \
  -F "resume_files=@cv.pdf"
```

---

## Content Humanization

After the main generation step, an optional **humanizer** rewrites AI-heavy phrasing into natural professional writing while preserving all factual content (names, dates, numbers, key highlights).

| Setting | Default | Description |
|---------|---------|-------------|
| `HUMANIZE_CONTENT_ENABLED` | `true` | Run humanizer after generation |
| `HUMANIZE_MODEL` | *(empty)* | Model to use; falls back to `GOOGLE_MODEL_A` |
| `HUMANIZE_FACT_RECALL_THRESHOLD` | `0.75` | Min fraction of facts that must survive rewrite |

In `DEBUG=true` mode, the dashboard exposes both the original AI output and the humanized version for comparison. In production only the humanized result is returned.

---

## Scenarios

Each user has 6 default scenarios seeded on registration (interview, MS, and PhD — for both email and cover letter document types). Scenarios are editable Markdown system prompts sent to the LLM. You can create, clone, and delete custom scenarios from the dashboard.

---

## Async Generation (optional)

Append `?async=true` to `POST /api/generations` to queue the job and return immediately with a `job_id`. Requires Redis and the worker process.

```bash
# Start worker in a separate terminal
make worker

# Submit async job
curl -b cookies.txt -X POST "http://127.0.0.1:8081/api/generations?async=true" \
  -F "purpose=ms" \
  -F "document_type=cover_letter" \
  -F "scenario_id=3" \
  -F "position_description=..." \
  -F "resume_files=@cv.pdf"

# Poll for completion
curl -b cookies.txt http://127.0.0.1:8081/api/jobs/<job_id>
```

Enable in `.env`:

```env
GENERATION_ASYNC_ENABLED=true
REDIS_URL=redis://localhost:6379/0
```

---

## Development

```bash
# Type check
uv run pyrefly check

# Lint and auto-fix
uv run ruff check --fix app tests
uv run ruff format app tests

# Run tests (with coverage)
uv run pytest

# Run tests without coverage gate
uv run pytest --no-cov
```

Coverage minimum is 60% of `app/` source.

---

## Project Layout

```
app/
├── main.py                    # App factory, lifespan, router mounting
├── core/                      # Settings, exceptions, CSRF helpers, rate limits
├── database/                  # Engine manager, models, migrations wrapper
├── domain/enums/              # GenerationKind, ApplicationPurpose, DocumentType
├── application/
│   ├── handlers/              # ApplicationDocumentHandler
│   ├── pipelines/             # 8-step GenerationPipeline + GenerationContext
│   ├── serializers/           # ORM → API response
│   └── services/              # Auth, scenarios, jobs, humanization, storage
├── api/
│   ├── dependencies/          # DI: auth, DB session, LLM client, storage
│   └── routes/                # JSON API + HTML page routes
├── infrastructure/
│   ├── large_language_model/  # Google GenAI wrapper (retry, token logging)
│   ├── export/                # ReportLab PDF builder
│   ├── storage/               # Local + S3 file storage
│   └── health/                # Readiness checks
├── middleware/                # CSRF, security headers, request logging
├── prompts/
│   ├── builders/              # Humanizer + application doc prompt builders
│   └── templates/             # Humanizer system rules
├── schemas/                   # Pydantic request/response models
├── static/js/                 # Bundled DOMPurify
├── templates/                 # Jinja2 HTML (base, layouts, pages, components)
└── worker/main.py             # ARQ background worker

alembic/versions/              # 6 migrations (0001–0006)
tests/
├── unit/
└── integration/
tools/reporting/               # Offline PDF report generators
docs/                          # Architecture and design documentation
```

---

## Docker

```bash
# Build and run (Postgres + app)
docker compose up

# Full stack with async worker, Redis, MinIO
docker compose --profile scale up
```

The app container runs `scripts/deploy.sh`: `alembic upgrade head` then `mailcraft`. Production settings go in `.env.production` (see `.env.production.example`).

---

## Documentation

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — Full technical reference (DB schema, pipeline, LLM, security, deployment)
- [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md) — Original build plan
- [`docs/ARCHITECTURE_AND_PRODUCTION_AUDIT.md`](docs/ARCHITECTURE_AND_PRODUCTION_AUDIT.md) — Production audit findings
