"""Profile Understanding Agent: CV text -> structured profile (skills, education, experience, roles)."""
import re
from datetime import date

from ..data.seed_jobs import ROLE_PROFILES
from ..taxonomy import SKILLS, extract_skills

HEADINGS = {
    "summary": {"summary", "profile", "objective", "about me", "career objective", "professional summary"},
    "experience": {"experience", "work experience", "employment", "employment history", "work history", "professional experience"},
    "education": {"education", "qualifications", "academic background"},
    "skills": {"skills", "technical skills", "key skills", "core competencies"},
    "projects": {"projects", "personal projects", "academic projects"},
    "certifications": {"certifications", "certificates", "licenses", "licences"},
}
_DEGREE = re.compile(r"\b(bachelor|master|phd|doctorate|diploma|associate degree|certificate (iii|iv)|b\.?sc|m\.?sc|b\.?eng|bit|mit)\b", re.I)
_RANGE = re.compile(r"((?:19|20)\d{2})\s*(?:-|–|—|to)\s*((?:19|20)\d{2}|present|current|now)", re.I)


def split_sections(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current = "header"
    for line in text.splitlines():
        key = line.strip().rstrip(":").lower()
        match = next((name for name, names in HEADINGS.items() if key in names), None)
        if match:
            current = match
            sections.setdefault(current, [])
        else:
            sections.setdefault(current, []).append(line)
    return {k: "\n".join(v).strip() for k, v in sections.items() if "\n".join(v).strip()}


def estimate_years(text: str, today_year: int | None = None) -> float:
    year_now = today_year or date.today().year
    spans = []
    for m in _RANGE.finditer(text):
        start = int(m.group(1))
        end_raw = m.group(2).lower()
        end = year_now if end_raw in {"present", "current", "now"} else int(end_raw)
        if 1970 <= start <= end <= year_now and end - start <= 45:
            spans.append((start, end))
    spans.sort()
    total, cur_s, cur_e = 0, None, None
    for s, e in spans:
        if cur_s is None:
            cur_s, cur_e = s, e
        elif s <= cur_e:
            cur_e = max(cur_e, e)
        else:
            total += cur_e - cur_s
            cur_s, cur_e = s, e
    if cur_s is not None:
        total += cur_e - cur_s
    return float(total)


def _name_guess(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line:
            ok = len(line.split()) <= 5 and not re.search(r"[\d@:/]", line) and line.lower() not in {h for hs in HEADINGS.values() for h in hs}
            return line if ok else ""
    return ""


def infer_roles(have: set[str]) -> list[dict]:
    scored = []
    for key, role in ROLE_PROFILES.items():
        core = len(have & set(role["core"])) / len(role["core"])
        extra = len(have & set(role["extras"])) / len(role["extras"])
        scored.append({"role": key, "label": role["label"], "score": round((core * 0.7 + extra * 0.3) * 100)})
    return sorted(scored, key=lambda r: -r["score"])


def analyse_cv(text: str) -> dict:
    sections = split_sections(text)
    slugs = extract_skills(text)
    exp_text = sections.get("experience") or text
    education = [l.strip() for l in sections.get("education", "").splitlines() if l.strip()][:5]
    if not education:
        education = [l.strip() for l in text.splitlines() if _DEGREE.search(l)][:5]
    experience = [l.strip(" -•*\t") for l in sections.get("experience", "").splitlines() if l.strip()][:10]
    summary = sections.get("summary", "")[:500]
    return {
        "name_guess": _name_guess(text),
        "summary": summary,
        "skills": [{"slug": s, "name": SKILLS[s].display, "category": SKILLS[s].category} for s in slugs],
        "education": education,
        "experience": experience,
        "years_experience": estimate_years(exp_text),
        "sections_found": sorted(k for k in sections if k != "header"),
        "word_count": len(text.split()),
        "inferred_roles": infer_roles(set(slugs)),
    }
