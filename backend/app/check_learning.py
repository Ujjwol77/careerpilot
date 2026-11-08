"""Show what the live learning sources return for a few skills.

Run from the backend folder:  python -m app.check_learning [skill ...]
Example:                      python -m app.check_learning sql power_bi siem
Skill names are taxonomy slugs (see app/taxonomy.py). Results are not cached by this script.
"""
import sys

from .config import settings
from .learning_sources import MicrosoftLearnSource, YouTubeSource


def main() -> int:
    skills = sys.argv[1:] or ["sql", "power_bi", "siem", "communication"]
    print(f"Microsoft Learn : {'on (no key needed)' if settings.learning_mslearn else 'off (LEARNING_MSLEARN=false)'}")
    print(f"YouTube         : {'key set' if settings.youtube_api_key else 'no key (YOUTUBE_API_KEY empty)'}\n")
    sources = [MicrosoftLearnSource(), YouTubeSource()]
    found_any = False
    for slug in skills:
        print(f"[{slug}]")
        for source in sources:
            if not source.enabled:
                continue
            items = source.find(slug)
            found_any |= bool(items)
            for it in items:
                print(f"  {source.name:<15} {it['title']}  ({it['hours']}h)\n  {'':<15} {it['url']}")
            if not items:
                print(f"  {source.name:<15} no match (curated catalogue will be used)")
        print()
    return 0 if found_any else 1


if __name__ == "__main__":
    sys.exit(main())
