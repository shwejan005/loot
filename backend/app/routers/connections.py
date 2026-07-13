from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app import models, schemas
from app.services import sync as sync_service

router = APIRouter(prefix="/connections", tags=["connections"])


@router.post("", response_model=schemas.PlatformConnectionOut, status_code=status.HTTP_201_CREATED)
def create_connection(payload: schemas.ConnectionCreate, db: Session = Depends(get_db)):
    if not db.get(models.User, payload.user_id):
        raise HTTPException(status_code=404, detail="User not found")
    conn = models.PlatformConnection(
        user_id=payload.user_id,
        platform=payload.platform,
        external_username=payload.external_username,
    )
    db.add(conn)
    db.commit()
    db.refresh(conn)
    return conn


@router.get("/users/{user_id}", response_model=list[schemas.PlatformConnectionOut])
def list_connections(user_id: int, db: Session = Depends(get_db)):
    if not db.get(models.User, user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return (
        db.query(models.PlatformConnection)
        .filter(models.PlatformConnection.user_id == user_id)
        .all()
    )


@router.post("/sync", status_code=status.HTTP_202_ACCEPTED)
def trigger_sync(db: Session = Depends(get_db)):
    """Manually run one sync pass across all enabled connections."""
    ingested = sync_service.poll_once(db)
    return {"ingested": ingested}
