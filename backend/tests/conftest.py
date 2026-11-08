import os
import tempfile
from pathlib import Path

_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["LLM_PROVIDER"] = "mock"
os.environ["ADZUNA_APP_ID"] = ""   # tests use the sample jobs; a developer's .env key is ignored
os.environ["ADZUNA_APP_KEY"] = ""
os.environ["LEARNING_MSLEARN"] = "false"  # tests never call live learning APIs
os.environ["YOUTUBE_API_KEY"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

SAMPLES = Path(__file__).resolve().parents[1] / "samples"


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


_counter = {"n": 0}


@pytest.fixture
def user(client):
    """A freshly registered user: returns (headers, email)."""
    _counter["n"] += 1
    email = f"user{_counter['n']}@example.com"
    r = client.post("/api/v1/auth/register", json={"email": email, "password": "password123", "name": "Test User"})
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}, email


@pytest.fixture
def stranger(client):
    """A different registered user, for ownership/isolation tests."""
    _counter["n"] += 1
    r = client.post("/api/v1/auth/register", json={"email": f"stranger{_counter['n']}@example.com", "password": "password123"})
    return {"Authorization": f"Bearer {r.json()['token']}"}


@pytest.fixture
def uploaded(client, user):
    """A user who has uploaded the sample DOCX CV."""
    headers, _ = user
    with open(SAMPLES / "sample_cv.docx", "rb") as f:
        r = client.post("/api/v1/profile/upload", headers=headers, files={"file": ("sample_cv.docx", f)})
    assert r.status_code == 201, r.text
    return headers, r.json()
