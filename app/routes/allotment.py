from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import batches, teachers
from app.models.models import batch_teachers
from app.schema import BatchTeacherCreate, BatchTeacherRead
from app.core.authen import get_current_user

router = APIRouter(prefix="/allotment", tags=["allotment"])

def _is_admin(user):
    return getattr(user, "role", "") == "admin"


@router.post("/", response_model=BatchTeacherRead)
def allot_teacher_to_batch(
    payload: BatchTeacherCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if not _is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin only")

    batch = db.query(batches).filter(batches.id == payload.batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    teacher = db.query(teachers).filter(teachers.id == payload.teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    existing = db.query(batch_teachers).filter(
        batch_teachers.batch_id == payload.batch_id,
        batch_teachers.teacher_id == payload.teacher_id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Teacher already allotted to this batch")

    row = batch_teachers(
        batch_id=payload.batch_id,
        teacher_id=payload.teacher_id
    )

    db.add(row)
    db.commit()
    db.refresh(row)
    return BatchTeacherRead.model_validate(row)
