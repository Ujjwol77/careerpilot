from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import error, get_current_user
from ..models import AuditLog, User
from ..schemas import LoginIn, RegisterIn
from ..security import create_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_out(user: User) -> dict:
    return {"id": user.id, "email": user.email, "name": user.name}


@router.post("/register", status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    if db.scalar(select(User).where(User.email == email)):
        raise error(409, "EMAIL_TAKEN", "An account with this email already exists.")
    user = User(email=email, name=body.name.strip(), password_hash=hash_password(body.password))
    db.add(user)
    db.commit()
    db.add(AuditLog(user_id=user.id, action="REGISTER"))
    db.commit()
    return {"token": create_token(user.id), "user": _user_out(user)}


@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.strip().lower()))
    if not user or not verify_password(body.password, user.password_hash):
        raise error(401, "BAD_CREDENTIALS", "Incorrect email or password.")
    db.add(AuditLog(user_id=user.id, action="LOGIN"))
    db.commit()
    return {"token": create_token(user.id), "user": _user_out(user)}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return _user_out(user)
