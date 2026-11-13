"""Job Matching Agent: ranks jobs by semantic similarity, skill coverage and experience fit.

score = 100 x (0.35 x semantic + 0.50 x skill coverage + 0.15 x experience fit)
semantic comes from a neural embedding model when one is configured (see semantic.py).
"""
from ..semantic import LOCAL_ENGINE, semantic_scores
from ..models import Job
from ..taxonomy import SKILLS, category, display

WEIGHTS = {"semantic": 0.35, "coverage": 0.50, "experience": 0.15}
BANDS = [(80, "HIGHLY_QUALIFIED"), (60, "QUALIFIED_WITH_GAPS"), (0, "DEVELOPMENT_REQUIRED")]
SKILL_WEIGHT = {"technical": 1.0, "tool": 1.0, "certification": 0.4, "soft": 0.5}


def readiness_band(score: float) -> str:
    return next(label for floor, label in BANDS if score >= floor)


def profile_text(skills: list[str], summary: str, experience: list[str]) -> str:
    return " ".join([", ".join(display(s) for s in skills), summary, " ".join(experience)])


def match_jobs(skills: set[str], text: str, years: float, jobs: list[Job], limit: int = 10,
               semantic: dict[int, float] | None = None, semantic_engine: str = LOCAL_ENGINE) -> list[dict]:
    """`semantic` = precomputed {job_id: 0..1} from semantic.semantic_scores(); computed locally if omitted."""
    if semantic is None:
        semantic, info = semantic_scores(None, text, jobs)
        semantic_engine = info["engine"]
    ranked = []
    for job in jobs:
        required = job.skills or []
        total_w = sum(SKILL_WEIGHT[category(s)] for s in required) or 1.0
        have_w = sum(SKILL_WEIGHT[category(s)] for s in required if s in skills)
        coverage = have_w / total_w
        sem = semantic.get(job.id, 0.0)
        experience = 1.0 if years >= job.min_years else max(0.0, 1 - (job.min_years - years) / 4)
        score = 100 * (WEIGHTS["semantic"] * sem + WEIGHTS["coverage"] * coverage + WEIGHTS["experience"] * experience)
        ranked.append({
            "job_id": job.id, "title": job.title, "company": job.company, "location": job.location,
            "level": job.level, "salary_min": job.salary_min, "salary_max": job.salary_max,
            "role_category": job.role_category, "source": job.source, "url": job.url or "",
            "score": round(score, 1), "readiness": readiness_band(score),
            "semantic_engine": semantic_engine,
            "components": {"semantic": round(sem, 2), "skill_coverage": round(coverage, 2), "experience_fit": round(experience, 2)},
            "matched_skills": [display(s) for s in required if s in skills],
            "missing_skills": [display(s) for s in required if s not in skills],
            "missing_slugs": [s for s in required if s not in skills],
        })
    ranked.sort(key=lambda r: -r["score"])
    return ranked[:limit]
