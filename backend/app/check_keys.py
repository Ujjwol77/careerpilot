"""Show which external-service keys the backend is using, with the values masked.

Run from the backend folder:   python -m app.check_keys
Add --all to also list the keys that are not set (and what the app falls back to).
Keys are never printed in full: only the first 4 and last 2 characters and the length.
"""
import os
import sys

from .config import settings

ENV_NOTE = "Values come from backend/.env (a Windows environment variable with the same name wins)."


def _mask(v: str) -> str:
    return f"{v[:4]}...{v[-2:]} ({len(v)} characters)" if len(v) > 8 else f"set ({len(v)} characters)"


# (service, what it is used for, [(ENV NAME, value)], settings worth showing, fallback when not set)
def _services() -> list[tuple[str, str, list[tuple[str, str]], str, str]]:
    llm_on = settings.llm_provider != "mock"
    return [
        ("Google Gemini (chat)", "CV rewrites, report summary, interview feedback",
         [("LLM_API_KEY", settings.llm_api_key if llm_on else "")],
         f"provider {settings.llm_provider}, model {settings.llm_model}", "built-in templates (LLM_PROVIDER=mock)"),
        ("Google Gemini (embeddings)", "semantic part of the match score",
         [("EMBEDDING_API_KEY", settings.embedding_api_key if settings.embedding_provider == "api" else "")],
         f"model {settings.embedding_model}" + ("; reuses LLM_API_KEY" if not os.getenv("EMBEDDING_API_KEY") and settings.embedding_api_key else ""),
         "local word-overlap similarity"),
        ("Adzuna Jobs API", "live Australian job ads",
         [("ADZUNA_APP_ID", settings.adzuna_app_id), ("ADZUNA_APP_KEY", settings.adzuna_app_key)],
         f"country {settings.adzuna_country}, {settings.adzuna_results} results a search, cached {settings.jobs_cache_hours} h",
         "180 sample postings"),
        ("APILayer Resume Parser", "ATS parse check of the CV file",
         [("APILAYER_API_KEY", settings.apilayer_api_key)], "", "Eden AI or Textkernel if set, else the check is off"),
        ("Eden AI", "ATS parse check (second choice)",
         [("EDENAI_API_KEY", settings.edenai_api_key)], f"model {settings.edenai_resume_model}", "not used"),
        ("Textkernel", "ATS parse check (third choice)",
         [("TEXTKERNEL_ACCOUNT_ID", settings.textkernel_account_id), ("TEXTKERNEL_SERVICE_KEY", settings.textkernel_service_key)],
         "", "not used"),
        ("YouTube Data API", "full-length video courses in the learning path",
         [("YOUTUBE_API_KEY", settings.youtube_api_key)], "", "curated course catalogue only"),
    ]


def main() -> int:
    show_all = "--all" in sys.argv
    services = _services()
    ready = [s for s in services if all(v for _, v in s[2])]
    print(f"Keys set up: {len(ready)} of {len(services)} services. {ENV_NOTE}\n")
    for name, use, keys, extra, fallback in services:
        is_set = all(v for _, v in keys)
        if not is_set and not show_all:
            continue
        print(f"{'[set]    ' if is_set else '[not set]'} {name}: {use}")
        for env, value in keys:
            print(f"            {env:<24} {_mask(value) if value else 'not set'}")
        if is_set and extra:
            print(f"            {extra}")
        if not is_set:
            print(f"            falls back to: {fallback}")
        print()
    if not show_all and len(ready) < len(services):
        print("Add --all to also list the services that are not set up.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
