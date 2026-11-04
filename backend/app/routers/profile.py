from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from ..agents.profile_agent import analyse_cv
from ..config import settings
from ..cv_extract import validate_and_extract
from ..data.seed_jobs import ROLE_PROFILES
from ..db import get_db
from ..deps import error, get_current_user, require_profile
from ..models import AuditLog, CVDocument, Profile, Skill, User
from ..schemas import PreferencesIn
from ..tracking import tracked

router = APIRouter(prefix="/profile", tags=["profile"])


def _profile_out(db: Session, user: User, profile: Profile) -> dict:
    skills = list(db.scalars(select(Skill).where(Skill.user_id == user.id)))
    cv = db.scalars(select(CVDocument).where(CVDocument.user_id == user.id, CVDocument.is_active.is_(True)).order_by(CVDocument.id.desc())).first()
    return {
        "has_profile": True,
        "name": user.name or profile.name_guess,
        "summary": profile.summary,
        "years_experience": profile.years_experience,
        "education": profile.education,
        "experience": profile.experience,
        "inferred_roles": profile.inferred_roles,
        "skills": [{"slug": s.slug, "name": s.name, "category": s.category} for s in skills],
        "cv": {"filename": cv.filename, "size_bytes": cv.size_bytes, "uploaded_at": cv.created_at.isoformat()} if cv else None,
        "preferences": {
            "target_roles": profile.target_roles, "location": profile.location, "min_salary": profile.min_salary,
            "experience_level": profile.experience_level, "goals": profile.goals,
        },
    }


@router.get("")
def get_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.get(Profile, user.id)
    return _profile_out(db, user, profile) if profile else {"has_profile": False, "name": user.name}


@router.put("/preferences")
def update_preferences(body: PreferencesIn, user: User = Depends(get_current_user), profile: Profile = Depends(require_profile), db: Session = Depends(get_db)):
    bad = [r for r in body.target_roles if r not in ROLE_PROFILES]
    if bad:
        raise error(422, "UNKNOWN_ROLE", f"Unknown target role(s): {', '.join(bad)}.")
    profile.target_roles, profile.location = body.target_roles, body.location.strip()
    profile.min_salary, profile.experience_level, profile.goals = body.min_salary, body.experience_level, body.goals.strip()
    db.add(AuditLog(user_id=user.id, action="UPDATE_PREFERENCES"))
    db.commit()
    return _profile_out(db, user, profile)


@router.post("/upload", status_code=201)
def upload_cv(overwrite: bool = False, file: UploadFile = File(...), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    data = file.file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    text = validate_and_extract(file.filename or "", data)      # 413 / 415 / 422 on failure
    existing = db.get(Profile, user.id)
    if existing and not overwrite:
        raise error(409, "PROFILE_EXISTS", "You already have a profile. Confirm to overwrite it with this CV.")

    with tracked(db, user.id, "profile_understanding") as step:
        parsed = analyse_cv(text)
        step["note"] = f"{len(parsed['skills'])} skills, {parsed['years_experience']:g} years"
        db.execute(update(CVDocument).where(CVDocument.user_id == user.id).values(is_active=False))
        db.add(CVDocument(user_id=user.id, filename=(file.filename or "cv")[:255], mime_type=file.content_type or "", size_bytes=len(data), text=text))
        profile = existing or Profile(user_id=user.id)
        profile.name_guess, profile.summary = parsed["name_guess"], parsed["summary"]
        profile.years_experience, profile.education = parsed["years_experience"], parsed["education"]
        profile.experience, profile.inferred_roles = parsed["experience"], parsed["inferred_roles"]
        if not profile.target_roles:
            profile.target_roles = []
        db.add(profile)
        db.execute(delete(Skill).where(Skill.user_id == user.id))
        db.add_all(Skill(user_id=user.id, slug=s["slug"], name=s["name"], category=s["category"]) for s in parsed["skills"])
        db.add(AuditLog(user_id=user.id, action="CV_UPLOAD", detail=f"{len(data)} bytes"))
        db.commit()
    return _profile_out(db, user, profile)
