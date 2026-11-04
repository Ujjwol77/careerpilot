"""LLMOps endpoints: run history, aggregate health and the prompt bank (scoped to the signed-in user)."""
from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from ..config import settings
from ..data.seed_jobs import ROLE_PROFILES
from ..db import get_db
from ..deps import get_current_user
from ..llm import get_llm
from ..models import AgentRun, User
from ..prompt_bank import PROMPTS

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
        "agents": [{"agent": a, "runs": n, "avg_ms": round(avg or 0), "errors": int(err or 0)} for a, n, avg, err in rows],
    }


@router.get("/ops/runs")
def runs(limit: int = 30, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(AgentRun).where(AgentRun.user_id == user.id).order_by(AgentRun.id.desc()).limit(min(limit, 100)))
    return [{"id": r.id, "agent": r.agent, "status": r.status, "duration_ms": r.duration_ms,
             "llm_source": r.llm_source, "note": r.note, "created_at": r.created_at.isoformat()} for r in rows]


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
