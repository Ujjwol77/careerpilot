import io

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
    assert body["jobs_analysed"] > 0 and body["missing"]
    assert set(body["grouped"]) == {"Technical skills", "Tools", "Soft skills", "Certifications"}
    assert all(m["priority"] in {"high", "medium", "low"} for m in body["missing"])


def test_cv_optimise(client, uploaded):
    headers, _ = uploaded
    body = client.get(f"{API}/cv/optimise", headers=headers).json()
    assert 0 <= body["ats_score"] <= 100
    areas = {s["area"] for s in body["suggestions"]}
    assert "wording" in areas  # the sample CV uses "Responsible for ..." and "Worked on ..."
    assert body["rewrite_source"] == "template"
    assert client.get(f"{API}/cv/optimise", headers=headers, params={"job_id": 99999}).status_code == 404


def test_learning_plan(client, uploaded):
    headers, _ = uploaded
    plan = client.get(f"{API}/learning", headers=headers, params={"hours_per_week": 10}).json()
    assert plan["total_hours"] == sum(i["hours"] for i in plan["items"])
    assert plan["total_weeks"] >= 1 and plan["weeks"][0]["week"] == 1
    assert client.get(f"{API}/learning", headers=headers, params={"hours_per_week": 0}).status_code == 422


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
    r = client.post(f"{API}/report/generate", headers=headers, json={"hours_per_week": 8})
    rep = r.json()
    assert r.status_code == 201
    agents = [t["agent"] for t in rep["agent_trace"]]
    assert agents == ["profile_understanding", "job_search", "job_matching", "skill_gap", "cv_optimisation", "learning_pathway", "interview_coach", "report"]
    assert all(t["status"] == "ok" for t in rep["agent_trace"])
    assert rep["readiness_band"] in {"HIGHLY_QUALIFIED", "QUALIFIED_WITH_GAPS", "DEVELOPMENT_REQUIRED"}
    assert rep["top_jobs"] and rep["cv"]["suggestions"] and rep["learning"]["weeks"] and rep["interview"]["schedule"]
    assert client.get(f"{API}/report/latest", headers=headers).json()["generated_at"] == rep["generated_at"]
    summary = client.get(f"{API}/ops/summary", headers=headers).json()
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
