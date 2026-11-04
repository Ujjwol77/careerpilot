from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .db import get_db
from .models import Profile, User
from .security import decode_token

_bearer = HTTPBearer(auto_error=False)


def error(status: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status, detail={"code": code, "message": message})


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer), db: Session = Depends(get_db)
) -> User:
    user_id = decode_token(creds.credentials) if creds else None
    user = db.get(User, user_id) if user_id else None
    if not user:
        raise error(401, "UNAUTHENTICATED", "Please log in to continue.")
    return user


def require_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Profile:
    profile = db.get(Profile, user.id)
    if not profile:
        raise error(409, "NO_PROFILE", "Upload your CV first so the Profile Understanding Agent can analyse it.")
    return profile
