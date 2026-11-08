"""Job Search Agent: finds candidate postings from job sources using keywords and filters.

`JobSource` is the extension point. Two sources ship:
  * AdzunaSource      - live Australian postings from the Adzuna API (needs ADZUNA_APP_ID / ADZUNA_APP_KEY)
  * SeedDatasetSource - the synthetic 45-posting dataset, used when no live source returns enough jobs

Live postings are saved to the jobs table, so matching, skill gaps and application tracking
work on them exactly as on the sample jobs.
"""
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Protocol

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..data.seed_jobs import ROLE_PROFILES
from ..embeddings import embed
from ..models import Job, JobQueryCache
from ..taxonomy import extract_skills

log = logging.getLogger("careerpilot.jobs")

MIN_LIVE_RESULTS = 3  # below this, the sample dataset is added so the user always sees jobs


class JobSource(Protocol):
    name: str
    live: bool

    def search(self, db: Session, **filters) -> list[Job]: ...


class SeedDatasetSource:
    name = "seed-dataset"
    live = False

    def search(self, db: Session, role_categories=None, **_) -> list[Job]:
        stmt = select(Job).where(Job.source == self.name)
        if role_categories:
            stmt = stmt.where(Job.role_category.in_(role_categories))
        return list(db.scalars(stmt))


# ---------------- Adzuna ----------------
_SENIOR = re.compile(r"\b(senior|sr\.?|lead|principal|head|manager|staff)\b", re.I)
_JUNIOR = re.compile(r"\b(junior|jr\.?|graduate|grad|entry|trainee|intern(ship)?|cadet|associate)\b", re.I)
_LEVEL_YEARS = {"junior": 0, "mid": 2, "senior": 5}
_TAGS = re.compile(r"<[^>]+>")


def infer_level(title: str) -> str:
    if _SENIOR.search(title):
        return "senior"
    if _JUNIOR.search(title):
        return "junior"
    return "mid"


class AdzunaSource:
    """Searches Adzuna by target role (and location), caches each search, and stores postings as Job rows."""
    name = "adzuna"
    live = True
    BASE = "https://api.adzuna.com/v1/api/jobs"

    def __init__(self, transport: httpx.BaseTransport | None = None):
        self._transport = transport  # tests inject a mock transport

    @property
    def enabled(self) -> bool:
        return bool(settings.adzuna_app_id and settings.adzuna_app_key)

    def search(self, db: Session, role_categories=None, location: str = "", **_) -> list[Job]:
        if not self.enabled:
            return []
        roles = [r for r in (role_categories or []) if r in ROLE_PROFILES]
        if not roles:  # no target role (e.g. "widen to all roles"): reuse saved postings, no new API calls
            return list(db.scalars(select(Job).where(Job.source == self.name)))
        jobs: list[Job] = []
        for role in roles:
            jobs.extend(self._search_role(db, role, location.strip()))
        return jobs

    def _search_role(self, db: Session, role: str, location: str) -> list[Job]:
        key = f"{settings.adzuna_country}|{role}|{location.lower()}"
        cached = db.scalar(select(JobQueryCache).where(JobQueryCache.key == key))
        fresh_after = datetime.now(timezone.utc) - timedelta(hours=settings.jobs_cache_hours)
        if cached and _aware(cached.fetched_at) > fresh_after:
            return self._saved(db, role, location)
        try:
            results = self._fetch(ROLE_PROFILES[role]["label"], location)
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            log.warning("Adzuna search failed for %s / %s: %s", role, location or "Australia", exc)
            return self._saved(db, role, location)  # serve whatever was saved earlier
        for item in results:
            self._upsert(db, item, role)
        if cached:
            cached.fetched_at, cached.result_count = datetime.now(timezone.utc), len(results)
        else:
            db.add(JobQueryCache(key=key, result_count=len(results)))
        db.commit()
        return self._saved(db, role, location)

    def _fetch(self, what: str, where: str) -> list[dict]:
        params = {
            "app_id": settings.adzuna_app_id, "app_key": settings.adzuna_app_key,
            "what": what, "results_per_page": max(1, min(settings.adzuna_results, 50)),
            "max_days_old": 30, "content-type": "application/json",
        }
        if where:
            params["where"] = where
        url = f"{self.BASE}/{settings.adzuna_country}/search/1"
        with httpx.Client(timeout=15, transport=self._transport) as client:
            r = client.get(url, params=params)
            r.raise_for_status()
            return r.json().get("results", [])

    def _upsert(self, db: Session, item: dict, role: str) -> None:
        ext_id = str(item.get("id", ""))
        if not ext_id:
            return
        title = _clean(item.get("title", ""))[:200] or "Untitled role"
        description = _clean(item.get("description", ""))
        company = _clean((item.get("company") or {}).get("display_name", "")) or "Company not listed"
        location = _clean((item.get("location") or {}).get("display_name", "")) or "Australia"
        level = infer_level(title)
        fields = {
            "title": title, "company": company[:200], "location": location[:120],
            "role_category": role, "level": level, "min_years": _LEVEL_YEARS[level],
            "salary_min": int(item.get("salary_min") or 0), "salary_max": int(item.get("salary_max") or 0),
            "description": description, "skills": extract_skills(f"{title}. {description}"),
            "embedding": embed(f"{title}. {description}"),
            "url": (item.get("redirect_url") or "")[:500], "source": self.name, "external_id": ext_id,
        }
        job = db.scalar(select(Job).where(Job.source == self.name, Job.external_id == ext_id))
        if job:
            for k, v in fields.items():
                setattr(job, k, v)
        else:
            db.add(Job(**fields))

    def _saved(self, db: Session, role: str, location: str) -> list[Job]:
        stmt = select(Job).where(Job.source == self.name, Job.role_category == role)
        jobs = list(db.scalars(stmt))
        if location:
            jobs = [j for j in jobs if location.lower() in j.location.lower()] or jobs
        return jobs


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)  # SQLite returns naive datetimes


def _clean(text: str) -> str:
    return " ".join(_TAGS.sub(" ", text or "").split())


SOURCES: list[JobSource] = [AdzunaSource(), SeedDatasetSource()]


def search_jobs(
    db: Session, keywords: str = "", role_categories: list[str] | None = None, location: str = "",
    min_salary: int = 0, level: str = "", limit: int = 60,
) -> list[Job]:
    live: list[Job] = []
    for source in SOURCES:
        if source.live:
            live.extend(source.search(db, role_categories=role_categories, location=location))
    candidates = list(live)
    if len(live) < MIN_LIVE_RESULTS:  # no key, API down or too few results: fall back to the sample jobs
        for source in SOURCES:
            if not source.live:
                candidates.extend(source.search(db, role_categories=role_categories))

    terms = [t for t in keywords.lower().split() if t]
    results = []
    for job in candidates:
        if location and location.lower() not in job.location.lower() and "remote" not in job.location.lower():
            continue
        if min_salary and job.salary_max and job.salary_max < min_salary:  # unknown salary (0) is kept
            continue
        if level and job.level != level:
            continue
        haystack_title, haystack_desc = job.title.lower(), job.description.lower()
        relevance = sum(3 for t in terms if t in haystack_title) + sum(1 for t in terms if t in haystack_desc)
        if terms and relevance == 0:
            continue
        results.append((relevance, job))
    results.sort(key=lambda r: (-r[0], r[1].id))
    return [job for _, job in results[:limit]]
