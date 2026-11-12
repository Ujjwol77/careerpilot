from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_profile
from ..models import AuditLog, Profile, Report, User
from ..orchestrator import run_full_evaluation
from ..schemas import ReportIn

router = APIRouter(prefix="/report", tags=["report"])


@router.post("/generate", status_code=201)
def generate(body: ReportIn | None = None, user: User = Depends(get_current_user), profile: Profile = Depends(require_profile), db: Session = Depends(get_db)):
    payload = run_full_evaluation(db, user, profile)
    db.add(Report(user_id=user.id, payload=payload))
    db.add(AuditLog(user_id=user.id, action="REPORT_GENERATED"))
    db.commit()
    return payload


@router.get("/latest")
def latest(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    report = db.scalars(select(Report).where(Report.user_id == user.id).order_by(Report.id.desc())).first()
    return report.payload if report else None
