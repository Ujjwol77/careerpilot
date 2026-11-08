# CareerPilot: multi-agent career platform (MVP)

Next.js 14 frontend + FastAPI backend. Seven agents: Profile Understanding, Job Search, Job Matching, Skill Gap, 
CV Optimisation, Learning Pathway, Interview Coach, coordinated by an orchestrator.

# however.. the interview can be limited as there are only 2 members

## Run it
```bash
# backend (http://localhost:8000, docs at /docs)
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload

# frontend (http://localhost:3000)
cd frontend && cp .env.example .env.local && npm install && npm run dev
```
Sample CVs for testing: `backend/samples/sample_cv.pdf` and `.docx`. Tests: `cd backend && pytest`.

## Brief to feature map
| # | Requirement | Where |
|---|---|---|
| 1 | Secure registration and login | `routers/auth.py`, pbkdf2 hashing, JWT |
| 2 | CV upload, validation, extraction | `cv_extract.py`, `/profile/upload`, profile page |
| 3 | Profile from CV, preferences | `agents/profile_agent.py`, `/profile/preferences` |
| 4 | Job search and matching | `job_search_agent.py`, `job_match_agent.py`, Jobs page |
| 5 | Skill gap analysis | `skill_gap_agent.py`, Skill gaps page |
| 6 | CV optimisation | `cv_agent.py`, CV review page |
| 7 | Learning pathway | `learning_agent.py`, Learning page |
| 8 | Interview coach | `interview_agent.py`, Interview page |
| 9 | Application tracking | `routers/applications.py` |
| 10 | Readiness report | `report_agent.py`, Report page (print to PDF) |
| 11 | Prompt bank, LLMOps, GitHub workflow, agent design | `prompt_bank.py`, Agent monitor, `.github/workflows/ci.yml`, `docs/` |
Agile/Scrum plans, UML diagrams and UI/UX design are written deliverables for your report; the workflow diagram is in `docs/AGENT_WORKFLOW.md`.

## Swapping the mock parts
- **LLM:** set `LLM_PROVIDER`, `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL` in `backend/.env` (any OpenAI-compatible endpoint).
- **Database:** set `DATABASE_URL` to a Postgres/Supabase URL. For pgvector, replace `embeddings.py` with hosted embeddings.
- **Jobs:** live Australian postings come from the Adzuna API. Get a free key at https://developer.adzuna.com, set `ADZUNA_APP_ID` and `ADZUNA_APP_KEY` in `backend/.env`, and check it with `cd backend && python -m app.check_jobs "data analyst" Melbourne`. Searches are cached for 12 hours (`JOBS_CACHE_HOURS`). Without a key, or if the API fails, the 45 sample postings are used. Other APIs plug in through the `JobSource` interface in `job_search_agent.py`.
- **Learning links:** `backend/app/data/learning.py` maps every skill to specific course pages (Kaggle Learn, Microsoft Learn, TryHackMe, Cisco NetAcad, Professor Messer, PortSwigger and others). Re-check them with `cd backend && python -m app.check_links`.
- **Before deploying:** set a long random `SECRET_KEY` and set `CORS_ORIGINS`.

## Known limitations

- Live jobs need an Adzuna key; without one the app uses a synthetic 45-posting dataset with fictional companies. Adzuna returns only a description snippet, so skills found in live postings can be incomplete. Learning links go to specific course pages, but the catalogue is hand-curated (no course API yet), and most study hours are estimates; durations published by the provider are flagged `hours_source: provider`.
- Processing is synchronous; the JWT is kept in localStorage (use httpOnly cookies in production); no rate limiting or email verification.
