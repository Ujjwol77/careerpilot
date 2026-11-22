import os
import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Response, UploadFile
from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from .. import ats_parser
from ..agents.profile_agent import analyse_cv, cv_check, experience_years, role_fit_detail, split_sections
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
        "years_detail": experience_years(cv.text) if cv else None,
        "education": profile.education,
        "experience": profile.experience,
        "inferred_roles": profile.inferred_roles,
        "role_fit": role_fit_detail({s.slug for s in skills}),
        "skills": [{"slug": s.slug, "name": s.name, "category": s.category} for s in skills],
        "cv": {"filename": cv.filename, "size_bytes": cv.size_bytes, "uploaded_at": _utc(cv.created_at).isoformat(),
               "has_file": bool(db.scalar(select(CVDocument.data.is_not(None)).where(CVDocument.id == cv.id)))} if cv else None,
        "preferences": {
            "target_roles": profile.target_roles, "location": profile.location, "min_salary": profile.min_salary,
            "experience_level": profile.experience_level, "goals": profile.goals,
        },
    }


@router.get("")
def get_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.get(Profile, user.id)
    return _profile_out(db, user, profile) if profile else {"has_profile": False, "name": user.name}


def _utc(dt):
    """SQLite returns naive datetimes; mark them UTC so browsers show the viewer's local time."""
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


# The type is set from the checked extension, never from the browser's claim, so a file can only
# ever be served as a PDF or a Word document (never as a web page that could run script).
_MIME = {".pdf": "application/pdf", ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}


def _active_cv(db: Session, user: User) -> CVDocument:
    cv = db.scalars(select(CVDocument).where(CVDocument.user_id == user.id, CVDocument.is_active.is_(True))
                    .order_by(CVDocument.id.desc())).first()
    if not cv:
        raise error(404, "NO_CV", "You haven't uploaded a CV yet.")
    return cv


@router.get("/cv")
def cv_view(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """The active CV's details and extracted text, for the CV viewer."""
    cv = _active_cv(db, user)
    return {"filename": cv.filename, "size_bytes": cv.size_bytes, "uploaded_at": _utc(cv.created_at).isoformat(),
            "kind": os.path.splitext(cv.filename)[1].lower().lstrip("."), "text": cv.text,
            "has_file": bool(db.scalar(select(CVDocument.data.is_not(None)).where(CVDocument.id == cv.id)))}


@router.get("/cv/file")
def cv_file(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """The original uploaded file, for viewing in the browser or downloading."""
    cv = _active_cv(db, user)
    data = db.scalar(select(CVDocument.data).where(CVDocument.id == cv.id))
    if data is None:
        raise error(404, "CV_FILE_NOT_STORED", "The original file wasn't kept for this upload. Upload your CV again to view it.")
    ext = os.path.splitext(cv.filename)[1].lower()
    safe = re.sub(r"[^A-Za-z0-9._ -]", "_", cv.filename)[:120] or f"cv{ext}"
    return Response(content=data, media_type=_MIME.get(ext, "application/octet-stream"), headers={
        "Content-Disposition": f'inline; filename="{safe}"', "X-Content-Type-Options": "nosniff",
        "Cache-Control": "private, no-store"})


def _ats_view(db: Session, user: User, cv: CVDocument) -> dict:
    """What the Textkernel ATS parser read from this CV, compared with CareerPilot's own reading."""
    base = {"configured": ats_parser.configured(), "provider": ats_parser.label(), "engine": ats_parser.engine(), "filename": cv.filename}
    saved = cv.ats_read
    if not saved:
        return {**base, "status": "not_run" if base["configured"] else "not_configured"}
    if saved.get("error"):
        return {**base, "status": "failed", "error": saved["error"], "read_at": saved.get("read_at")}
    profile = db.get(Profile, user.id)
    skills = [s.name for s in db.scalars(select(Skill).where(Skill.user_id == user.id))]
    result = ats_parser.compare(saved["summary"], cv.text, split_sections(cv.text), skills, profile.name_guess if profile else "")
    return {**base, "status": "done", "read_at": saved.get("read_at"), "result": result, "engine": saved["summary"].get("engine", base["engine"]),
            "credits_remaining": saved["summary"].get("credits_remaining"), "parse_code": saved["summary"].get("parse_code")}


@router.get("/cv/ats-read")
def ats_read_get(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _ats_view(db, user, _active_cv(db, user))


@router.post("/cv/ats-read")
def ats_read_run(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Send the original file to the ATS parser once (the user asked for it), store the summary, return the comparison."""
    cv = _active_cv(db, user)
    if cv.ats_read:
        return _ats_view(db, user, cv)          # already read (or found unreadable): never spend another credit on the same file
    if not ats_parser.configured():
        raise error(409, "ATS_PARSER_NOT_CONFIGURED", ats_parser.NOT_SET_UP)
    data = db.scalar(select(CVDocument.data).where(CVDocument.id == cv.id))
    if data is None:
        raise error(409, "CV_FILE_NOT_STORED", "The original file wasn't kept for this upload. Upload your CV again first.")
    now_iso = datetime.now(timezone.utc).isoformat()
    with tracked(db, user.id, "ats_parser") as step:
        step["llm_source"] = ats_parser.provider() or "ats-parser"
        try:
            summary = ats_parser.parse_cv(data, cv.filename)
        except ats_parser.AtsParserError as exc:
            step["note"] = f"{ats_parser.label()} failed: {exc.code}"
            if exc.code == "ConversionException":   # same file fails again and still costs a credit: remember it
                cv.ats_read = {"error": {"code": exc.code, "message": str(exc)}, "read_at": now_iso}
                db.commit()
                return _ats_view(db, user, cv)
            raise error(502 if exc.code in ("NETWORK", "Timeout") else 409, f"ATS_{exc.code.upper()}", str(exc))
        cv.ats_read = {"summary": summary, "read_at": now_iso}
        db.add(AuditLog(user_id=user.id, action="ATS_PARSE", detail=f"cv sent to {ats_parser.label()}"))
        step["note"] = (f"{len(summary['positions'])} jobs, {len(summary['skills'])} skills read"
                        + (f"; {summary['credits_remaining']:g} credits left" if isinstance(summary.get("credits_remaining"), (int, float)) else ""))
        db.commit()
    return _ats_view(db, user, cv)


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
    check = cv_check(text)                                       # checked before anything is replaced
    if not check["is_cv"]:
        reasons = check["against"] + check["missing"]
        raise error(422, "NOT_A_CV", "This file doesn't look like a CV, so your profile was not changed: "
                    + "; ".join(reasons[:3]) + ". Upload your CV or résumé instead.")
    existing = db.get(Profile, user.id)
    if existing and not overwrite:
        raise error(409, "PROFILE_EXISTS", "You already have a profile. Confirm to overwrite it with this CV.")

    with tracked(db, user.id, "profile_understanding") as step:
        parsed = analyse_cv(text)
        yd = parsed["years_detail"]
        step["note"] = (f"{len(parsed['skills'])} skills, {yd['years']:g} years "
                        + ("(stated in CV" + (f"; job dates add up to {yd['from_dates']:g})" if yd["from_dates"] != yd["years"] else ")")
                           if yd["source"] == "stated" else "(from job dates)"))
        db.execute(update(CVDocument).where(CVDocument.user_id == user.id).values(is_active=False))
        db.add(CVDocument(user_id=user.id, filename=(file.filename or "cv")[:255], mime_type=file.content_type or "", size_bytes=len(data), text=text, data=data))
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
