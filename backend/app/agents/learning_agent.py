"""Learning Pathway Agent: turns prioritised skill gaps into recommended courses.

For each gap it combines live results (Microsoft Learn, YouTube; see learning_sources.py) with one
trusted pick from the curated catalogue. With no live source available, the full curated list is used.
"""
from ..data.learning import resources_for
from ..learning_sources import live_resources
from ..taxonomy import CATEGORY_ORDER

PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}


def resources_for_gap(slug: str) -> list[dict]:
    curated = [{**r, "origin": "curated"} for r in resources_for(slug)]
    live = [{**r, "skill": slug} for r in live_resources(slug)]
    return live + curated[:1] if live else curated

def suitable_for(res: dict, skill: str, category: str) -> str:
    """One plain sentence on who a recommendation suits, built from its type, level hints and cost."""
    kind = res.get("type")
    if kind == "certification":
        who = f"People who want a recognised credential to prove {skill} to employers"
    elif kind == "lab":
        who = f"Learners who prefer hands-on practice to reading when building {skill}"
    elif kind == "project":
        who = f"People who learn best by building a small real {skill} project for their portfolio"
    elif kind == "practice":
        who = f"Anyone who wants to build {skill} through real workplace situations, not theory"
    elif kind == "video":
        who = f"Visual learners who want a full video walkthrough of {skill}"
    elif category == "soft":
        who = f"Students and graduates who want a structured way to show {skill} in interviews"
    else:
        who = f"Beginners and career changers who need a structured start with {skill}"
    if res.get("hours", 0) <= 3:
        who += "; short enough to finish in an evening"
    elif res.get("hours", 0) >= 30:
        who += "; best if you can commit to longer, steady study"
    return who + "."


def build_plan(missing: list[dict], max_skills: int = 6) -> dict:
    ordered = sorted(missing, key=lambda m: (PRIORITY_RANK[m["priority"]], CATEGORY_ORDER.index(m["category"]), -m["demand_pct"]))
    focus = ordered[:max_skills]
    items, seen_urls = [], set()
    for gap in focus:
        for res in resources_for_gap(gap["slug"]):
            if res["url"] in seen_urls:  # one course can cover two gaps; recommend it once
                continue
            seen_urls.add(res["url"])
            items.append({**res, "skill_name": gap["skill"], "priority": gap["priority"],
                          "suitable_for": suitable_for(res, gap["skill"], gap["category"])})
    return {
        "total_hours": sum(i["hours"] for i in items),
        "focus_skills": [g["skill"] for g in focus],
        "live_sources": sorted({i["provider"].split(" · ")[0] for i in items if i.get("origin") == "live"}),
        "items": items,
    }
