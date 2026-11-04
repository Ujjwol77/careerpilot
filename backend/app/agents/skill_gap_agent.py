"""Skill Gap Analysis Agent: what is missing across the top matching jobs, split by category."""
from collections import Counter

from ..models import Job
from ..taxonomy import CATEGORY_ORDER, SKILLS, category, display

IMPORTANCE = {"technical": 1.0, "tool": 1.0, "soft": 0.8, "certification": 0.5}
GROUPS = {"technical": "Technical skills", "tool": "Tools", "soft": "Soft skills", "certification": "Certifications"}


def analyse_gaps(skills: set[str], jobs: list[Job], years: float) -> dict:
    n = max(len(jobs), 1)
    demand = Counter(s for j in jobs for s in set(j.skills or []))
    missing = []
    for slug, count in demand.items():
        if slug in skills:
            continue
        pct = round(100 * count / n)
        weighted = pct * IMPORTANCE[category(slug)]  # a certificate matters less than a core skill
        missing.append({
            "slug": slug, "skill": display(slug), "category": category(slug), "demand_pct": pct,
            "priority": "high" if weighted >= 50 else "medium" if weighted >= 25 else "low",
            "_w": weighted,
        })
    missing.sort(key=lambda m: (-m["_w"], CATEGORY_ORDER.index(m["category"])))
    for m in missing:
        m.pop("_w")
    strengths = sorted(
        ({"skill": display(s), "demand_pct": round(100 * c / n)} for s, c in demand.items() if s in skills),
        key=lambda x: -x["demand_pct"],
    )
    needed_years = max((j.min_years for j in jobs), default=0)
    grouped = {GROUPS[c]: [m for m in missing if m["category"] == c] for c in CATEGORY_ORDER}
    return {
        "jobs_analysed": len(jobs),
        "missing": missing,
        "grouped": grouped,
        "strengths": strengths[:8],
        "experience": {
            "your_years": years, "typical_required_years": needed_years,
            "gap_years": max(0.0, round(needed_years - years, 1)),
            "advice": ("Your experience level fits these roles."
                       if years >= needed_years else
                       "Offset the experience gap with projects, internships or volunteering that show real outcomes."),
        },
    }
