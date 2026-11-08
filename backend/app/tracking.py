"""LLMOps run tracking: every agent execution is timed and logged to `agent_runs`.

llm_source says what produced an agent's output:
  rules             - deterministic code (scoring formulas, taxonomy matching, API retrieval); no LLM involved
  llm               - text written by the language model
  template          - an LLM-capable agent ran without a model configured (LLM_PROVIDER=mock)
  template-fallback - the model call failed, so the agent used its built-in template
"""
import time
from contextlib import contextmanager

from sqlalchemy.orm import Session

from .models import AgentRun


@contextmanager
def tracked(db: Session, user_id: int, agent: str, trace: list | None = None):
    step = {"agent": agent, "status": "ok", "note": "", "llm_source": "rules"}
    t0 = time.perf_counter()
    try:
        yield step
    except Exception as exc:
        db.rollback()
        step["status"], step["note"] = "error", str(exc)[:250]
        raise
    finally:
        step["duration_ms"] = int((time.perf_counter() - t0) * 1000)
        db.add(AgentRun(user_id=user_id, agent=agent, status=step["status"], duration_ms=step["duration_ms"],
                        llm_source=step["llm_source"], note=step["note"][:300]))
        db.commit()
        if trace is not None:
            trace.append(dict(step))
