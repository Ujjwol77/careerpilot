import re

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)")
_URL = re.compile(r"https?://\S+|www\.\S+")
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def redact_pii(text: str) -> str:
    """Strip contact details before text leaves our infrastructure (e.g. to an external LLM)."""
    text = _EMAIL.sub("[email]", text)
    text = _URL.sub("[link]", text)
    return _PHONE.sub("[phone]", text)


def clean_text(text: str, limit: int = 20000) -> str:
    return _CONTROL.sub("", text).strip()[:limit]
