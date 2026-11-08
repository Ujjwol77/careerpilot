"""Learning Pathway Agent: turns prioritised skill gaps into a week-by-week plan.

For each gap it combines live results (Microsoft Learn, YouTube; see learning_sources.py) with one
trusted pick from the curated catalogue. With no live source available, the full curated list is used.
"""
import math

from ..data.learning import resources_for
from ..learning_sources import live_resources
from ..taxonomy import CATEGORY_ORDER

PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}


def resources_for_gap(slug: str) -> list[dict]:
    curated = [{**r, "origin": "curated"} for r in resources_for(slug)]
    live = [{**r, "skill": slug} for r in live_resources(slug)]
    return live + curated[:1] if live else curated

def build_plan(missing: list[dict], hours_per_week: int = 8, max_skills: int = 6) -> dict:
    hours_per_week = max(1, min(hours_per_week, 40))
    ordered = sorted(missing, key=lambda m: (PRIORITY_RANK[m["priority"]], CATEGORY_ORDER.index(m["category"]), -m["demand_pct"]))
    focus = ordered[:max_skills]
    items, cursor, seen_urls = [], 0, set()
    for gap in focus:
        for res in resources_for_gap(gap["slug"]):
            if res["url"] in seen_urls:  # one course can cover two gaps; schedule it once
                continue
            seen_urls.add(res["url"])
            start_week = math.floor(cursor / hours_per_week) + 1
            cursor += res["hours"]
            end_week = math.ceil(cursor / hours_per_week)
            items.append({**res, "skill_name": gap["skill"], "priority": gap["priority"],
                          "start_week": start_week, "end_week": max(start_week, end_week)})
    total_hours = sum(i["hours"] for i in items)
    weeks = {}
    for item in items:
        weeks.setdefault(item["start_week"], []).append(item)
    return {
        "hours_per_week": hours_per_week,
        "total_hours": total_hours,
        "total_weeks": math.ceil(total_hours / hours_per_week) if total_hours else 0,
        "focus_skills": [g["skill"] for g in focus],
        "live_sources": sorted({i["provider"].split(" · ")[0] for i in items if i.get("origin") == "live"}),
        "items": items,
        "weeks": [{"week": w, "items": weeks[w]} for w in sorted(weeks)],
    }