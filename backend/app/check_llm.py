"""Check the language-model connection set in backend/.env.

Run from the backend folder:  python -m app.check_llm
"""
import sys
import time

from .config import settings
from .llm import LLMError, get_llm


def main() -> int:
    key = settings.llm_api_key
    print(f"Provider : {settings.llm_provider}")
    print(f"Base URL : {settings.llm_base_url}")
    print(f"Model    : {settings.llm_model}")
    print(f"API key  : {'set (' + key[:4] + '...' + key[-4:] + ')' if len(key) > 8 else 'NOT SET'}")
    llm = get_llm()
    if llm.is_mock:
        print("\nStill in mock mode. Set LLM_PROVIDER=openai and LLM_API_KEY in backend/.env.")
        return 1
    start = time.perf_counter()
    try:
        reply = llm.complete("You are a test endpoint.", "Reply with exactly: CareerPilot connected")
    except LLMError as exc:
        print(f"\nFAILED: {exc}")
        print("400/404: check LLM_MODEL and LLM_BASE_URL.  401/403: check the key.  429: quota or rate limit.")
        return 1
    print(f"\nOK in {time.perf_counter() - start:.1f}s. Model replied: {reply!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
