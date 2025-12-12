from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.db.session import get_db
from app.models.models import users, enrollments, batches  
from app.schema import EnrollmentCreate, EnrollmentUpdate, EnrollmentRead, StudentRead

router = APIRouter(prefix="/students", tags=["students"])


def _enrollment_to_response(e_row) -> EnrollmentRead:
    return EnrollmentRead(
        id=e_row.id,
        batch_id=e_row.batch_id,
        student_id=e_row.student_id,
        joined_at=e_row.joined_at,
        is_active=e_row.is_active,
        role_in_batch=e_row.role_in_batch,
    )


@router.post("/{user_id}/enroll", response_model=EnrollmentRead, status_code=status.HTTP_201_CREATED)
def enroll_student(user_id: int, payload: EnrollmentCreate, db: Session = Depends(get_db)):

        user = db.query(users).filter(users.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        batch = db.query(batches).filter(batches.id == payload.batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")

        existing = db.query(enrollments).filter(
            enrollments.batch_id == payload.batch_id,
            enrollments.student_id == user_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="User already enrolled in this batch")

        enroll_row = enrollments(
            batch_id=payload.batch_id,
            student_id=user_id,
            role_in_batch=payload.role_in_batch or "student"
        )
        db.add(enroll_row)
        db.commit()
        db.refresh(enroll_row)
        return _enrollment_to_response(enroll_row)


@router.get("/user/{user_id}", response_model=StudentRead)
def get_student_by_user(user_id: int, db: Session = Depends(get_db)):
  
        user = db.query(users).filter(users.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        rows = db.query(enrollments).filter(enrollments.student_id == user_id).all()
        enrolls = [_enrollment_to_response(r) for r in rows]

        return StudentRead(
            id=user.id,
            email=user.email,
            full_name=getattr(user, "full_name", None),
            role=getattr(user, "role", None),
            enrollments=enrolls,
        )



@router.get("/enrollments/{enrollment_id}", response_model=EnrollmentRead)
def get_enrollment(enrollment_id: int, db: Session = Depends(get_db)):
    try:
        e = db.query(enrollments).filter(enrollments.id == enrollment_id).first()
        if not e:
            raise HTTPException(status_code=404, detail="Enrollment not found")
        return _enrollment_to_response(e)
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=List[StudentRead])
def list_students(db: Session = Depends(get_db)):

        rows = db.query(enrollments).all()
        student_ids = sorted({r.student_id for r in rows})

        result: List[StudentRead] = []
        for sid in student_ids:
            user = db.query(users).filter(users.id == sid).first()
            if not user:
                continue
            user_enrolls = db.query(enrollments).filter(enrollments.student_id == sid).all()
            result.append(
                StudentRead(
                    id=user.id,
                    email=user.email,
                    full_name=getattr(user, "full_name", None),
                    role=getattr(user, "role", None),
                    enrollments=[_enrollment_to_response(er) for er in user_enrolls],
                )
            )
        return result


@router.put("/enrollments/{enrollment_id}", response_model=EnrollmentRead)
def update_enrollment(enrollment_id: int, payload: EnrollmentUpdate, db: Session = Depends(get_db)):

        e = db.query(enrollments).filter(enrollments.id == enrollment_id).first()
        if not e:
            raise HTTPException(status_code=404, detail="Enrollment not found")

        if payload.is_active is not None:
            e.is_active = payload.is_active
        if payload.role_in_batch is not None:
            e.role_in_batch = payload.role_in_batch

        db.add(e)
        db.commit()
        db.refresh(e)
        return _enrollment_to_response(e)


@router.delete("/enrollments/{enrollment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_enrollment(enrollment_id: int, db: Session = Depends(get_db)):

        e = db.query(enrollments).filter(enrollments.id == enrollment_id).first()
        if not e:
            raise HTTPException(status_code=404, detail="Enrollment not found")
        db.delete(e)
        db.commit()
        return None

