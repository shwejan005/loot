from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app import models, schemas
from app.ai.analyzer import analyze_submission

router = APIRouter(prefix="/submissions", tags=["submissions"])


@router.post("", response_model=schemas.SubmissionOut, status_code=status.HTTP_201_CREATED)
def create_submission(payload: schemas.SubmissionCreate, db: Session = Depends(get_db)):
    if not db.get(models.User, payload.user_id):
        raise HTTPException(status_code=404, detail="User not found")
    if not db.get(models.Problem, payload.problem_id):
        raise HTTPException(status_code=404, detail="Problem not found")
    submission = models.Submission(**payload.model_dump())
    db.add(submission)
    db.commit()
    db.refresh(submission)

    # Automatically analyze accepted submissions.
    if submission.accepted:
        analyze_submission(db, submission)
    return submission


@router.get("/{submission_id}", response_model=schemas.SubmissionOut)
def get_submission(submission_id: int, db: Session = Depends(get_db)):
    submission = db.get(models.Submission, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return submission
