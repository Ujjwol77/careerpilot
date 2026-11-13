"""Skill gap, CV optimisation, learning pathway and interview coach endpoints."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..agents.cv_agent import optimise_cv
from ..agents.interview_agent import build_questions, evaluate_answer
from ..agents.job_match_agent import WEIGHTS, match_jobs
from ..semantic import semantic_scores
from ..agents.learning_agent import build_plan
from ..agents.skill_gap_agent import analyse_gaps
from ..data.seed_jobs import ROLE_PROFILES
from ..db import get_db
from ..deps import error, get_current_user, require_profile
from ..models import InterviewSession, Job, Profile, User
from ..orchestrator import load_context, search_and_match, top_job_objects
from ..schemas import InterviewAnswerIn, InterviewStartIn
from ..tracking import tracked

router = APIRouter(tags=["analysis"])


def _context(db: Session, user: User, profile: Profile):
    ctx = load_context(db, user, profile)
    matches = search_and_match(db, user, profile, ctx)
    return ctx, matches, top_job_objects(db, matches)


@router.get("/skill-gap")
def skill_gap(user: User = Depends(get_current_user), profile: Profile = Depends(require_profile), db: Session = Depends(get_db)):
    ctx, matches, jobs = _context(db, user, profile)
    with tracked(db, user.id, "skill_gap") as step:
        result = analyse_gaps(ctx["skills"], jobs, ctx["years"])
        step["note"] = f"{len(result['missing'])} gaps"
    return result


@router.get("/cv/optimise")
def cv_optimise(job_id: int | None = Query(None), user: User = Depends(get_current_user), profile: Profile = Depends(require_profile), db: Session = Depends(get_db)):
    ctx, matches, jobs = _context(db, user, profile)
    target = db.get(Job, job_id) if job_id else (jobs[0] if jobs else None)
    if job_id and not target:
        raise error(404, "JOB_NOT_FOUND", "That job posting does not exist.")
    with tracked(db, user.id, "cv_optimisation") as step:
        result = optimise_cv(ctx["cv_text"], ctx["skills"], target)
        step["note"], step["llm_source"] = f"ATS score {result['ats_score']}", result["rewrite_source"]
    result["target_reason"] = explain_target(target, matches, ctx, chosen=bool(job_id), db=db)
    return result


def explain_target(target: Job | None, matches: list[dict], ctx: dict, chosen: bool, db: Session | None = None) -> dict | None:
    """Why the review is tailored to this job: its rank and match-score breakdown among the user's matches."""
    if not target:
        return None
    rank = next((i for i, m in enumerate(matches) if m["job_id"] == target.id), None)
    if rank is not None:
        m = matches[rank]
    else:
        sem, info = semantic_scores(db, ctx["text"], [target])
        m = match_jobs(ctx["skills"], ctx["text"], ctx["years"], [target], semantic=sem, semantic_engine=info["engine"])[0]
    return {
        "mode": "chosen" if chosen else "best_match",
        "rank": rank + 1 if rank is not None else None, "of": len(matches),
        "score": m["score"], "readiness": m["readiness"], "components": m["components"], "semantic_engine": m.get("semantic_engine"),
        "weights": {"semantic": WEIGHTS["semantic"], "skill_coverage": WEIGHTS["coverage"], "experience_fit": WEIGHTS["experience"]},
        "matched_skills": m["matched_skills"], "missing_skills": m["missing_skills"],
        "runners_up": [{"job_id": r["job_id"], "title": r["title"], "company": r["company"], "score": r["score"]}
                       for r in matches if r["job_id"] != target.id][:3],
    }


@router.get("/learning")
def learning(user: User = Depends(get_current_user), profile: Profile = Depends(require_profile), db: Session = Depends(get_db)):
    ctx, matches, jobs = _context(db, user, profile)
    gaps = analyse_gaps(ctx["skills"], jobs, ctx["years"])
    with tracked(db, user.id, "learning_pathway") as step:
        plan = build_plan(gaps["missing"])
        step["note"] = f"{len(plan['items'])} courses"
    return plan


@router.post("/interview/start", status_code=201)
def interview_start(body: InterviewStartIn, user: User = Depends(get_current_user), profile: Profile = Depends(require_profile), db: Session = Depends(get_db)):
    ctx, matches, jobs = _context(db, user, profile)
    role = body.role or (matches[0]["role_category"] if matches else ctx["roles"][0])
    if role not in ROLE_PROFILES:
        raise error(422, "UNKNOWN_ROLE", "Unknown role.")
    gaps = analyse_gaps(ctx["skills"], jobs, ctx["years"])
    with tracked(db, user.id, "interview_coach") as step:
        questions = build_questions(role, [m["slug"] for m in gaps["missing"]], sorted(ctx["skills"]))
        session = InterviewSession(user_id=user.id, role=role, questions=questions, answers=[])
        db.add(session)
        db.commit()
        step["note"] = f"{len(questions)} questions for {role}"
    public = [{"index": i, "type": q["type"], "skill": q["skill"], "question": q["question"]} for i, q in enumerate(questions)]
    return {"session_id": session.id, "role": role, "role_label": ROLE_PROFILES[role]["label"], "questions": public}


@router.post("/interview/answer")
def interview_answer(body: InterviewAnswerIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = db.get(InterviewSession, body.session_id)
    if not session or session.user_id != user.id:
        raise error(404, "SESSION_NOT_FOUND", "Interview session not found.")
    if body.index >= len(session.questions):
        raise error(422, "BAD_QUESTION_INDEX", "That question does not exist in this session.")
    with tracked(db, user.id, "interview_coach") as step:
        result = evaluate_answer(session.questions[body.index], body.answer, session.role)
        step["note"], step["llm_source"] = f"scored {result['score']}/10", result["feedback_source"]
        answers = [a for a in session.answers if a["index"] != body.index]
        answers.append({"index": body.index, "answer": body.answer, "score": result["score"]})
        session.answers = sorted(answers, key=lambda a: a["index"])
        db.commit()
    scores = [a["score"] for a in session.answers]
    return {**result, "answered": len(scores), "total": len(session.questions), "average_score": round(sum(scores) / len(scores), 1)}


@router.get("/interview/sessions")
def interview_sessions(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(InterviewSession).where(InterviewSession.user_id == user.id).order_by(InterviewSession.id.desc()).limit(10))
    return [{"id": s.id, "role": s.role, "created_at": s.created_at.isoformat(), "answered": len(s.answers), "total": len(s.questions),
             "average_score": round(sum(a["score"] for a in s.answers) / len(s.answers), 1) if s.answers else None} for s in rows]
