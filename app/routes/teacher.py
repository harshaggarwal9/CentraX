from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import users, teachers
from app.schema import TeacherCreate, TeacherUpdate, TeacherRead

router = APIRouter(prefix="/teachers", tags=["teachers"])

@router.post("/{user_id}", response_model=TeacherRead)
def create_teacher(user_id: int, payload: TeacherCreate, db: Session = Depends(get_db)):

    user = db.query(users).filter(users.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    if user.role != "teacher":
        raise HTTPException(400, "This user is not a teacher")

    existing = db.query(teachers).filter(teachers.user_id == user_id).first()
    if existing:
        raise HTTPException(400, "Teacher profile already exists")

    teacher = teachers(
        user_id=user_id,
        subjects=",".join(payload.subjects),
        experience=payload.experience,
        qualifications=payload.qualifications,
    )

    db.add(teacher)
    db.commit()
    db.refresh(teacher)

    return TeacherRead(
        id=teacher.id,
        user_id=user_id,
        subjects=teacher.subjects.split(",") if teacher.subjects else [],
        experience=teacher.experience,
        qualifications=teacher.qualifications,
        created_at=teacher.created_at,
    )

@router.get("/user/{user_id}", response_model=TeacherRead)
def get_teacher(user_id: int, db: Session = Depends(get_db)):

    teacher = db.query(teachers).filter(teachers.user_id == user_id).first()
    if not teacher:
        raise HTTPException(404, "Teacher not found")

    return TeacherRead(
        id=teacher.id,
        user_id=teacher.user_id,
        subjects=teacher.subjects.split(",") if teacher.subjects else [],
        experience=teacher.experience,
        qualifications=teacher.qualifications,
        created_at=teacher.created_at,
    )


@router.get("/", response_model=list[TeacherRead])
def list_teachers(db: Session = Depends(get_db)):

    teachers_list = db.query(teachers).all()

    return [
        TeacherRead(
            id=t.id,
            user_id=t.user_id,
            subjects=t.subjects.split(",") if t.subjects else [],
            experience=t.experience,
            qualifications=t.qualifications,
            created_at=t.created_at,
        )
        for t in teachers_list
    ]


@router.put("/{teacher_id}", response_model=TeacherRead)
def update_teacher(teacher_id: int, payload: TeacherUpdate, db: Session = Depends(get_db)):

    teacher = db.query(teachers).filter(teachers.id == teacher_id).first()
    if not teacher:
        raise HTTPException(404, "Teacher not found")

    if payload.subjects is not None:
        teacher.subjects = ",".join(payload.subjects)

    if payload.experience is not None:
        teacher.experience = payload.experience

    if payload.qualifications is not None:
        teacher.qualifications = payload.qualifications

    db.commit()
    db.refresh(teacher)

    return TeacherRead(
        id=teacher.id,
        user_id=teacher.user_id,
        subjects=teacher.subjects.split(",") if teacher.subjects else [],
        experience=teacher.experience,
        qualifications=teacher.qualifications,
        created_at=teacher.created_at,
    )


@router.delete("/{teacher_id}", status_code=204)
def delete_teacher(teacher_id: int, db: Session = Depends(get_db)):

    teacher = db.query(teachers).filter(teachers.id == teacher_id).first()
    if not teacher:
        raise HTTPException(404, "Teacher not found")

    db.delete(teacher)
    db.commit()

    return None