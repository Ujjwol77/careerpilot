"""How a commercial ATS parser reads the user's CV.

Providers (the first one with a key in backend/.env is used):
- APILayer Resume Parser (free plan: 100 parses a month, no card): POST https://api.apilayer.com/resume_parser/upload
  with the raw file as the body and an "apikey" header; returns name, email, skills, education, experience.
  Docs: https://marketplace.apilayer.com/resume_parser-api
- Eden AI: one API key for several commercial resume parsers; default model Affinda.
  POST {base}/upload (multipart "file") -> file_id, then POST {base}/universal-ai
  {"model": "ocr/resume_parser/affinda", "input": {"file": file_id}} -> output.extracted_data.
  Docs: https://www.edenai.co/docs/v3/expert-models/features/ocr/resume-parser
- Textkernel Tx v10 Resume Parser (alternative).

Real applicant tracking systems first PARSE a CV into fields (name, contact details, jobs with titles
and dates, education, skills). If the parser misses something, the ATS never sees it, however good
the CV is. CareerPilot's own checks only see extracted text, so they can't tell when a layout
(columns, tables, text boxes, headers) confuses a parser. This module sends the original file to
Textkernel, an industry resume parser, and compares what it read with what CareerPilot read.

- Only on request: the user presses "Check with Textkernel" (consent to send the file; 1 credit).
- Cached: the summary is stored with that CV (cv_documents.ats_read), so it is never re-parsed.
- Only a summary is kept, not the parser's full response.
- Textkernel's "ResumeQuality" output is not used: its docs say to ignore it unless approved by them.
API: POST {base}/parser/resume, headers Tx-AccountId and Tx-ServiceKey,
body {DocumentAsBase64String, DocumentLastModified}. Docs: https://developer.textkernel.com/tx-platform/v10/
"""
import base64
import logging
import re
from datetime import date

import httpx

from .config import settings
from .utils import BULLET_CHARS

log = logging.getLogger("careerpilot.ats_parser")
ENGINE = "Textkernel Tx v10 Resume Parser"
NOT_SET_UP = "No ATS parser is set up. Add APILAYER_API_KEY (free) to backend/.env."


class AtsParserError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def provider() -> str | None:
    if settings.apilayer_api_key:
        return "apilayer"
    if settings.edenai_api_key:
        return "edenai"
    if settings.textkernel_account_id and settings.textkernel_service_key:
        return "textkernel"
    return None


def configured() -> bool:
    return provider() is not None


def label() -> str:
    """Name shown to the user, e.g. 'Eden AI (Affinda parser)'."""
    if provider() == "apilayer":
        return "APILayer Resume Parser"
    if provider() == "edenai":
        parser = settings.edenai_resume_model.split("/")[2] if settings.edenai_resume_model.count("/") >= 2 else settings.edenai_resume_model
        return f"Eden AI ({parser.title()} parser)"
    return "Textkernel" if provider() == "textkernel" else "an ATS parser"


def engine() -> str:
    if provider() == "apilayer":
        return "APILayer Resume Parser API"
    return f"{settings.edenai_resume_model} via Eden AI" if provider() == "edenai" else ENGINE


# ---------- APILayer ----------
def _apilayer_call(data: bytes, transport: httpx.BaseTransport | None) -> dict:
    headers = {"apikey": settings.apilayer_api_key, "Content-Type": "application/octet-stream"}
    try:
        with httpx.Client(timeout=90, transport=transport) as client:
            r = client.post(settings.apilayer_url, content=data, headers=headers)
    except httpx.HTTPError as exc:
        raise AtsParserError("NETWORK", f"Could not reach APILayer ({type(exc).__name__}).") from exc
    if r.status_code in (401, 403):
        raise AtsParserError("AuthenticationError", "APILayer rejected the API key, or you haven't subscribed to the Resume Parser's free plan. Check APILAYER_API_KEY in backend/.env.")
    if r.status_code == 429:
        raise AtsParserError("NO_CREDITS", "You've used this month's free APILayer parses (100 a month). Try again next month.")
    if r.status_code in (400, 415, 422):
        raise AtsParserError("ConversionException", _apilayer_unreadable(_eden_error(r), len(data)))
    if r.status_code >= 400:
        raise AtsParserError(f"HTTP_{r.status_code}", f"APILayer error (HTTP {r.status_code}): {_eden_error(r)}")
    try:
        body = r.json()
    except ValueError as exc:
        raise AtsParserError("BAD_RESPONSE", "APILayer returned something that isn't JSON.") from exc
    if not isinstance(body, dict):
        raise AtsParserError("BAD_RESPONSE", "APILayer returned an unexpected answer.")
    return body


def summarise_apilayer(body: dict) -> dict:
    def first(v):
        return (v[0] if v else "") if isinstance(v, list) else (v or "")
    phone = body.get("phone", body.get("phones"))
    positions = [{"title": _txt(e.get("title")), "employer": _txt(e.get("organization")),
                  "start": _txt(e.get("dates")), "end": "", "dates": _txt(e.get("dates"))}
                 for e in (body.get("experience") or [])[:15] if isinstance(e, dict)]
    education = [{"school": _txt(e.get("name")), "degree": _txt(e.get("degree")), "end": _txt(e.get("dates"))}
                 for e in (body.get("education") or [])[:8] if isinstance(e, dict)]
    return {
        "engine": engine(), "name": _txt(first(body.get("name"))),
        "emails": [m for m in ([_txt(first(body.get("email")))] if body.get("email") else []) if m],
        # APILayer's documented output has no phone field; None leaves the phone check out instead of failing it
        "phones": None if phone is None else [_txt(p) for p in (phone if isinstance(phone, list) else [phone]) if _txt(p)],
        "positions": positions, "education": education,
        "skills": [_txt(s) for s in (body.get("skills") or []) if isinstance(s, str) and _txt(s)][:60],
        "sections": None, "parse_code": "success", "credits_used": 1, "credits_remaining": None,
    }


def _apilayer_unreadable(reason: str, size: int) -> str:
    """Plain-English message for a file APILayer refused (HTTP 400/415/422)."""
    if "small" in reason.lower():
        return (f"APILayer rejected this file as too small ({size / 1024:.1f} KB). Very small PDFs, like those made by some "
                "generators or 'print to PDF' tools, are refused."
                " A CV saved from Word or "
                "Google Docs (File > Download > PDF or .docx) is usually 20 KB or more: upload that version.")
    return (f"The parser couldn't read this file ({reason}). Save your CV from Word or Google Docs as a standard PDF or "
            "DOCX (not a scan, image or unusual template) and upload it again.")


# ---------- Eden AI ----------
def _eden_error(r: httpx.Response) -> str:
    try:
        body = r.json()
    except ValueError:
        return r.text[:160]
    if isinstance(body, dict):
        for key in ("detail", "message", "error"):
            v = body.get(key)
            if isinstance(v, dict):
                v = v.get("message") or v.get("type")
            if isinstance(v, list) and v:
                v = v[0].get("msg") if isinstance(v[0], dict) else v[0]
            if v:
                return str(v)[:200]
    return str(body)[:160]


def _eden_call(data: bytes, filename: str, transport: httpx.BaseTransport | None) -> dict:
    base = settings.edenai_base_url.rstrip("/")
    headers = {"Authorization": f"Bearer {settings.edenai_api_key}"}
    try:
        with httpx.Client(timeout=90, transport=transport) as client:
            up = client.post(f"{base}/upload", files={"file": (filename, data)}, headers=headers)
            if up.status_code >= 400:
                raise AtsParserError(_eden_code(up.status_code), _eden_message(up))
            file_id = (up.json() or {}).get("file_id")
            if not file_id:
                raise AtsParserError("BAD_RESPONSE", "Eden AI didn't return a file ID for the upload.")
            r = client.post(f"{base}/universal-ai", headers=headers,
                            json={"model": settings.edenai_resume_model, "input": {"file": file_id}})
    except httpx.HTTPError as exc:
        raise AtsParserError("NETWORK", f"Could not reach Eden AI ({type(exc).__name__}).") from exc
    if r.status_code >= 400:
        raise AtsParserError(_eden_code(r.status_code), _eden_message(r))
    body = r.json()
    if (body.get("status") or "").lower() in ("fail", "failed", "error"):
        raise AtsParserError("ConversionException", "The parser couldn't read this file. A real ATS may struggle with it too.")
    return body


def _eden_code(status: int) -> str:
    return {401: "AuthenticationError", 403: "AuthenticationError", 402: "NO_CREDITS"}.get(status, "ConversionException" if status in (400, 415, 422) else f"HTTP_{status}")


def _eden_message(r: httpx.Response) -> str:
    code = _eden_code(r.status_code)
    if code == "AuthenticationError":
        return "Eden AI rejected the API key. Check EDENAI_API_KEY in backend/.env."
    if code == "NO_CREDITS":
        return "Your Eden AI credits have run out."
    if code == "ConversionException":
        return f"The parser couldn't read this file ({_eden_error(r)}). Save your CV as a standard PDF and upload it again."
    return f"Eden AI error (HTTP {r.status_code}): {_eden_error(r)}"


def _txt(v) -> str:
    return str(v or "").strip()


def summarise_eden(body: dict) -> dict:
    out = body.get("output") or body
    d = out.get("extracted_data") or {}
    pi = d.get("personal_infos") or {}
    nm = pi.get("name") or {}
    name = _txt(nm.get("raw_name")) or " ".join(x for x in (_txt(nm.get("first_name")), _txt(nm.get("last_name"))) if x)
    positions = [{"title": _txt(e.get("title")), "employer": _txt(e.get("company")),
                  "start": _txt(e.get("start_date")), "end": _txt(e.get("end_date"))}
                 for e in ((d.get("work_experience") or {}).get("entries") or [])[:15]]
    education = [{"school": _txt(e.get("establishment")), "degree": _txt(e.get("title") or e.get("accreditation")),
                  "end": _txt(e.get("end_date"))} for e in ((d.get("education") or {}).get("entries") or [])[:8]]
    cost = body.get("cost") if isinstance(body.get("cost"), (int, float)) else None
    return {
        "engine": engine(), "name": name,
        "emails": [_txt(m) for m in (pi.get("mails") or []) if _txt(m)][:3],
        "phones": [_txt(p) for p in (pi.get("phones") or []) if _txt(p)][:3],
        "positions": positions, "education": education,
        "skills": [_txt(s.get("name")) for s in (d.get("skills") or []) if isinstance(s, dict) and _txt(s.get("name"))][:60],
        "sections": None,   # the shared Eden schema doesn't report which headings were found
        "parse_code": _txt(body.get("status")) or "success",
        "credits_used": cost, "credits_remaining": None,
    }


def _call(data: bytes, transport: httpx.BaseTransport | None) -> dict:
    url = settings.textkernel_base_url.rstrip("/") + "/parser/resume"
    headers = {"Tx-AccountId": settings.textkernel_account_id, "Tx-ServiceKey": settings.textkernel_service_key,
               "Content-Type": "application/json", "Accept": "application/json"}
    body = {"DocumentAsBase64String": base64.b64encode(data).decode("ascii"),
            "DocumentLastModified": date.today().isoformat()}
    try:
        with httpx.Client(timeout=60, transport=transport) as client:
            r = client.post(url, json=body, headers=headers)
    except httpx.HTTPError as exc:
        raise AtsParserError("NETWORK", f"Could not reach Textkernel ({type(exc).__name__}).") from exc
    try:
        payload = r.json()
    except ValueError:
        payload = {}
    info = payload.get("Info") or {}
    code = info.get("Code") or f"HTTP {r.status_code}"
    if r.status_code >= 400 or code not in ("Success",):
        msg = {"AuthenticationError": "Textkernel rejected the account ID or service key. Check them in backend/.env.",
               "ConversionException": "Textkernel couldn't read this file at all. A real ATS may struggle with it too.",
               "Timeout": "Textkernel took too long to read this file."}.get(code, info.get("Message") or f"Textkernel error ({code}).")
        if r.status_code == 402 or "credit" in str(info.get("Message", "")).lower():
            code, msg = "NO_CREDITS", "Your Textkernel credits have run out."
        raise AtsParserError(code, msg)
    return payload


def _raw(obj) -> str:
    """Textkernel values are often {"Raw": "...", "Normalized": "..."} objects."""
    if isinstance(obj, dict):
        return str(obj.get("Raw") or obj.get("Normalized") or obj.get("Name") or "").strip()
    return str(obj or "").strip()


def _date(d) -> str:
    if not isinstance(d, dict):
        return ""
    if d.get("IsCurrentDate"):
        return "Present"
    if not d.get("FoundYear"):
        return ""
    value = str(d.get("Date") or "")[:10]  # YYYY-MM-DD
    return value[:7] if d.get("FoundMonth") else value[:4]


def summarise(payload: dict) -> dict:
    """The parts of Textkernel's answer CareerPilot shows (a few KB, not the whole response)."""
    value = payload.get("Value") or {}
    rd = value.get("ResumeData") or {}
    contact = rd.get("ContactInformation") or {}
    name = (contact.get("CandidateName") or {}).get("FormattedName") or ""
    positions = []
    for p in ((rd.get("EmploymentHistory") or {}).get("Positions") or [])[:15]:
        positions.append({"title": _raw(p.get("JobTitle")), "employer": _raw((p.get("Employer") or {}).get("Name")),
                          "start": _date(p.get("StartDate")), "end": _date(p.get("EndDate")) or ("Present" if p.get("IsCurrent") else "")})
    education = []
    for e in ((rd.get("Education") or {}).get("EducationDetails") or [])[:8]:
        degree = e.get("Degree") or {}
        education.append({"school": _raw(e.get("SchoolName")), "degree": _raw(degree.get("Name") if isinstance(degree, dict) and "Name" in degree else degree),
                          "end": _date(e.get("EndDate") or e.get("LastEducationDate"))})
    skills = (rd.get("Skills") or {}).get("Raw") or []
    sections = [{"type": s.get("SectionType", ""), "header": (s.get("HeaderTextFound") or "").strip()}
                for s in ((rd.get("ResumeMetadata") or {}).get("FoundSections") or [])]
    info = payload.get("Info") or {}
    return {
        "engine": ENGINE,
        "name": name,
        "emails": list(contact.get("EmailAddresses") or [])[:3],
        "phones": [_raw(t) for t in (contact.get("Telephones") or [])][:3],
        "positions": positions,
        "education": education,
        "skills": [s.get("Name", "") for s in skills if s.get("Name")][:60],
        "sections": sections,
        "parse_code": (value.get("ParsingResponse") or {}).get("Code", ""),
        "credits_used": info.get("TransactionCost"),
        "credits_remaining": (info.get("CustomerDetails") or {}).get("CreditsRemaining"),
    }


def parse_cv(data: bytes, filename: str = "cv.pdf", transport: httpx.BaseTransport | None = None) -> dict:
    which = provider()
    if which == "apilayer":
        return summarise_apilayer(_apilayer_call(data, transport))
    if which == "edenai":
        return summarise_eden(_eden_call(data, filename, transport))
    if which == "textkernel":
        return summarise(_call(data, transport))
    raise AtsParserError("NOT_CONFIGURED", NOT_SET_UP)


# ---------- comparison with CareerPilot's own reading ----------
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE = re.compile(r"(?<!\w)(?:\+?\d[\d ()-]{7,}\d)(?!\w)")
_YEAR_RANGE = re.compile(r"(?:19|20)\d{2}\s*(?:-|–|—|to)\s*(?:(?:[A-Za-z]{3,9}\.?\s+)?(?:19|20)\d{2}|present|current|now)", re.I)


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9+#]", "", s.lower())


def compare(ats: dict, text: str, sections: dict[str, str], skill_names: list[str], name_guess: str) -> dict:
    """Item by item: what the ATS parser found vs what CareerPilot found, and why it matters."""
    exp = sections.get("experience", "")
    job_lines = [l.strip(" \t" + BULLET_CHARS) for l in exp.splitlines() if _YEAR_RANGE.search(l)]
    ours_jobs = len(job_lines)
    pos = ats["positions"]
    dated = sum(1 for p in pos if p["start"])
    titled = sum(1 for p in pos if p["title"])
    ats_skills = {_norm(s) for s in ats["skills"]}
    shared = [s for s in skill_names if _norm(s) in ats_skills]
    found_types = {s["type"].upper() for s in (ats.get("sections") or [])}
    our_heads = sorted(k for k in sections if k != "header")

    items = []

    def item(key, label, ats_found, ours, ok, why):
        items.append({"key": key, "label": label, "ats": ats_found, "careerpilot": ours, "ok": ok, "why": why})

    item("name", "Your name", ats["name"] or "not found", name_guess or "not found", bool(ats["name"]),
         "An ATS files your application under the name it reads. If it can't find one, recruiters may not find you.")
    ours_email = bool(_EMAIL.search(text))
    item("email", "Email address", ats["emails"][0] if ats["emails"] else "not found", "found" if ours_email else "not found",
         bool(ats["emails"]) or not ours_email,
         "Recruiters contact you through the email the ATS stores. Put it as plain text near the top, not in a header or image.")
    ours_phone = bool(_PHONE.search("\n".join(text.splitlines()[:15])))
    if ats.get("phones") is not None:   # some parsers don't extract phone numbers at all
        item("phone", "Phone number", ats["phones"][0] if ats["phones"] else "not found", "found" if ours_phone else "not found",
             bool(ats["phones"]) or not ours_phone, "A phone number the ATS can't read means one less way to reach you.")
    item("jobs", "Jobs in your work history", f"{len(pos)} job{'s' if len(pos) != 1 else ''}", f"{ours_jobs} dated line{'s' if ours_jobs != 1 else ''}",
         len(pos) >= ours_jobs and (len(pos) > 0 or ours_jobs == 0),
         "Each role the ATS misses is experience recruiters never see. Use one line per role: title, employer, dates.")
    item("titles", "Job titles", f"{titled} of {len(pos)}" if pos else "no jobs read", "-", not pos or titled == len(pos),
         "Recruiters search an ATS by job title, so every role needs a clear title.")
    item("dates", "Job dates", f"{dated} of {len(pos)}" if pos else "no jobs read", f"{ours_jobs} with dates", not pos or dated == len(pos),
         "Years of experience are calculated from dates. Write them as 'Jan 2024 – May 2025' on the same line as the role.")
    item("education", "Education", f"{len(ats['education'])} entr{'ies' if len(ats['education']) != 1 else 'y'}",
         "found" if "education" in sections else "not found", bool(ats["education"]) or "education" not in sections,
         "Many job filters check for a degree; an education entry the ATS can't read can screen you out.")
    item("skills", "Skills recognised", f"{len(ats['skills'])} skills",
         f"{len(shared)} of your {len(skill_names)} detected skills also found" if skill_names else "none detected",
         not skill_names or len(shared) >= max(1, round(0.6 * len(skill_names))),
         "ATS keyword searches only match skills the parser recognised. List skills by name in a Skills section.")
    if ats.get("sections") is not None:
        item("sections", "Sections recognised", ", ".join(sorted({s['header'] or s['type'] for s in ats['sections']})[:6]) or "none",
             ", ".join(h.title() for h in our_heads) or "none", len(found_types) >= min(len(our_heads), 3),
             "Standard headings (Experience, Education, Skills) tell the parser where each part of your CV starts.")
    ok = sum(1 for i in items if i["ok"])
    return {"items": items, "read_ok": ok, "total": len(items),
            "headline": (f"The ATS parser read {ok} of {len(items)} items as expected." if ok < len(items)
                         else "The ATS parser read every item as expected, so your layout is ATS-friendly."),
            "positions": pos, "education": ats["education"], "missed_skills": [s for s in skill_names if _norm(s) not in ats_skills][:12]}
