"""Live learning sources for the Learning Pathway agent.

  * MicrosoftLearnSource - Microsoft Learn Catalog API: free, no key. Real modules and learning
                           paths with real durations. Covers Microsoft-related skills (Azure, Power BI,
                           Excel, C#, Python, SQL, security...). The catalogue is downloaded at most once a day.
  * YouTubeSource        - YouTube Data API v3: free key, 100 searches/day. Finds a full-length course
                           video for any skill and reads its real duration and view count.

Every link comes from an API response, never from a language model, so no link is invented.
Results are cached per skill on disk (LEARNING_CACHE_DAYS, default 7) to protect free quotas.
When a source is off, has no key or fails, it returns nothing and the curated catalogue is used.
"""
import json
import logging
import math
import re
import time
from pathlib import Path

import httpx

from .config import settings
from .taxonomy import SKILLS

log = logging.getLogger("careerpilot.learning")

CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache"
_SKILL_CACHE_FILE = CACHE_DIR / "learning_cache.json"
_RETRY_AFTER_FAILURE = 30 * 60  # seconds before a failed source is tried again


def _terms(slug: str) -> list[str]:
    """Words that identify a skill in a course title: its display name plus unambiguous aliases."""
    skill = SKILLS.get(slug)
    if not skill:
        return [slug.replace("_", " ")]
    words = {skill.display.lower(), *skill.aliases, *(a.lower() for a in skill.case_sensitive_aliases)}
    return sorted((w for w in words if len(w) >= 3 or w in {"c#", "r"}), key=len, reverse=True)


def _contains(text: str, term: str) -> bool:
    return re.search(rf"(?<![\w#+]){re.escape(term)}(?![\w#+])", text) is not None


def _write_json(path: Path, data) -> None:
    """Write JSON atomically: a crash or reload mid-write can't leave an empty or half-written file."""
    CACHE_DIR.mkdir(exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data), encoding="utf-8")
    tmp.replace(path)


def _hours(minutes: float) -> int:
    return max(1, math.ceil(minutes / 60))


# ---------------- per-skill disk cache ----------------
class _SkillCache:
    def __init__(self):
        self._data: dict | None = None

    def _load(self) -> dict:
        if self._data is None:
            try:
                self._data = json.loads(_SKILL_CACHE_FILE.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                self._data = {}
        return self._data

    def get(self, key: str):
        entry = self._load().get(key)
        if entry and time.time() - entry["at"] < settings.learning_cache_days * 86400:
            return entry["items"]
        return None

    def put(self, key: str, items: list[dict]) -> None:
        self._load()[key] = {"at": time.time(), "items": items}
        try:
            _write_json(_SKILL_CACHE_FILE, self._data)
        except OSError as exc:  # read-only disk: keep the in-memory cache
            log.warning("could not write learning cache: %s", exc)


skill_cache = _SkillCache()


# ---------------- Microsoft Learn ----------------
class MicrosoftLearnSource:
    name = "Microsoft Learn"
    URL = "https://learn.microsoft.com/api/catalog/"
    _CATALOG_FILE = CACHE_DIR / "mslearn_catalog.json"

    def __init__(self, transport: httpx.BaseTransport | None = None):
        self._transport = transport
        self._items: list[dict] | None = None
        self._failed_at = 0.0

    @property
    def enabled(self) -> bool:
        return settings.learning_mslearn

    def _catalog(self) -> list[dict]:
        if self._items is not None:
            return self._items
        if time.time() - self._failed_at < _RETRY_AFTER_FAILURE:
            return []
        raw = None
        try:
            if self._CATALOG_FILE.exists() and time.time() - self._CATALOG_FILE.stat().st_mtime < 86400:
                raw = json.loads(self._CATALOG_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raw = None
        if raw is None:
            try:
                with httpx.Client(timeout=30, transport=self._transport) as client:
                    r = client.get(self.URL, params={"locale": "en-us", "type": "modules,learningPaths"})
                    r.raise_for_status()
                    raw = r.json()
            except (httpx.HTTPError, ValueError) as exc:
                log.warning("Microsoft Learn catalogue unavailable: %s", exc)
                self._failed_at = time.time()
                return []
            try:
                _write_json(self._CATALOG_FILE, raw)
            except OSError:
                pass
        items = []
        for kind in ("learningPaths", "modules"):
            for it in raw.get(kind, []):
                if not it.get("url") or not it.get("title"):
                    continue
                items.append({
                    "kind": "learning path" if kind == "learningPaths" else "module",
                    "title": it["title"], "title_l": it["title"].lower(),
                    "tags": " ".join(it.get("products", []) + it.get("subjects", [])).replace("-", " ").lower(),
                    "url": it["url"].split("?")[0], "minutes": it.get("duration_in_minutes") or 0,
                    "levels": it.get("levels", []), "popularity": it.get("popularity") or 0,
                })
        self._items = items
        return items

    def find(self, slug: str, limit: int = 1) -> list[dict]:
        if not self.enabled or SKILLS.get(slug) and SKILLS[slug].category == "soft":
            return []
        terms = _terms(slug)
        scored = []
        for it in self._catalog():
            if not any(_contains(it["title_l"], t) for t in terms):
                continue  # the skill must be named in the title, not just mentioned
            score = 2.0 + (1.0 if it["kind"] == "learning path" else 0) + (1.0 if "beginner" in it["levels"] else 0)
            score += it["popularity"]
            if it["minutes"] > 20 * 60:
                score -= 1.5  # very long paths overload a weekly plan
            scored.append((score, it))
        scored.sort(key=lambda s: -s[0])
        return [{
            "type": "course" if it["kind"] == "learning path" else "tutorial",
            "title": it["title"], "provider": "Microsoft Learn", "url": it["url"],
            "hours": _hours(it["minutes"] or 60), "cost": "free",
            "hours_source": "provider" if it["minutes"] else "estimate", "origin": "live",
        } for _, it in scored[:limit]]


# ---------------- YouTube ----------------
_ISO_DURATION = re.compile(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?")


def _iso_minutes(value: str) -> float:
    m = _ISO_DURATION.fullmatch(value or "")
    if not m:
        return 0
    h, mins, s = (int(x or 0) for x in m.groups())
    return h * 60 + mins + s / 60


class YouTubeSource:
    name = "YouTube"
    SEARCH = "https://www.googleapis.com/youtube/v3/search"
    VIDEOS = "https://www.googleapis.com/youtube/v3/videos"

    def __init__(self, transport: httpx.BaseTransport | None = None):
        self._transport = transport
        self._failed_at = 0.0

    @property
    def enabled(self) -> bool:
        return bool(settings.youtube_api_key)

    def query_for(self, slug: str) -> tuple[str, str]:
        skill = SKILLS.get(slug)
        name = skill.display if skill else slug.replace("_", " ")
        category = skill.category if skill else "technical"
        if category == "soft":
            return f"how to improve {name} skills at work", "medium"
        if category == "certification":
            return f"{name} exam full course", "long"
        return f"{name} full course for beginners", "long"

    def find(self, slug: str, limit: int = 1) -> list[dict]:
        if not self.enabled or time.time() - self._failed_at < _RETRY_AFTER_FAILURE:
            return []
        q, duration = self.query_for(slug)
        key = settings.youtube_api_key
        try:
            with httpx.Client(timeout=15, transport=self._transport) as client:
                r = client.get(self.SEARCH, params={
                    "part": "snippet", "q": q, "type": "video", "videoDuration": duration, "maxResults": 8,
                    "relevanceLanguage": "en", "safeSearch": "strict", "videoEmbeddable": "true", "key": key})
                r.raise_for_status()
                ids = [i["id"]["videoId"] for i in r.json().get("items", []) if i.get("id", {}).get("videoId")]
                if not ids:
                    return []
                r = client.get(self.VIDEOS, params={"part": "snippet,contentDetails,statistics", "id": ",".join(ids), "key": key})
                r.raise_for_status()
                videos = r.json().get("items", [])
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            log.warning("YouTube search failed for %s: %s", slug, exc)
            self._failed_at = time.time()
            return []
        terms = _terms(slug)
        picks = []
        for v in videos:
            title = v.get("snippet", {}).get("title", "")
            minutes = _iso_minutes(v.get("contentDetails", {}).get("duration", ""))
            views = int(v.get("statistics", {}).get("viewCount", 0) or 0)
            if minutes < 10:
                continue
            relevant = any(_contains(title.lower(), t) for t in terms)
            picks.append(((relevant, views), v, title, minutes))
        picks.sort(key=lambda p: p[0], reverse=True)
        return [{
            "type": "video", "title": title,
            "provider": f"YouTube · {v['snippet'].get('channelTitle', 'unknown channel')}",
            "url": f"https://www.youtube.com/watch?v={v['id']}", "hours": _hours(minutes),
            "cost": "free", "hours_source": "provider", "origin": "live",
        } for _, v, title, minutes in picks[:limit]]


LIVE_SOURCES = [MicrosoftLearnSource(), YouTubeSource()]


def live_resources(slug: str) -> list[dict]:
    """Live picks for one skill: up to one per source, cached per skill."""
    enabled = [s for s in LIVE_SOURCES if s.enabled]
    if not enabled:
        return []
    key = f"{slug}|{','.join(s.name for s in enabled)}"
    cached = skill_cache.get(key)
    if cached is not None:
        return cached
    items = []
    for source in enabled:
        items.extend(source.find(slug))
    if items:  # don't cache an empty result caused by an outage
        skill_cache.put(key, items)
    return items
