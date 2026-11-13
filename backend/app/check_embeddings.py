"""Check the embedding API and compare it with the old word-overlap similarity.

Run from the backend folder:  python -m app.check_embeddings [path-to-cv]
Default CV: samples/sample_cv.docx. Uses the jobs already in your database.
"""
import sys
from pathlib import Path

from sqlalchemy import select

from .agents.profile_agent import analyse_cv
from .agents.job_match_agent import profile_text
from .config import settings
from .cv_extract import validate_and_extract
from .db import SessionLocal
from .embeddings import cosine, embed
from .models import Job
from .semantic import LOCAL_SCALE, api_enabled, semantic_scores


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "samples" / "sample_cv.docx"
    key = settings.embedding_api_key
    print(f"Provider : {settings.embedding_provider}")
    print(f"Model    : {settings.embedding_model}")
    print(f"Base URL : {settings.embedding_base_url}")
    print(f"API key  : {'set (' + key[:4] + '...)' if key else 'NOT SET'}")
    if not api_enabled():
        print("\nEmbedding API is off. Set EMBEDDING_PROVIDER=api and LLM_API_KEY (or EMBEDDING_API_KEY) in backend/.env.")
        return 1
    text = validate_and_extract(path.name, path.read_bytes())
    p = analyse_cv(text)
    skills = [s if isinstance(s, str) else s["slug"] for s in p["skills"]]
    cv = profile_text(skills, p.get("summary", ""), p.get("experience", []))
    with SessionLocal() as db:
        jobs = list(db.scalars(select(Job).where(Job.source == "seed-dataset")))
        if not jobs:
            print("\nNo sample jobs in the database yet. Start the backend once (uvicorn) so it seeds them.")
            return 1
        scores, info = semantic_scores(db, cv, jobs)
        if "calibration" not in info:
            print(f"\nFAILED: {info.get('fallback_reason')}. 401/403 = key, 404 = model name, 429 = quota.")
            return 1
        cal = info["calibration"]
        print(f"\nOK. Calibration ({cal.get('method')}): {cal['different_role_pairs']} unrelated and {cal['same_role_pairs']} same-role pairs")
        print(f"  cosine {cal['floor']:.3f} (median, unrelated role) -> 0%    cosine {cal['ceiling']:.3f} (90th percentile, same role) -> 100%\n")
        local_vec = embed(cv)
        rows = sorted(jobs, key=lambda j: -scores[j.id])
        print(f"CV: {path.name}\n{'Job':<42}{'Role':<24}{'Embedding':>10}{'Word overlap':>14}")
        for j in rows[:6] + rows[-3:]:
            old = min(1.0, max(0.0, cosine(local_vec, j.embedding) * LOCAL_SCALE))
            print(f"{j.title[:40]:<42}{j.role_category:<24}{scores[j.id]:>9.0%}{old:>14.0%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
