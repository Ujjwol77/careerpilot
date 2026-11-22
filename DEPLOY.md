# Deploying CareerPilot

This branch (`deploy`) is the public version of CareerPilot. Compared with `main` it:

- removes the Agent monitor page and its menu link
- removes the developer endpoints `/ops/summary`, `/ops/runs` and `/prompts` (`/meta` stays, the website needs it)
- removes developer labels from the pages (the agent workflow strip on Jobs, "How this report was produced" and "summary source" on the report, "Feedback source" in interview practice, model names and API credit counts on CV review, and the "add a key to backend/.env" hints)
- hides the "How an ATS reads your CV" card until the parser key is set on the server
- turns off the interactive API docs (`/docs`, `/redoc`, `/openapi.json`) when `APP_ENV=production`
- refuses to start in production with the development `SECRET_KEY`
- accepts the `postgres://` URLs that hosts give out, and includes the PostgreSQL driver (`psycopg`)
- shows "Starting the server…" on the log-in page when the free host is waking up

The full test suite (62 tests) passes on both SQLite and PostgreSQL.

## What runs where

| Part | Host | Free plan notes |
|---|---|---|
| Backend (FastAPI) | Render web service, `backend/` folder | Sleeps after 15 minutes without traffic; the next request takes about a minute while it wakes |
| Database | Render PostgreSQL | Free databases expire 30 days after creation; Supabase or Neon also work through `DATABASE_URL` |
| Website (Next.js) | Vercel, `frontend/` folder | No sleep |

Both hosts redeploy automatically each time you push to the `deploy` branch.

## 1. Push this branch

```powershell
cd "C:\Users\S W I F T 3\careerpilot-1"
git checkout deploy
git add -A
git commit -m "Deploy version: remove developer tools, add hosting config"
git push -u origin deploy
```

Switch back to the full development version at any time with `git checkout main`, and return with `git checkout deploy`. Commit or stash your changes before switching.

## 2. Backend and database on Render

1. Sign in at https://render.com with GitHub.
2. Click **New → Blueprint**, choose the CareerPilot repository and the **deploy** branch. Render reads `render.yaml` and proposes two resources: `careerpilot-api` and `careerpilot-db`.
3. Fill in the values it asks for. Leave a key blank to use that feature's fallback.

   | Variable | Value |
   |---|---|
   | `CORS_ORIGINS` | your Vercel address from step 3 (put `http://localhost:3000` for now and change it later) |
   | `LLM_API_KEY` | your Gemini key |
   | `ADZUNA_APP_ID`, `ADZUNA_APP_KEY` | your Adzuna keys |
   | `APILAYER_API_KEY` | your APILayer key |
   | `YOUTUBE_API_KEY` | your YouTube Data API key |

   `SECRET_KEY` is generated for you and `DATABASE_URL` is linked to the database automatically.
4. Click **Apply**. The first build takes a few minutes. When it is live, open `https://<your-service>.onrender.com/health`; it should show `{"status":"ok"}`.
5. Copy the service address (for example `https://careerpilot-api.onrender.com`).

## 3. Website on Vercel

1. Sign in at https://vercel.com with GitHub and click **Add New → Project**.
2. Import the CareerPilot repository. Set **Root Directory** to `frontend` (the framework is detected as Next.js).
3. Under **Environment Variables** add `NEXT_PUBLIC_API_URL` = the Render address from step 2.5 (no trailing slash).
4. Under **Settings → Git**, set the **Production Branch** to `deploy`, then deploy.
5. Copy the website address (for example `https://careerpilot.vercel.app`).

`NEXT_PUBLIC_API_URL` is built into the pages, so after changing it you must redeploy the website.

## 4. Connect the two

1. In Render, open `careerpilot-api` → **Environment**, set `CORS_ORIGINS` to the Vercel address (no trailing slash; separate several addresses with commas) and save. Render restarts the service.
2. Open the Vercel address, register an account and upload a sample CV from `backend/samples/cv_set/`.

## 5. Check it works

- [ ] `/health` on the Render address shows `{"status":"ok"}`
- [ ] `/docs` on the Render address shows "Not Found" (docs are off in production)
- [ ] Register, log in and upload a CV
- [ ] Jobs and matching shows "Live · Adzuna" badges (or "Sample job" if no Adzuna key)
- [ ] CV review, Skill gaps, Learning path, Interview practice and the Readiness report all load
- [ ] The menu has no Agent monitor

If the website says it cannot reach the server, check that `NEXT_PUBLIC_API_URL` is the Render address and that `CORS_ORIGINS` is exactly the Vercel address, then redeploy.

## Keys and data

- Keys live only in Render's environment settings. Never put them in the repository.
- Uploaded CVs are stored in the database, so they survive restarts. Cached course and calibration data is rebuilt after each restart.
- When the free Render database expires, create a new one (or a Supabase/Neon database) and paste its URL into `DATABASE_URL`; the tables and sample jobs are created on the next start.
