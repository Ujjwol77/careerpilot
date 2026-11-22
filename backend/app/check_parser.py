"""Check which resume parser the "How an ATS reads your CV" card will use, and why.

Run from the backend folder:   python -m app.check_parser
Add --parse to test it on a sample CV (uses 1 parse of your quota):   python -m app.check_parser --parse
Or test your own file:                                                python -m app.check_parser --parse samples/cv_set/cv_07_good_data.docx
Keys are never printed in full.
"""
import os
import re
import sys
from pathlib import Path

from . import ats_parser
from .config import settings

ENV = Path(__file__).resolve().parent.parent / ".env"
NAMES = ("APILAYER_API_KEY", "EDENAI_API_KEY", "TEXTKERNEL_ACCOUNT_ID", "TEXTKERNEL_SERVICE_KEY")


def _mask(v: str) -> str:
    return f"set ({v[:4]}...{v[-2:]}, {len(v)} characters)" if len(v) > 8 else ("set (very short)" if v else "not set")


def main() -> int:
    print(f".env file : {ENV} ({'found' if ENV.exists() else 'NOT FOUND'})")
    if ENV.exists():
        print("\nParser-related lines in .env (values hidden):")
        seen = False
        for n, line in enumerate(ENV.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if line.strip().startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            if re.search(r"api.?layer|eden|textkernel|parser", name, re.I):
                seen = True
                v = value.strip()
                problems = []
                if name != name.strip():
                    problems.append("space before '='")
                if name.strip() not in NAMES:
                    problems.append(f"unknown name (expected one of {', '.join(NAMES)})")
                if v[:1] in "\"'":
                    problems.append("value has quotes; remove them")
                if value != value.strip() and v:
                    problems.append("space around the value")
                print(f"  line {n}: {name.strip():<24} {'has a value' if v else 'empty'}" + (f"   <-- {'; '.join(problems)}" if problems else ""))
        if not seen:
            print("  none found. Add a line:  APILAYER_API_KEY=your-key")
    print("\nWhat the backend reads (environment variables win over .env):")
    for name in NAMES:
        src = " (from a Windows environment variable)" if name in os.environ and ENV.exists() and name + "=" not in ENV.read_text(encoding="utf-8", errors="replace") else ""
        print(f"  {name:<24} {_mask(getattr(settings, name.lower()))}{src}")
    which = ats_parser.provider()
    print(f"\nProvider in use: {ats_parser.label() if which else 'none'}  (order: APILayer, then Eden AI, then Textkernel)")
    if which != "apilayer" and settings.apilayer_api_key == "":
        print("APILAYER_API_KEY is empty, so APILayer is not used. After editing .env, stop the backend (Ctrl+C) and start it again:"
              " uvicorn --reload does not notice .env changes.")
    if "--parse" not in sys.argv:
        print("\nTo test the parser on a sample CV (uses 1 parse):  python -m app.check_parser --parse")
        return 0 if which else 1
    args = [a for a in sys.argv[1:] if a != "--parse"]
    sample = Path(args[0]) if args else Path(__file__).resolve().parent.parent / "samples" / "cv_set" / "cv_10_best_data.pdf"
    if args and not sample.exists():
        print(f"\nFile not found: {sample}")
        return 1
    if not sample.exists():
        sample = Path(__file__).resolve().parent.parent / "samples" / "sample_cv.pdf"
    print(f"\nParsing {sample.name} ({sample.stat().st_size / 1024:.1f} KB) with {ats_parser.label()} ...")
    try:
        s = ats_parser.parse_cv(sample.read_bytes(), sample.name)
    except ats_parser.AtsParserError as exc:
        print(f"FAILED ({exc.code}): {exc}")
        return 1
    print(f"OK: name '{s['name']}', {len(s['emails'])} email(s), {len(s['positions'])} job(s), {len(s['education'])} education entr(ies), {len(s['skills'])} skills")
    for p in s["positions"][:5]:
        print(f"   - {p['title'] or '(no title)'} | {p['employer'] or '(no employer)'} | {p.get('dates') or (p['start'] + ' - ' + p['end'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
