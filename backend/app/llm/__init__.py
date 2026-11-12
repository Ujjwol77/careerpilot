"""LLM layer. `mock` is the default; `openai` works with any OpenAI-compatible endpoint."""
import logging
from functools import lru_cache

import httpx

from ..config import settings
from ..prompt_bank import render
from ..utils import redact_pii

log = logging.getLogger("careerpilot.llm")


class LLMError(RuntimeError):
    pass


_last_error = ""


def last_error() -> str:
    """Short reason for the most recent failed model call ("" after a success); shown on the Agent monitor."""
    return _last_error


def _describe(exc: Exception) -> str:
    """Turn an HTTP failure into a short, key-free reason such as 'HTTP 429: Resource has been exhausted'."""
    if isinstance(exc, httpx.HTTPStatusError):
        msg = ""
        try:
            body = exc.response.json()
            body = body[0] if isinstance(body, list) and body else body
            msg = (body.get("error") or {}).get("message", "") if isinstance(body, dict) else ""
        except ValueError:
            msg = exc.response.text[:120]
        return f"HTTP {exc.response.status_code}" + (f": {msg.strip()[:120]}" if msg else "")
    if isinstance(exc, httpx.TimeoutException):
        return "timed out after 30 s"
    if isinstance(exc, httpx.ConnectError):
        return "could not connect (check LLM_BASE_URL and your internet connection)"
    return f"{type(exc).__name__}: {str(exc)[:120]}"


class MockLLM:
    is_mock = True

    def complete(self, system: str, user: str) -> str:  # never called by agents in mock mode
        return ""


class OpenAICompatLLM:
    is_mock = False

    def __init__(self, api_key: str, base_url: str, model: str, transport: httpx.BaseTransport | None = None):
        self.api_key, self.base_url, self.model = api_key, base_url.rstrip("/"), model
        self._transport = transport

    def complete(self, system: str, user: str) -> str:
        payload = {
            "model": self.model,
            "temperature": 0.3,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        }
        try:
            with httpx.Client(timeout=30, transport=self._transport) as client:
                r = client.post(f"{self.base_url}/chat/completions", json=payload,
                                headers={"Authorization": f"Bearer {self.api_key}"})
                r.raise_for_status()
                return r.json()["choices"][0]["message"]["content"].strip()
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
            raise LLMError(_describe(exc)) from exc


@lru_cache
def get_llm():
    if settings.llm_provider == "openai" and settings.llm_api_key:
        return OpenAICompatLLM(settings.llm_api_key, settings.llm_base_url, settings.llm_model)
    return MockLLM()


def try_llm(prompt_id: str, fallback: str, **variables: str) -> tuple[str, str]:
    """Return (text, source). source is 'llm', 'template' (mock mode) or 'template-fallback' (LLM failed)."""
    llm = get_llm()
    if llm.is_mock:
        return fallback, "template"
    safe = {k: redact_pii(str(v))[:4000] for k, v in variables.items()}
    system, user = render(prompt_id, **safe)
    global _last_error
    try:
        text = llm.complete(system, user)
        _last_error = "" if text else "the model returned an empty reply"
        return (text or fallback), ("llm" if text else "template-fallback")
    except LLMError as exc:
        _last_error = str(exc)
        log.warning("LLM call failed for %s: %s", prompt_id, exc)
        return fallback, "template-fallback"
