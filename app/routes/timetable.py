from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import timetable_slots, teachers, batches, subjects, students
from app.schema import SlotCreate, SlotUpdate, SlotRead
from app.core.authen import get_current_user

router = APIRouter(prefix="/timetable", tags=["timetable"])



def _is_admin(u): return getattr(u, "role", "") == "admin"
def _is_teacher(u): return getattr(u, "role", "") == "teacher"


@router.post("/teachers/{teacher_id}", response_model=SlotRead)
def create_slot(teacher_id: int, payload: SlotCreate, db: Session = Depends(get_db)):
    t = db.query(teachers).filter(teachers.id == teacher_id).first()
    if not t: raise HTTPException(404, "Teacher not found")
    c = db.query(batches).filter(batches.id == payload.class_id).first()
    if not c: raise HTTPException(404, "Class not found")
    s = db.query(subjects).filter(subjects.id == payload.subject_id).first()
    if not s: raise HTTPException(404, "Subject not found")

    conflict = db.query(timetable_slots).filter(
        timetable_slots.class_id == payload.class_id,
        timetable_slots.day == payload.day,
        timetable_slots.start_time == payload.start_time
    ).first()
    if conflict:
        raise HTTPException(400, "Slot already exists for this class at this time")

    row = timetable_slots(
        teacher_id=teacher_id,
        class_id=payload.class_id,
        subject_id=payload.subject_id,
        day=payload.day,
        start_time=payload.start_time,
        end_time=payload.end_time
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return SlotRead.model_validate(row)


@router.get("/teachers/me", response_model=List[SlotRead])
def get_my_slots(day: Optional[str] = None, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    tr = db.query(teachers).filter(teachers.user_id == current_user.id).first()
    if not tr: raise HTTPException(404, "Teacher not found")

    q = db.query(timetable_slots).filter(timetable_slots.teacher_id == tr.id)
    if day: q = q.filter(timetable_slots.day == day)
    rows = q.order_by(timetable_slots.day, timetable_slots.start_time).all()
    return [SlotRead.model_validate(r) for r in rows]


@router.get("/classes/me", response_model=List[SlotRead])
def get_class_slots(day: Optional[str] = None, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    st = db.query(students).filter(students.user_id == current_user.id).first()
    if not st: raise HTTPException(404, "Student not found")

    class_id = getattr(st, "class_id", None)
    if not class_id: raise HTTPException(400, "Student has no class")

    q = db.query(timetable_slots).filter(timetable_slots.class_id == class_id)
    if day: q = q.filter(timetable_slots.day == day)
    rows = q.order_by(timetable_slots.day, timetable_slots.start_time).all()
    return [SlotRead.model_validate(r) for r in rows]


@router.get("/{slot_id}", response_model=SlotRead)
def get_slot(slot_id: int, db: Session = Depends(get_db)):
    row = db.query(timetable_slots).filter(timetable_slots.id == slot_id).first()
    if not row: raise HTTPException(404, "Slot not found")
    return SlotRead.model_validate(row)


@router.put("/{slot_id}", response_model=SlotRead)
def update_slot(slot_id: int, payload: SlotUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    row = db.query(timetable_slots).filter(timetable_slots.id == slot_id).first()
    if not row: raise HTTPException(404, "Slot not found")

    teacher_owner = db.query(teachers).filter(teachers.id == row.teacher_id).first()
    if not (_is_admin(current_user) or (teacher_owner and teacher_owner.user_id == current_user.id)):
        raise HTTPException(403, "Not allowed")

    data = payload.dict(exclude_none=True)
    for k, v in data.items():
        setattr(row, k, v)

    db.commit()
    db.refresh(row)
    return SlotRead.model_validate(row)


@router.delete("/{slot_id}")
def delete_slot(slot_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    row = db.query(timetable_slots).filter(timetable_slots.id == slot_id).first()
    if not row: raise HTTPException(404, "Slot not found")

    teacher_owner = db.query(teachers).filter(teachers.id == row.teacher_id).first()
    if not (_is_admin(current_user) or (teacher_owner and teacher_owner.user_id == current_user.id)):
        raise HTTPException(403, "Not allowed")

    db.delete(row)
    db.commit()
    return {"message": "Deleted"}
