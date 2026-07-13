from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app import models, schemas

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/pages/{problem_id}", response_model=schemas.KnowledgePageOut)
def get_knowledge_page(problem_id: int, db: Session = Depends(get_db)):
    page = (
        db.query(models.KnowledgePage)
        .filter(models.KnowledgePage.problem_id == problem_id)
        .first()
    )
    if not page:
        raise HTTPException(status_code=404, detail="Knowledge page not found")
    return page
