"""Job Search Agent: finds candidate postings from a job source using keywords and filters.

`JobSource` is the extension point. The default `SeedDatasetSource` queries the jobs table
(seeded with a synthetic dataset). To add live jobs, implement `search()` against an API/dataset
and append it to SOURCES.
"""
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Job


class JobSource(Protocol):
    name: str

    def search(self, db: Session, **filters) -> list[Job]: ...


class SeedDatasetSource:
    name = "seed-dataset"

    def search(self, db: Session, role_categories=None, **_) -> list[Job]:
        stmt = select(Job)
        if role_categories:
            stmt = stmt.where(Job.role_category.in_(role_categories))
        return list(db.scalars(stmt))


SOURCES: list[JobSource] = [SeedDatasetSource()]


def search_jobs(
    db: Session, keywords: str = "", role_categories: list[str] | None = None, location: str = "",
    min_salary: int = 0, level: str = "", limit: int = 60,
) -> list[Job]:
    candidates: list[Job] = []
    for source in SOURCES:
        candidates.extend(source.search(db, role_categories=role_categories))

    terms = [t for t in keywords.lower().split() if t]
    results = []
    for job in candidates:
        if location and location.lower() not in job.location.lower() and "remote" not in job.location.lower():
            continue
        if min_salary and job.salary_max < min_salary:
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
