from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import batches as Batch 
from app.schema.schema import Batch as BatchBase 
from app.core.authen import get_current_user 

router = APIRouter(prefix="/batches", tags=["batches"])


class BatchUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    coordinator_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None
 

class BatchCreate(BatchBase):
    pass


class BatchRead(BatchBase):
    id: int
    created_at: Optional[datetime]

    class Config:
        orm_mode = True


def _is_admin(user) -> bool:
    return getattr(user, "is_admin", False) or getattr(user, "role", "") == "admin"


@router.post("/", response_model=BatchRead, status_code=status.HTTP_201_CREATED)
def create_batch(
    payload: BatchCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    if not _is_admin(current_user):
        raise HTTPException(status_code=403, detail="Only admin may create batches")

    data = payload.dict(exclude_none=True)

    db_obj = Batch(**data)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


@router.get("/", response_model=List[BatchRead])
def list_batches(db: Session = Depends(get_db)):
    return db.query(Batch).all()


@router.get("/{batch_id}", response_model=BatchRead)
def get_batch(batch_id: int, db: Session = Depends(get_db)):
    obj = db.query(Batch).filter(Batch.id == batch_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Batch not found")
    return obj


@router.put("/{batch_id}", response_model=BatchRead)
def update_batch(
    batch_id: int,
    payload: BatchUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    obj = db.query(Batch).filter(Batch.id == batch_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Batch not found")

    if not _is_admin(current_user):
        raise HTTPException(status_code=403, detail="Only admin may update batches")

    data = payload.dict(exclude_none=True)

    for field, value in data.items():
        setattr(obj, field, value)

    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{batch_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    obj = db.query(Batch).filter(Batch.id == batch_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Batch not found")

    if not _is_admin(current_user):
        raise HTTPException(status_code=403, detail="Only admin may delete batches")

    db.delete(obj)
    db.commit()
    return None
