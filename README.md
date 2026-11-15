# CareerPilot

A multi-agent career platform. Upload a CV, and seven cooperating agents build a profile, find and score matching jobs, find skill gaps, suggest CV improvements, plan learning, run mock interviews and produce a readiness report.

- **Frontend:** Next.js (App Router) + TypeScript, in `frontend/`
- **Backend:** FastAPI + SQLAlchemy, in `backend/` (SQLite by default; PostgreSQL/Supabase supported)
- **AI:** any OpenAI-compatible LLM (Gemini, OpenAI, Groq, Ollama…), or a built-in **mock** mode that needs no key

The app runs with **no API keys at all**. Every external service has an offline fallback, so you can clone it and run it right away.

---

## Contents

- [Quick start](#quick-start)
- [Configuration](#configuration)
- [How it works](#how-it-works)
- [Project structure](#project-structure)
- [Testing and diagnostics](#testing-and-diagnostics)
- [Requirement → feature map](#requirement--feature-map)
- [Known limitations](#known-limitations)

---

## Quick start

**Prerequisites:** Python 3.11+, Node.js 20+.

### 1. Backend (http://localhost:8000, interactive API docs at http://localhost:8000/docs)

macOS / Linux:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Windows (PowerShell):
```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

On first start the backend creates the database tables and loads 45 sample job postings.

### 2. Frontend (http://localhost:3000)

In a second terminal:
```bash
cd frontend
cp .env.example .env.local      # Windows: copy .env.example .env.local
npm install
npm run dev
```

### 3. Try it

1. Open http://localhost:3000 and register an account.
2. Upload a CV from the **Profile** page. Test CVs are in `backend/samples/` (a data-analyst CV as PDF/DOCX, plus a cybersecurity one) and `Sample CVs/` (five IT CVs from student to senior level).
3. Work through **Jobs → Skill gaps → CV review → Learning → Interview → Report**.
4. Open **Agent monitor** to see each agent run, its latency and whether it used the LLM or a template.

---

## Configuration

All backend settings live in `backend/.env` (copy from [backend/.env.example](backend/.env.example)). Every value has a safe default.

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./careerpilot.db` | Use `postgresql+psycopg://…` for Postgres/Supabase (`pip install "psycopg[binary]"` first) |
| `SECRET_KEY` | dev value | JWT signing key. **Set a long random value before deploying** |
| `TOKEN_MINUTES` | `720` | Login session length |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed frontend origins |
| `MAX_UPLOAD_MB` | `5` | CV upload size limit |
| `LLM_PROVIDER` | `mock` | `mock` (rule-based templates, free) or `openai` (any OpenAI-compatible API) |
| `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL` | – | LLM connection; see the Gemini example in `.env.example` |
| `EMBEDDING_PROVIDER` | `api` | `api` = neural embeddings for semantic matching; `local` = word overlap only |
| `EMBEDDING_MODEL` | `gemini-embedding-001` | Embedding model; key and URL default to the LLM's |
| `ADZUNA_APP_ID`, `ADZUNA_APP_KEY` | blank | Live Australian job postings ([free key](https://developer.adzuna.com)). Blank = sample jobs |
| `ADZUNA_COUNTRY` / `ADZUNA_RESULTS` / `JOBS_CACHE_HOURS` | `au` / `30` / `12` | Job search tuning |
| `LEARNING_MSLEARN` | `true` | Search the Microsoft Learn catalogue (free, no key) |
| `YOUTUBE_API_KEY` | blank | YouTube course search (free, 100 searches/day) |
| `LEARNING_CACHE_DAYS` | `7` | How long live learning results are cached in `backend/.cache/` |

The frontend needs one setting, in `frontend/.env.local`:

| Variable | Default | Purpose |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Where the backend runs |

**Recommended free setup:** a Google Gemini key from https://aistudio.google.com/apikey powers both the LLM and the embeddings. See the commented Gemini block in `.env.example`.

---

## How it works

An orchestrator ([backend/app/orchestrator.py](backend/app/orchestrator.py)) runs seven agents in [backend/app/agents/](backend/app/agents/):

```
CV ─► 1 Profile ─► 2 Job Search ─► 3 Job Matching ─┬─► 4 Skill Gap ─┬─► 6 Learning Pathway
                        ▲               │          │                └─► 7 Interview Coach
                        └── reflection ─┘          └─► 5 CV Optimisation
                  (too few / weak matches:                    all ─► Readiness report
                   relax filters, widen roles)
```

- **Match score** = 0.35 semantic similarity + 0.50 weighted skill coverage + 0.15 experience fit. Bands: 80+ *Highly qualified*, 60+ *Qualified with gaps*, otherwise *Development required*.
- **LLM fallback:** text-producing steps call the LLM when configured. In mock mode, or if the model fails, they use rule-based templates (labelled `template` / `template-fallback` in the Agent monitor).
- **Privacy:** contact details are removed from CV text before it is sent to any external API.
- **Logging:** every agent run is recorded (status, latency, engine) and shown on the Agent monitor page.

More detail: [docs/AGENT_WORKFLOW.md](docs/AGENT_WORKFLOW.md) (Mermaid diagram) and [docs/PROMPT_BANK.md](docs/PROMPT_BANK.md) (prompts used by each agent).

### Main API routes

All routes are under the `/api/v1` prefix (for example `POST /api/v1/auth/login`).

| Area | Routes |
|---|---|
| Auth | `POST /auth/register`, `POST /auth/login`, `GET /auth/me` |
| Profile | `POST /profile/upload`, `GET /profile`, `PUT /profile/preferences` |
| Jobs | `GET /jobs/search`, `POST /jobs/match`, `GET /jobs/{id}` |
| Analysis | `GET /skill-gap`, `GET /cv/optimise`, `GET /learning`, `POST /interview/start`, `POST /interview/answer` |
| Applications | `GET/POST /applications`, `PATCH/DELETE /applications/{id}` |
| Report | `POST /report/generate`, `GET /report/latest` |
| Ops | `GET /ops/runs`, `GET /ops/summary`, `GET /prompts` |

See http://localhost:8000/docs for the full, current list with request and response schemas.

---

## Project structure

```
careerpilot/
├── backend/
│   ├── app/
│   │   ├── agents/          # the seven agents + report agent
│   │   ├── routers/         # FastAPI endpoints (auth, profile, jobs, analysis, applications, report, ops)
│   │   ├── data/            # seed jobs, learning catalogue, interview question bank
│   │   ├── llm/             # LLM client (mock / OpenAI-compatible)
│   │   ├── orchestrator.py  # runs the agent pipeline
│   │   ├── semantic.py      # semantic similarity for matching
│   │   ├── embeddings.py    # embedding API client
│   │   ├── taxonomy.py      # skill taxonomy and aliases
│   │   ├── cv_extract.py    # PDF/DOCX text extraction and validation
│   │   ├── prompt_bank.py   # versioned prompts
│   │   ├── check_*.py       # diagnostic scripts (see below)
│   │   └── main.py          # app entry point
│   ├── tests/               # pytest API tests
│   ├── samples/             # sample CVs used by tests and demos
│   └── requirements.txt
├── frontend/
│   ├── app/                 # Next.js pages: landing, login, dashboard/*
│   ├── components/          # UI kit, charts, theme toggle, info tips
│   └── lib/api.ts           # typed API client
├── docs/                    # agent workflow diagram, prompt bank
├── Sample CVs/              # extra test CVs
└── .github/workflows/ci.yml # CI: backend tests, frontend typecheck and build
```

---

## Testing and diagnostics

```bash
# Backend tests (run from backend/)
pytest

# Frontend typecheck and production build (run from frontend/)
npm run typecheck
npm run build
```

GitHub Actions runs all three on every push and pull request.

Diagnostic scripts check each external connection. Run them from `backend/`:

| Command | Checks |
|---|---|
| `python -m app.check_llm` | LLM connection and response time |
| `python -m app.check_embeddings [cv-path]` | Embedding API, compared with word-overlap similarity |
| `python -m app.check_jobs "data analyst" Melbourne` | Adzuna connection, shows live postings |
| `python -m app.check_learning sql power_bi siem` | Microsoft Learn / YouTube results per skill |
| `python -m app.check_links` | Every curated learning link still loads (exits 1 if any are broken) |
| `python make_sample_cv.py` | Regenerates `samples/sample_cv.pdf` and `.docx` |

---

## Requirement → feature map

| # | Requirement | Where |
|---|---|---|
| 1 | Secure registration and login | `routers/auth.py`, PBKDF2 password hashing, JWT |
| 2 | CV upload, validation, extraction | `cv_extract.py`, `/profile/upload`, Profile page |
| 3 | Profile from CV, preferences | `agents/profile_agent.py`, `/profile/preferences` |
| 4 | Job search and matching | `job_search_agent.py`, `job_match_agent.py`, `semantic.py`, Jobs page |
| 5 | Skill gap analysis | `skill_gap_agent.py`, Skill gaps page |
| 6 | CV optimisation | `cv_agent.py`, CV review page |
| 7 | Learning pathway | `learning_agent.py`, `learning_sources.py`, Learning page |
| 8 | Interview coach | `interview_agent.py`, `data/interview_bank.py`, Interview page |
| 9 | Application tracking | `routers/applications.py`, Applications page |
| 10 | Readiness report | `report_agent.py`, Report page (print to PDF) |
| 11 | Prompt bank, LLMOps, GitHub workflow, agent design | `prompt_bank.py`, Agent monitor page, `.github/workflows/ci.yml`, `docs/` |

Agile/Scrum plans, UML diagrams and UI/UX designs are part of the written report. The workflow diagram is in `docs/AGENT_WORKFLOW.md`.

---

## Data sources and extending

- **Jobs:** live postings come from Adzuna. Without a key, or if the API fails, the 45 sample postings are used. Other job APIs can be added through the `JobSource` interface in `agents/job_search_agent.py`.
- **Learning:** `data/learning.py` maps each skill to specific course pages (Kaggle Learn, Microsoft Learn, TryHackMe, Cisco NetAcad, Professor Messer, PortSwigger and others). When enabled, Microsoft Learn and YouTube results are added for each skill gap, keeping one curated pick per skill.
- **Database:** switch to PostgreSQL by changing `DATABASE_URL`. New columns are added automatically on startup; there are no separate migrations.

---

## Known limitations

- Without an Adzuna key the app uses 45 synthetic postings with fictional companies. Adzuna returns only a description snippet, so skills taken from live postings can be incomplete.
- The learning catalogue is hand-curated, and most study hours are estimates. Durations published by the provider are flagged `hours_source: provider`.
- Processing is synchronous (no job queue).
- The JWT is stored in `localStorage`. Use httpOnly cookies in production. There is no rate limiting or email verification.
- The interview coach uses a fixed question bank plus LLM feedback, so question variety is limited.

## Before deploying

- Set a long random `SECRET_KEY`.
- Set `CORS_ORIGINS` to the real frontend URL, and `NEXT_PUBLIC_API_URL` to the real backend URL.
- Use PostgreSQL instead of SQLite.
- Never commit `backend/.env`. It is already in `.gitignore`.
