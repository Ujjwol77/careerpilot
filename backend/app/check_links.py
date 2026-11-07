"""Check that every learning-catalogue link still loads.

Run from the backend folder:  python -m app.check_links
Exits with code 1 if any link is broken, so it can also run in CI on a schedule.
"""
import sys

import httpx

from .data.learning import all_urls

HEADERS = {"User-Agent": "Mozilla/5.0 (CareerPilot link checker)"}


def check(url: str, client: httpx.Client) -> tuple[bool, str]:
    try:
        r = client.head(url)
        if r.status_code in (403, 405) or r.status_code >= 500:  # some sites refuse HEAD
            r = client.get(url)
        return r.status_code < 400 or r.status_code == 403, str(r.status_code)
    except httpx.HTTPError as e:
        return False, type(e).__name__


def main() -> int:
    broken = []
    with httpx.Client(follow_redirects=True, timeout=20, headers=HEADERS) as client:
        for slug, url in all_urls():
            ok, status = check(url, client)
            print(f"{'OK ' if ok else 'BAD'} {status:>4}  {slug:<18} {url}")
            if not ok:
                broken.append(url)
    print(f"\n{len(broken)} broken link(s)" if broken else "\nAll links OK")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
