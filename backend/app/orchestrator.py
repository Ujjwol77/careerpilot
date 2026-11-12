"""Orchestrator: plans the run, calls each agent in order, reflects when results are weak, logs every step.

Reflection rules (the "agentic" part):
  * fewer than 3 jobs after filters  -> relax location/salary/level filters and retry
  * best match score below 35        -> widen from the target roles to every role and retry
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from .agents.cv_agent import optimise_cv
from .agents.interview_agent import preparation_plan
from .agents.job_match_agent import match_jobs, profile_text
from .agents.job_search_agent import search_jobs, describe_sources, reset_source_status
from .agents.learning_agent import build_plan
from .agents.report_agent import build_report
from .agents.skill_gap_agent import analyse_gaps
from .data.seed_jobs import ROLE_PROFILES
from .models import CVDocument, Job, Profile, Skill, User
from .tracking import tracked

MIN_JOBS = 3
MIN_TOP_SCORE = 35


def load_context(db: Session, user: User, profile: Profile) -> dict:
    skills = list(db.scalars(select(Skill.slug).where(Skill.user_id == user.id)))
    cv = db.scalars(select(CVDocument).where(CVDocument.user_id == user.id, CVDocument.is_active.is_(True)).order_by(CVDocument.id.desc())).first()
    roles = [r for r in (profile.target_roles or []) if r in ROLE_PROFILES]
    if not roles and profile.inferred_roles:
        roles = [profile.inferred_roles[0]["role"]]
    return {
        "skills": set(skills),
        "years": profile.years_experience,
        "text": profile_text(skills, profile.summary, profile.experience),
        "cv_text": cv.text if cv else "",
        "roles": roles,
    }


def search_and_match(db: Session, user: User, profile: Profile, ctx: dict, trace: list | None = None, limit: int = 10) -> list[dict]:
    with tracked(db, user.id, "job_search", trace) as step:
        reset_source_status()
        jobs = search_jobs(db, role_categories=ctx["roles"], location=profile.location, min_salary=profile.min_salary, level=profile.experience_level)
        step["note"] = f"{len(jobs)} postings after filters"
        if len(jobs) < MIN_JOBS:
            jobs = search_jobs(db, role_categories=ctx["roles"])
            step["note"] += f"; reflected: relaxed filters -> {len(jobs)} postings"
        step["llm_source"], sources_note = describe_sources(jobs)
        step["note"] += f" ({sources_note})"
    with tracked(db, user.id, "job_matching", trace) as step:
        matches = match_jobs(ctx["skills"], ctx["text"], ctx["years"], jobs, limit=limit)
        step["note"] = f"ranked {len(jobs)} postings"
        if not matches or matches[0]["score"] < MIN_TOP_SCORE:
            matches = match_jobs(ctx["skills"], ctx["text"], ctx["years"], search_jobs(db), limit=limit)
            step["note"] += "; reflected: widened to all roles"
    return matches


def top_job_objects(db: Session, matches: list[dict], n: int = 5) -> list[Job]:
    return [j for m in matches[:n] if (j := db.get(Job, m["job_id"]))]


def benchmark_jobs(db: Session, ctx: dict, matches: list[dict], limit: int = 60) -> tuple[list[Job], str]:
    """Postings used as the benchmark for skill gaps: every posting for the target role we hold.

    Using only the 5 best matches is biased (they are the jobs the candidate already fits), so the gap
    analysis uses the whole role pool, falling back to the best matches when the pool is small.
    """
    roles = ctx["roles"] or ([matches[0]["role_category"]] if matches else [])
    label = " / ".join(ROLE_PROFILES[r]["label"] for r in roles if r in ROLE_PROFILES) or "target role"
    pool = list(db.scalars(select(Job).where(Job.role_category.in_(roles)).order_by(Job.id.desc()).limit(limit))) if roles else []
    if len(pool) < 6:
        pool, label = top_job_objects(db, matches, 10), "best-matching"
    return pool, label


def run_full_evaluation(db: Session, user: User, profile: Profile) -> dict:
    trace: list[dict] = []
    ctx = load_context(db, user, profile)
    with tracked(db, user.id, "profile_understanding", trace) as step:
        step["note"] = f"{len(ctx['skills'])} skills, {profile.years_experience:g} years, roles: {', '.join(ctx['roles']) or 'none'}"

    matches = search_and_match(db, user, profile, ctx, trace)
    jobs = top_job_objects(db, matches)

    with tracked(db, user.id, "skill_gap", trace) as step:
        pool, role_label = benchmark_jobs(db, ctx, matches)
        gaps = analyse_gaps(ctx["skills"], pool, ctx["years"], role_label)
        step["note"] = f"{len(gaps['missing'])} gaps across {len(pool)} {role_label} postings"
    with tracked(db, user.id, "cv_optimisation", trace) as step:
        cv = optimise_cv(ctx["cv_text"], ctx["skills"], jobs[0] if jobs else None)
        step["note"], step["llm_source"] = f"ATS score {cv['ats_score']}", cv["rewrite_source"]
    with tracked(db, user.id, "learning_pathway", trace) as step:
        learning = build_plan(gaps["missing"])
        step["note"] = f"{len(learning['items'])} recommended courses"
    role = matches[0]["role_category"] if matches else (ctx["roles"][0] if ctx["roles"] else "data_analyst")
    with tracked(db, user.id, "interview_coach", trace) as step:
        interview = preparation_plan(role, [g["skill"] for g in gaps["missing"]])
        step["note"] = f"plan for {role}"
    with tracked(db, user.id, "report", trace) as step:
        report = build_report(
            name=user.name or profile.name_guess or "Job seeker",
            target_label=ROLE_PROFILES.get(role, {}).get("label", role),
            matches=matches, cv=cv, gaps=gaps, learning=learning, interview=interview, trace=trace,
        )
        step["note"], step["llm_source"] = f"readiness {report['readiness_score']}", report["summary_source"]
    # trace was captured before the report step finished; refresh it so the report shows every step
    report["agent_trace"] = list(trace)
    return report
