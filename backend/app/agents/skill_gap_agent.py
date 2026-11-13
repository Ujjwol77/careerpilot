"""Skill Gap Analysis Agent.

Compares the candidate with the skills that postings for their target role actually ask for, and
explains every gap: how common it is, how much of the role it unlocks, how close the candidate
already is, and how quickly it can be started. All figures are calculated by rules, never by a model.

Method (each step is shown to the user):
  1. Benchmark  - the pool of postings for the target role (see orchestrator.benchmark_jobs).
  2. Demand     - for every skill, the share of those postings that ask for it.
  3. Gaps       - demanded skills the candidate lacks, tiered by demand (core / common / nice to have),
                  then ranked by demand x skill importance, with a one-level boost when closing the
                  skill finishes the candidate's list for 2 or more postings.
  4. Coverage   - per skill type, how much of the demand the candidate already covers.
  5. Experience - the median years requested (not the maximum, which one senior advert can inflate).
"""
from collections import Counter
from statistics import median

from ..data.learning import resources_for
from ..models import Job
from ..taxonomy import CATEGORY_ORDER, SKILLS, category, display

IMPORTANCE = {"technical": 1.0, "tool": 1.0, "soft": 0.8, "certification": 0.5}
GROUPS = {"technical": "Technical skills", "tool": "Tools", "soft": "Soft skills", "certification": "Certifications"}
TIER_CORE, TIER_COMMON = 60, 30  # demand % at or above which a skill is core / common for the role
QUICK_WIN_HOURS = 8
PRIORITY_ORDER = ["low", "medium", "high"]

# Skills that are close cousins: knowing one makes learning another a short step, not a fresh start.
_FAMILIES = [
    {"sql", "mysql", "postgresql"},
    {"tableau", "power_bi", "excel", "data_viz"},
    {"aws", "azure", "gcp"},
    {"aws_ccp", "az900"},
    {"docker", "kubernetes"},
    {"python", "pandas", "numpy"},
    {"javascript", "typescript", "react", "node"},
    {"django", "flask", "fastapi"},
    {"java", "csharp", "cpp"},
    {"sec_plus", "net_plus", "cissp", "ceh"},
    {"siem", "security_tools", "vuln_assessment", "incident_response"},
    {"network_security", "firewalls", "networking"},
    {"statistics", "machine_learning", "data_cleaning"},
    {"communication", "stakeholder", "leadership", "teamwork"},
]
FAMILIES = [{s for s in fam if s in SKILLS} for fam in _FAMILIES]


def _tier(pct: int) -> str:
    return "core" if pct >= TIER_CORE else "common" if pct >= TIER_COMMON else "nice_to_have"


def _adjacent(slug: str, skills: set[str]) -> str | None:
    """A related skill the candidate already has, if any."""
    for fam in FAMILIES:
        if slug in fam:
            owned = sorted(s for s in fam if s in skills and s != slug)
            if owned:
                return display(owned[0])
    return None


def _quick_start_hours(slug: str) -> int | None:
    hours = [r["hours"] for r in resources_for(slug)]
    return min(hours) if hours else None


def analyse_gaps(skills: set[str], jobs: list[Job], years: float, role_label: str = "") -> dict:
    n = max(len(jobs), 1)
    role = role_label or "target role"
    job_skills = [set(j.skills or []) for j in jobs]
    demand = Counter(s for js in job_skills for s in js)

    # jobs where one particular skill is the only thing missing (closing it completes the list)
    only_missing: Counter = Counter()
    for js in job_skills:
        lacking = [s for s in js if s not in skills]
        if len(lacking) == 1:
            only_missing[lacking[0]] += 1

    missing = []
    for slug, count in demand.items():
        if slug in skills:
            continue
        pct = round(100 * count / n)
        cat = category(slug)
        weighted = pct * IMPORTANCE[cat]
        priority = "high" if weighted >= 50 else "medium" if weighted >= 25 else "low"
        unlocks = only_missing[slug]
        boosted = unlocks >= 2 and priority != "high"
        if boosted:
            priority = PRIORITY_ORDER[PRIORITY_ORDER.index(priority) + 1]
        adjacent = _adjacent(slug, skills)
        hours = _quick_start_hours(slug)
        why = [f"Asked for in {count} of {len(jobs)} {role} postings ({pct}%)."]
        if unlocks:
            why.append(f"It is the only skill missing for {unlocks} of them.")
        if adjacent:
            why.append(f"You already know {adjacent}, which is closely related.")
        if hours is not None:
            why.append(f"A first course takes about {hours}h.")
        missing.append({
            "slug": slug, "skill": display(slug), "category": cat, "demand_pct": pct, "jobs_asking": count,
            "tier": _tier(pct), "priority": priority, "unlocks": unlocks, "adjacent": adjacent,
            "start_hours": hours, "quick_win": hours is not None and hours <= QUICK_WIN_HOURS,
            "why": " ".join(why), "_impact": weighted + 8 * unlocks,
        })
    missing.sort(key=lambda m: (-PRIORITY_ORDER.index(m["priority"]), -m["_impact"], CATEGORY_ORDER.index(m["category"]), m["skill"]))
    for m in missing:
        m.pop("_impact")

    have = [{"skill": display(s), "demand_pct": round(100 * c / n)} for s, c in demand.items() if s in skills]
    strengths = sorted(have, key=lambda x: (-x["demand_pct"], x["skill"]))
    extras = sorted(display(s) for s in skills if s not in demand)

    # coverage: how much of the demand in each skill type the candidate already covers
    coverage = []
    total_w = covered_w = 0.0
    for cat in CATEGORY_ORDER:
        wanted = {s: c for s, c in demand.items() if category(s) == cat}
        if not wanted:
            continue
        all_d, own_d = sum(wanted.values()), sum(c for s, c in wanted.items() if s in skills)
        coverage.append({
            "category": cat, "label": GROUPS[cat], "coverage_pct": round(100 * own_d / all_d),
            "have": sum(1 for s in wanted if s in skills), "wanted": len(wanted),
        })
        total_w += IMPORTANCE[cat] * all_d
        covered_w += IMPORTANCE[cat] * own_d
    overall = round(100 * covered_w / total_w) if total_w else 0

    core_gaps = [m for m in missing if m["tier"] == "core"]
    quick = [m for m in missing if m["quick_win"]]
    headline = (f"You already cover {overall}% of what {role} postings ask for, "
                f"with {len(missing)} gap{'s' if len(missing) != 1 else ''} to close"
                f"{f' ({len(core_gaps)} core)' if core_gaps else ''}.") if jobs else "No postings to compare with yet."
    if missing:
        top = missing[0]
        next_step = f"Start with {top['skill']}: " + top["why"]
    else:
        next_step = "No gaps against these postings. Focus on your CV wording and interview practice."

    years_asked = [j.min_years for j in jobs]
    typical = float(median(years_asked)) if years_asked else 0.0
    meets = round(100 * sum(1 for y in years_asked if years >= y) / n) if years_asked else 0
    avg_skills = round(sum(len(js) for js in job_skills) / n, 1)
    low_conf = len(jobs) < 8 or avg_skills < 3
    grouped = {GROUPS[c]: [m for m in missing if m["category"] == c] for c in CATEGORY_ORDER}
    return {
        "jobs_analysed": len(jobs),
        "role": role,
        "headline": headline,
        "next_step": next_step,
        "overall_coverage_pct": overall,
        "coverage": coverage,
        "missing": missing,
        "grouped": grouped,
        "strengths": strengths[:8],
        "extras": extras[:8],
        "quick_wins": [m["skill"] for m in quick[:3]],
        "confidence": {
            "level": "low" if low_conf else "good", "avg_skills_per_job": avg_skills,
            "note": ("Few postings, or short adverts with few detectable skills, so treat percentages as rough."
                     if low_conf else "Based on enough postings with detailed skill lists."),
        },
        "experience": {
            "your_years": years, "typical_required_years": typical,
            "range": [min(years_asked), max(years_asked)] if years_asked else [0, 0],
            "meets_pct": meets, "gap_years": max(0.0, round(typical - years, 1)),
            "advice": ("Your experience meets the typical requirement for these roles."
                       if years >= typical else
                       "Offset the experience gap with projects, internships or volunteering that show real outcomes."),
        },
    }
