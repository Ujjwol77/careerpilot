from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..agents.job_search_agent import search_jobs
from ..db import get_db
from ..deps import error, get_current_user, require_profile
from ..models import AuditLog, Job, Profile, User
from ..orchestrator import load_context, search_and_match

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _job_out(j: Job) -> dict:
    return {"id": j.id, "title": j.title, "company": j.company, "location": j.location, "level": j.level,
            "role_category": j.role_category, "salary_min": j.salary_min, "salary_max": j.salary_max,
            "description": j.description, "source": j.source}


@router.get("/search")
def search(q: str = "", role: str = "", location: str = "", min_salary: int = Query(0, ge=0), level: str = "",
           user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    jobs = search_jobs(db, keywords=q, role_categories=[role] if role else None, location=location, min_salary=min_salary, level=level)
    return {"count": len(jobs), "jobs": [_job_out(j) for j in jobs]}


@router.post("/match")
def match(user: User = Depends(get_current_user), profile: Profile = Depends(require_profile), db: Session = Depends(get_db)):
    ctx = load_context(db, user, profile)
    trace: list[dict] = []
    matches = search_and_match(db, user, profile, ctx, trace)
    db.add(AuditLog(user_id=user.id, action="MATCH_CALCULATION", detail=f"{len(matches)} results"))
    db.commit()
    for m in matches:
        m.pop("missing_slugs", None)
    return {"count": len(matches), "matches": matches, "agent_trace": trace}


@router.get("/{job_id}")
def get_job(job_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise error(404, "JOB_NOT_FOUND", "That job posting does not exist.")
    return _job_out(job)
