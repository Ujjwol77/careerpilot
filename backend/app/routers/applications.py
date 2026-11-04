from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import error, get_current_user
from ..models import Application, Job, User
from ..schemas import ApplicationIn, ApplicationPatch

router = APIRouter(prefix="/applications", tags=["applications"])


def _out(app: Application, job: Job) -> dict:
    return {"id": app.id, "job_id": job.id, "title": job.title, "company": job.company, "location": job.location,
            "status": app.status, "notes": app.notes, "updated_at": app.updated_at.isoformat()}


def _own(db: Session, user: User, app_id: int) -> Application:
    app = db.get(Application, app_id)
    if not app or app.user_id != user.id:
        raise error(404, "APPLICATION_NOT_FOUND", "Application not found.")
    return app


@router.get("")
def list_applications(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.execute(select(Application, Job).join(Job, Job.id == Application.job_id).where(Application.user_id == user.id).order_by(Application.updated_at.desc()))
    return [_out(a, j) for a, j in rows]


@router.post("", status_code=201)
def add_application(body: ApplicationIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = db.get(Job, body.job_id)
    if not job:
        raise error(404, "JOB_NOT_FOUND", "That job posting does not exist.")
    if db.scalar(select(Application).where(Application.user_id == user.id, Application.job_id == job.id)):
        raise error(409, "ALREADY_TRACKED", "You are already tracking this job.")
    app = Application(user_id=user.id, job_id=job.id, status=body.status, notes=body.notes)
    db.add(app)
    db.commit()
    return _out(app, job)


@router.patch("/{app_id}")
def update_application(app_id: int, body: ApplicationPatch, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    app = _own(db, user, app_id)
    if body.status is not None:
        app.status = body.status
    if body.notes is not None:
        app.notes = body.notes
    db.commit()
    return _out(app, db.get(Job, app.job_id))


@router.delete("/{app_id}", status_code=204)
def delete_application(app_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.delete(_own(db, user, app_id))
    db.commit()
