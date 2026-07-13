import json
import logging

from sqlalchemy.orm import Session

from app import models
from app.config import settings

logger = logging.getLogger("loot.ai")


def _embed(text: str) -> list[float]:
    """Generate an embedding vector for retrieval-based personalization.

    Returns an empty list when no API key is configured (local/dev fallback).
    """
    if not settings.openai_api_key:
        return []
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        resp = client.embeddings.create(model=settings.embedding_model, input=text[:8000])
        return resp.data[0].embedding
    except Exception as exc:  # pragma: no cover - network dependent
        logger.warning("Embedding failed: %s", exc)
        return []


def _explain(submission: models.Submission, problem: models.Problem) -> dict:
    """Generate an AI explanation based on the user's exact implementation.

    Falls back to a heuristic template when no API key is configured.
    """
    code = (submission.source_code or "").strip()
    if settings.openai_api_key:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=settings.openai_api_key)
            prompt = (
                "Explain the following accepted coding solution for the problem "
                f"'{problem.title}'. Identify the approach, time/space complexity, "
                "the key insight, and any likely mistakes. Be concise.\n\n"
                f"Language: {submission.language}\nCode:\n{code}"
            )
            resp = client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            text = resp.choices[0].message.content or ""
            return _parse_explanation(text)
        except Exception as exc:  # pragma: no cover - network dependent
            logger.warning("Explanation generation failed: %s", exc)

    return {
        "approach": "Heuristic analysis (no AI key configured).",
        "time_complexity": "unknown",
        "space_complexity": "unknown",
        "key_insight": f"Solved '{problem.title}' in {submission.language}.",
        "mistake_notes": "",
    }


def _parse_explanation(text: str) -> dict:
    out = {
        "approach": text,
        "time_complexity": "unknown",
        "space_complexity": "unknown",
        "key_insight": "",
        "mistake_notes": "",
    }
    for key, label in [
        ("time_complexity", "Time"),
        ("space_complexity", "Space"),
        ("key_insight", "Insight"),
        ("mistake_notes", "Mistake"),
    ]:
        for line in text.splitlines():
            if line.lower().startswith(label.lower()) and ":" in line:
                out[key] = line.split(":", 1)[1].strip()
    return out


def analyze_submission(db: Session, submission: models.Submission) -> models.SubmissionAnalysis:
    """Analyze an accepted submission and persist the structured result."""
    problem = db.get(models.Problem, submission.problem_id)
    explanation = _explain(submission, problem)
    vector = _embed((submission.source_code or "") + " " + (explanation.get("approach") or ""))

    analysis = models.SubmissionAnalysis(
        submission_id=submission.id,
        approach=explanation["approach"],
        time_complexity=explanation["time_complexity"],
        space_complexity=explanation["space_complexity"],
        key_insight=explanation["key_insight"],
        mistake_notes=explanation["mistake_notes"],
        embedding=json.dumps(vector),
    )
    db.add(analysis)

    # Ensure a knowledge page exists for this problem.
    if problem and not problem.knowledge_page:
        page = models.KnowledgePage(
            problem_id=problem.id,
            explanation=explanation["approach"],
            revision_notes=explanation["key_insight"],
        )
        db.add(page)

    db.commit()
    db.refresh(analysis)
    return analysis
