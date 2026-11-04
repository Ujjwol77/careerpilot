"""Local, dependency-free text embeddings (signed feature hashing) + cosine similarity.

This is the mock-friendly stand-in for a hosted embedding model. Swap `embed()` for an API call and
store the vectors in a pgvector column when you move to Supabase/PostgreSQL; nothing else changes.
"""
import math
import re
import zlib

from .taxonomy import canonicalise_text

DIM = 1024
_STOP = {
    "the", "and", "for", "with", "you", "our", "will", "are", "have", "has", "that", "this", "from",
    "your", "their", "who", "all", "can", "per", "into", "such", "any", "was", "were", "been",
    "a", "an", "of", "in", "on", "to", "as", "at", "by", "or", "is", "it", "be", "we", "i",
}
_TOKEN = re.compile(r"[a-z0-9_]+")


def embed(text: str) -> list[float]:
    tokens = [t for t in _TOKEN.findall(canonicalise_text(text)) if t not in _STOP and len(t) > 1]
    grams = tokens + [f"{a}_{b}" for a, b in zip(tokens, tokens[1:])]
    vec = [0.0] * DIM
    for g in grams:
        h = zlib.crc32(g.encode())
        weight = 3.0 if g.startswith("skill_") else 1.0  # canonical skill tokens count more
        vec[h % DIM] += weight if (h >> 16) & 1 else -weight
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))
