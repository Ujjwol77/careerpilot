"""Runtime settings, read from environment variables (see .env.example)."""
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load backend/.env into the environment. Real environment variables (e.g. on a host) win.
load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)


def _split(value: str) -> tuple[str, ...]:
    return tuple(v.strip() for v in value.split(",") if v.strip())


@dataclass(frozen=True)
class Settings:
    # SQLite by default so the project runs with zero setup.
    # For Supabase/PostgreSQL use e.g. postgresql+psycopg://user:pass@host:5432/postgres
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./careerpilot.db")
    secret_key: str = os.getenv("SECRET_KEY", "dev-only-secret-change-me-before-deploying-0123456789")
    token_minutes: int = int(os.getenv("TOKEN_MINUTES", "720"))
    max_upload_mb: int = int(os.getenv("MAX_UPLOAD_MB", "5"))

    # LLM: "mock" (default, no key needed) or "openai" (any OpenAI-compatible API,
    # including Groq/Ollama via LLM_BASE_URL).
    llm_provider: str = os.getenv("LLM_PROVIDER", "mock")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")

    # Live learning resources. Microsoft Learn needs no key; YouTube needs a free Data API key.
    # Semantic matching: a neural embedding model through an OpenAI-compatible /embeddings endpoint.
    # "api" uses it (defaults to the LLM's key and URL, e.g. Gemini); "local" uses word overlap only.
    embedding_provider: str = os.getenv("EMBEDDING_PROVIDER", "api")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
    embedding_api_key: str = os.getenv("EMBEDDING_API_KEY", os.getenv("LLM_API_KEY", ""))
    embedding_base_url: str = os.getenv("EMBEDDING_BASE_URL", os.getenv("LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/"))

    learning_mslearn: bool = os.getenv("LEARNING_MSLEARN", "true").lower() in ("1", "true", "yes")
    youtube_api_key: str = os.getenv("YOUTUBE_API_KEY", "")
    learning_cache_days: int = int(os.getenv("LEARNING_CACHE_DAYS", "7"))

    # Live jobs from Adzuna (free key: https://developer.adzuna.com). Blank = sample jobs only.
    adzuna_app_id: str = os.getenv("ADZUNA_APP_ID", "")
    adzuna_app_key: str = os.getenv("ADZUNA_APP_KEY", "")
    adzuna_country: str = os.getenv("ADZUNA_COUNTRY", "au")
    adzuna_results: int = int(os.getenv("ADZUNA_RESULTS", "30"))
    jobs_cache_hours: int = int(os.getenv("JOBS_CACHE_HOURS", "12"))

    cors_origins: tuple[str, ...] = field(
        default_factory=lambda: _split(os.getenv("CORS_ORIGINS", "http://localhost:3000"))
    )


settings = Settings()
