"""Semantic similarity between a CV and job adverts using a neural text-embedding model.

How the semantic part of the match score is produced
1. The CV and each advert are sent to an embedding model (default: Google `gemini-embedding-001`
   through its OpenAI-compatible /embeddings endpoint). Each text becomes a vector that encodes its
   meaning, so "built Power BI dashboards" sits close to "data visualisation" even with no shared words.
2. Similarity = cosine of the two vectors.
3. Calibration. Embedding models give even unrelated texts a fairly high cosine, so raw cosine would
   inflate every score. We measure the model's own scale with CVs whose target role is known (the two
   sample CVs: a data analyst and a cyber security analyst) against the sample job dataset:
     floor   = median cosine between a sample CV and adverts for OTHER roles
     ceiling = 90th percentile cosine between a sample CV and adverts for ITS OWN role
   semantic = clamp((cosine - floor) / (ceiling - floor), 0, 1)
   so 0% means "no closer than an unrelated job" and 100% means "as close as a strong same-role match".
   CV-vs-advert pairs are used (not advert-vs-advert) because a CV is a different kind of text from an
   advert and scores lower against any advert; anchors must compare like with like.
   If the sample CVs are missing, advert-vs-advert pairs are used instead.
4. Advert vectors are stored in the job_embeddings table (each job is embedded once); CV vectors are
   cached in memory. If no key is set or the API fails, the local word-overlap method in embeddings.py
   is used instead, and the result says so.
"""
import hashlib
import json
import logging
import statistics
from collections import OrderedDict
from pathlib import Path

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .embeddings import cosine, embed
from .models import Job, JobEmbedding

log = logging.getLogger("careerpilot.semantic")

LOCAL_SCALE = 2.0          # legacy calibration for the local hashed vectors
MAX_CHARS = 8000           # keep inputs inside the model's token limit
BATCH = 50
CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache"
LOCAL_ENGINE = "local word overlap"


class EmbeddingError(RuntimeError):
    pass


def api_enabled() -> bool:
    return settings.embedding_provider == "api" and bool(settings.embedding_api_key)


def _post(texts: list[str], transport: httpx.BaseTransport | None) -> list[list[float]]:
    url = settings.embedding_base_url.rstrip("/") + "/embeddings"
    headers = {"Authorization": f"Bearer {settings.embedding_api_key}"}
    with httpx.Client(timeout=30, transport=transport) as client:
        r = client.post(url, json={"model": settings.embedding_model, "input": texts}, headers=headers)
        r.raise_for_status()
        data = sorted(r.json()["data"], key=lambda d: d.get("index", 0))
        vecs = [d["embedding"] for d in data]
    if len(vecs) != len(texts):
        raise EmbeddingError(f"expected {len(texts)} vectors, got {len(vecs)}")
    return vecs


def embed_many(texts: list[str], transport: httpx.BaseTransport | None = None) -> list[list[float]]:
    """Embed texts in batches; if the endpoint rejects a list input, fall back to one text per call."""
    texts = [t[:MAX_CHARS] or " " for t in texts]
    out: list[list[float]] = []
    try:
        for i in range(0, len(texts), BATCH):
            chunk = texts[i:i + BATCH]
            try:
                out.extend(_post(chunk, transport))
            except (httpx.HTTPStatusError, EmbeddingError) as exc:
                if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code in (401, 403, 404, 429):
                    raise
                out.extend(v for t in chunk for v in _post([t], transport))
    except httpx.HTTPStatusError as exc:
        raise EmbeddingError(f"HTTP {exc.response.status_code}") from exc
    except (httpx.HTTPError, KeyError, ValueError, TypeError) as exc:
        raise EmbeddingError(type(exc).__name__) from exc
    return out


def _normalise(v: list[float]) -> list[float]:
    n = sum(x * x for x in v) ** 0.5 or 1.0
    return [x / n for x in v]


_cv_cache: "OrderedDict[str, list[float]]" = OrderedDict()


def _cv_vector(text: str, transport) -> list[float]:
    key = hashlib.sha256(f"{settings.embedding_model}|{text}".encode()).hexdigest()
    if key not in _cv_cache:
        _cv_cache[key] = _normalise(embed_many([text], transport)[0])
        if len(_cv_cache) > 256:
            _cv_cache.popitem(last=False)
    _cv_cache.move_to_end(key)
    return _cv_cache[key]


def _job_text(job: Job) -> str:
    return f"{job.title}. {job.description}"


def _job_vectors(db: Session, jobs: list[Job], transport) -> dict[int, list[float]]:
    model = settings.embedding_model
    have = {e.job_id: e.vector for e in db.scalars(
        select(JobEmbedding).where(JobEmbedding.model == model, JobEmbedding.job_id.in_([j.id for j in jobs])))}
    todo = [j for j in jobs if j.id not in have]
    if todo:
        for job, vec in zip(todo, embed_many([_job_text(j) for j in todo], transport)):
            vec = _normalise(vec)
            have[job.id] = vec
            db.add(JobEmbedding(job_id=job.id, model=model, vector=vec))
        db.commit()
    return have


def calibration(db: Session, transport=None) -> dict:
    """floor/ceiling for this model, measured once on the sample jobs and saved in .cache/."""
    path = CACHE_DIR / f"semantic_calibration_{settings.embedding_model.replace('/', '_')}.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    seeds = list(db.scalars(select(Job).where(Job.source == "seed-dataset")))
    if len(seeds) < 6:
        raise EmbeddingError("not enough sample jobs to calibrate")
    vecs = _job_vectors(db, seeds, transport)
    same, diff = [], []
    anchors = _anchor_cvs()
    if anchors:
        method = "sample CVs vs sample jobs"
        cv_vecs = [_normalise(v) for v in embed_many([text for text, _ in anchors], transport)]
        for (_, role), cv in zip(anchors, cv_vecs):
            for job in seeds:
                (same if job.role_category == role else diff).append(cosine(cv, vecs[job.id]))
    else:
        method = "sample jobs vs sample jobs"
        for i, a in enumerate(seeds):
            for b in seeds[i + 1:]:
                (same if a.role_category == b.role_category else diff).append(cosine(vecs[a.id], vecs[b.id]))
    floor = statistics.median(diff)
    ceiling = statistics.quantiles(same, n=10)[-1] if len(same) >= 2 else max(same or [floor + 0.2])
    if ceiling - floor < 0.02:
        raise EmbeddingError("calibration range too small")
    cal = {"model": settings.embedding_model, "method": method, "floor": round(floor, 4), "ceiling": round(ceiling, 4),
           "same_role_pairs": len(same), "different_role_pairs": len(diff)}
    try:
        CACHE_DIR.mkdir(exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(cal), encoding="utf-8")
        tmp.replace(path)
    except OSError:
        pass
    return cal


SAMPLES = Path(__file__).resolve().parent.parent / "samples"
ANCHOR_CVS = [("sample_cv.docx", "data_analyst"), ("sample_cv_cyber.pdf", "cybersecurity_analyst")]


def _anchor_cvs() -> list[tuple[str, str]]:
    """(matcher text, target role) for each sample CV, built exactly as the matcher builds a user's text."""
    from .agents.job_match_agent import profile_text
    from .agents.profile_agent import analyse_cv
    from .cv_extract import validate_and_extract
    out = []
    for name, role in ANCHOR_CVS:
        try:
            p = analyse_cv(validate_and_extract(name, (SAMPLES / name).read_bytes()))
        except Exception:  # missing or unreadable sample: skip it
            continue
        skills = [s if isinstance(s, str) else s["slug"] for s in p["skills"]]
        out.append((profile_text(skills, p.get("summary", ""), p.get("experience", [])), role))
    return out


def _scale(cos: float, cal: dict) -> float:
    return min(1.0, max(0.0, (cos - cal["floor"]) / (cal["ceiling"] - cal["floor"])))


def semantic_scores(db: Session | None, cv_text: str, jobs: list[Job],
                    transport: httpx.BaseTransport | None = None) -> tuple[dict[int, float], dict]:
    """{job_id: 0..1 semantic similarity} plus info on which engine produced it (and why, if it fell back)."""
    if db is not None and api_enabled() and jobs:
        try:
            cal = calibration(db, transport)
            cv = _cv_vector(cv_text, transport)
            vecs = _job_vectors(db, jobs, transport)
            scores = {j.id: _scale(cosine(cv, vecs[j.id]), cal) for j in jobs}
            return scores, {"engine": settings.embedding_model, "calibration": cal}
        except EmbeddingError as exc:
            db.rollback()
            log.warning("embedding API unavailable, using local similarity: %s", exc)
            reason = str(exc)
    else:
        reason = "no embedding API configured" if not api_enabled() else ""
    cv_vec = embed(cv_text)
    scores = {j.id: min(1.0, max(0.0, cosine(cv_vec, j.embedding or embed(_job_text(j))) * LOCAL_SCALE)) for j in jobs}
    return scores, {"engine": LOCAL_ENGINE, "fallback_reason": reason}
