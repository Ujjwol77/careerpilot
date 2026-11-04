"""Report Agent: combines every agent's output into the career readiness report."""
from datetime import datetime, timezone

from ..llm import try_llm
from .job_match_agent import readiness_band


def build_report(*, name: str, target_label: str, matches: list[dict], cv: dict, gaps: dict,
                 learning: dict, interview: dict, trace: list[dict]) -> dict:
    top = matches[:5]
    readiness = round(sum(m["score"] for m in top[:3]) / max(len(top[:3]), 1), 1)
    top_gap = gaps["missing"][0]["skill"] if gaps["missing"] else "none identified"
    best = top[0] if top else None
    fallback = (
        (f"Your best current match is {best['title']} at {best['company']} ({best['score']}%). " if best else "No matching jobs were found yet. ")
        + f"The biggest skill gap across your top matches is {top_gap}. "
        + (f"Following the {learning['total_weeks']}-week plan is the fastest way to raise your readiness." if learning["total_weeks"] else "Focus on polishing your CV and interview answers.")
    )
    facts = f"readiness={readiness}; best={best['title'] if best else 'n/a'}; gap={top_gap}; ats={cv['ats_score']}; weeks={learning['total_weeks']}"
    summary, source = try_llm("report_summary.v1", fallback, facts=facts)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "candidate": name,
        "target_role": target_label,
        "readiness_score": readiness,
        "readiness_band": readiness_band(readiness),
        "summary": summary,
        "summary_source": source,
        "top_jobs": [{k: m[k] for k in ("job_id", "title", "company", "location", "score", "readiness", "matched_skills", "missing_skills")} for m in top],
        "cv": {k: cv[k] for k in ("ats_score", "keyword_coverage", "missing_keywords", "suggestions", "rewrite_examples", "target_job")},
        "skill_gaps": {"missing": gaps["missing"][:12], "strengths": gaps["strengths"], "experience": gaps["experience"]},
        "learning": {k: learning[k] for k in ("hours_per_week", "total_hours", "total_weeks", "focus_skills", "weeks")},
        "interview": interview,
        "agent_trace": trace,
    }
