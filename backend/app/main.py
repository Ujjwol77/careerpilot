from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import func, inspect, select, text

from .config import settings
from .data.seed_jobs import build_seed_jobs
from .db import Base, SessionLocal, engine
from .models import Job
from .routers import analysis, applications, auth, jobs, ops, profile, report


def seed_jobs() -> None:
    with SessionLocal() as db:
        if db.scalar(select(func.count()).select_from(Job)) == 0:
            db.add_all(Job(**j) for j in build_seed_jobs())
            db.commit()


def add_missing_columns() -> None:
    """create_all() never alters existing tables, so add columns introduced after a DB was created."""
    new_cols = {"jobs": {"url": "VARCHAR(500) DEFAULT ''", "external_id": "VARCHAR(80) DEFAULT ''"}}
    insp = inspect(engine)
    with engine.begin() as conn:
        for table, cols in new_cols.items():
            if not insp.has_table(table):
                continue
            have = {c["name"] for c in insp.get_columns(table)}
            for name, ddl in cols.items():
                if name not in have:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    add_missing_columns()
    seed_jobs()
    yield


app = FastAPI(title="CareerPilot API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins), allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(HTTPException)
async def http_error(_: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, dict) else {"code": "ERROR", "message": str(exc.detail)}
    return JSONResponse(status_code=exc.status_code, content={"error": detail})


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError):
    first = exc.errors()[0] if exc.errors() else {}
    field = ".".join(str(x) for x in first.get("loc", []) if x not in ("body", "query"))
    message = f"{field}: {first.get('msg', 'invalid value')}" if field else first.get("msg", "Invalid request.")
    return JSONResponse(status_code=422, content={"error": {"code": "VALIDATION_ERROR", "message": message}})


@app.get("/health")
def health():
    return {"status": "ok"}


for r in (auth, profile, jobs, analysis, applications, report, ops):
    app.include_router(r.router, prefix="/api/v1")
