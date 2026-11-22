"""Profile Understanding Agent: CV text -> structured profile (skills, education, experience, roles)."""
import re
from datetime import date

from ..data.seed_jobs import ROLE_PROFILES
from ..taxonomy import SKILLS, extract_skills
from ..utils import BULLET_CHARS

HEADINGS = {
    "summary": {"summary", "profile", "objective", "about me", "career objective", "professional summary"},
    "experience": {"experience", "work experience", "employment", "employment history", "work history", "professional experience"},
    "education": {"education", "qualifications", "academic background"},
    "skills": {"skills", "technical skills", "key skills", "core competencies"},
    "projects": {"projects", "personal projects", "academic projects"},
    "certifications": {"certifications", "certificates", "licenses", "licences"},
}
_DEGREE = re.compile(r"\b(bachelor|master|phd|doctorate|diploma|associate degree|certificate (iii|iv)|b\.?sc|m\.?sc|b\.?eng|bit|mit)\b", re.I)
# A date range such as "2021 - 2023", "Jan 2024 – May 2025", "06/2025 - Present". Months are optional.
_MONTH = r"(?:(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+|(\d{1,2})\s*/\s*)?"
_RANGE = re.compile(_MONTH + r"((?:19|20)\d{2})\s*(?:-|–|—|to)\s*" + _MONTH + r"((?:19|20)\d{2}|present|current|now)\b", re.I)
_MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
# A figure the candidate states, e.g. "1.5 years of hands-on experience", "5+ years' experience".
_NUMBER_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
_STATED = re.compile(r"\b(\d{1,2}(?:\.\d)?|" + "|".join(_NUMBER_WORDS) + r")\s*\+?\s*(?:years?|yrs?)['’]?\s+(?:of\s+)?(?:[a-z-]+\s+){0,3}?experience", re.I)


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


def _month(name: str | None, number: str | None) -> int | None:
    if name:
        return _MONTHS.index(name.lower()[:3]) + 1
    if number and 1 <= int(number) <= 12:
        return int(number)
    return None


def estimate_years(text: str, today_year: int | None = None, today_month: int | None = None) -> float:
    """Years covered by the date ranges in the text, overlaps merged, to one decimal place.

    Counted in months: "Jan 2024 – May 2025" is 17 months (both months included). Ranges with years
    only count whole years ("2021 - 2023" = 2). "Present" means the current month (or the current
    year when the start has no month).
    """
    today = date.today()
    year_now = today_year or today.year
    month_now = today_month or (today.month if today_year in (None, today.year) else 12)
    spans = []
    for m in _RANGE.finditer(text):
        s_month, e_month = _month(m.group(1), m.group(2)), _month(m.group(4), m.group(5))
        s_year, end_raw = int(m.group(3)), m.group(6).lower()
        start = s_year * 12 + (s_month - 1 if s_month else 0)
        if end_raw in {"present", "current", "now"}:
            end = year_now * 12 + (month_now if s_month else 0)
        else:
            end = int(end_raw) * 12 + (e_month or 0)
        if 1970 * 12 <= start < end <= year_now * 12 + month_now and end - start <= 45 * 12:
            spans.append((start, end))
    spans.sort()
    months, cur_s, cur_e = 0, None, None
    for s, e in spans:
        if cur_s is None:
            cur_s, cur_e = s, e
        elif s <= cur_e:
            cur_e = max(cur_e, e)
        else:
            months += cur_e - cur_s
            cur_s, cur_e = s, e
    if cur_s is not None:
        months += cur_e - cur_s
    return round(months / 12, 1)


def stated_years(text: str) -> float | None:
    """The years of experience the candidate states in their own words, if any."""
    m = _STATED.search(text)
    if not m:
        return None
    raw = m.group(1).lower()
    value = float(_NUMBER_WORDS.get(raw, raw))
    return value if 0 < value <= 50 else None


def experience_years(text: str, sections: dict[str, str] | None = None) -> dict:
    """Years of experience and where the figure came from.

    A figure stated in the summary wins, because the candidate knows things dates can't show
    (part-time work, gaps). Otherwise the job dates in the experience section are added up.
    """
    sections = sections if sections is not None else split_sections(text)
    from_dates = estimate_years(sections.get("experience") or text)
    stated = stated_years(sections.get("summary") or sections.get("header") or "")
    if stated is not None:
        return {"years": stated, "source": "stated", "stated": stated, "from_dates": from_dates}
    return {"years": from_dates, "source": "dates" if from_dates else "none", "stated": None, "from_dates": from_dates}


# Signals used to tell a CV apart from other documents (reports, cover letters, job adverts).
_REPORT_HEADINGS = {"abstract", "introduction", "conclusion", "conclusions", "references", "bibliography", "reference list",
                    "table of contents", "contents", "methodology", "methods", "literature review", "appendix", "appendices",
                    "executive summary", "discussion", "results", "findings", "recommendations", "background"}
_ADVERT_HEADINGS = {"responsibilities", "requirements", "about the role", "about you", "about us", "what you'll do",
                    "what you will do", "how to apply", "key responsibilities", "selection criteria", "benefits"}
_HEADING_PREFIX = re.compile(r"^\s*(?:\d+(?:\.\d+)*\.?\s+)?")  # "1.", "2.3 " numbering on report headings
_CITATION = re.compile(r"\([A-Z][A-Za-z'-]+(?: et al\.?| (?:&|and) [A-Z][A-Za-z'-]+)?,? (?:19|20)\d{2}[a-z]?\)|\bet al\.")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE = re.compile(r"(?:\+?\d[\d ()-]{7,}\d)")


def cv_check(text: str) -> dict:
    """Does this text look like a CV? Rule-based, so it works without the language model.

    Points for: CV headings (Experience, Education, Skills, Summary, Projects, Certifications; up to 3),
    contact details near the top, employment or study date ranges, 5 or more recognised skills.
    Points against: report headings (Introduction, References...), academic citations, a letter
    greeting, job-advert headings, more than 2,500 words. A score of 2 or more is accepted.
    """
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    headings = {_HEADING_PREFIX.sub("", l).rstrip(":").lower() for l in lines if len(l) <= 40}
    cv_heads = sorted(k for k in split_sections(text) if k != "header")
    top = "\n".join(lines[:15])
    has_contact = bool(_EMAIL.search(top) or _PHONE.search(top))
    has_dates = bool(_RANGE.search(text))
    n_skills = len(extract_skills(text))
    report_heads = sorted(headings & _REPORT_HEADINGS)
    advert_heads = sorted(headings & _ADVERT_HEADINGS)
    citations = len(_CITATION.findall(text))
    letter = any(re.match(r"dear\b", l, re.I) for l in lines[:25])
    words = len(text.split())

    score = min(len(cv_heads), 3) + has_contact + has_dates + (n_skills >= 5)
    against = []
    if len(report_heads) >= 2:
        score -= 2
        against.append(f"it has report headings ({', '.join(h.title() for h in report_heads[:4])})")
    if citations >= 3:
        score -= 1
        against.append(f"it cites {citations} sources like an essay")
    if letter:
        score -= 2
        against.append("it starts like a letter (\"Dear ...\"), so it may be a cover letter")
    if len(advert_heads) >= 2:
        score -= 2
        against.append(f"it reads like a job advert ({', '.join(h.title() for h in advert_heads[:3])})")
    if words > 2500:
        score -= 1
        against.append(f"it is {words:,} words long; most CVs are under 1,500")
    missing = [m for m, ok in [("no Experience, Education or Skills heading", bool(set(cv_heads) & {"experience", "education", "skills"})),
                               ("no email or phone number near the top", has_contact),
                               ("no dates for jobs or study", has_dates)] if not ok]
    return {"is_cv": score >= 2, "score": score, "cv_headings": cv_heads, "has_contact": has_contact,
            "has_dates": has_dates, "skills_found": n_skills, "against": against, "missing": missing}


def _name_guess(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line:
            ok = len(line.split()) <= 5 and not re.search(r"[\d@:/]", line) and line.lower() not in {h for hs in HEADINGS.values() for h in hs}
            return line if ok else ""
    return ""


ROLE_CORE_WEIGHT, ROLE_EXTRA_WEIGHT = 0.7, 0.3


def infer_roles(have: set[str]) -> list[dict]:
    """Score each role by the CV's skills: 70% for the role's core skills, 30% for its useful extras."""
    scored = []
    for key, role in ROLE_PROFILES.items():
        core_have = [s for s in role["core"] if s in have]
        extra_have = [s for s in role["extras"] if s in have]
        score = (ROLE_CORE_WEIGHT * len(core_have) / len(role["core"])
                 + ROLE_EXTRA_WEIGHT * len(extra_have) / len(role["extras"]))
        scored.append({"role": key, "label": role["label"], "score": round(score * 100)})
    return sorted(scored, key=lambda r: -r["score"])


def role_fit_detail(have: set[str]) -> list[dict]:
    """The working behind infer_roles, for the "roles that fit" explanation on the profile page."""
    out = []
    for r in infer_roles(have):
        role = ROLE_PROFILES[r["role"]]
        out.append({**r,
                    "core_have": sum(1 for s in role["core"] if s in have), "core_total": len(role["core"]),
                    "extra_have": sum(1 for s in role["extras"] if s in have), "extra_total": len(role["extras"]),
                    "core_missing": [SKILLS[s].display for s in role["core"] if s not in have and s in SKILLS]})
    return out


def analyse_cv(text: str) -> dict:
    sections = split_sections(text)
    slugs = extract_skills(text)
    education = [l.strip() for l in sections.get("education", "").splitlines() if l.strip()][:5]
    if not education:
        education = [l.strip() for l in text.splitlines() if _DEGREE.search(l)][:5]
    experience = [l.strip(" \t" + BULLET_CHARS) for l in sections.get("experience", "").splitlines() if l.strip()][:10]
    summary = sections.get("summary", "")[:500]
    years = experience_years(text, sections)
    return {
        "name_guess": _name_guess(text),
        "summary": summary,
        "skills": [{"slug": s, "name": SKILLS[s].display, "category": SKILLS[s].category} for s in slugs],
        "education": education,
        "experience": experience,
        "years_experience": years["years"],
        "years_detail": years,
        "sections_found": sorted(k for k in sections if k != "header"),
        "word_count": len(text.split()),
        "inferred_roles": infer_roles(set(slugs)),
    }
