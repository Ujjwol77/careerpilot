"""Interview Coach Agent: role-specific technical + behavioural questions and answer feedback."""
import random
import re

from ..data.interview_bank import BEHAVIOURAL, ROLE_QUESTIONS, SKILL_QUESTIONS
from ..data.seed_jobs import ROLE_PROFILES
from ..llm import try_llm
from ..taxonomy import display

STAR = {
    "situation": ["when", "situation", "project", "team", "during", "at my", "last year"],
    "task": ["needed to", "responsible", "goal", "task", "objective", "had to", "challenge"],
    "action": ["i built", "i created", "i led", "i decided", "implemented", "designed", "analysed", "i wrote", "i organised", "i asked"],
    "result": ["result", "reduced", "increased", "improved", "saved", "delivered", "learned", "outcome", "%"],
}


def build_questions(role: str, gap_slugs: list[str], have_slugs: list[str], n_tech: int = 4, n_beh: int = 3, seed: int | None = None) -> list[dict]:
    rng = random.Random(seed)
    tech: list[dict] = []
    # Prioritise questions on skills the user is missing (they'll be asked about them), then strengths.
    for slug in gap_slugs + have_slugs:
        for q, kw in SKILL_QUESTIONS.get(slug, []):
            if len(tech) < n_tech and q not in {t["question"] for t in tech}:
                tech.append({"type": "technical", "skill": display(slug), "question": q, "keywords": kw})
    for q, kw in ROLE_QUESTIONS.get(role, []):
        if len(tech) < n_tech:
            tech.append({"type": "technical", "skill": ROLE_PROFILES.get(role, {}).get("label", role), "question": q, "keywords": kw})
    beh = [{"type": "behavioural", "skill": "STAR", "question": q, "keywords": []} for q in rng.sample(BEHAVIOURAL, n_beh)]
    return tech + beh


def evaluate_answer(question: dict, answer: str, role: str) -> dict:
    text = answer.lower()
    words = len(answer.split())
    tips: list[str] = []
    if question["type"] == "behavioural":
        hits = {k: any(w in text for w in v) for k, v in STAR.items()}
        score = sum(2 for v in hits.values() if v) + (2 if words >= 60 else 1 if words >= 30 else 0)
        for part, ok in hits.items():
            if not ok:
                tips.append(f"Add the {part.upper()} of your story ({'what was happening' if part == 'situation' else 'what you were responsible for' if part == 'task' else 'what you personally did' if part == 'action' else 'the measurable outcome'}).")
        detail = {"star": hits}
    else:
        kws = question["keywords"]
        found = [k for k in kws if k in text]
        coverage = len(found) / max(len(kws), 1)
        reasoning = any(w in text for w in ["because", "for example", "trade-off", "however", "so that", "e.g"])
        score = round(6 * coverage + (2 if words >= 40 else 1 if words >= 20 else 0) + (2 if reasoning else 0))
        missing = [k for k in kws if k not in text][:4]
        if missing:
            tips.append(f"Cover key ideas such as: {', '.join(missing)}.")
        if not reasoning:
            tips.append("Explain why, with a short example or trade-off.")
        detail = {"keywords_found": found}
    if words < 20:
        tips.append("Your answer is very short; aim for 4 to 6 sentences.")
    score = max(0, min(10, score))
    fallback = ("Strength: " + ("clear structure." if score >= 6 else "you attempted the question.") + " Next: " + (tips[0] if tips else "keep practising with new examples."))
    feedback, source = try_llm("interview_feedback.v1", fallback, role=role, question=question["question"], answer=answer)
    return {"score": score, "tips": tips, "feedback": feedback, "feedback_source": source, "detail": detail}


def preparation_plan(role: str, gaps: list[str]) -> dict:
    label = ROLE_PROFILES.get(role, {}).get("label", "your target role")
    return {
        "focus_areas": gaps[:4] or ["Review fundamentals for " + label],
        "schedule": [
            "Session 1: answer two technical questions out loud, then review the gaps",
            "Session 2: prepare three STAR stories (learning fast, teamwork, a mistake)",
            "Session 3: full mock interview in the Interview tab; repeat until every answer scores 7+",
        ],
        "tips": ["Use real numbers in results", "Keep answers to about 90 seconds", "Prepare two questions to ask the interviewer"],
    }
