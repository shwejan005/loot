"""Background synchronization worker.

Polls each user's connected coding platforms for recently accepted submissions,
normalizes them, upserts them into the Loot knowledge store, and triggers AI
analysis. Intended to run as a long-lived process (or a Celery/Redis worker in
production); here it is structured as a standalone loop for local runs.
"""

import logging
import time
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.db import SessionLocal
from app import models
from app.ai.analyzer import analyze_submission
from app.platforms.base import NormalizedSubmission
from app.platforms.registry import build_client

logger = logging.getLogger("loot.sync")


def _upsert_topics(db: Session, names: list[str]) -> list[models.Topic]:
    topics: list[models.Topic] = []
    for name in names:
        name = name.strip()
        if not name:
            continue
        topic = db.query(models.Topic).filter(models.Topic.name == name).first()
        if topic is None:
            topic = models.Topic(name=name)
            db.add(topic)
            db.flush()
        topics.append(topic)
    return topics


def ingest_submission(
    db: Session, user_id: int, platform: str, norm: NormalizedSubmission
) -> bool:
    """Upsert a normalized submission. Returns True if a new row was created."""
    existing = (
        db.query(models.Submission)
        .filter(
            models.Submission.user_id == user_id,
            models.Submission.external_submission_id == norm.external_id,
        )
        .first()
    )
    if existing:
        return False

    problem = _get_or_create_problem_for_platform(db, user_id, platform, norm)
    submission = models.Submission(
        user_id=user_id,
        problem_id=problem.id,
        external_submission_id=norm.external_id,
        language=norm.language,
        source_code=norm.source_code,
        runtime_ms=norm.runtime_ms,
        memory_kb=norm.memory_kb,
        accepted=norm.accepted,
        submitted_at=norm.submitted_at,
    )
    db.add(submission)
    db.flush()

    if norm.accepted:
        analyze_submission(db, submission)
    return True


def _get_or_create_problem_for_platform(
    db: Session, user_id: int, platform: str, norm: NormalizedSubmission
) -> models.Problem:
    problem = (
        db.query(models.Problem)
        .filter(
            models.Problem.platform == platform,
            models.Problem.external_id == norm.external_problem_id,
        )
        .first()
    )
    if problem is None:
        problem = models.Problem(
            platform=platform,
            external_id=norm.external_problem_id,
            title=norm.title,
            difficulty=norm.difficulty,
            url=norm.url,
        )
        db.add(problem)
        db.flush()
    else:
        if problem.difficulty is None and norm.difficulty:
            problem.difficulty = norm.difficulty
        if problem.url is None and norm.url:
            problem.url = norm.url

    for topic in _upsert_topics(db, norm.topics):
        if topic not in problem.topics:
            problem.topics.append(topic)
    return problem


def sync_connection(db: Session, conn: models.PlatformConnection) -> int:
    """Sync a single platform connection. Returns count of new submissions."""
    if not conn.enabled:
        return 0
    try:
        client = build_client(conn)
    except ValueError as exc:
        logger.warning("Skipping connection %s: %s", conn.id, exc)
        return 0

    try:
        norms = client.fetch_recent(count=settings.sync_batch_size)
    except Exception as exc:  # pragma: no cover - network dependent
        logger.exception("Failed to fetch from %s: %s", conn.platform, exc)
        return 0

    ingested = 0
    for norm in norms:
        try:
            if ingest_submission(db, conn.user_id, conn.platform, norm):
                ingested += 1
        except Exception as exc:  # pragma: no cover - keep processing the rest
            logger.exception("Failed to ingest submission %s: %s", norm.external_id, exc)

    conn.last_synced_at = datetime.now(timezone.utc)
    db.commit()
    return ingested


def poll_once(db: Session) -> int:
    """Iterate all enabled connections and sync them."""
    connections = db.query(models.PlatformConnection).all()
    total = 0
    for conn in connections:
        total += sync_connection(db, conn)
    return total


def run_forever() -> None:
    logger.info("Starting Loot sync worker (interval=%ss)", settings.sync_poll_interval_seconds)
    while True:
        try:
            with SessionLocal() as db:
                count = poll_once(db)
            if count:
                logger.info("Ingested %d new submissions", count)
        except Exception as exc:  # pragma: no cover - keep worker alive
            logger.exception("Sync iteration failed: %s", exc)
        time.sleep(settings.sync_poll_interval_seconds)


if __name__ == "__main__":
    run_forever()
