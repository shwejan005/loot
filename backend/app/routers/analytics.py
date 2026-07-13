from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app import models

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/users/{user_id}/readiness")
def interview_readiness(user_id: int, db: Session = Depends(get_db)):
    if not db.get(models.User, user_id):
        raise HTTPException(status_code=404, detail="User not found")

    solved = (
        db.query(func.count(models.Submission.id))
        .filter(models.Submission.user_id == user_id, models.Submission.accepted == True)  # noqa: E712
        .scalar()
    )
    analyzed = (
        db.query(func.count(models.SubmissionAnalysis.id))
        .join(models.Submission, models.SubmissionAnalysis.submission_id == models.Submission.id)
        .filter(models.Submission.user_id == user_id)
        .scalar()
    )
    topics_covered = (
        db.query(func.count(func.distinct(models.problem_topics.c.topic_id)))
        .join(models.Problem, models.problem_topics.c.problem_id == models.Problem.id)
        .join(models.Submission, models.Submission.problem_id == models.Problem.id)
        .filter(models.Submission.user_id == user_id, models.Submission.accepted == True)  # noqa: E712
        .scalar()
    )

    # Readiness: coverage of analysis and topic breadth (simple composite score).
    coverage = (analyzed / solved) if solved else 0.0
    breadth = min(topics_covered / 15.0, 1.0)
    readiness = round((0.6 * coverage + 0.4 * breadth) * 100, 1)

    return {
        "user_id": user_id,
        "solved_count": solved,
        "analyzed_count": analyzed,
        "topics_covered": topics_covered,
        "readiness_score": readiness,
    }
