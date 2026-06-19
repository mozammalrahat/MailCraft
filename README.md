# MailCraft

AI-powered professional email generation with advanced metrics. Built with FastAPI, Jinja2, and Google GenAI.

## Stack

- **Backend:** FastAPI, Pydantic v2
- **Templates:** Jinja2 + Tailwind CSS
- **LLM:** Google GenAI SDK (`google-genai`)
- **Package manager:** uv
- **Lint / format:** ruff
- **Type checking:** pyrefly
- **Tests:** pytest

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Google API key with Gemini access

## Setup

```bash
uv sync
cp .env.example .env
# Set GOOGLE_API_KEY in .env
```

## Run the app

```bash
uv run mailcraft
```

Open http://127.0.0.1:8000

- **Home:** `/`
- **Generate email UI:** `/generate`

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/emails/generate` | POST | Generate email from intent, key facts, tone |
| `/api/evaluation/run` | POST | Run full 10-scenario evaluation |
| `/api/evaluation/latest` | GET | Read latest comparison report metadata |

### Example: generate email

```bash
curl -X POST http://127.0.0.1:8000/api/emails/generate \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "Follow up after product demo",
    "key_facts": ["Demo held on May 12", "Requested pricing for 50 seats"],
    "tone": "formal"
  }'
```

## Run evaluation

```bash
uv run mailcraft-eval
# or
uv run python scripts/run_evaluation.py
```

Outputs to `reports/` (gitignored):

- `evaluation_strategy_a.json`
- `evaluation_strategy_b.json`
- `evaluation_full.json`
- `evaluation_comparison.json`
- `evaluation_summary.csv`

Generate comparison analysis doc:

```bash
uv run python scripts/generate_comparison_doc.py
```

Sample report artifacts are in `data/sample_reports/`.

## Development

```bash
# Type check
uv run pyrefly check

# Lint and format
uv run ruff check --fix app tests scripts
uv run ruff format app tests scripts

# Tests
uv run pytest
```

## Project layout

```
app/
├── main.py
├── config.py
├── dependencies.py
├── routers/          # pages + API
├── schemas/          # Pydantic models
├── services/         # email, llm, evaluation
├── prompts/          # Jinja prompt templates
└── templates/        # Jinja UI

data/
├── scenarios/        # 10 evaluation scenarios
└── sample_reports/   # example evaluation output

scripts/
├── run_evaluation.py
└── generate_comparison_doc.py

tests/
├── unit/
├── integration/
└── fixtures/
```

## Documentation

- `docs/PROMPT_ENGINEERING.md` — advanced prompting technique (Role-Playing + Few-Shot)
- `docs/MODEL_COMPARISON.md` — strategy comparison analysis (populate via eval run)
- `docs/IMPLEMENTATION_PLAN.md` — full build plan
