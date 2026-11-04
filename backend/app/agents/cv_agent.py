"""CV Optimisation Agent: ATS-style checks plus job-specific keyword advice.

Rule: it never tells users to add skills they do not have. Missing keywords are framed as
"add only if genuine, otherwise see your learning plan".
"""
import re

from ..llm import try_llm
from ..models import Job
from ..taxonomy import category, display
from .profile_agent import split_sections

ACTION_VERBS = {
    "built", "created", "designed", "developed", "implemented", "led", "managed", "analysed", "analyzed",
    "improved", "reduced", "increased", "automated", "delivered", "launched", "optimised", "optimized",
    "deployed", "resolved", "investigated", "trained", "coordinated", "migrated", "tested", "configured",
}
WEAK = ["responsible for", "duties included", "worked on", "helped with", "assisted with", "involved in"]
_BULLET = re.compile(r"^\s*(?:[-•*·▪]|\d+[.)])\s+(.*\S)")


def _bullets(text: str) -> list[str]:
    return [m.group(1) for line in text.splitlines() if (m := _BULLET.match(line))]


def optimise_cv(text: str, skills: set[str], target: Job | None) -> dict:
    sections = split_sections(text)
    words = len(text.split())
    bullets = _bullets(text)
    suggestions: list[dict] = []
    penalty = 0.0

    def add(sev, area, msg, cost):
        nonlocal penalty
        suggestions.append({"severity": sev, "area": area, "message": msg})
        penalty += cost

    for name, label in [("summary", "professional summary"), ("skills", "skills section"),
                        ("experience", "work experience section"), ("education", "education section")]:
        if name not in sections:
            add("high" if name in {"experience", "skills"} else "medium", "structure",
                f"Add a clearly labelled {label}; recruiters and ATS software look for standard headings.", 8)
    if not re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text):
        add("medium", "contact", "Add a professional email address near the top of the CV.", 5)
    if words < 250:
        add("medium", "length", f"The CV is short ({words} words). Add detail on projects and outcomes.", 5)
    elif words > 900:
        add("low", "length", f"The CV is long ({words} words). Aim for one to two pages.", 4)

    if not bullets:
        add("high", "format", "Use bullet points under each role or project so achievements are easy to scan.", 10)
    else:
        quantified = sum(1 for b in bullets if re.search(r"\d", b)) / len(bullets)
        if quantified < 0.3:
            add("high", "impact", f"Only {round(quantified * 100)}% of bullets contain numbers. "
                "Add scale and results (time saved, % improved, users, volume).", 10)
        verbs = sum(1 for b in bullets if b.split()[0].lower().strip(",.") in ACTION_VERBS) / len(bullets)
        if verbs < 0.5:
            add("medium", "wording", "Start bullets with strong action verbs (built, reduced, led, automated).", 8)
    weak_hits = [p for p in WEAK if p in text.lower()]
    if weak_hits:
        add("medium", "wording", f"Replace passive phrases ({', '.join(repr(w) for w in weak_hits)}) with what you achieved.", 5)

    coverage = 1.0
    missing_keywords: list[str] = []
    if target:
        required = [s for s in (target.skills or []) if category(s) in {"technical", "tool"}]
        missing_keywords = [display(s) for s in required if s not in skills]
        coverage = 1 - len(missing_keywords) / max(len(required), 1)
        if missing_keywords:
            add("high", "keywords",
                f"For '{target.title}', the posting mentions: {', '.join(missing_keywords[:6])}. "
                "Add these only where you have genuine experience; otherwise see your Learning plan.", 25 * (1 - coverage))
        if target.title.lower() not in text.lower():
            add("low", "alignment", f"Mirror the target job title ('{target.title}') in your summary if it describes your goal.", 3)

    weak_bullets = [b for b in bullets if any(w in b.lower() for w in WEAK) or not re.search(r"\d", b)][:3]
    fallback = "\n".join(
        f"Rewrite: '{b[:90]}' -> start with an action verb and add a result, e.g. 'Improved <process> by [X%] by <what you did>'."
        for b in weak_bullets
    )
    rewrites, source = try_llm("cv_rewrite.v1", fallback, role=target.title if target else "target role", bullets="\n".join(weak_bullets))

    return {
        "ats_score": max(0, round(100 - penalty)),
        "word_count": words,
        "bullet_count": len(bullets),
        "keyword_coverage": round(coverage, 2),
        "missing_keywords": missing_keywords,
        "suggestions": sorted(suggestions, key=lambda s: {"high": 0, "medium": 1, "low": 2}[s["severity"]]),
        "rewrite_examples": [r for r in rewrites.splitlines() if r.strip()],
        "rewrite_source": source,
        "target_job": {"id": target.id, "title": target.title, "company": target.company} if target else None,
    }
