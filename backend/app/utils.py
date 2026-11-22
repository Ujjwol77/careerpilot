import re

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)")
_URL = re.compile(r"https?://\S+|www\.\S+")
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
# Bullet marks as they come out of real documents. PDF text extraction often turns a "•" into an odd
# character (U+007F, or U+F0B7 / U+F0A7 from the Symbol and Wingdings fonts Word uses for bullets).
BULLET_CHARS = "-\u2013*\u2022\u00b7\u25aa\u25cf\u25e6\u2023\u25cb\u25a0\u25a1\u27a2\u25ba\u2713\u2714\uf0b7\uf0a7\uf076\uf0d8\uf0fc\x7f"


def redact_pii(text: str) -> str:
    """Strip contact details before text leaves our infrastructure (e.g. to an external LLM)."""
    text = _EMAIL.sub("[email]", text)
    text = _URL.sub("[link]", text)
    return _PHONE.sub("[phone]", text)


def clean_text(text: str, limit: int = 20000) -> str:
    return _CONTROL.sub("", text).strip()[:limit]
