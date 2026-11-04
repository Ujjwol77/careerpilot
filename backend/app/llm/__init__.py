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
            raise LLMError(str(exc)) from exc


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
    try:
        text = llm.complete(system, user)
        return (text or fallback), ("llm" if text else "template-fallback")
    except LLMError as exc:
        log.warning("LLM call failed for %s: %s", prompt_id, exc)
        return fallback, "template-fallback"
