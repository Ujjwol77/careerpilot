"""CV Optimisation Agent: ATS-style checks plus job-specific keyword advice.

Every check is reported, passed or not, with what was measured, the target, the points it
cost and why it matters, so the ATS score is fully explained:
    ATS score = 100 - sum(points lost on each check)
Suggestions are ranked by the points a fix would win back (largest first), then severity.

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
SEVERITY_RANK = {"high": 0, "medium": 1, "low": 2}

# Targets used by the checks (shown to the user as the benchmark for each check).
MIN_WORDS, MAX_WORDS = 250, 900
MIN_QUANTIFIED, MIN_ACTION_VERBS = 0.30, 0.50
KEYWORD_POINTS = 25


def _bullets(text: str) -> list[str]:
    return [m.group(1) for line in text.splitlines() if (m := _BULLET.match(line))]


def _pct(x: float) -> str:
    return f"{round(x * 100)}%"


def optimise_cv(text: str, skills: set[str], target: Job | None) -> dict:
    sections = split_sections(text)
    words = len(text.split())
    bullets = _bullets(text)
    checks: list[dict] = []

    def check(cid, label, area, found, goal, why, lost, max_loss, severity=None, message=None):
        checks.append({
            "id": cid, "label": label, "area": area, "found": found, "target": goal, "why": why,
            "points_lost": round(lost, 1), "max_points": max_loss, "passed": lost == 0,
            "severity": severity if lost else None, "message": message if lost else None,
        })

    # 1. Standard section headings (8 points each)
    for name, label in [("experience", "Work experience"), ("skills", "Skills"),
                        ("summary", "Professional summary"), ("education", "Education")]:
        present = name in sections
        check(f"section_{name}", f"{label} heading", "structure", "found" if present else "missing", "present",
              "ATS software and recruiters look for standard headings to find each part of your CV.",
              0 if present else 8, 8, "high" if name in {"experience", "skills"} else "medium",
              f"Add a clearly labelled {label.lower()} section.")

    # 2. Contact email (5)
    has_email = bool(re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text))
    check("contact", "Email address", "contact", "found" if has_email else "missing", "present",
          "Recruiters can't contact you without it, and some ATS reject CVs with no email.",
          0 if has_email else 5, 5, "medium", "Add a professional email address near the top of the CV.")

    # 3. Length (5 short / 4 long)
    if words < MIN_WORDS:
        lost, sev, msg = 5, "medium", f"Your CV has {words} words. Add detail on projects, tools used and outcomes to reach at least {MIN_WORDS}."
    elif words > MAX_WORDS:
        lost, sev, msg = 4, "low", f"Your CV has {words} words. Trim to one or two pages (under {MAX_WORDS} words)."
    else:
        lost, sev, msg = 0, None, None
    check("length", "Length", "length", f"{words} words", f"{MIN_WORDS}–{MAX_WORDS} words",
          "Too short gives little evidence of your skills; too long hides the important parts.",
          lost, 5, sev, msg)

    # 4–6. Bullets, numbers, action verbs
    check("bullets", "Bullet points", "format", f"{len(bullets)} bullets", "at least 1",
          "Bullets make achievements quick to scan; recruiters skim CVs in seconds.",
          0 if bullets else 10, 10, "high", "Use bullet points under each role or project.")
    if bullets:
        quantified = sum(1 for b in bullets if re.search(r"\d", b)) / len(bullets)
        check("numbers", "Bullets with numbers", "impact", _pct(quantified), f"at least {_pct(MIN_QUANTIFIED)}",
              "Numbers (time saved, % improved, users, volume) prove impact instead of just listing duties.",
              10 if quantified < MIN_QUANTIFIED else 0, 10, "high",
              f"Only {_pct(quantified)} of your bullets contain a number. Add scale or results to more of them.")
        verbs = sum(1 for b in bullets if b.split()[0].lower().strip(",.") in ACTION_VERBS) / len(bullets)
        check("verbs", "Bullets starting with an action verb", "wording", _pct(verbs), f"at least {_pct(MIN_ACTION_VERBS)}",
              "Starting with a verb (built, reduced, led) shows what you did, not just what you were assigned.",
              8 if verbs < MIN_ACTION_VERBS else 0, 8, "medium",
              "Start more bullets with strong action verbs such as built, reduced, led or automated.")

    # 7. Passive phrases (5)
    weak_hits = [p for p in WEAK if p in text.lower()]
    check("passive", "Passive phrases", "wording", ", ".join(f"'{w}'" for w in weak_hits) or "none", "none",
          "Phrases like 'responsible for' describe duties, not results, and read as filler to recruiters.",
          5 if weak_hits else 0, 5, "medium",
          f"Replace {', '.join(repr(w) for w in weak_hits)} with what you actually achieved.")

    # 8–9. Target job alignment
    coverage, missing_keywords, required = 1.0, [], []
    if target:
        required = [s for s in (target.skills or []) if category(s) in {"technical", "tool"}]
        missing_keywords = [display(s) for s in required if s not in skills]
        coverage = 1 - len(missing_keywords) / max(len(required), 1)
        check("keywords", "Job keywords in your CV", "keywords",
              f"{len(required) - len(missing_keywords)} of {len(required)} ({_pct(coverage)})", "100%",
              "ATS ranks CVs by how many of the advert's skills they mention; missing ones lower your rank.",
              KEYWORD_POINTS * (1 - coverage), KEYWORD_POINTS, "high",
              f"The advert asks for {', '.join(missing_keywords[:6])}. Add these only where you have genuine experience; otherwise see your Learning plan.")
        titled = target.title.lower() in text.lower()
        check("title", "Target job title in CV", "alignment", "found" if titled else "not found", f"'{target.title}'",
              "Recruiters and ATS search by job title, so using the same title helps your CV surface.",
              0 if titled else 3, 3, "low",
              f"Use the title '{target.title}' in your summary if it describes the role you want.")

    failed = [c for c in checks if not c["passed"]]
    suggestions = sorted(
        [{"severity": c["severity"], "area": c["area"], "message": c["message"], "points": c["points_lost"],
          "found": c["found"], "target": c["target"], "why": c["why"], "check": c["label"]} for c in failed],
        key=lambda s: (-s["points"], SEVERITY_RANK[s["severity"]]),
    )

    # Rewrites: the weakest bullets (passive phrase or no number), with the reason each was chosen.
    picked = []
    for b in bullets:
        reasons = []
        hit = next((w for w in WEAK if w in b.lower()), None)
        if hit:
            reasons.append(f"starts with a passive phrase ('{hit}')")
        if not re.search(r"\d", b):
            reasons.append("has no number or result")
        if reasons:
            picked.append((b, hit, reasons))
    picked = picked[:3]
    fallback_lines = []
    for b, hit, _ in picked:
        rest = re.sub(re.escape(hit), "", b, count=1, flags=re.I).strip(" ,.") if hit else b.rstrip(".")
        if rest.split()[0].lower().strip(",.") in ACTION_VERBS:  # already starts with a strong verb: only add the result
            fallback_lines.append(f"{rest[:1].upper() + rest[1:]}, resulting in [measurable result, e.g. X% faster].")
        else:
            fallback_lines.append(f"[Action verb] {rest[:1].lower() + rest[1:]}, resulting in [measurable result, e.g. X% faster].")
    rewrites, source = try_llm("cv_rewrite.v1", "\n".join(fallback_lines),
                               role=target.title if target else "target role", bullets="\n".join(b for b, _, _ in picked))
    after_lines = [re.sub(r"^\s*(?:[-•*]|\d+[.)])\s*", "", r).strip() for r in rewrites.splitlines() if r.strip()]
    rewrite_pairs = [
        {"before": b, "after": after_lines[i] if i < len(after_lines) else "", "why": reasons}
        for i, (b, _, reasons) in enumerate(picked) if i < len(after_lines)
    ]

    lost_total = sum(c["points_lost"] for c in checks)
    return {
        "ats_score": max(0, round(100 - lost_total)),
        "score_breakdown": {"start": 100, "deductions": [{"check": c["label"], "points": c["points_lost"]} for c in suggestions_order(failed)],
                            "passed": sum(1 for c in checks if c["passed"]), "total_checks": len(checks)},
        "checks": checks,
        "word_count": words,
        "bullet_count": len(bullets),
        "keyword_coverage": round(coverage, 2),
        "missing_keywords": missing_keywords,
        "suggestions": suggestions,
        "rewrites": rewrite_pairs,
        "rewrite_examples": after_lines,
        "rewrite_source": source,
        "target_job": {"id": target.id, "title": target.title, "company": target.company} if target else None,
    }


def suggestions_order(failed: list[dict]) -> list[dict]:
    return sorted(failed, key=lambda c: (-c["points_lost"], SEVERITY_RANK[c["severity"]]))
