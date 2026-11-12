from typing import Literal

from pydantic import BaseModel, Field

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
Status = Literal["saved", "applied", "interview", "offer", "rejected"]


class RegisterIn(BaseModel):
    email: str = Field(pattern=EMAIL_PATTERN, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(default="", max_length=120)


class LoginIn(BaseModel):
    email: str
    password: str


class PreferencesIn(BaseModel):
    target_roles: list[str] = []
    location: str = Field(default="", max_length=120)
    min_salary: int = Field(default=0, ge=0, le=1_000_000)
    experience_level: Literal["", "junior", "mid", "senior"] = ""
    goals: str = Field(default="", max_length=1000)


class ApplicationIn(BaseModel):
    job_id: int
    status: Status = "saved"
    notes: str = Field(default="", max_length=1000)


class ApplicationPatch(BaseModel):
    status: Status | None = None
    notes: str | None = Field(default=None, max_length=1000)


class InterviewStartIn(BaseModel):
    role: str | None = None


class InterviewAnswerIn(BaseModel):
    session_id: int
    index: int = Field(ge=0)
    answer: str = Field(min_length=1, max_length=4000)


class ReportIn(BaseModel):
    pass  # report takes no options; kept so clients can still POST an empty body
