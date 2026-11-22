"""Reference data the website needs (roles, fields, levels, statuses).

The deploy version drops the developer endpoints (agent run history, service status and the prompt bank)."""
from fastapi import APIRouter

from ..data.seed_jobs import ROLE_PROFILES, fields_with_roles

router = APIRouter(tags=["meta"])


@router.get("/meta")
def meta():
    return {
        "roles": [{"key": k, "label": v["label"], "field": v["field"]} for k, v in ROLE_PROFILES.items()],
        "fields": fields_with_roles(),  # field -> roles, for the two-step pickers
        "levels": ["junior", "mid", "senior"],
        "statuses": ["saved", "applied", "interview", "offer", "rejected"],
    }
