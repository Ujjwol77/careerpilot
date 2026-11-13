"""LLMOps endpoints: run history, aggregate health and the prompt bank (scoped to the signed-in user)."""
from datetime import timezone

from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from ..agents.job_search_agent import job_source_mode
from ..config import settings
from ..data.seed_jobs import ROLE_PROFILES
from ..db import get_db
from ..deps import get_current_user
from ..llm import get_llm
from ..models import AgentRun, User
from ..prompt_bank import PROMPTS
from ..semantic import api_enabled

router = APIRouter(tags=["ops"])


@router.get("/ops/summary")
def summary(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.execute(
        select(AgentRun.agent, func.count(), func.avg(AgentRun.duration_ms),
               func.sum(case((AgentRun.status == "error", 1), else_=0)))
        .where(AgentRun.user_id == user.id).group_by(AgentRun.agent)
    ).all()
    return {
        "llm_provider": "mock" if get_llm().is_mock else settings.llm_provider,
        "job_source": job_source_mode(),
        # which external services are configured (set up does not guarantee working; see each agent run's note)
        "services": {
            "gemini": {"set_up": not get_llm().is_mock, "detail": settings.llm_model},
            "embeddings": {"set_up": api_enabled(), "detail": settings.embedding_model},
            "adzuna": {"set_up": job_source_mode() == "adzuna", "detail": f"country {settings.adzuna_country}"},
            "mslearn": {"set_up": settings.learning_mslearn, "detail": "no key needed"},
            "youtube": {"set_up": bool(settings.youtube_api_key), "detail": "YouTube Data API v3"},
        },
        "agents": [{"agent": a, "runs": n, "avg_ms": round(avg or 0), "errors": int(err or 0)} for a, n, avg, err in rows],
    }


@router.get("/ops/runs")
def runs(limit: int = 30, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(AgentRun).where(AgentRun.user_id == user.id).order_by(AgentRun.id.desc()).limit(min(limit, 100)))
    return [{"id": r.id, "agent": r.agent, "status": r.status, "duration_ms": r.duration_ms,
             "llm_source": r.llm_source, "note": r.note, "created_at": _utc(r.created_at).isoformat()} for r in rows]


def _utc(dt):
    """SQLite returns naive datetimes; mark them UTC so browsers convert to the viewer's local time."""
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


@router.get("/prompts")
def prompts(user: User = Depends(get_current_user)):
    return [{"id": pid, **{k: v for k, v in p.items()}} for pid, p in PROMPTS.items()]


@router.get("/meta")
def meta():
    return {
        "roles": [{"key": k, "label": v["label"]} for k, v in ROLE_PROFILES.items()],
        "levels": ["junior", "mid", "senior"],
        "statuses": ["saved", "applied", "interview", "offer", "rejected"],
    }
