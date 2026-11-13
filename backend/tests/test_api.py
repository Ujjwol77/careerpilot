import io
import json

import httpx
import pytest

from conftest import SAMPLES

API = "/api/v1"


# ---------- auth ----------
def test_register_login_me(client):
    r = client.post(f"{API}/auth/register", json={"email": "a@example.com", "password": "password123", "name": "A"})
    assert r.status_code == 201
    assert client.post(f"{API}/auth/register", json={"email": "A@example.com", "password": "password123"}).status_code == 409
    assert client.post(f"{API}/auth/login", json={"email": "a@example.com", "password": "wrong-password"}).status_code == 401
    token = client.post(f"{API}/auth/login", json={"email": "a@example.com", "password": "password123"}).json()["token"]
    me = client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json()["email"] == "a@example.com"


def test_validation_and_auth_required(client):
    assert client.post(f"{API}/auth/register", json={"email": "bad", "password": "password123"}).status_code == 422
    assert client.post(f"{API}/auth/register", json={"email": "b@example.com", "password": "short"}).status_code == 422
    r = client.get(f"{API}/profile")
    assert r.status_code == 401 and r.json()["error"]["code"] == "UNAUTHENTICATED"


def test_endpoints_need_cv_first(client, user):
    headers, _ = user
    r = client.post(f"{API}/jobs/match", headers=headers)
    assert r.status_code == 409 and r.json()["error"]["code"] == "NO_PROFILE"


# ---------- upload validation (FR: type, size, signature, readable text) ----------
def _upload(client, headers, name, data, **params):
    return client.post(f"{API}/profile/upload", headers=headers, params=params, files={"file": (name, io.BytesIO(data))})


def test_rejects_wrong_extension(client, user):
    r = _upload(client, user[0], "cv.png", b"\x89PNG....")
    assert r.status_code == 415 and r.json()["error"]["code"] == "UNSUPPORTED_FILE_TYPE"


def test_rejects_oversize(client, user):
    r = _upload(client, user[0], "cv.pdf", b"%PDF-" + b"0" * (5 * 1024 * 1024 + 10))
    assert r.status_code == 413 and r.json()["error"]["code"] == "FILE_TOO_LARGE"


def test_rejects_fake_pdf_signature(client, user):
    r = _upload(client, user[0], "cv.pdf", b"MZ this is an exe renamed to pdf" * 5)
    assert r.status_code == 415 and r.json()["error"]["code"] == "INVALID_FILE_CONTENT"


def test_rejects_unreadable_file(client, user):
    r = _upload(client, user[0], "cv.pdf", b"%PDF-1.4 not really a pdf at all" * 3)
    assert r.status_code == 422 and r.json()["error"]["code"] == "TEXT_EXTRACTION_FAILED"
    # nothing was saved: still no profile
    assert client.get(f"{API}/profile", headers=user[0]).json()["has_profile"] is False


def test_upload_docx_and_pdf_extract_profile(client, user):
    headers, _ = user
    r = _upload(client, headers, "sample_cv.pdf", (SAMPLES / "sample_cv.pdf").read_bytes())
    assert r.status_code == 201
    names = {s["name"] for s in r.json()["skills"]}
    assert {"SQL", "Excel", "Power BI"} <= names


def test_docx_profile_content(uploaded):
    _, profile = uploaded
    assert profile["name"]
    assert 2 <= profile["years_experience"] <= 6
    assert profile["inferred_roles"][0]["role"] == "data_analyst"
    assert any("Bachelor" in e for e in profile["education"])


def test_reupload_requires_confirmation(client, uploaded):
    headers, _ = uploaded
    data = (SAMPLES / "sample_cv.docx").read_bytes()
    r = _upload(client, headers, "sample_cv.docx", data)
    assert r.status_code == 409 and r.json()["error"]["code"] == "PROFILE_EXISTS"
    assert _upload(client, headers, "sample_cv.docx", data, overwrite="true").status_code == 201


def test_preferences(client, uploaded):
    headers, _ = uploaded
    r = client.put(f"{API}/profile/preferences", headers=headers, json={"target_roles": ["data_analyst"], "location": "Melbourne", "min_salary": 70000, "experience_level": "junior", "goals": "x"})
    assert r.status_code == 200 and r.json()["preferences"]["location"] == "Melbourne"
    assert client.put(f"{API}/profile/preferences", headers=headers, json={"target_roles": ["astronaut"]}).status_code == 422


# ---------- agents via API ----------
def test_job_search_filters(client, user):
    headers, _ = user
    r = client.get(f"{API}/jobs/search", headers=headers, params={"q": "security", "level": "senior"})
    jobs = r.json()["jobs"]
    assert jobs and all(j["level"] == "senior" for j in jobs)
    r = client.get(f"{API}/jobs/search", headers=headers, params={"min_salary": 200000})
    assert r.json()["count"] == 0


def test_job_match_ranks_relevant_role_first(client, uploaded):
    headers, _ = uploaded
    r = client.post(f"{API}/jobs/match", headers=headers)
    body = r.json()
    assert r.status_code == 200 and body["count"] > 0
    scores = [m["score"] for m in body["matches"]]
    assert scores == sorted(scores, reverse=True)
    assert body["matches"][0]["role_category"] == "data_analyst"
    assert body["matches"][0]["matched_skills"]


def test_skill_gap(client, uploaded):
    headers, _ = uploaded
    body = client.get(f"{API}/skill-gap", headers=headers).json()
    assert body["jobs_analysed"] >= 6 and body["missing"]  # role-wide benchmark, not just 5 jobs
    assert set(body["grouped"]) == {"Technical skills", "Tools", "Soft skills", "Certifications"}
    assert all(m["priority"] in {"high", "medium", "low"} for m in body["missing"])
    assert all(m["tier"] in {"core", "common", "nice_to_have"} and m["why"] for m in body["missing"])
    assert 0 <= body["overall_coverage_pct"] <= 100 and body["headline"] and body["next_step"]
    assert body["confidence"]["level"] in {"good", "low"}


def test_cv_optimise(client, uploaded):
    headers, _ = uploaded
    body = client.get(f"{API}/cv/optimise", headers=headers).json()
    assert 0 <= body["ats_score"] <= 100
    areas = {s["area"] for s in body["suggestions"]}
    assert "wording" in areas  # the sample CV uses "Responsible for ..." and "Worked on ..."
    assert body["rewrite_source"] == "template"
    # every point lost is explained, and the score adds up
    lost = sum(c["points_lost"] for c in body["checks"])
    assert body["ats_score"] == max(0, round(100 - lost))
    assert all(c["found"] and c["target"] and c["why"] for c in body["checks"])
    pts = [s["points"] for s in body["suggestions"]]
    assert pts == sorted(pts, reverse=True)  # ranked by points a fix would win back
    reason = body["target_reason"]
    assert reason["mode"] == "best_match" and reason["rank"] == 1 and set(reason["components"]) == {"semantic", "skill_coverage", "experience_fit"}
    assert all(r["score"] <= reason["score"] for r in reason["runners_up"])
    for pair in body["rewrites"]:
        assert pair["before"] and pair["after"] and pair["why"]
    assert client.get(f"{API}/cv/optimise", headers=headers, params={"job_id": 99999}).status_code == 404


def test_learning_plan(client, uploaded):
    headers, _ = uploaded
    plan = client.get(f"{API}/learning", headers=headers).json()
    assert plan["items"] and plan["total_hours"] == sum(i["hours"] for i in plan["items"])
    assert all(i["suitable_for"].endswith(".") for i in plan["items"])  # every course says who it suits
    assert not {"weeks", "total_weeks", "hours_per_week"} & plan.keys()  # no week schedule
    assert not any("start_week" in i for i in plan["items"])


def test_interview_flow(client, uploaded):
    headers, _ = uploaded
    s = client.post(f"{API}/interview/start", headers=headers, json={}).json()
    assert len(s["questions"]) == 7 and "keywords" not in s["questions"][0]
    strong = ("When I joined a reporting project, my task was to cut manual work. I built a pivot table workflow in Excel, "
              "which reduced the weekly effort by 6 hours, and I learned to document the result for the whole team.")
    beh = next(q for q in s["questions"] if q["type"] == "behavioural")
    r = client.post(f"{API}/interview/answer", headers=headers, json={"session_id": s["session_id"], "index": beh["index"], "answer": strong}).json()
    weak = client.post(f"{API}/interview/answer", headers=headers, json={"session_id": s["session_id"], "index": beh["index"], "answer": "idk"}).json()
    assert r["score"] > weak["score"] and weak["tips"]
    assert client.post(f"{API}/interview/answer", headers=headers, json={"session_id": s["session_id"], "index": 99, "answer": "x"}).status_code == 422
    assert client.get(f"{API}/interview/sessions", headers=headers).json()[0]["answered"] == 1


def test_interview_sessions_are_private(client, uploaded, stranger):
    headers, _ = uploaded
    s = client.post(f"{API}/interview/start", headers=headers, json={}).json()
    other = stranger
    r = client.post(f"{API}/interview/answer", headers=other, json={"session_id": s["session_id"], "index": 0, "answer": "hello"})
    assert r.status_code == 404


# ---------- applications ----------
def test_applications_crud_and_isolation(client, uploaded, stranger):
    headers, _ = uploaded
    job_id = client.get(f"{API}/jobs/search", headers=headers).json()["jobs"][0]["id"]
    app = client.post(f"{API}/applications", headers=headers, json={"job_id": job_id}).json()
    assert app["status"] == "saved"
    assert client.post(f"{API}/applications", headers=headers, json={"job_id": job_id}).status_code == 409
    upd = client.patch(f"{API}/applications/{app['id']}", headers=headers, json={"status": "applied", "notes": "sent CV"}).json()
    assert upd["status"] == "applied"
    other = stranger
    assert client.patch(f"{API}/applications/{app['id']}", headers=other, json={"status": "offer"}).status_code == 404
    assert client.delete(f"{API}/applications/{app['id']}", headers=headers).status_code == 204
    assert client.get(f"{API}/applications", headers=headers).json() == []


# ---------- orchestrator, report, LLMOps ----------
def test_full_report_and_ops(client, uploaded):
    headers, _ = uploaded
    r = client.post(f"{API}/report/generate", headers=headers, json={})
    rep = r.json()
    assert r.status_code == 201
    agents = [t["agent"] for t in rep["agent_trace"]]
    assert agents == ["profile_understanding", "job_search", "job_matching", "skill_gap", "cv_optimisation", "learning_pathway", "interview_coach", "report"]
    assert all(t["status"] == "ok" for t in rep["agent_trace"])
    sources = {t["agent"]: t["llm_source"] for t in rep["agent_trace"]}
    assert sources["job_matching"] == "rules" and sources["skill_gap"] == "rules"  # calculations are not "template"
    assert sources["cv_optimisation"] == "template"  # LLM-capable agent in mock mode
    assert sources["job_search"] == "sample-data"  # no Adzuna key in tests
    assert "Adzuna off" in next(t["note"] for t in rep["agent_trace"] if t["agent"] == "job_search")
    assert rep["readiness_band"] in {"HIGHLY_QUALIFIED", "QUALIFIED_WITH_GAPS", "DEVELOPMENT_REQUIRED"}
    assert rep["top_jobs"] and rep["cv"]["suggestions"] and rep["learning"]["items"] and rep["interview"]["schedule"]
    assert client.get(f"{API}/report/latest", headers=headers).json()["generated_at"] == rep["generated_at"]
    summary = client.get(f"{API}/ops/summary", headers=headers).json()
    assert set(summary["services"]) == {"gemini", "embeddings", "adzuna", "mslearn", "youtube"}
    assert summary["services"]["gemini"]["set_up"] is False  # mock LLM in tests
    assert summary["llm_provider"] == "mock" and any(a["agent"] == "report" for a in summary["agents"])
    assert client.get(f"{API}/ops/runs", headers=headers).json()[0]["status"] == "ok"
    ids = [p["id"] for p in client.get(f"{API}/prompts", headers=headers).json()]
    assert "cv_rewrite.v1" in ids


def test_orchestrator_reflects_when_filters_too_strict(client, uploaded):
    headers, _ = uploaded
    client.put(f"{API}/profile/preferences", headers=headers, json={"target_roles": ["data_analyst"], "location": "Hobart", "min_salary": 300000})
    rep = client.post(f"{API}/report/generate", headers=headers, json={}).json()
    search = next(t for t in rep["agent_trace"] if t["agent"] == "job_search")
    assert "reflected: relaxed filters" in search["note"]
    assert rep["top_jobs"]


# ---------- unit tests ----------
def test_taxonomy_aliases_resolve_to_same_skill():
    from app.taxonomy import extract_skills
    for text in ["ReactJS", "React.js", "Built UIs with React"]:
        assert "react" in extract_skills(text)
    assert "react" not in extract_skills("We react quickly to incidents")
    assert "java" in extract_skills("Java developer") and "javascript" not in extract_skills("Java developer")
    assert {"csharp", "cpp"} <= set(extract_skills("C# and C++"))


def test_years_estimate_merges_overlap():
    from app.agents.profile_agent import estimate_years
    assert estimate_years("2018 - 2021 and 2020 - 2022", today_year=2026) == 4
    assert estimate_years("2022 - Present", today_year=2026) == 4


def test_redaction():
    from app.utils import redact_pii
    out = redact_pii("Email me at jo@example.com or call +61 400 000 000, see https://github.com/jo")
    assert "jo@example.com" not in out and "400 000" not in out and "github.com" not in out


def test_llm_path_uses_provider_and_redacts(monkeypatch):
    import app.llm as llm
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = request.read().decode()
        return httpx.Response(200, json={"choices": [{"message": {"content": "Great answer."}}]})

    fake = llm.OpenAICompatLLM("key", "https://example.test/v1", "m", transport=httpx.MockTransport(handler))
    monkeypatch.setattr(llm, "get_llm", lambda: fake)
    text, source = llm.try_llm("interview_feedback.v1", "fallback", role="data_analyst", question="Q?", answer="Mail me jo@example.com")
    assert (text, source) == ("Great answer.", "llm")
    assert "jo@example.com" not in seen["body"] and "<answer>" in seen["body"] and "untrusted" in seen["body"]


def test_llm_failure_falls_back(monkeypatch):
    import app.llm as llm
    fake = llm.OpenAICompatLLM("key", "https://example.test/v1", "m", transport=httpx.MockTransport(lambda r: httpx.Response(500)))
    monkeypatch.setattr(llm, "get_llm", lambda: fake)
    assert llm.try_llm("report_summary.v1", "fallback text", facts="x") == ("fallback text", "template-fallback")
    assert llm.last_error() == "HTTP 500"


def test_llm_failure_reason_is_shown_without_the_key(monkeypatch):
    import app.llm as llm
    gemini_429 = [{"error": {"code": 429, "message": "Resource has been exhausted (e.g. check quota).", "status": "RESOURCE_EXHAUSTED"}}]
    fake = llm.OpenAICompatLLM("secret-key-123", "https://example.test/v1", "m",
                               transport=httpx.MockTransport(lambda r: httpx.Response(429, json=gemini_429)))
    monkeypatch.setattr(llm, "get_llm", lambda: fake)
    llm.try_llm("report_summary.v1", "fallback", facts="x")
    assert llm.last_error() == "HTTP 429: Resource has been exhausted (e.g. check quota)." and "secret" not in llm.last_error()


def test_every_skill_has_direct_learning_links():
    from urllib.parse import urlparse
    from app.data.learning import resources_for
    from app.taxonomy import SKILLS
    for slug in SKILLS:
        res = resources_for(slug)
        assert res, slug
        for r in res:
            u = urlparse(r["url"])
            assert u.scheme == "https" and u.netloc, (slug, r["url"])
            assert not u.path.startswith("/search") and "q=" not in u.query, (slug, r["url"])  # no web searches
            assert r["provider"] and r["hours"] > 0


def test_learning_plan_items_link_to_course_pages(client, uploaded):
    headers, _ = uploaded
    plan = client.get(f"{API}/learning", headers=headers).json()
    urls = [i["url"] for i in plan["items"]]
    assert urls and all(u.startswith("https://") for u in urls)
    assert len(urls) == len(set(urls))  # shared courses are scheduled once


# ---------- live jobs (Adzuna) with a fake server ----------
def _fake_adzuna(calls):
    def handler(request):
        calls.append(request)
        return httpx.Response(200, json={"results": [
            {"id": "a1", "title": "Junior <strong>Data Analyst</strong>", "company": {"display_name": "Acme"},
             "location": {"display_name": "Melbourne, Victoria"}, "description": "Use SQL, Power BI and Excel daily.",
             "salary_min": 70000, "salary_max": 85000, "redirect_url": "https://www.adzuna.com.au/details/a1"},
            {"id": "a2", "title": "Senior Data Analyst", "company": {"display_name": "Beta"},
             "location": {"display_name": "Melbourne, Victoria"}, "description": "Python, statistics, stakeholder management.",
             "redirect_url": "https://www.adzuna.com.au/details/a2"},
            {"id": "a3", "title": "Data Analyst", "company": {}, "location": {"display_name": "Melbourne CBD"},
             "description": "Tableau dashboards", "redirect_url": "https://www.adzuna.com.au/details/a3"},
        ]})
    return handler


def test_adzuna_source_saves_and_caches(client, monkeypatch):
    import app.agents.job_search_agent as js
    from app.config import settings
    from app.db import SessionLocal
    object.__setattr__(settings, "adzuna_app_id", "id"); object.__setattr__(settings, "adzuna_app_key", "key")
    calls = []
    source = js.AdzunaSource(transport=httpx.MockTransport(_fake_adzuna(calls)))
    monkeypatch.setattr(js, "SOURCES", [source, js.SeedDatasetSource()])
    try:
        with SessionLocal() as db:
            jobs = js.search_jobs(db, role_categories=["data_analyst"], location="Melbourne")
            assert {j.source for j in jobs} == {"adzuna"} and len(jobs) == 3  # live results, no sample jobs
            junior = next(j for j in jobs if j.external_id == "a1")
            assert junior.title == "Junior Data Analyst" and junior.level == "junior"
            assert {"sql", "power_bi", "excel"} <= set(junior.skills) and junior.url.startswith("https://")
            assert next(j for j in jobs if j.external_id == "a2").level == "senior"
            assert calls[0].url.params["what"] == "Data Analyst" and calls[0].url.params["where"] == "Melbourne"
            engine, note = js.describe_sources(jobs)
            assert engine == "adzuna" and note.startswith("3 Adzuna + 0 sample") and "1 API call" in note
            js.reset_source_status()
            js.search_jobs(db, role_categories=["data_analyst"], location="Melbourne")
            assert len(calls) == 1  # second search served from the cache, no extra API call
            assert "1 cached search" in js.describe_sources(jobs)[1]
    finally:
        object.__setattr__(settings, "adzuna_app_id", ""); object.__setattr__(settings, "adzuna_app_key", "")


def test_adzuna_failure_falls_back_to_sample_jobs(client, monkeypatch):
    import app.agents.job_search_agent as js
    from app.config import settings
    from app.db import SessionLocal
    object.__setattr__(settings, "adzuna_app_id", "id"); object.__setattr__(settings, "adzuna_app_key", "key")
    source = js.AdzunaSource(transport=httpx.MockTransport(lambda r: httpx.Response(401)))
    monkeypatch.setattr(js, "SOURCES", [source, js.SeedDatasetSource()])
    try:
        with SessionLocal() as db:
            jobs = js.search_jobs(db, role_categories=["software_developer"])
            assert jobs and all(j.source == "seed-dataset" for j in jobs)
            engine, note = js.describe_sources(jobs)
            assert engine == "sample-data" and "Adzuna failed (HTTP 401)" in note
    finally:
        object.__setattr__(settings, "adzuna_app_id", ""); object.__setattr__(settings, "adzuna_app_key", "")


def test_no_adzuna_key_uses_sample_jobs(client):
    from app.agents.job_search_agent import search_jobs
    from app.db import SessionLocal
    with SessionLocal() as db:
        assert all(j.source == "seed-dataset" for j in search_jobs(db))


# ---------- live learning sources with fake servers ----------
FAKE_MSLEARN = {"learningPaths": [
    {"uid": "lp1", "title": "Get started with Microsoft Power BI", "url": "https://learn.microsoft.com/en-us/training/paths/get-started-power-bi/?WT.mc_id=api",
     "duration_in_minutes": 180, "levels": ["beginner"], "products": ["power-bi"], "subjects": ["data-analytics"], "popularity": 0.9}],
  "modules": [
    {"uid": "m1", "title": "Explore Azure SQL Database", "url": "https://learn.microsoft.com/en-us/training/modules/azure-sql/",
     "duration_in_minutes": 45, "levels": ["intermediate"], "products": ["azure-sql-database"], "subjects": [], "popularity": 0.5},
    {"uid": "m2", "title": "Teamwork in Microsoft Teams", "url": "https://learn.microsoft.com/en-us/training/modules/teams/",
     "duration_in_minutes": 30, "levels": ["beginner"], "products": [], "subjects": [], "popularity": 0.9}]}


def _fake_youtube(calls):
    def handler(request):
        calls.append(request.url.path)
        if request.url.path.endswith("/search"):
            return httpx.Response(200, json={"items": [{"id": {"videoId": "short1"}}, {"id": {"videoId": "long1"}}, {"id": {"videoId": "long2"}}]})
        return httpx.Response(200, json={"items": [
            {"id": "short1", "snippet": {"title": "SIEM in 60 seconds", "channelTitle": "A"}, "contentDetails": {"duration": "PT1M"}, "statistics": {"viewCount": "999999"}},
            {"id": "long1", "snippet": {"title": "SIEM Full Course for Beginners", "channelTitle": "Sec Academy"}, "contentDetails": {"duration": "PT2H30M"}, "statistics": {"viewCount": "50000"}},
            {"id": "long2", "snippet": {"title": "Cyber career talk", "channelTitle": "B"}, "contentDetails": {"duration": "PT1H"}, "statistics": {"viewCount": "900000"}},
        ]})
    return handler


@pytest.fixture
def live_learning(tmp_path, monkeypatch):
    import app.learning_sources as ls
    from app.config import settings
    monkeypatch.setattr(ls, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(ls, "_SKILL_CACHE_FILE", tmp_path / "learning_cache.json")
    monkeypatch.setattr(ls.MicrosoftLearnSource, "_CATALOG_FILE", tmp_path / "mslearn.json")
    monkeypatch.setattr(ls, "skill_cache", ls._SkillCache())
    yt_calls = []
    ms = ls.MicrosoftLearnSource(transport=httpx.MockTransport(lambda r: httpx.Response(200, json=FAKE_MSLEARN)))
    yt = ls.YouTubeSource(transport=httpx.MockTransport(_fake_youtube(yt_calls)))
    monkeypatch.setattr(ls, "LIVE_SOURCES", [ms, yt])
    object.__setattr__(settings, "learning_mslearn", True); object.__setattr__(settings, "youtube_api_key", "k")
    yield ls, yt_calls
    object.__setattr__(settings, "learning_mslearn", False); object.__setattr__(settings, "youtube_api_key", "")


def test_mslearn_matches_skill_in_title_and_uses_real_duration(live_learning):
    ls, _ = live_learning
    ms = ls.LIVE_SOURCES[0]
    pbi = ms.find("power_bi")
    assert pbi[0]["url"] == "https://learn.microsoft.com/en-us/training/paths/get-started-power-bi/"  # tracking query removed
    assert pbi[0]["hours"] == 3 and pbi[0]["hours_source"] == "provider"
    assert ms.find("sql")[0]["title"] == "Explore Azure SQL Database"
    assert ms.find("teamwork") == []  # soft skills are not searched on Microsoft Learn
    assert ms.find("siem") == []      # no title match -> nothing, rather than a loose guess


def test_youtube_picks_relevant_full_length_video(live_learning):
    ls, _ = live_learning
    pick = ls.LIVE_SOURCES[1].find("siem")[0]
    assert pick["url"] == "https://www.youtube.com/watch?v=long1"  # not the 1-minute or the off-topic video
    assert pick["hours"] == 3 and pick["provider"] == "YouTube · Sec Academy"


def test_plan_combines_live_and_curated_and_caches(live_learning):
    ls, yt_calls = live_learning
    from app.agents.learning_agent import build_plan
    gap = [{"slug": "siem", "skill": "SIEM", "priority": "high", "category": "tool", "demand_pct": 80}]
    plan = build_plan(gap, 8)
    origins = [i["origin"] for i in plan["items"]]
    assert origins == ["live", "curated"] and plan["live_sources"] == ["YouTube"]
    build_plan(gap, 8)
    assert len(yt_calls) == 2  # search + videos once; the second plan came from the cache


def test_live_failure_falls_back_to_curated(tmp_path, monkeypatch):
    import app.learning_sources as ls
    from app.config import settings
    from app.agents.learning_agent import build_plan
    monkeypatch.setattr(ls, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(ls.MicrosoftLearnSource, "_CATALOG_FILE", tmp_path / "ms.json")
    monkeypatch.setattr(ls, "skill_cache", ls._SkillCache())
    monkeypatch.setattr(ls, "_SKILL_CACHE_FILE", tmp_path / "c.json")
    down = httpx.MockTransport(lambda r: httpx.Response(503))
    monkeypatch.setattr(ls, "LIVE_SOURCES", [ls.MicrosoftLearnSource(transport=down), ls.YouTubeSource(transport=down)])
    object.__setattr__(settings, "learning_mslearn", True); object.__setattr__(settings, "youtube_api_key", "k")
    try:
        plan = build_plan([{"slug": "sql", "skill": "SQL", "priority": "high", "category": "technical", "demand_pct": 90}], 8)
        assert plan["items"] and all(i["origin"] == "curated" for i in plan["items"]) and plan["live_sources"] == []
    finally:
        object.__setattr__(settings, "learning_mslearn", False); object.__setattr__(settings, "youtube_api_key", "")


# ---------- semantic matching through an embedding API (fake server) ----------
_TOPICS = [("data", "analyst", "sql", "power bi", "dashboard", "statistics"),
           ("security", "cyber", "siem", "incident", "vulnerab", "threat"),
           ("software", "developer", "react", "api", "javascript", "backend"),
           ("cloud", "aws", "azure", "devops", "kubernetes", "infrastructure")]


def _fake_vector(text: str) -> list[float]:
    t = text.lower()
    return [0.3] + [sum(t.count(w) for w in topic) for topic in _TOPICS]  # shared base keeps unrelated cosine > 0


def _fake_embeddings(calls):
    def handler(request):
        body = json.loads(request.content)
        calls.append(len(body["input"]))
        return httpx.Response(200, json={"data": [{"index": i, "embedding": _fake_vector(t)} for i, t in enumerate(body["input"])]})
    return handler


@pytest.fixture
def embedding_api(client, tmp_path, monkeypatch):
    import app.semantic as sem
    from app.config import settings
    monkeypatch.setattr(sem, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(sem, "_cv_cache", sem.OrderedDict())
    object.__setattr__(settings, "embedding_provider", "api"); object.__setattr__(settings, "embedding_api_key", "k")
    object.__setattr__(settings, "embedding_model", f"fake-{tmp_path.name}")  # fresh stored vectors per test
    yield sem
    object.__setattr__(settings, "embedding_provider", "local"); object.__setattr__(settings, "embedding_api_key", "")


def test_semantic_scores_use_embedding_api_with_calibration(embedding_api):
    from sqlalchemy import select
    from app.db import SessionLocal
    from app.models import Job
    sem, calls = embedding_api, []
    transport = httpx.MockTransport(_fake_embeddings(calls))
    with SessionLocal() as db:
        jobs = list(db.scalars(select(Job).where(Job.source == "seed-dataset")))
        cv = "Data analyst: SQL, Power BI dashboards, statistics for reporting."
        scores, info = sem.semantic_scores(db, cv, jobs, transport=transport)
        assert info["engine"].startswith("fake-") and info["calibration"]["floor"] < info["calibration"]["ceiling"]
        assert all(0 <= v <= 1 for v in scores.values())
        by_role = lambda r: max(scores[j.id] for j in jobs if j.role_category == r)
        assert by_role("data_analyst") > by_role("cybersecurity_analyst")
        n_after_first = len(calls)
        sem.semantic_scores(db, cv, jobs, transport=transport)
        assert len(calls) == n_after_first  # job vectors stored, CV vector cached, calibration saved


def test_semantic_falls_back_to_local_when_api_fails(embedding_api):
    from sqlalchemy import select
    from app.db import SessionLocal
    from app.models import Job
    sem = embedding_api
    with SessionLocal() as db:
        jobs = list(db.scalars(select(Job).where(Job.source == "seed-dataset")))[:5]
        scores, info = sem.semantic_scores(db, "data analyst", jobs, transport=httpx.MockTransport(lambda r: httpx.Response(500)))
        assert info["engine"] == sem.LOCAL_ENGINE and info["fallback_reason"] == "HTTP 500" and len(scores) == 5


# ---------- skill gap agent (pure function, no database) ----------
from types import SimpleNamespace as _NS

from app.agents.skill_gap_agent import analyse_gaps


def _job(skills, years=0):
    return _NS(skills=skills, min_years=years)


def test_gap_demand_tier_and_unlocks():
    jobs = [_job(["sql", "tableau"]), _job(["sql", "tableau", "python"]), _job(["sql"]), _job(["sql", "excel"], 3)]
    r = analyse_gaps({"sql", "excel"}, jobs, 1)
    gaps = {m["slug"]: m for m in r["missing"]}
    assert set(gaps) == {"tableau", "python"}                 # skills you have are not gaps
    assert gaps["tableau"]["demand_pct"] == 50 and gaps["tableau"]["tier"] == "common"
    assert gaps["tableau"]["unlocks"] == 1                    # only skill missing for job 1
    assert gaps["tableau"]["adjacent"] == "Excel"             # same family as a skill you have
    assert r["missing"][0]["slug"] == "tableau"               # higher demand ranks first


def test_gap_coverage_and_experience_use_demand_and_median():
    jobs = [_job(["sql"], 1), _job(["sql"], 2), _job(["sql", "docker"], 10)]
    r = analyse_gaps({"sql"}, jobs, 2)
    cov = {c["category"]: c for c in r["coverage"]}
    assert cov["technical"]["coverage_pct"] == 100 and cov["tool"]["coverage_pct"] == 0
    assert r["experience"]["typical_required_years"] == 2     # median, so one senior advert does not distort it
    assert r["experience"]["range"] == [1, 10] and r["experience"]["meets_pct"] == 67


def test_gap_low_confidence_with_few_postings():
    r = analyse_gaps(set(), [_job(["sql"])], 0)
    assert r["confidence"]["level"] == "low"
