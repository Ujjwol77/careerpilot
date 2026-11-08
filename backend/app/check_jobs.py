"""Check the Adzuna connection set in backend/.env and show a few live postings.

Run from the backend folder:  python -m app.check_jobs ["role words"] ["location"]
Example:                      python -m app.check_jobs "cybersecurity analyst" Melbourne
"""
import sys

import httpx

from .agents.job_search_agent import AdzunaSource
from .config import settings
from .taxonomy import display, extract_skills


def main() -> int:
    what = sys.argv[1] if len(sys.argv) > 1 else "data analyst"
    where = sys.argv[2] if len(sys.argv) > 2 else ""
    key = settings.adzuna_app_key
    print(f"Country : {settings.adzuna_country}")
    print(f"App ID  : {settings.adzuna_app_id or 'NOT SET'}")
    print(f"App key : {'set (' + key[:4] + '...)' if key else 'NOT SET'}")
    source = AdzunaSource()
    if not source.enabled:
        print("\nAdd ADZUNA_APP_ID and ADZUNA_APP_KEY to backend/.env first.")
        return 1
    try:
        results = source._fetch(what, where)
    except httpx.HTTPStatusError as exc:
        code = exc.response.status_code
        hint = {401: "check the app ID and key", 403: "check the app ID and key",
                429: "rate limit reached, wait and retry", 400: "check ADZUNA_COUNTRY"}.get(code, "")
        print(f"\nFAILED: HTTP {code}. {hint}")
        return 1
    except httpx.HTTPError as exc:
        print(f"\nFAILED: {type(exc).__name__}: {exc}")
        return 1
    print(f"\nOK: {len(results)} postings for '{what}'{' in ' + where if where else ''}\n")
    for item in results[:5]:
        title = item.get("title", "")
        skills = extract_skills(f"{title}. {item.get('description', '')}")
        print(f"- {title} | {(item.get('company') or {}).get('display_name', '?')} | "
              f"{(item.get('location') or {}).get('display_name', '?')}")
        print(f"  skills found: {', '.join(display(s) for s in skills) or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
